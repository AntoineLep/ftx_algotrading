from typing import TypedDict, Optional

from core.enums.position_state_enum import PositionStateEnum
from core.stock.crypto_pair_manager import CryptoPairManager
from core.trading.position_driver import PositionDriver


class PairManagerDict(TypedDict):
    """Pair manager dict"""

    crypto_pair_manager: CryptoPairManager
    position_driver: Optional[PositionDriver]
    last_position_driver_state: PositionStateEnum
    jail_start_timestamp: int
