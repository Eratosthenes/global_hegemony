"""A strategy that alternates between raiding and cooperative healing."""

from ..models import Action, GameView, Modification, Number
from ..player import Player

class RaidAndHeal(Player):
    """
    Raid a cooperative opponent, then seek a C/C round to rearm.
    """

    def __init__(
        self,
        name: str = "Raid and Heal",
        *,
        capital: Number = Player.STARTING_CAPITAL,
        c: int = 7,
        d: int = 3,
    ) -> None:
        super().__init__(
            name=name,
            capital=capital,
            c=c,
            d=d,
        )

    def choose_action(self, view: GameView) -> Action:
        """
        Raid whenever the weapon is ready.
        """
        if view.own_d > view.opponent_d >= 0 or view.own_c <= 0:
            # The weapon is ready and the opponent is vulnerable, or we do not have capacity to extract. Raid.
            return Action.DEFECT

        # Either the weapon is not ready, or the opponent is not vulnerable. Cooperate.
        return Action.COOPERATE

    def choose_self_modification(
        self,
        view: GameView,
    ) -> Modification:
        """
        Rearm after a successful C/C healing round.
        """
        return Modification.INCREASE_D

    def choose_opponent_modification(
        self,
        view: GameView,
    ) -> Modification:
        """
        Choose the structural edit after unilateral defection.
        """
        return Modification.INCREASE_D