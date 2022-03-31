from typing import TypedDict


class TickerDataDict(TypedDict):
    """Ticker data dict"""

    bid: float
    ask: float
    bid_size: float
    ask_size: float
    last: float
    time: float
