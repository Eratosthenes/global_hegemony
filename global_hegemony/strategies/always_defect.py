"""An unconditional predator that deindustrializes cooperating victims."""

from ..models import Action, GameView, Modification
from ..player import Player


class AlwaysDefect(Player):
    def choose_action(self, view: GameView) -> Action:
        return Action.DEFECT

    def choose_opponent_modification(self, view: GameView) -> Modification:
        return Modification.DECREASE_C
