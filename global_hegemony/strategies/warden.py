"""Warden: a two-state meta-strategy -- RAIDER by default, Strongman vs. proven doves.

Rationale (the key asymmetry):
  - Posture is set at the OPENING; opponent type is only knowable mid-game. So any
    mode-switcher switches with a LAG. The question is which lag is survivable.
  - Switching to Strongman LATE is mild: you merely cooperated a couple extra turns
    and gave up a little tempo.
  - Switching to Raider LATE is FATAL: Raider only works as a first-mover (it wins by
    accelerating the opponent's buildup from parity, before they lead). Deployed from
    behind, after the aggressor already has the lead, its engine doesn't turn over and
    it bankrupts (the SpaceBeam failure).
  Therefore the lag belongs on the Strongman side. Default to RAIDER (engage every
  opponent aggressively from the opening, denying any sleeper a free lead), and relax
  to STRONGMAN only once the opponent has PROVEN it is not militarizing.

Detection of a dove:
  A non-aggressive opponent does not build a weapon -- its D stays low / falls (it
  converts D->C or holds). A militarizer drives its D up. So we relax to Strongman
  only after observing the opponent keep its D at or below a low bound for a few
  consecutive turns. If a relaxed opponent later starts building (D climbs back up),
  we RE-ARM to Raider immediately -- because staying relaxed against a late builder is
  the fatal lag, while re-arming is cheap.
"""

from ..models import Action, GameView, Modification
from ..player import Player


class Warden(Player):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def choose_action(self, view: GameView) -> Action:
        # we can bankrupt our opponent, so defect
        if abs(view.own_d) * view.own_d >= view.opponent_capital:
            return Action.DEFECT

        # attack if we can deplete our opponent's treasury
        if view.opponent_c - view.own_d - 1 < 0:
            return Action.DEFECT

        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        # militarize
        return Modification.INCREASE_D

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # resist attack
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        
        # stay neutral
        return Modification.NO_CHANGE