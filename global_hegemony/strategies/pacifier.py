"""A disarming pacifist: drag the opponent into negative-D tribute without bleeding out.
 
Design thesis (from observed matches):
    The action choice barely matters in this game; the modification war decides outcomes. AlwaysCooperate beats AlwaysDefect not by fighting but by pushing the defector's C up every turn until its D goes negative and its 'attacks' become tribute. AC's only flaw is that its unconditional self-INCREASE_C drives its own C deeply negative, so it bleeds abs(C) capital on every cooperative turn and only survives because matches are short.
 
    Pacifier keeps AC's winning engine -- relentlessly push the opponent's C up (their D down, toward negative-D tribute) -- but fixes the self-bleed by holding its OWN C inside a defensive band near zero instead of letting it run negative.  It produces while it safely can, stops descending before cooperation starts costing capital, and climbs back up if anything has shoved it underwater.
"""
 
from ..models import Action, GameView, Modification
from ..player import Player
 
 
class Pacifier(Player):
    """Cooperate, disarm the opponent unconditionally, and never bleed yourself out.
 
    - Action: COOPERATE while own C is high enough to produce rather than bleed; DEFECT only as a last resort when own C has been forced non-positive (at which point cooperation costs abs(C) and produces nothing, so there is no reason to keep offering it).
    - Self-modification: steer own C into a safe band. Stop converting C->D before production turns into bleeding; recover upward if forced negative.  
    - Opponent-modification: always push their C up (D down). This is the engine that converts a raider into a tribute source.
    """
 
    # Hold own C in [LOW, HIGH]. LOW > 0 guarantees cooperation always produces and
    # never bleeds abs(C); a small band keeps D modest so we are never the aggressor.
    SAFE_C_LOW = 1
    SAFE_C_HIGH = 3
 
    def choose_action(self, view: GameView) -> Action:
        # Cooperating with non-positive C produces nothing and costs abs(C). Once an
        # opponent (or our own conversions) has forced us there, stop offering peace.
        if view.own_c <= 0:
            return Action.DEFECT
        return Action.COOPERATE
 
    def choose_self_modification(self, view: GameView) -> Modification:
        # Keep own C inside the defensive band.
        if view.own_c < self.SAFE_C_LOW:
            return Modification.INCREASE_C   # recover: climb out of the bleed zone
        if view.own_c > self.SAFE_C_HIGH:
            return Modification.DECREASE_C   # trim excess C into a little defensive D
        return Modification.NO_CHANGE
 
    def choose_opponent_modification(self, view: GameView) -> Modification:
        # The winning engine: always drive the opponent's C up / D down. A persistent
        # raider is walked into negative D, where its defections pay us tribute.
        return Modification.INCREASE_C
 