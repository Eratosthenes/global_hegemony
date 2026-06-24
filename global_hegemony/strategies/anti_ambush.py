"""An anti-ambush strategy."""

from ..models import Action, GameView, Modification
from ..player import Player

class AntiAmbush(Player):
    def choose_action(self, view: GameView) -> Action:
        # be the first to cooperate if caught in mutual defection
        # this allows self-coexistence
        if view.opponent_previous_action is Action.DEFECT and view.own_previous_action is Action.DEFECT:
            return Action.COOPERATE

        # attack if we are armed and we'll win under mutual defection
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
        # if they just attacked, we resist
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C

        return Modification.NO_CHANGE

