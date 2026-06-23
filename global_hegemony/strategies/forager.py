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

    def _victim_defanged(self, view: GameView) -> bool:
        # Opponent has no functioning weapon: free to raid, cannot punish back.
        return view.opponent_d <= 0

    def choose_action(self, view: GameView) -> Action:
        # Feed on a defanged opponent: defection strictly dominates here.
        if self._victim_defanged(view) and view.own_d > 0:
            return Action.DEFECT

        # If WE are defanged, cooperating only bleeds abs(C); defect instead.
        if view.own_c <= 0:
            return Action.DEFECT

        # Opponent is re-fanged (can punish) and we are healthy: coexist + industrialize.
        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        # While feeding, hold the weapon: INCREASE_C raises our C and keeps D from being
        # dragged negative by the victim's disarm, so we can keep defecting. When coexisting,
        # the same INCREASE_C is just industrialization. Either way, never self-convert to
        # negative C (no self-bleed that would persist into later matches).
        if view.own_d > 3:
            return Modification.INCREASE_C
        elif view.own_d < 3:
            return Modification.DECREASE_C 
        else:
            return Modification.NO_CHANGE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # While feeding on a defanged victim, suppress its production (DECREASE_C) -- a
        # high-C victim that we knock down stays a victim AND exits the match crippled.
        if self._victim_defanged(view):
            return Modification.DECREASE_C
        # Against a re-fanged opponent that we may have to defect on, push it back toward
        # negative D (disarm) so it cannot sustain an attack on us.
        return Modification.INCREASE_C