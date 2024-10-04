
import ast

#=================

##### 1) ADD DECORATORS TO FUNCTION DEFINITIONS

class FuncDec(ast.NodeTransformer):
    """ Add @func_name to any function definition """
    
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        node.decorator_list = [ast.Name(id='func_name', ctx=ast.Load())] + node.decorator_list
        return node

#=================

##### 2) ADD GENERATORS TO ITERATORS IN COMPREHENSIONS

class IterWrap(ast.NodeTransformer):
    """ Wrap iter_name to iterators of comprehensions (list, set, dict, generator) """

    def visit_comprehension(self, node):
        self.generic_visit(node)
        node.iter = ast.Call(func=ast.Name(id='iter_name', ctx=ast.Load()), args=[node.iter], keywords=[])
        return node

#=================

##### 3) ADD CONTEXTS TO FOR AND WHILE LOOPS

class LoopCxt(ast.NodeTransformer):
    """ Enclose all for loops in Loop_name context and add counter at the end of the loop body """
    
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
    for t in ast_transformers:
        tree = t.visit(tree)
    tree = ast.fix_missing_locations(tree)
    return(tree)
    
