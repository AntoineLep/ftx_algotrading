from enum import Enum


class OrderTypeEnum(Enum):
    """Order type enum"""

    LIMIT = 0
    MARKET = 1
