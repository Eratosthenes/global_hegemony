"""Prophet: a one-step expected-value maximizer.

ACTION (choose_action): predicts the opponent (assuming WE cooperate) and plays the
higher-EV move, with a kill-trigger (finish a bankruptable opponent) and a survival
override (cooperate out of a losing position to stay mirror-viable).

SELF-MODIFICATION (choose_self_modification): EV-driven arming. Assume the opponent will
COOPERATE next turn, then compare our best-achievable EV if we INCREASE_D (arm) vs if we
INCREASE_C (build economy). Arm only when a bigger weapon would out-earn more production --
which, against a cooperator, happens precisely when the opponent is worth raiding (has C to
intercept). So Prophet arms toward exploitable opponents and builds economy otherwise.

Mechanics (B = operating cost; defection does interception + full bank-raid, all to raider):
  CC: C1 - B
  DC: D1 + min(D1, C2) - B
  CD: C1 - min(C1, D2) - D2 - B
  DD: D1 - D2 - B
"""

from ..models import Action, GameView, Modification
from ..player import Player

B = 1  # operating cost burned per move


class Prophet(Player):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._starting_capital = None

    # --- EV cells (from the acting player's perspective) -------------------

    @staticmethod
    def _ev_CC(c_act):            
        return c_act - B

    @staticmethod
    def _ev_DC(d_act, c_opp):     
        return d_act + min(d_act, c_opp) - B

    @staticmethod
    def _ev_CD(c_act, d_opp):     
        return c_act - min(c_act, d_opp) - d_opp - B

    @staticmethod
    def _ev_DD(d_act, d_opp):     
        return d_act - d_opp - B

    def _predict_opponent(self, view: GameView) -> Action:
        """Assume WE cooperate; predict the opponent picks its more profitable move."""
        c1 = view.own_c
        c2, d2 = view.opponent_c, view.opponent_d
        opp_ev_coop = self._ev_CC(c2)
        opp_ev_def = self._ev_DC(d2, c1)
        # TIE-BREAK: opponent COOPERATES on a tie. Use `>=` to make it defect on ties instead.
        if opp_ev_def > opp_ev_coop:
            return Action.DEFECT
        return Action.COOPERATE

    # --- action (UNCHANGED) ------------------------------------------------

    def choose_action(self, view: GameView) -> Action:
        if view.turn_number == 1:
            self._starting_capital = view.own_capital

        c1, d1 = view.own_c, view.own_d
        c2, d2 = view.opponent_c, view.opponent_d

        prediction = self._predict_opponent(view)

        if prediction is Action.COOPERATE:
            ev_cooperate = self._ev_CC(c1)            # CC
            ev_defect = self._ev_DC(d1, c2)           # DC
        else:  # predict opponent defects
            ev_cooperate = self._ev_CD(c1, d2)        # CD (we are the victim)
            ev_defect = self._ev_DD(d1, d2)           # DD

        # SURVIVAL OVERRIDE (non-EV): if losing (below starting capital) and even our best
        # option is negative, cooperate to break out of a death spiral / mutual-defect
        # attrition. Makes the strategy mirror-viable; only fires when genuinely underwater.
        best_ev = max(ev_cooperate, ev_defect)
        if best_ev < 0 and view.own_capital < self._starting_capital:
            return Action.COOPERATE

        # KILL-TRIGGER: if our weapon can bankrupt the opponent this turn, finish them.
        if abs(view.own_d) * view.own_d >= view.opponent_capital:
            return Action.DEFECT

        # TIE-BREAK: COOPERATE when EVs are equal. Use `>=` to prefer defection on ties.
        if ev_defect > ev_cooperate:
            return Action.DEFECT
        return Action.COOPERATE

    # --- EV-driven self-modification --------------------------------------

    def choose_self_modification(self, view: GameView) -> Modification:
        """Assume the opponent cooperates next turn; arm (INCREASE_D) iff that yields a higher best-achievable EV than building economy (INCREASE_C)."""
        # if we're underwater, don't arm; we need to build economy to survive
        if view.own_capital < self._starting_capital:
            return Modification.INCREASE_C

        c1, d1 = view.own_c, view.own_d
        c2 = view.opponent_c
        # If we INCREASE_C: next-turn structure (c1+1, d1-1). Best move vs a cooperator:
        #   produce CC(c1+1) or raid DC(d1-1, c2).
        ev_inc_c = max(self._ev_CC(c1 + 1), self._ev_DC(d1 - 1, c2))

        # If we INCREASE_D: next-turn structure (c1-1, d1+1). Best move vs a cooperator:
        #   produce CC(c1-1) or raid DC(d1+1, c2).
        ev_inc_d = max(self._ev_CC(c1 - 1), self._ev_DC(d1 + 1, c2))

        # TIE-BREAK: build economy (INCREASE_C) on a tie. Use `>=` to prefer arming on ties.
        if ev_inc_d > ev_inc_c:
            return Modification.INCREASE_D

        return Modification.INCREASE_C

    # --- opponent-modification (unchanged) --------------------------------

    def choose_opponent_modification(self, view: GameView) -> Modification:
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        return Modification.NO_CHANGE