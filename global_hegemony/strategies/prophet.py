"""Prophet: a one-step expected-value maximizer.

Unlike Strongman (which reads structural POSITION and largely ignores the opponent's
last action), Prophet is an explicit EV calculator. Each turn it:
  1. PREDICTS the opponent's move, by assuming WE cooperate and asking which is more
     profitable for THEM -- cooperate (produce) or defect (raid us).
  2. Picks its own move (C or D) with the highest EV, conditioned on that prediction.

This is a deliberately MYOPIC strategy: it optimizes the current turn's capital only.
It has no de-escalation clause, no mirror-handling, no long-horizon/positional logic.
The point is to test the hypothesis: does greedy one-turn EV-maximization match or beat
Strongman's positional play? If Prophet over-defects against cooperators (never settling
into the cooperative lock-in) or fails its own mirror (locks into D/D with no escape),
that is itself the result -- it would show that Strongman's non-EV clauses (de-escalate,
cooperate-when-you-could-extract) are doing necessary long-horizon work that one-step EV
cannot see.

Mechanics (B = operating cost burned from bank each move; here B = 1):
  Defection does damage on TWO axes simultaneously:
    - INTERCEPT: the raider takes min(D_raider, C_victim) from the victim's C
      (this transfers to the raider's capital).
    - BANK RAID: the raider takes D_raider from the victim's bank.

EVs (from the acting player's perspective):
  CC: C1 - B                                   (produce)
  DC: D1 + min(D1, C2) - B                      (raid: bank D1 + intercept min(D1,C2))
  CD: C1 - min(C1, D2) - D2 - B                 (victim: production suppressed + bank raided)
  DD: D1 - D2 - B                               (net differential to larger D)
"""

from ..models import Action, GameView, Modification
from ..player import Player

B = 1  # operating cost burned per move


class Prophet(Player):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._starting_capital = None

    def _predict_opponent(self, view: GameView) -> Action:
        """Assume WE cooperate; predict the opponent picks its more profitable move."""
        c1 = view.own_c
        c2, d2 = view.opponent_c, view.opponent_d
        # Opponent's EVs, assuming we cooperate:
        opp_ev_coop = c2 - B
        opp_ev_def = d2 + min(d2, c1) - B   # opponent raids us: bank d2 + intercept min(d2,c1)
        # TIE-BREAK: opponent assumed to COOPERATE on a tie. Change `>` to `>=` here to make
        # the opponent predicted to DEFECT on ties instead.
        if opp_ev_def > opp_ev_coop:
            return Action.DEFECT
        return Action.COOPERATE

    def choose_action(self, view: GameView) -> Action:
        if view.turn_number == 1:
            self._starting_capital = view.own_capital

        c1, d1 = view.own_c, view.own_d
        c2, d2 = view.opponent_c, view.opponent_d

        prediction = self._predict_opponent(view)

        if prediction is Action.COOPERATE:
            ev_cooperate = c1 - B                    # CC
            ev_defect = d1 + min(d1, c2) - B         # DC
        else:  # predict opponent defects
            ev_cooperate = c1 - min(c1, d2) - d2 - B  # CD (we are the victim)
            ev_defect = d1 - d2 - B                   # DD
        
        # if we are losing and the opponent has more capital, cooperate
        # this fixes the mirror problem
        best_ev = max(ev_cooperate, ev_defect)
        if best_ev < 0 and view.own_capital < self._starting_capital:
            return Action.COOPERATE

        # TIE-BREAK: COOPERATE when EVs are equal (ev_defect must strictly exceed to defect).
        # To prefer defection on ties, change `>` to `>=`.
        if ev_defect > ev_cooperate:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        # Grow production capacity by default. (Prophet has no explicit rearm logic; if you
        # want it to sustain a weapon while it is profitably raiding, gate INCREASE_D on
        # "did I just defect / will I keep defecting" -- left as INCREASE_C for now so the
        # pure EV-action logic is tested without a confounding self-mod policy.)
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # Resist an attacker (push their C up / D down) so they cannot sustain a raid on us.
        # This is the one non-EV concession -- without SOME defense, a committed raider bleeds
        # Prophet out. Remove this (return NO_CHANGE) if you want a PURE EV bot with no
        # defensive opponent-modification at all.
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        return Modification.NO_CHANGE