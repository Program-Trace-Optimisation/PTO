from ..base import Tracer

from .annotators import Name

class AutoPlayTracer(Tracer):
    # Function to initialize automatic names
    def play(self, *args):
        Name.__init__() # initialize automatic names
        return super().play(*args)

# Create an instance of AutoPlayTracer
tracer = AutoPlayTracer()    

