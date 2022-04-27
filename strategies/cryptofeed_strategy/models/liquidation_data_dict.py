from typing import TypedDict

from strategies.cryptofeed_strategy.enums.cryptofeed_side_enum import CryptofeedSideEnum


class LiquidationDataDict(TypedDict):
    """Liquidation data dict"""

    exchange: str
    price: float
    quantity: float
    side: CryptofeedSideEnum
    status: str
    symbol: str
    timestamp: float
