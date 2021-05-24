from typing import TypedDict


class MarketDataDict(TypedDict):
    """Market data dict"""

    market: str
    price: float
    ask: float
    bid: float
    change1h: float
    change24h: float
