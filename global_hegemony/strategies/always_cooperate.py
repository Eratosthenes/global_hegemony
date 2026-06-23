"""An unconditional cooperator that industrializes and disarms attackers."""

from ..models import Action, GameView, Modification
from ..player import Player


class AlwaysCooperate(Player):
    def choose_action(self, view: GameView) -> Action:
        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        return Modification.INCREASE_C
