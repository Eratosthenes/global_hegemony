"""A conditional cooperator with retaliation and liquidation behavior."""

from ..models import Action, GameView, Modification
from ..player import Player


class CautiousIndustrialist(Player):

    OWN_TARGET_D = 3
    OPP_TARGET_D = 2
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.prev_capital = None

    def choose_action(self, view: GameView) -> Action:
        if view.turn_number == 1:
            self.prev_capital = view.own_capital

        # break mutual destruction cycles
        if (
            view.own_previous_action is Action.DEFECT and 
            view.opponent_previous_action is Action.DEFECT and
            view.own_d == view.opponent_d
        ):
            self.prev_capital = view.own_capital
            return Action.COOPERATE

        if view.own_d > self.OWN_TARGET_D:
            self.prev_capital = view.own_capital
            return Action.DEFECT
        
        if (
            view.opponent_d < self.OPP_TARGET_D or
            view.opponent_d > self.OPP_TARGET_D
        ):
            # if we're losing capital, bail
            if view.own_capital < self.prev_capital:
                self.prev_capital = view.own_capital
                return Action.COOPERATE

            self.prev_capital = view.own_capital
            return Action.DEFECT

        self.prev_capital = view.own_capital
        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        if view.own_d < self.OWN_TARGET_D:
            return Modification.INCREASE_D
        elif view.own_d > self.OWN_TARGET_D:
            return Modification.INCREASE_C
        else:
            return Modification.NO_CHANGE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # if the opponent is more militarized than us, disarm them
        if view.opponent_d > view.own_d:
            return Modification.INCREASE_C

        # attempt to maintain a target level of militarization for the opponent
        if view.opponent_d > self.OPP_TARGET_D:
            return Modification.INCREASE_C
        elif view.opponent_d < self.OPP_TARGET_D:
            return Modification.INCREASE_D
        else:
            return Modification.NO_CHANGE
