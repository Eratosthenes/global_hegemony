"""Base class for all submitted player strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .formatting import format_number
from .models import Action, GameView, Modification, Number


class Player(ABC):
    STARTING_CAPITAL = 50
    STRUCTURAL_TOTAL = 10
    OPERATING_COST = 1

    def __init__(
        self,
        name: str,
        capital: Number = STARTING_CAPITAL,
        c: int = 5,
        d: int = 5,
    ) -> None:
        if c + d != self.STRUCTURAL_TOTAL:
            raise ValueError(
                f"C and D must sum to {self.STRUCTURAL_TOTAL}; got C={c}, D={d}."
            )

        self.name = name
        self.capital: Number = capital
        self.c = c
        self.d = d

        self.previous_action: Optional[Action] = None
        self.opponent_previous_action: Optional[Action] = None

    @abstractmethod
    def choose_action(self, view: GameView) -> Action:
        """Choose C or D without seeing the opponent's current action."""
        raise NotImplementedError

    def choose_self_modification(self, view: GameView) -> Modification:
        """Called after C/C. The default is no structural change."""
        return Modification.NO_CHANGE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        """Called when this player may modify its opponent."""
        return Modification.NO_CHANGE

    def apply_modification(self, modification: Modification) -> None:
        self.c += modification.value
        self.d -= modification.value

        if self.c + self.d != self.STRUCTURAL_TOTAL:
            raise RuntimeError("Structural invariant C + D = 10 was violated.")

    def pay_operating_cost(self) -> None:
        self.capital -= self.OPERATING_COST

    @property
    def is_bankrupt(self) -> bool:
        return self.capital <= 0

    def __str__(self) -> str:
        return (
            f"{self.name}: capital={format_number(self.capital)}, "
            f"C={self.c}, D={self.d}"
        )

    def __repr__(self) -> str:
        return str(self)
