"""An unconditional predator that deindustrializes cooperating victims."""

from ..models import Action, GameView, Modification
from ..player import Player


class AlwaysDefect(Player):
    def choose_action(self, view: GameView) -> Action:
        if view.own_d > 0:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        return Modification.INCREASE_D
    
    def choose_self_modification(self, view):
        return Modification.INCREASE_D
