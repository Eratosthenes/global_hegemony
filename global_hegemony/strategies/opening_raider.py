"""
OpeningRaider: spend the free starting weapon early, then industrialize forever.
"""

from ..models import Action, GameView, Modification
from ..player import Player


class OpeningRaider(Player):

    def choose_action(self, view: GameView) -> Action:
        if view.own_d > 2 and view.opponent_d >= 0:
            return Action.DEFECT

        if view.own_c <= 0:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        return Modification.INCREASE_D