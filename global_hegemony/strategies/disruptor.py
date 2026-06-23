"""Disruptor: cooperate for production, but never finance an uninterrupted buildup.

The lesson from Sentinel vs Ambush:
    A launch detector that fires on the first defection fires too late -- by then the sleeper has banked its full D-reserve and wins the ensuing D/D differential. The buildup is uncontestable *while you keep cooperating*, because no one modifies anyone on a C/C turn. The only lever against a militarizing opponent is to STOP cooperating: 
    
    A defection (a) denies the harvest the opponent is banking and (b) unlocks choose_opponent_modification, the sole means of reaching into its structure mid-buildup.  
    
    So the counter is not "out-produce" and not "detect-then-counterstrike". It is "never let any opponent enjoy an unbroken cooperation streak long enough to build a decisive weapon". Interrupt early, while the opponent's D is still small and a clash is even, and use the interruption's modification to push its C back up.

Disruptor therefore:
    - Cooperates by default to capture production (it is fundamentally an industrialist).
    - Tracks the opponent's *current* cooperation streak. Before that streak reaches a safety horizon, it throws a single disarming defection: this resets any buildup, denies the opponent a harvest, and -- via opponent-modification -- shoves the opponent's C up / D down.
    - Disarms unconditionally (INCREASE_C on the opponent) whenever it gets the chance.
    - Falls back to defection if forced non-positive in C (cooperating there only bleeds).

Against a fellow cooperator/industrialist the periodic single defection is a small, bounded tax (one denied harvest per horizon) and structure stays near parity. Against a sleeper, it caps the reserve the sleeper can ever accumulate, so the eventual strike is weak and the clash is winnable.
"""

from ..models import Action, GameView, Modification
from ..player import Player


class Disruptor(Player):
    # Never let the opponent string together more than this many cooperations before
    # we break the streak. Small enough that a sleeper's D-reserve stays modest; large
    # enough that against a genuine cooperator we still harvest most turns peacefully.
    DISRUPT_HORIZON = 3

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._opp_coop_streak = 0
        self._we_just_disrupted = False

    def _observe(self, view: GameView) -> None:
        last = view.opponent_previous_action
        if last is None:
            return
        if last is Action.COOPERATE:
            self._opp_coop_streak += 1
        else:
            self._opp_coop_streak = 0

    def choose_action(self, view: GameView) -> Action:
        self._observe(view)
        self._we_just_disrupted = False

        # Cooperating with non-positive C produces nothing and costs abs(C).
        if view.own_c <= 0:
            return Action.DEFECT

        # Break the opponent's buildup before it reaches the safety horizon.
        # (Only meaningful while the opponent still has a real weapon to grow; once its
        #  D is already non-positive it cannot build a threat, so we can keep harvesting.)
        if self._opp_coop_streak >= self.DISRUPT_HORIZON and view.opponent_d > 0:
            self._we_just_disrupted = True
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        # Industrialize when safely productive; never let own C run negative (no self-bleed).
        if view.own_c <= 0:
            return Modification.INCREASE_C
        return Modification.INCREASE_C  # default posture: build production capacity

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # Always drive the opponent toward negative D. On a disruption turn this is the
        # mid-buildup interference that pure cooperation can never deliver.
        return Modification.INCREASE_C