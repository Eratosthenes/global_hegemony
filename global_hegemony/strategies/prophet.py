"""Prophet: a one-step expected-value maximizer.

Each turn Prophet:
  1. PREDICTS the opponent's move, by assuming WE cooperate and asking which is more
     profitable for THEM -- cooperate (produce) or defect (raid us).
  2. Picks its own move (C or D) with the highest EV, conditioned on that prediction.
  3. SURVIVAL OVERRIDE: if it's losing (below starting capital) and even its best option is
     negative, it cooperates -- breaking out of a death-spiral / mutual-defection attrition.
     This non-EV clause is what makes the strategy mirror-viable.

NOTE: a 2-ply variant (assume the opponent BEST-RESPONDS to each of our moves) was tested
and performed WORSE (bankruptcy 0.04 -> 0.21). Reason: perfect one-step opponent-modeling
at capability parity almost always predicts the opponent will defect (raiding us is
lucrative), which makes Prophet defect defensively almost every turn -- and defection-
proneness is exactly what the game punishes. The naive "assume the opponent cooperates"
optimism is load-bearing: it lets Prophet see cooperation as safe and settle into it.
One ply of realism is the worst of both worlds -- realistic enough to foresee the immediate
raid, too shallow to foresee the long-run cost of triggering the D/D. Hence: reverted to 1-ply.

Mechanics (B = operating cost burned per move; defection does BOTH interception and a
full bank-raid, all transferring to the raider):
  CC: C1 - B
  DC: D1 + min(D1, C2) - B           (we raid: bank D1 + intercept min(D1,C2))
  CD: C1 - min(C1, D2) - D2 - B      (we are victim: production suppressed + bank raided)
  DD: D1 - D2 - B                    (net differential to larger D)
"""

from ..models import Action, GameView, Modification
from ..player import Player

B = 1  # operating cost burned per move
class Prophet(Player):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._starting_capital = None
        self._campaign = False  # whether the player is currently in a campaign (attacking)

    def _predict_opponent(self, view: GameView) -> Action:
        """Assume WE cooperate; predict the opponent picks its more profitable move."""
        c1 = view.own_c
        c2, d2 = view.opponent_c, view.opponent_d
        opp_ev_coop = c2 - B
        opp_ev_def = d2 + min(d2, c1) - B   # opponent raids us: bank d2 + intercept min(d2,c1)
        # TIE-BREAK: opponent COOPERATES on a tie. Use `>=` to make it defect on ties instead.
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
            ev_cooperate = c1 - B                     # CC
            ev_defect = d1 + min(d1, c2) - B          # DC
        else:  # predict opponent defects
            ev_cooperate = c1 - min(c1, d2) - d2 - B  # CD (we are the victim)
            ev_defect = d1 - d2 - B                   # DD

        # SURVIVAL OVERRIDE (non-EV): if we're losing (below starting capital) and even our
        # best option is negative, cooperate to break out of a death spiral / mutual-defect
        # attrition. Makes the strategy mirror-viable; gated on own_capital so it only fires
        # when genuinely underwater, never from a position of strength.
        best_ev = max(ev_cooperate, ev_defect)
        if best_ev < 0 and view.own_capital < self._starting_capital:
            self._campaign = False
            return Action.COOPERATE

        # we can bankrupt our opponent, so defect
        if abs(view.own_d) * view.own_d >= view.opponent_capital:
            self._campaign = True
            return Action.DEFECT

        # if we are unarmed, focus on building up our capital
        if view.own_d <= 0:
            self._campaign = False

        # TIE-BREAK: COOPERATE when EVs are equal. Use `>=` to prefer defection on ties.
        if ev_defect > ev_cooperate:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        if self._campaign:
            # if we are striking, we need to rearm
            return Modification.INCREASE_D

        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        if view.opponent_previous_action is Action.DEFECT:
            self._campaign = False
            return Modification.INCREASE_C

        return Modification.NO_CHANGE