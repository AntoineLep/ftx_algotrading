from typing import TypedDict, Optional

from core.enums.order_type_enum import OrderTypeEnum


class OpeningConfigDict(TypedDict):
    """Opening config dict"""

    price: Optional[float]  # None for market
    size: float
    type: OrderTypeEnum
