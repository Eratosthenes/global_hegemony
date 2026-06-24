"""A sleeper predator that builds a large D reserve before striking."""

from ..models import Action, GameView, Modification, Number
from ..player import Player


class Ambush(Player):
    """
    Cooperate while secretly converting productive capacity into predatory
    capacity, then launch a permanent offensive before cooperation would
    cause bankruptcy or end the match.

    BUILDING PHASE
        - Cooperate.
        - After every C/C turn, decrease C and increase D.

    STRIKE PHASE
        - Defect permanently.
        - Use structural modifications to disarm the opponent.

    The strategy is intentionally patient. It may tolerate many cooperative turns while accumulating capital and building a large D reserve.
    """

    def __init__(
        self,
        name: str = "Striker",
        *,
        capital: Number = Player.STARTING_CAPITAL,
        c: int = 5,
        d: int = 5,
    ) -> None:
        super().__init__(
            name=name,
            capital=capital,
            c=c,
            d=d,
        )

        self.has_launched = False

    def choose_action(self, view: GameView) -> Action:
        """
        Cooperate until another cooperative turn would be unsafe.

        Launch conditions:

        1. Another cooperative turn would reduce capital to zero or below.
        2. Another mutual-cooperation turn would exhaust the environment.
        3. The offensive has already begun.
        """

        if self.has_launched:
            return Action.DEFECT

        projected_capital = self._project_capital_after_cooperation(view)

        capital_deadline = projected_capital <= 0
        environment_deadline = self._cooperation_would_end_match(view)

        if view.own_d > 0 and (
            capital_deadline
            or environment_deadline
        ):
            self.has_launched = True
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(
        self,
        view: GameView,
    ) -> Modification:
        """
        During the buildup, convert one point of C into one point of D.
        """

        if self.has_launched:
            return Modification.NO_CHANGE

        return Modification.INCREASE_D

    def choose_opponent_modification(
        self,
        view: GameView,
    ) -> Modification:
        """
        Disarm the opponent after unilateral defection.

        Increasing the opponent's C reduces its D, which makes future weapon
        clashes more favorable to Striker.
        """
        if self.has_launched and view.own_d <= view.opponent_c:
            return Modification.INCREASE_D

        return Modification.INCREASE_C

    @staticmethod
    def _project_capital_after_cooperation(
        view: GameView,
    ) -> Number:
        """
        Estimate capital after one more cooperative turn.

        This assumes the opponent also cooperates and that sufficient
        environmental wealth remains for the requested extraction.
        """

        if view.own_c >= 0:
            production_change = view.own_c
        else:
            production_change = -abs(view.own_c)

        return (
            view.own_capital
            + production_change
            - Player.OPERATING_COST
        )

    @staticmethod
    def _cooperation_would_end_match(
        view: GameView,
    ) -> bool:
        """
        Return True when the next C/C turn would consume the environment.

        Two synergy points are added when combined raw C exceeds two.
        Negative C values request no environmental extraction.
        """

        synergy = (
            2
            if view.own_c + view.opponent_c > 2
            else 0
        )

        available = view.environment_bank + synergy

        own_request = max(0, view.own_c)
        opponent_request = max(0, view.opponent_c)
        total_request = own_request + opponent_request

        return total_request >= available