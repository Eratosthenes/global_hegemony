"""A conditional cooperator with retaliation and liquidation behavior."""

from ..models import Action, GameView, Modification
from ..player import Player


class CautiousIndustrialist(Player):
    def choose_action(self, view: GameView) -> Action:
        if (
            view.own_d > 0
            and view.opponent_capital <= view.own_d + self.OPERATING_COST
        ):
            return Action.DEFECT

        if view.opponent_previous_action is Action.DEFECT:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        if view.own_d <= 2:
            return Modification.NO_CHANGE
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        if view.opponent_d > 0:
            return Modification.INCREASE_C
        return Modification.NO_CHANGE
