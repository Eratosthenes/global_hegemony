"""Built-in example strategies."""

from .always_cooperate import AlwaysCooperate
from .always_defect import AlwaysDefect
from .cautious_industrialist import CautiousIndustrialist
from .tit_for_tat import TitForTat
from .raid_and_heal import RaidAndHeal
from .ambush import Ambush
from .pacifier import Pacifier
from .sentinel import Sentinel
from .disruptor import Disruptor
from .disciplined_ambush import DisciplinedAmbush
from .opening_raider import OpeningRaider
from .saboteur_ambush import SaboteurAmbush
from .forager import Forager
from .cycle_defector import CycleDefector
from .anti_ambush import AntiAmbush
from .warden import Warden

__all__ = [
    "AlwaysCooperate",
    "AlwaysDefect",
    "CautiousIndustrialist",
    "TitForTat",
    "RaidAndHeal",
    "Ambush",
    "Pacifier",
    "Sentinel",
    "Disruptor",
    "DisciplinedAmbush",
    "OpeningRaider",
    "SaboteurAmbush",
    "Forager",
    "CycleDefector",
    "AntiAmbush",
    "Warden",
]
