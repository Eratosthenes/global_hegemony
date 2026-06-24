"""A basic Tit-for-Tat strategy adapted to the structural game."""

from ..models import Action, GameView, Modification
from ..player import Player


class TitForTat(Player):
    def choose_action(self, view: GameView) -> Action:
        if view.opponent_previous_action is None:
            return Action.COOPERATE
        return view.opponent_previous_action

    def choose_self_modification(self, view: GameView) -> Modification:
        if view.own_c < view.opponent_c:
            return Modification.INCREASE_C
        elif view.own_c > view.opponent_c:
            return Modification.INCREASE_D
        else:
            return Modification.NO_CHANGE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        if view.own_c > view.opponent_c:
            return Modification.INCREASE_C
        elif view.own_c < view.opponent_c:
            return Modification.INCREASE_D
        else:
            return Modification.NO_CHANGE