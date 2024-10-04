
import inspect

class Node():
    
    def __init__(self, name, count = None):
        frame = inspect.currentframe().f_back.f_back # frame in which function was called
        self.name = name                             # function name
        self.line_no = frame.f_lineno                # line number
        self.idx = frame.f_lasti                     # index in code (surrogate for column number)
        self.count = count                           # initialise counter
        
    def inc_count(self):
        self.count = 0 if self.count is None else self.count + 1        
        
    def __repr__(self):
        out = '%s@(%s,%s)' % (self.name, self.line_no, self.idx)
        if self.count is not None:
            out += ':%s' % self.count
        return out    
