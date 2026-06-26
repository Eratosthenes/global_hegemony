"""A perpetual war economy that deindustrializes cooperating victims."""

from ..models import Action, GameView, Modification
from ..player import Player


class AlwaysDefect(Player):
    def choose_action(self, view: GameView) -> Action:
        # defect when we can win in a mutual defection
        if view.own_d > 0 and view.own_d > view.opponent_d:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view):
        # don't deindustrialize all the way to extinction
        if view.own_c < 2:
            return Modification.INCREASE_C
        
        # stabilize at a high level of military capacity
        if view.own_c == 2:
            return Modification.NO_CHANGE

        # increase military capacity by default
        return Modification.INCREASE_D

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # resist attacks
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        
        # try to disarm opponent if they have more military capacity than us
        if view.opponent_d > view.own_d:
            return Modification.INCREASE_C

        # if we have equal military capacity, don't change anything
        if view.opponent_d == view.own_d:
            return Modification.NO_CHANGE

        # we have at least as much military capacity, so we can afford to deindustrialize them
        return Modification.INCREASE_D
    