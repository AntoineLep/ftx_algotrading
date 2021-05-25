from typing import TypedDict, Optional

from core.enums.side_enum import SideEnum


class PositionDataDict(TypedDict):
    """Position data dict"""

    future: str
    size: float
    side: SideEnum
    net_size: float
    long_order_size: float
    short_order_size: float
    cost: float
    entry_price: Optional[float]
    unrealized_pnl: float
    realized_pnl: float
    initial_margin_requirement: float
    maintenance_margin_requirement: float
    open_size: float
    collateral_used: float
    estimated_liquidation_price: Optional[float]
