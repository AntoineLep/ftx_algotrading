from typing import TypedDict, List, Optional

from core.models.trigger_order_config_dict import TriggerOrderConfigDict
from core.models.opening_config_dict import OpeningConfigDict


class PositionConfigDict(TypedDict):
    """Position config dict"""

    openings: List[OpeningConfigDict]
    trigger_orders: Optional[List[TriggerOrderConfigDict]]
    max_open_duration: Optional[int]
