from typing import TypedDict


class WalletDict(TypedDict):
    """Wallet dict"""

    coin: str
    total: float
    free: float
    available_without_borrow: float
    usd_value: float
    spot_borrow: float
