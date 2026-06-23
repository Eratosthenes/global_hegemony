"""Built-in example strategies."""

from .always_cooperate import AlwaysCooperate
from .always_defect import AlwaysDefect
from .cautious_industrialist import CautiousIndustrialist
from .tit_for_tat import TitForTat
from .raid_and_heal import RaidAndHeal
from .counter_raider import CounterRaider
from .ambush import Ambush

__all__ = [
    "AlwaysCooperate",
    "AlwaysDefect",
    "CautiousIndustrialist",
    "TitForTat",
    "RaidAndHeal",
    "CounterRaider",
    "Ambush"
]
