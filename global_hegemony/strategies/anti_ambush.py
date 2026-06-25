""" An anti-ambush strategy (Strongman). """

from ..models import Action, GameView, Modification
from ..player import Player

class AntiAmbush(Player):
    def choose_action(self, view: GameView) -> Action:
        # be the first to cooperate if caught in mutual defection
        # this allows self-coexistence
        if view.opponent_previous_action is Action.DEFECT and view.own_previous_action is Action.DEFECT:
            return Action.COOPERATE

        # attack if we are armed and we'll win under mutual defection
        # bias toward defection to win more frequently
        if view.own_d > 0 and view.own_d >= view.opponent_d:
            return Action.DEFECT

        # if we are fully armed, there's no point in cooperating
        if view.own_c <= 0:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view):
        # grow by default
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # they are attacking us
        if view.opponent_previous_action is Action.DEFECT:
            # resist attacks
            return Modification.INCREASE_C

        # we are attacking; remain unopinionated
        return Modification.NO_CHANGE