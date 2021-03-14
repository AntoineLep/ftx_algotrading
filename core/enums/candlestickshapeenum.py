from enum import Enum


class CandlestickShapeEnum(Enum):
    """Candlestick shape enum"""

    UNDEFINED = 0
    HAMMER_OR_HANGING_MAN = 1
    REVERSED_HAMMER_OR_FALLING_STAR = 2
    SWALLOWING = 3
    HARAMI = 4
