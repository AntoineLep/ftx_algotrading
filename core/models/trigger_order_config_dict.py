from typing import TypedDict, Optional

from core.enums.trigger_order_type_enum import TriggerOrderTypeEnum


class TriggerOrderConfigDict(TypedDict):
    """Trigger order config dict"""

    size: float
    type: TriggerOrderTypeEnum
    reduce_only: bool  # Default used value is True for PositionDriver
    trigger_price: Optional[float]  # For stop loss or take profit orders
    order_price: Optional[float]  # Order type is limit if this is specified; otherwise market
    trail_value: Optional[float]  # For trailing stop orders. Negative for "sell"; positive for "buy"
