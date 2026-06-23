"""A self-stable strategy designed to punish Raid and Heal."""

from ..models import Action, GameView, Modification
from ..player import Player


class CounterRaider(Player):
    """
    Cooperate while weapons are equal, but raid from structural superiority.

    Unlike RaidAndHeal, this strategy does not continually militarize during peaceful rounds. Two CounterRaiders therefore cooperate safely with one another.

    When attacked, it retaliates by disarming the attacker. Because RaidAndHeal simultaneously increases the victim's D, the attack tends to reverse the coercive advantage and create an opening for a counterraid.
    """

    def choose_action(self, view: GameView) -> Action:
        # if our productive capacity is higher than our opponent's, then we gain an edge by cooperating.
        if view.own_c >= view.opponent_c >= 0:
            return Action.COOPERATE

        # Attack only from a genuine predatory advantage, or when defensively necessary.
        if view.own_d > view.opponent_d >= 0 \
            or view.own_c <= 0 \
                or view.opponent_c >= view.own_c > 0:
            return Action.DEFECT
        
        return Action.COOPERATE

    def choose_self_modification(
        self,
        view: GameView,
    ) -> Modification:
        return Modification.INCREASE_C

    def choose_opponent_modification(
        self,
        view: GameView,
    ) -> Modification:
        # The Match engine has already recorded this turn's revealed action
        # when structural modifications are requested.
        # if view.own_previous_action is Action.DEFECT:
            # We were the attacker. Damage the victim's productive capacity and increase its D.
            # return Modification.DECREASE_C
        
        if view.opponent_c >= view.own_c:
            return Modification.DECREASE_C

        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C

        return Modification.NO_CHANGE
