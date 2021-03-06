from enum import Enum


class ProbabilityEnum(Enum):
    """Probability enum"""

    NOT_PROBABLE = 0
    MAYBE_PROBABLE = 1
    PROBABLE = 2
    NO_DOUBT = 3
    UNKNOWN = 4
