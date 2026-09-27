/**
 * compiler.js — AST compiler for structured trace naming.
 *
 * This is the JS port of Python PTO's compiled_names/compiler.py.
 * It transforms a generator function's source code so that every rnd.X()
 * call gets an injected `{ name: ... }` argument with a hierarchical
 * structural name derived from the code location.
 *
 * Why structural names?
 * ---------------------
 * With linear naming (integer keys 0, 1, 2, ...), the trace is a flat
 * sequence. Crossover and mutation operate blindly — they don't know that
 * entry 5 and entry 6 were produced in the same loop iteration, or that
 * entries 0-9 form one logical group. Structural names encode the program
 * flow, enabling operators that respect the solution's structure.
 *
 * Name format:
 *   root/<funcName>@<line>.<col>/<loopType>@<line>.<col>:<iter>/.../<method>@<line>.<col>
 *
 * Example:
 *   root/generator@1.0/for@3.4:0/choice@4.8
 *   root/generator@1.0/for@3.4:1/choice@4.8
 *
 * Transformation rules:
 * ---------------------
 * 1. rnd.X(args)       → rnd.X(args, { name: <nameExpr> })
 * 2. loops (for, for-in, for-of, while, do-while) → inject counter, prefix save/restore
 * 3. callbacks of array iteration methods (xs.map(cb), Array.from(xs, cb),
 *    forEach, filter, reduce, ...) → name segment from the callback's index
 * 4. Nested functions   → thread __prefix__ parameter (also when passed by
 *    name as such a callback, eg xs.map(helper))
 * 5. Top-level function → inject __prefix__ = "root/..." preamble
 *
 * Statements inside if/else, switch, try/catch/finally and labelled
 * statements are transformed too. Each executed rnd call must get a unique
 * name; the tracer throws if a name repeats. Not supported: nested functions
 * used as values other than such callbacks, and callbacks whose index
 * parameter is a destructuring pattern.
 *
 * Uses Acorn for parsing and astring for code generation. Acorn provides
 * line/column location on every AST node when parsed with `locations: true`.
 *
 * Usage:
 *   import { compileGenerator } from './compiler.js';
 *
 *   const compiled = compileGenerator(
 *     (rnd) => { ... },       // original generator
 *   );
 *   // compiled._originalSource and compiled._compiledSource available
 */

import * as acorn from 'acorn';
import { generate } from 'astring';

// ---------------------------------------------------------------------------
// AST builder helpers — create ESTree-compliant nodes
// ---------------------------------------------------------------------------

function ident(name) {
  return { type: 'Identifier', name };
}

function literal(value) {
  return { type: 'Literal', value, raw: JSON.stringify(value) };
}

function binop(op, left, right) {
  return { type: 'BinaryExpression', operator: op, left, right };
}

function assign(name, value) {
  return {
    type: 'ExpressionStatement',
    expression: {
      type: 'AssignmentExpression',
      operator: '=',
      left: ident(name),
      right: value,
    },
  };
}

function callExpr(callee, args) {
  return { type: 'CallExpression', callee, arguments: args, optional: false };
}

function memberExpr(obj, prop) {
  return { type: 'MemberExpression', object: obj, property: prop, computed: false, optional: false };
}

function strConcat(...parts) {
  // Build a + b + c + ... chain
  let result = parts[0];
  for (let i = 1; i < parts.length; i++) {
    result = binop('+', result, parts[i]);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Name expression builder
// ---------------------------------------------------------------------------

/**
 * Build an expression: __prefix__ + compSegments + "/<label>@<line>.<col>"
 *
 * @param {string} label     Method name or loop type
 * @param {object} loc       { line, column } from Acorn node.loc.start
 * @param {Array}  compSegs  Stack of [label, line, col, counterVar] for comprehensions
 * @returns {object} ESTree expression node
 */
function makeNameExpr(label, loc, compSegs = []) {
  let expr = ident('__prefix__');

  for (const [segLabel, segLine, segCol, segVar] of compSegs) {
    expr = strConcat(
      expr,
      literal(`/${segLabel}@${segLine}.${segCol}:`),
      callExpr(ident('String'), [ident(segVar)]),
    );
  }

  expr = strConcat(expr, literal(`/${label}@${loc.line}.${loc.column}`));
  return expr;
}

/**
 * Build: __prefix__ = <saveVar> + "/<label>@<line>.<col>:" + String(<counterVar>)
 */
function makePrefixUpdate(saveVar, label, loc, counterVar) {
  return assign('__prefix__', strConcat(
    ident(saveVar),
    literal(`/${label}@${loc.line}.${loc.column}:`),
    callExpr(ident('String'), [ident(counterVar)]),
  ));
}

function makeSave(saveVar) {
  return {
    type: 'VariableDeclaration',
    declarations: [{
      type: 'VariableDeclarator',
      id: ident(saveVar),
      init: ident('__prefix__'),
    }],
    kind: 'let',
  };
}

function makeRestore(saveVar) {
  return assign('__prefix__', ident(saveVar));
}

// ---------------------------------------------------------------------------
// Variable name helpers (unique per location)
// ---------------------------------------------------------------------------

function counterVar(loc) {
  return `__c_L${loc.line}_${loc.column}__`;
}

function saveVar(loc) {
  return `__ps_L${loc.line}_${loc.column}__`;
}

// ---------------------------------------------------------------------------
// Array iteration methods
// ---------------------------------------------------------------------------

/** Methods that call their first argument once per element, and the position of the index parameter. */
const ITERATION_METHODS = {
  map: 1, forEach: 1, flatMap: 1, filter: 1, some: 1, every: 1,
  find: 1, findIndex: 1, findLast: 1, findLastIndex: 1,
  reduce: 2, reduceRight: 2,
};

/**
 * If node is a call like xs.map(cb) or Array.from(xs, cb), return
 * { label, argIndex, indexPos }: the method name, which argument is the
 * callback, and which callback parameter receives the element index.
 */
function iterationCallback(node) {
  const callee = node.callee;
  if (callee.type !== 'MemberExpression' || callee.computed || callee.property.type !== 'Identifier') {
    return null;
  }
  const method = callee.property.name;
  if (method === 'from' && callee.object.type === 'Identifier' && callee.object.name === 'Array') {
    return { label: 'from', argIndex: 1, indexPos: 1 };
  }
  if (Object.hasOwn(ITERATION_METHODS, method)) {
    return { label: method, argIndex: 0, indexPos: ITERATION_METHODS[method] };
  }
  return null;
}

// ---------------------------------------------------------------------------
// AST Walker / Transformer
// ---------------------------------------------------------------------------

/**
 * Transform a generator function's AST to inject structural names.
 *
 * This is a recursive walk that modifies the AST in place, mirroring
 * the Python NameCompiler class. The key differences from Python:
 *
 * - JS doesn't have list comprehensions as a distinct AST node. Instead,
 *   we detect patterns like `Array.from({length: n}, (_, i) => ...)` and
 *   `arr.map((x, i) => ...)` and treat them like comprehensions.
 *
 * - For/while/nested functions work the same conceptually.
 *
 * - The generator receives `rnd` as a parameter (not a global import),
 *   so we look for `rnd.X()` calls on the parameter name.
 */
class NameCompiler {
  constructor() {
    this.funcDepth = 0;
    this.nestedFuncNames = new Set();
    this.compSegments = [];
    this.rndParamName = 'rnd'; // default, detected from function params
  }

  /**
   * Main entry: transform a function body.
   */
  compile(funcNode) {
    // Detect the rnd parameter name (first param of arrow/function)
    if (funcNode.params && funcNode.params.length > 0) {
      const first = funcNode.params[0];
      if (first.type === 'Identifier') {
        this.rndParamName = first.name;
      }
    }

    // An arrow function with an expression body, eg (rnd) => [rnd.random()],
    // gets a block body so that the __prefix__ preamble can be added
    if (funcNode.body.type !== 'BlockStatement') {
      funcNode.body = {
        type: 'BlockStatement',
        body: [{ type: 'ReturnStatement', argument: funcNode.body }],
      };
      funcNode.expression = false;
    }

    this.funcDepth = 1;
    this._collectNestedFuncs(funcNode);
    this._walkBody(funcNode);

    // Inject __prefix__ preamble at start of function body
    const loc = this._pos(funcNode);
    const funcName = funcNode.id ? funcNode.id.name : 'generator';
    const preamble = this._makeVarDecl('__prefix__', literal(`root/${funcName}@${loc.line}.${loc.column}`));

    funcNode.body.body = [preamble, ...funcNode.body.body];

    return funcNode;
  }

  /**
   * Source position of a node as { line, column }. compileGenerator parses the
   * generator wrapped in "(" ... ")", so Acorn's columns on the first line are
   * one too large; correct for that.
   */
  _pos(node) {
    if (!node.loc) return { line: 0, column: 0 };
    const { line, column } = node.loc.start;
    return { line, column: line === 1 ? column - 1 : column };
  }

  // -- Collect nested function names ----------------------------------------

  _collectNestedFuncs(node) {
    const body = node.body.type === 'BlockStatement' ? node.body.body : [];
    for (const stmt of body) {
      if (stmt.type === 'FunctionDeclaration' && stmt.id) {
        this.nestedFuncNames.add(stmt.id.name);
      }
      if (stmt.type === 'VariableDeclaration') {
        for (const decl of stmt.declarations) {
          if (decl.init &&
              (decl.init.type === 'FunctionExpression' || decl.init.type === 'ArrowFunctionExpression') &&
              decl.id && decl.id.type === 'Identifier') {
            this.nestedFuncNames.add(decl.id.name);
          }
        }
      }
    }
  }

  // -- Walk all nodes -------------------------------------------------------

  _walkBody(node) {
    if (node.body && node.body.type === 'BlockStatement') {
      node.body.body = this._walkStatements(node.body.body);
    } else if (node.body && Array.isArray(node.body)) {
      node.body = this._walkStatements(node.body);
    }
  }

  _walkStatements(stmts) {
    const result = [];
    for (const stmt of stmts) {
      const transformed = this._visitStatement(stmt);
      if (Array.isArray(transformed)) {
        result.push(...transformed);
      } else {
        result.push(transformed);
      }
    }
    return result;
  }

  _visitStatement(node) {
    switch (node.type) {
      case 'ForStatement':
      case 'ForInStatement':
      case 'ForOfStatement':
        return this._visitLoop(node, 'for');
      case 'WhileStatement':
        return this._visitLoop(node, 'while');
      case 'DoWhileStatement':
        return this._visitLoop(node, 'do');
      case 'LabeledStatement': {
        const body = node.body;
        const visited = this._visitStatement(body);
        if (Array.isArray(visited)) {
          // A labelled loop becomes [save, counter, loop, restore]: keep the
          // label on the loop itself, so that `continue label` still works
          node.body = body;
          return visited.map(s => (s === body ? node : s));
        }
        node.body = visited;
        return node;
      }
      case 'SwitchStatement':
        node.discriminant = this._visitExpr(node.discriminant);
        for (const switchCase of node.cases) {
          if (switchCase.test) switchCase.test = this._visitExpr(switchCase.test);
          switchCase.consequent = this._walkStatements(switchCase.consequent);
        }
        return node;
      case 'TryStatement':
        this._walkBlock(node.block);
        if (node.handler) this._walkBlock(node.handler.body);
        if (node.finalizer) this._walkBlock(node.finalizer);
        return node;
      case 'ThrowStatement':
        node.argument = this._visitExpr(node.argument);
        return node;
      case 'FunctionDeclaration':
        return this._visitFunctionDecl(node);
      case 'VariableDeclaration':
        return this._visitVarDecl(node);
      case 'ReturnStatement':
        if (node.argument) {
          node.argument = this._visitExpr(node.argument);
        }
        return node;
      case 'ExpressionStatement':
        node.expression = this._visitExpr(node.expression);
        return node;
      case 'IfStatement':
        node.test = this._visitExpr(node.test);
        if (node.consequent) this._walkBlock(node.consequent);
        if (node.alternate) {
          if (node.alternate.type === 'IfStatement') {
            this._visitStatement(node.alternate);
          } else {
            this._walkBlock(node.alternate);
          }
        }
        return node;
      case 'BlockStatement':
        node.body = this._walkStatements(node.body);
        return node;
      default:
        this._walkGeneric(node);
        return node;
    }
  }

  _walkBlock(node) {
    if (node.type === 'BlockStatement') {
      node.body = this._walkStatements(node.body);
    } else {
      // Single statement — wrap
      const visited = this._visitStatement(node);
      if (Array.isArray(visited)) {
        // Replace with block
        Object.assign(node, { type: 'BlockStatement', body: visited });
      }
    }
  }

  _walkGeneric(node) {
    if (!node || typeof node !== 'object') return;
    for (const key of Object.keys(node)) {
      if (key === 'type' || key === 'loc' || key === 'start' || key === 'end') continue;
      const child = node[key];
      if (Array.isArray(child)) {
        for (let i = 0; i < child.length; i++) {
          if (child[i] && typeof child[i] === 'object' && child[i].type) {
            child[i] = this._visitExpr(child[i]);
          }
        }
      } else if (child && typeof child === 'object' && child.type) {
        node[key] = this._visitExpr(child);
      }
    }
  }

  // -- Loops: for, for-in, for-of, while, do-while ---------------------------

  /**
   * Give each iteration of a loop its own name prefix:
   *
   *   let __ps__ = __prefix__; let __c__ = 0;
   *   <loop> { __prefix__ = __ps__ + "/<label>@<line>.<col>:" + String(__c__); __c__++; ... }
   *   __prefix__ = __ps__;
   *
   * The counter is incremented at the start of the body, so that `continue`
   * cannot skip it.
   */
  _visitLoop(node, label) {
    const loc = this._pos(node);
    const cv = counterVar(loc);
    const sv = saveVar(loc);

    // Loop header. init and the iterated object (`right`) are evaluated once,
    // before the loop. test and update are evaluated between iterations, when
    // __prefix__ holds the latest iteration's prefix, so rnd calls there get
    // a distinct name each time too.
    for (const key of ['init', 'right', 'test', 'update']) {
      if (!node[key]) continue;
      node[key] = node[key].type === 'VariableDeclaration'
        ? this._visitVarDecl(node[key])
        : this._visitExpr(node[key]);
    }

    this._walkBlock(node.body);

    const prefixUpdate = makePrefixUpdate(sv, label, loc, cv);
    const counterInc = {
      type: 'ExpressionStatement',
      expression: {
        type: 'UpdateExpression',
        operator: '++',
        argument: ident(cv),
        prefix: false,
      },
    };

    if (node.body.type === 'BlockStatement') {
      node.body.body = [prefixUpdate, counterInc, ...node.body.body];
    } else {
      node.body = {
        type: 'BlockStatement',
        body: [prefixUpdate, counterInc, node.body],
      };
    }

    return [makeSave(sv), this._makeVarDecl(cv, literal(0)), node, makeRestore(sv)];
  }

  // -- Function declarations (nested) ---------------------------------------

  _visitFunctionDecl(node) {
    if (this.funcDepth >= 1) {
      // Nested function: add __prefix__ as first parameter
      node.params = [ident('__prefix__'), ...node.params];
    }

    this.funcDepth++;
    const savedNested = new Set(this.nestedFuncNames);
    this._collectNestedFuncs(node);
    this._walkBody(node);
    this.nestedFuncNames = savedNested;
    this.funcDepth--;

    return node;
  }

  // -- Variable declarations ------------------------------------------------

  _visitVarDecl(node) {
    for (const decl of node.declarations) {
      if (decl.init) {
        // Check for nested function expression
        if ((decl.init.type === 'FunctionExpression' || decl.init.type === 'ArrowFunctionExpression') &&
            decl.id && decl.id.type === 'Identifier' &&
            this.nestedFuncNames.has(decl.id.name)) {
          // Nested function: add __prefix__ as first parameter
          decl.init.params = [ident('__prefix__'), ...decl.init.params];
          this.funcDepth++;
          const savedNested = new Set(this.nestedFuncNames);
          this._collectNestedFuncs(decl.init);
          this._walkFuncBody(decl.init);
          this.nestedFuncNames = savedNested;
          this.funcDepth--;
        } else {
          decl.init = this._visitExpr(decl.init);
        }
      }
    }
    return node;
  }

  _walkFuncBody(funcNode) {
    if (funcNode.body.type === 'BlockStatement') {
      funcNode.body.body = this._walkStatements(funcNode.body.body);
    } else {
      // Arrow function with expression body
      funcNode.body = this._visitExpr(funcNode.body);
    }
  }

  // -- Expression visitor ---------------------------------------------------

  _visitExpr(node) {
    if (!node) return node;

    switch (node.type) {
      case 'CallExpression':
        return this._visitCall(node);
      case 'ArrowFunctionExpression':
      case 'FunctionExpression':
        return this._visitArrowOrFuncExpr(node);
      case 'ArrayExpression':
        node.elements = node.elements.map(e => e ? this._visitExpr(e) : e);
        return node;
      case 'ObjectExpression':
        for (const prop of node.properties) {
          if (prop.type === 'SpreadElement') {
            prop.argument = this._visitExpr(prop.argument);
          } else {
            if (prop.computed) prop.key = this._visitExpr(prop.key);
            prop.value = this._visitExpr(prop.value);
          }
        }
        return node;
      case 'BinaryExpression':
      case 'LogicalExpression':
        node.left = this._visitExpr(node.left);
        node.right = this._visitExpr(node.right);
        return node;
      case 'UnaryExpression':
      case 'UpdateExpression':
        node.argument = this._visitExpr(node.argument);
        return node;
      case 'ConditionalExpression':
        node.test = this._visitExpr(node.test);
        node.consequent = this._visitExpr(node.consequent);
        node.alternate = this._visitExpr(node.alternate);
        return node;
      case 'AssignmentExpression':
        node.right = this._visitExpr(node.right);
        return node;
      case 'MemberExpression':
        node.object = this._visitExpr(node.object);
        if (node.computed) node.property = this._visitExpr(node.property);
        return node;
      case 'TemplateLiteral':
        node.expressions = node.expressions.map(e => this._visitExpr(e));
        return node;
      case 'SequenceExpression':
        node.expressions = node.expressions.map(e => this._visitExpr(e));
        return node;
      case 'SpreadElement':
        node.argument = this._visitExpr(node.argument);
        return node;
      default:
        // Any other expression (new, await, optional chains, tagged templates,
        // ...): visit its sub-expressions
        this._walkGeneric(node);
        return node;
    }
  }

  // -- Call expression visitor -----------------------------------------------

  _visitCall(node) {
    const loc = this._pos(node);

    // The callee may itself contain calls, eg rnd.sample(xs, 2).map(...)
    node.callee = this._visitExpr(node.callee);

    // Visit arguments; a callback of eg xs.map(cb) is named per element index
    const iteration = iterationCallback(node);
    node.arguments = node.arguments.map((a, i) =>
      (iteration && i === iteration.argIndex)
        ? this._visitIterationCallback(a, iteration, loc)
        : this._visitExpr(a));

    // rnd.X(args) → rnd.X(args, { name: <nameExpr> })
    if (node.callee.type === 'MemberExpression' &&
        node.callee.object.type === 'Identifier' &&
        node.callee.object.name === this.rndParamName &&
        node.callee.property.type === 'Identifier') {

      const method = node.callee.property.name;
      const nameExpr = makeNameExpr(method, loc, this.compSegments);

      // Add { name: <nameExpr> } as last argument
      node.arguments.push({
        type: 'ObjectExpression',
        properties: [{
          type: 'Property',
          key: ident('name'),
          value: nameExpr,
          kind: 'init',
          computed: false,
          shorthand: false,
          method: false,
        }],
      });
      return node;
    }

    // Nested function call: inject __prefix__ as first argument
    if (node.callee.type === 'Identifier' &&
        this.nestedFuncNames.has(node.callee.name)) {
      const prefixExpr = makeNameExpr(node.callee.name, loc, this.compSegments);
      node.arguments = [prefixExpr, ...node.arguments];
      return node;
    }

    return node;
  }

  // -- Callbacks of array iteration methods (map, forEach, Array.from, ...) ----

  /**
   * A callback called once per element, eg in xs.map(cb), plays the role of a
   * loop body: its rnd calls get a name segment "/map@<line>.<col>:<index>",
   * using the index the method passes to the callback.
   */
  _visitIterationCallback(cb, { label, indexPos }, loc) {
    const indexName = `__i_L${loc.line}_${loc.column}__`;
    const pad = (k) => ident(`__a${k}_L${loc.line}_${loc.column}__`);

    // Nested function passed by name, eg xs.map(bit): wrap it in an arrow
    // function that passes __prefix__, like a direct call bit() would
    if (cb.type === 'Identifier' && this.nestedFuncNames.has(cb.name)) {
      const params = [];
      for (let k = 0; k < indexPos; k++) params.push(pad(k));
      params.push(ident(indexName));
      this.compSegments.push([label, loc.line, loc.column, indexName]);
      const prefix = makeNameExpr(cb.name, loc, this.compSegments);
      this.compSegments.pop();
      const rest = `__rest_L${loc.line}_${loc.column}__`;
      return {
        type: 'ArrowFunctionExpression',
        id: null,
        params: [...params, { type: 'RestElement', argument: ident(rest) }],
        body: callExpr(ident(cb.name), [
          prefix,
          ...params.map(p => ident(p.name)),
          { type: 'SpreadElement', argument: ident(rest) },
        ]),
        expression: true,
        async: false,
        generator: false,
      };
    }

    if (cb.type !== 'ArrowFunctionExpression' && cb.type !== 'FunctionExpression') {
      return this._visitExpr(cb);
    }

    // Inline callback: use its index parameter, adding one if it has none
    const params = cb.params;
    let indexVar;
    if (params.length > indexPos) {
      if (params[indexPos].type !== 'Identifier') return this._visitExpr(cb); // eg a pattern: unsupported
      indexVar = params[indexPos].name;
    } else {
      if (params.some(p => p.type !== 'Identifier')) return this._visitExpr(cb); // eg a rest parameter
      while (params.length < indexPos) params.push(pad(params.length));
      params.push(ident(indexName));
      indexVar = indexName;
    }

    this.compSegments.push([label, loc.line, loc.column, indexVar]);
    const visited = this._visitArrowOrFuncExpr(cb);
    this.compSegments.pop();
    return visited;
  }

  // -- Arrow/function expression (inline callbacks for map etc.) --------------

  _visitArrowOrFuncExpr(node) {
    // Don't add __prefix__ to anonymous inline callbacks — they inherit it
    // from the enclosing scope. But we do need to walk their body.
    if (node.body.type === 'BlockStatement') {
      node.body.body = this._walkStatements(node.body.body);
    } else {
      node.body = this._visitExpr(node.body);
    }
    return node;
  }

  // -- Utility ---------------------------------------------------------------

  _makeVarDecl(name, init) {
    return {
      type: 'VariableDeclaration',
      declarations: [{
        type: 'VariableDeclarator',
        id: ident(name),
        init,
      }],
      kind: 'let',
    };
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Compile a PTO generator by injecting structured name= arguments into
 * every rnd.X() call. The compiled generator works with the existing
 * tracer and rnd — it just provides richer trace keys.
 *
 * The generator source is extracted via Function.prototype.toString(),
 * parsed with Acorn, transformed, and regenerated with astring.
 *
 * @param {Function} func  Generator function: (rnd) => { ... }
 * @returns {Function}  Compiled generator with ._originalSource and ._compiledSource
 */
export function compileGenerator(func) {
  const source = func.toString();

  // Parse as expression (it's a function value, not a declaration)
  // Wrap in parens to make it a valid expression statement
  const wrappedSource = `(${source})`;
  const tree = acorn.parse(wrappedSource, {
    ecmaVersion: 2022,
    locations: true,
    sourceType: 'module',
  });

  // The parsed tree is: Program > ExpressionStatement > FunctionExpression/ArrowFunctionExpression
  const exprStmt = tree.body[0];
  const funcNode = exprStmt.expression;

  const compiler = new NameCompiler();
  compiler.compile(funcNode);

  const compiledSource = generate(funcNode);

  // Create new function from compiled source
  // eslint-disable-next-line no-eval
  const compiledFunc = eval(`(${compiledSource})`);

  compiledFunc._originalSource = source;
  compiledFunc._compiledSource = compiledSource;

  return compiledFunc;
}
