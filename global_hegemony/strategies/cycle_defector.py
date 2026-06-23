"""CycleDefector: a duty-cycle predator driven by a hysteresis band on its own D.
"""

from ..models import Action, GameView, Modification
from ..player import Player

class CycleDefector(Player):

    D_HIGH = 17 
    D_LOW = 1

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._striking = False

    # --- phase ------------------------------------------------------------

    def _update_phase(self, view: GameView) -> bool:
        """Latch the strike phase on at D>=HIGH, off at D<=LOW; hold otherwise."""
        if not self._striking and view.own_d >= self.D_HIGH:
            self._striking = True
        elif self._striking and view.own_d <= self.D_LOW:
            self._striking = False

        return self._striking

    # --- decisions --------------------------------------------------------

    def choose_action(self, view: GameView) -> Action:
        striking = self._update_phase(view)

        if striking:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        return Modification.DECREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        return Modification.DECREASE_C