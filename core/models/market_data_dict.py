from typing import TypedDict


class MarketDataDict(TypedDict):
    """Market data dict"""

    name: str
    price: float
    ask: float
    bid: float
    change1h: float
    change24h: float
