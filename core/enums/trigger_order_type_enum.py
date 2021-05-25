from enum import Enum


class TriggerOrderTypeEnum(Enum):
    """Trigger order type enum"""

    STOP = 0
    TAKE_PROFIT = 1
    TRAILING_STOP = 2
