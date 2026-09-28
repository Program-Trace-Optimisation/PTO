from functools import wraps

from ..fine_distributions import RandomTraceable

from .annotators import func_name, Name
from .autoplay import tracer


class AutoNamedRandomTraceable(RandomTraceable):
    """
    RandomTraceable that names random values automatically.

    With naming='dynamic', a call without a name gets one at run time:
    sequential ('lin') or from the naming stack ('str').
    With naming='static', names are injected into the generator's source
    beforehand (see compiled_names), so every traced call must have one.
    """

    NAME_GENERATORS = {"lin": Name.get_seq_name, "str": Name.get_stack_name}
    NAMINGS = ["dynamic", "static"]

    def __init__(self, name_type="str", naming="dynamic", **kwargs):
        self._check(name_type, naming)
        self.name_type = name_type
        self.naming = naming
        super().__init__(**kwargs)  # binds the functions, via _wrap

    def _check(self, name_type, naming):
        if name_type not in self.NAME_GENERATORS:
            raise ValueError(
                f"Invalid name_type: {name_type}. Must be one of {list(self.NAME_GENERATORS)}"
            )
        if naming not in self.NAMINGS:
            raise ValueError(f"Invalid naming: {naming}. Must be one of {self.NAMINGS}")
        if naming == "static" and name_type != "str":
            raise ValueError("naming='static' computes structured names: use name_type='str'")

    def CONFIG(self, name_type=None, dist_type=None, naming=None):
        """
        Configure naming and distribution types.
        If no arguments provided, returns current configuration.
        """
        if name_type is None and dist_type is None and naming is None:
            return (self.dist_type, self.name_type)

        # Keep existing values if not specified
        name_type = name_type or self.name_type
        naming = naming or self.naming
        self._check(name_type, naming)
        self.name_type = name_type
        self.naming = naming

        # Rebind all functions from scratch (so they are never wrapped twice)
        self.config(dist_type or self.dist_type)

        return (self.dist_type, self.name_type)

    def _wrap(self, traceable):
        """Name the calls of a traceable function that are made without a name."""
        if self.naming == "static":

            @wraps(traceable)
            def static(*args, name=None, **kwargs):
                if name is None and self.tracer.active:
                    raise ValueError(
                        f"rnd.{traceable.__name__}() was called without a name under "
                        "naming='static'. Static naming only sees rnd calls written in "
                        "the generator and its nested functions; for helpers defined "
                        "elsewhere use naming='dynamic' (the default)."
                    )
                return traceable(*args, name=name, **kwargs)

            return static

        get_name = self.NAME_GENERATORS[self.name_type]

        @wraps(traceable)
        def dynamic(*args, name=None, **kwargs):
            return traceable(*args, name=name or get_name(), **kwargs)

        return func_name(dynamic, args_name=False)


rnd = AutoNamedRandomTraceable(tracer=tracer)
