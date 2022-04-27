from typing import TypedDict


class OpenInterestDataDict(TypedDict):
    """Open interest data dict"""

    exchange: str
    symbol: str
    open_interest: float
    timestamp: float
