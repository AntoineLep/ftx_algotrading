from typing import TypedDict


class MarketDataDict(TypedDict):
    """Market data dict"""

    name: str
    price: float
    ask: float
    bid: float
    sizeIncrement: float
    change1h: float
    change24h: float
