"""The finite environmental resource available during one match."""

from __future__ import annotations

from .formatting import format_number
from .models import Number


class Environment:
    STARTING_BANK = 200
    SYNERGY_AMOUNT = 2
    DEFECTION_COST = 1

    def __init__(self, starting_bank: Number = STARTING_BANK) -> None:
        if starting_bank < 0:
            raise ValueError("Starting environment bank cannot be negative.")

        self.starting_bank = starting_bank
        self.bank: Number = starting_bank

    def apply_synergy(self, c1: int, c2: int) -> Number:
        """Add synergy only when raw combined productive capacity exceeds two."""
        if c1 + c2 > self.SYNERGY_AMOUNT:
            self.bank += self.SYNERGY_AMOUNT
            return self.SYNERGY_AMOUNT
        return 0

    def apply_defection_cost(self) -> Number:
        burned = min(self.DEFECTION_COST, self.bank)
        self.bank -= burned
        return burned

    def extract(self, requested: Number) -> Number:
        if requested < 0:
            raise ValueError("Environmental extraction cannot be negative.")

        extracted = min(requested, self.bank)
        self.bank -= extracted
        return extracted

    @property
    def is_exhausted(self) -> bool:
        return self.bank <= 0

    def reset(self) -> None:
        self.bank = self.starting_bank

    def __str__(self) -> str:
        return f"Environment Bank: {format_number(self.bank)}"

    def __repr__(self) -> str:
        return str(self)
