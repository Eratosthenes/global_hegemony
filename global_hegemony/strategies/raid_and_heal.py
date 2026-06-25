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
        c: int = 5,
        d: int = 5,
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
        # if we have no capacity to extract, then raid
        if view.own_c <= 0:
            return Action.DEFECT

        # if we are ready and we have more military capacity than the opponent, raid.
        if view.own_d > 0 and view.own_d > view.opponent_d:
            return Action.DEFECT

        # either we are not not ready, or the opponent is not vulnerable. 
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