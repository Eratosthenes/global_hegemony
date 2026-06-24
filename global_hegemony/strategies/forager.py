"""Forager: exploit any defanged opponent, hold the weapon against their disarm.

The dominance argument (yours):
    If the opponent has D <= 0 then (C + D = 10) they have C >= 10 -- a fat producer with
    no functioning weapon. Against such a target, defection STRICTLY dominates cooperation:
    you intercept and raid AND pay no price, because a negative-D opponent cannot retaliate
    with force. So the rational play vs a defanged opponent is: defect EVERY turn, and
    INCREASE your own C so your own D stays positive and your weapon stays loaded -- a
    feeding loop. Return to cooperation only once the victim has clawed its D back positive
    (i.e. re-fanged itself and can punish you).

This is the precise counter to PI / AlwaysCooperate. PI's engine drives BOTH players toward
the C>=10 / D<=0 corner -- it manufactures exactly the defanged victim that makes it prey,
and it has no defection branch to interrupt the loop. PI is the best response to another PI
and a near-worst response to a committed self-arming defector; it is half a coordination
equilibrium, not a winning strategy.

Crucially, Forager holds its own D against the victim's disarm. PI beat AlwaysDefect only by
dragging it to negative-D tribute; Forager counters that by self-INCREASE_C each feeding turn
so the victim's INCREASE_C-on-us is cancelled and our D never crosses to tribute.

Phase logic, keyed entirely on the opponent's D sign:
    opponent_d <= 0  (defanged)  -> FEED:  DEFECT, hold weapon (self INCREASE_C), suppress.
    opponent_d  > 0  (re-fanged) -> COEXIST: cooperate and industrialize (PI-vs-PI peace),
                                     unless WE are the one defanged (own_c <= 0), then defect.
"""

from ..models import Action, GameView, Modification
from ..player import Player


class Forager(Player):

    def choose_action(self, view: GameView) -> Action:
        # feed on a helpless opponent: defection strictly dominates here.
        if view.opponent_d <= 0 and view.own_d > 0:
            return Action.DEFECT

        # If WE are fully armed, there's no point in cooperating
        if view.own_c <= 0:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        return Modification.INCREASE_C

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # if they just attacked, we resist
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        
        return Modification.NO_CHANGE