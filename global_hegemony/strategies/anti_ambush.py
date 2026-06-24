"""An anti-ambush strategy."""

from ..models import Action, GameView, Modification
from ..player import Player

class AntiAmbush(Player):
    def choose_action(self, view: GameView) -> Action:
        if view.own_d > 4:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C

        return Modification.DECREASE_C

    def choose_self_modification(self, view):
        return Modification.INCREASE_C
