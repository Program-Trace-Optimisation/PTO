
import ast

#=================

##### 1) ADD DECORATORS TO FUNCTION DEFINITIONS

class FuncDec(ast.NodeTransformer):
   """
   Add @func_name decorator to any function definition.
   
   Transforms functions to enable call tracking.
   
   Example:
       Input:
           def process(x):
               return x + 1
               
       Output:
           @func_name
           def process(x):
               return x + 1
   """
   
   def visit_FunctionDef(self, node):
       self.generic_visit(node)
       node.decorator_list = [ast.Name(id='func_name', ctx=ast.Load())] + node.decorator_list
       return node

#=================

##### 2) ADD GENERATORS TO ITERATORS IN COMPREHENSIONS

class IterWrap(ast.NodeTransformer):
   """
   Wrap iter_name around iterators in comprehensions.
   
   Works with list, set, dict and generator comprehensions.
   
   Example:
       Input:
           [x*2 for x in items]
           
       Output:
           [x*2 for x in iter_name(items)]
   """

   def visit_comprehension(self, node):
       self.generic_visit(node)
       node.iter = ast.Call(func=ast.Name(id='iter_name', ctx=ast.Load()), args=[node.iter], keywords=[])
       return node

#=================

##### 3) ADD CONTEXTS TO FOR AND WHILE LOOPS

class LoopCxt(ast.NodeTransformer):
   """
   Add Loop_name context manager to for and while loops.
   
   Adds both context and counter increment at end of loop body.
   
   Example:
       Input:
           for x in items:
               process(x)
               
       Output:
           with Loop_name() as count:
               for x in items:
                   process(x)
                   count()
   """
   
   def visit_Loop(self, node):
       self.generic_visit(node)
       node.body = node.body + [ast.Expr(value=ast.Call(func=ast.Name(id='count', ctx=ast.Load()), args=[], keywords=[]))]
       node = ast.With(
           items=[ast.withitem(context_expr=ast.Call(func=ast.Name(id='Loop_name', ctx=ast.Load()), args=[], keywords=[]), 
                               optional_vars=ast.Name(id='count', ctx=ast.Store()))],
           body=[node])
       return node
   
   visit_For = visit_Loop
   visit_While = visit_Loop
               
#=================

##### LIST OF TRANFORMERS

ast_transformers = [FuncDec(), IterWrap(), LoopCxt()]

def transform_ast(tree):
   """
   Apply all AST transformations in sequence.
   
   Example:
       Input:
           def process(items):
               for x in items:
                   result = [y*2 for y in x]
               
       Output:
           @func_name
           def process(items):
               with Loop_name() as count:
                   for x in items:
                       result = [y*2 for y in iter_name(x)]
                       count()
   """
   for t in ast_transformers:
       tree = t.visit(tree)
   tree = ast.fix_missing_locations(tree)
   return(tree)