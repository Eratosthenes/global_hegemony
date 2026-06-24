"""Shared enums and immutable data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional, TypeAlias


Number: TypeAlias = int | float


class Action(Enum):
    COOPERATE = "C"
    DEFECT = "D"


class Modification(Enum):
    """The change applied to the target's C value."""

    INCREASE_D = -1
    NO_CHANGE = 0
    INCREASE_C = 1


@dataclass(frozen=True)
class GameView:
    """Read-only state supplied to a player's decision functions."""

    turn_number: int
    environment_bank: Number

    own_capital: Number
    own_c: int
    own_d: int

    opponent_capital: Number
    opponent_c: int
    opponent_d: int

    own_previous_action: Optional[Action]
    opponent_previous_action: Optional[Action]


@dataclass(frozen=True)
class TurnRecord:
    """Complete end-of-turn record used for reporting and CSV output."""

    turn: int

    p1_action: str
    p1_mod_dc: int
    p1_c: int
    p1_d: int
    p1_capital_delta: Number
    p1_vulture_prize: Number
    p1_capital: Number

    p2_action: str
    p2_mod_dc: int
    p2_c: int
    p2_d: int
    p2_capital_delta: Number
    p2_vulture_prize: Number
    p2_capital: Number

    environment_delta: Number
    environment: Number

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
