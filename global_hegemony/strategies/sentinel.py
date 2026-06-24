"""Sentinel: a disarming pacifist with a launch detector and a counterstrike.

Observed failure of pure pacifism (Pacifier vs Ambush):
    A +1/turn disarm cannot outrun a high-magnitude raid. Ambush spends ~18 turns building D up past 20, then strikes. Pacifier's INCREASE_C disarm would eventually flip Ambush to negative-D tribute, but the victim bankrupts first -- the strike outruns the disarm by a couple of turns.

Key exploitable fact:
    Ambush launches from its OWN bankruptcy boundary (capital ~5). At the exact moment it reveals a permanent strike, it is at its weakest capital. A counter that keeps cooperating feeds the raid and dies. A counter that flips to DEFECT turns C/D into D/D: Ambush no longer has a cooperator's harvest to intercept, and the match becomes a capital race that the just-launched predator -- broke and committed -- is poorly
    positioned to win.

Sentinel therefore:
    1. Plays the disarming-pacifist game by default (cooperate, hold own C in a safe band, always push opponent C up).
    2. Watches for a launch signature: a sufficiently long opponent cooperation streak followed by defection (an Ambush-style sleeper revealing itself).
    3. On detection, latches into ARMED mode -- unconditional DEFECT to deny the harvest and grind capital in D/D -- while continuing to shove the opponent's C up so its D keeps falling toward the tribute regime during the clash.

The detector is an explicit state machine so the trigger condition is testable in isolation, independent of the action/modification policy.
"""

from ..models import Action, GameView, Modification
from ..player import Player


class Sentinel(Player):
    SAFE_C_LOW = 1
    SAFE_C_HIGH = 3

    # A "sleeper" is an opponent that cooperated at least this many turns in a row
    # before its first defection. Tuned above incidental one-off defections but below
    # Ambush's long buildup (~18 turns), so a genuine launch trips it immediately.
    SLEEPER_COOP_THRESHOLD = 4

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._coop_streak = 0      # consecutive opponent cooperations observed
        self._armed = False        # latched once a launch is detected

    def _observe(self, view: GameView) -> None:
        """Update the launch detector from the opponent's last revealed action."""
        last = view.opponent_previous_action
        if last is None:
            return
        if last is Action.COOPERATE:
            self._coop_streak += 1
        else:
            # First defection after a long peaceful streak == a sleeper launching.
            if self._coop_streak >= self.SLEEPER_COOP_THRESHOLD:
                self._armed = True
            self._coop_streak = 0

    def choose_action(self, view: GameView) -> Action:
        self._observe(view)

        # Counterstrike: deny the launched predator its harvest and race capital in D/D.
        if self._armed:
            return Action.DEFECT

        # Pacifist default: cooperating with non-positive C only bleeds, so defect there.
        if view.own_c <= 0:
            return Action.DEFECT
        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        # Keep own C in the defensive band whether pacifist or armed.
        if view.own_c < self.SAFE_C_LOW:
            return Modification.INCREASE_C
        if view.own_c > self.SAFE_C_HIGH:
            return Modification.INCREASE_D
        return Modification.NO_CHANGE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # Always drive the opponent toward negative D -- this is the disarm engine, and
        # it keeps working during the D/D clash, accelerating the predator's collapse.
        return Modification.INCREASE_C