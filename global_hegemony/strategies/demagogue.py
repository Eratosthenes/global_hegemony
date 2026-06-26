"""Demagogue: a simple strategy built to EXPLOIT Strongman's de-escalation handshake.

Strongman (and any mirror-viable strategy) carries a de-escalation clause:

    if both defected last turn -> cooperate

This is necessary for self-coexistence, but it is UNCONDITIONAL forgiveness after mutual defection, and that is exploitable. Demagogue pumps it:

    - After a mutual defection, DEFECT again. A Strongman, seeing "both defected last turn," will reflexively COOPERATE -- so we raid a cooperator (DC, big gain).
    - The next turn it is no longer mutual defection (we defected, they cooperated), so the handshake doesn't fire; Strongman defends/defects, re-establishing D/D -- which re-arms the handshake for us to slap again.

Otherwise Demagogue is simple: build economy by default, defend when attacked.
"""

from ..models import Action, GameView, Modification
from ..player import Player


class Demagogue(Player):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._starting_capital = None
        self._prev_capital = None 
        self._losing_money = False 

    def choose_action(self, view: GameView) -> Action:
        if view.turn_number == 1:
            self._starting_capital = view.own_capital
            self._prev_capital = view.own_capital
        
        # if we are losing money late in the game, cooperate
        # this is the same type of vulnerability that Strongman has, but it makes the stategy mirror-viable
        self._losing_money = view.turn_number > 10 and view.own_capital < self._prev_capital
        self._prev_capital = view.own_capital # update for next turn
        if self._losing_money:
            return Action.COOPERATE

        my_prev = view.own_previous_action
        op_prev = view.opponent_previous_action

        # EXPLOIT: after a mutual defection, defect again -- a handshake-using opponent will
        # cooperate this turn (trying to de-escalate), so we raid their cooperation.
        if my_prev is Action.DEFECT and op_prev is Action.DEFECT:
            return Action.DEFECT

        # DEFEND: if we were just attacked (opponent defected while we didn't mutually-defect),
        # retaliate to establish the mutual defection that arms the exploit -- and to not be a free victim.
        if op_prev is Action.DEFECT:
            return Action.DEFECT

        # PROBE: if we are armed and hold a weapon edge, defect to initiate -- this kicks off the first D/D so the handshake pump can begin. 
        # Only from a non-losing position.
        if view.own_d > 0 and view.own_d >= view.opponent_d:
            return Action.DEFECT

        # Otherwise cooperate (build the relationship / our own economy).
        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        # Grow economy by default.
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        if view.own_previous_action is Action.DEFECT and \
            view.opponent_previous_action is Action.COOPERATE:
            # we are exploiting them; keep them from re-arming
            return Modification.INCREASE_C
        
        # Defend: if attacked, push their C up / D down so they can't sustain a raid on us.
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        
        return Modification.NO_CHANGE