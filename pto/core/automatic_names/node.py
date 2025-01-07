import inspect


class Node:
    """
    Track function calls with their location in source code.

    This class creates nodes that record where a function was called from,
    including line number and instruction index. It can also maintain a counter
    for tracking number of calls.

    Args:
        name: Name identifier (typically function name)
        count: Optional counter initialization value

    Attributes:
        name: Name identifier
        line_no: Line number in source code where called
        idx: Index of last instruction (pseudo column number)
        count: Optional counter value

    Note:
        Uses frame inspection to get caller's caller location.
        Format when printed: name@(line,index):count
    """

    def __init__(self, name, count=None):
        frame = (
            inspect.currentframe().f_back.f_back
        )  # frame in which function was called
        self.name = name  # function name
        self.line_no = frame.f_lineno  # line number
        self.idx = frame.f_lasti  # index in code (surrogate for column number)
        self.count = count  # initialise counter

    def inc_count(self):
        """Initialize counter to 0 if None, otherwise increment by 1."""
        self.count = 0 if self.count is None else self.count + 1

    def __repr__(self):
        """
        String representation showing name, location and count.
        Format: name@(line,index):count
        """
        out = "%s@(%s,%s)" % (self.name, self.line_no, self.idx)
        if self.count is not None:
            out += ":%s" % self.count
        return out
