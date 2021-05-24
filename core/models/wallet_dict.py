from typing import TypedDict


class WalletDict(TypedDict):
    """Wallet dict"""

    coin: str
    total: float
    free: float
    availableWithoutBorrow: float
    usdValue: float
    spotBorrow: float
