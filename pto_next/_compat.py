"""Running generators written for the original core (pto) on this one."""


def is_old_rnd(value):
    """Whether value is the rnd of the original core, which this core's rnd replaces."""
    return type(value).__module__.startswith("pto.core.") and hasattr(value, "choice")
