""" An anti-ambush strategy (Strongman). """

from ..models import Action, GameView, Modification
from ..player import Player

class AntiAmbush(Player):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._campaign = False # whether the player is currently in a campaign (attacking)

    def choose_action(self, view: GameView) -> Action:
        # be the first to cooperate if caught in mutual defection
        # this allows self-coexistence
        if view.opponent_previous_action is Action.DEFECT and view.own_previous_action is Action.DEFECT:
            self._campaign = False
            return Action.COOPERATE
        
        # we can bankrupt our opponent, so defect
        if abs(view.own_d) * view.own_d >= view.opponent_capital:
            self._campaign = True
            return Action.DEFECT

        # attack if we are armed and we'll win under mutual defection
        # bias toward defection to win more frequently
        if view.own_d > 0 and view.own_d >= view.opponent_d:
            self._campaign = True
            return Action.DEFECT

        # if we are fully armed, there's no point in cooperating
        if view.own_c <= 0:
            self._campaign = True
            return Action.DEFECT
        
        # if we are unarmed, focus on building up our capital
        if view.own_d <= 0:
            self._campaign = False

        # runaway productivity condition
        if view.own_c > 0 and view.own_c > view.own_d + view.opponent_d:
            self._campaign = False
            return Action.COOPERATE

        return Action.COOPERATE

    def choose_self_modification(self, view):
        if self._campaign:
            # if we are striking, we need to rearm
            return Modification.INCREASE_D

        # grow by default
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # they are attacking us
        if view.opponent_previous_action is Action.DEFECT:
            # resist attacks
            self._campaign = False
            return Modification.INCREASE_C
        
        # we are attacking; remain unopinionated
        return Modification.NO_CHANGE