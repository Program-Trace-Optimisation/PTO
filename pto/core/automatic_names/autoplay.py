from ..base import Tracer
from .annotators import Name

class AutoPlayTracer(Tracer):
    """
    Tracer that automatically reinitializes the naming system before each replay.
    
    Extends the base Tracer class to ensure naming is reset (stack cleared and 
    sequence restarted) before each trace replay, preventing name collision and
    ensuring clean naming state.
    
    Example:
        tracer = AutoPlayTracer()
        
        # Each play starts with fresh naming state
        solution, trace = tracer.play(generator, {})
        solution2, trace2 = tracer.play(generator, trace)
    """
    
    def play(self, *args):
        """
        Execute trace replay with fresh naming state.
        
        Reinitializes the naming system and then delegates to parent's 
        play method for actual trace replay.
        
        Args:
            *args: Arguments to pass to parent's play method
            
        Returns:
            Result from parent's play method
        """
        Name.__init__()  # initialize automatic names
        return super().play(*args)

# Create an instance of AutoPlayTracer
tracer = AutoPlayTracer()

