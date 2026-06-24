"""DisciplinedAmbush: Ambush's strike timing, minus the suicide.

The original Ambush has one fatal bug: has_launched is a one-way latch to PERMANENT defection. Permanent defection is self-terminating -- the defector pays operating cost forever while its raid/tribute income dries up (victims get disarmed, the environment burns down), so it rides its own capital to zero. It wins matches (Vulture Prizes, big blowouts) but bankrupts itself doing so, and an eligibility-based tournament scores every such "win" as a zero. The lethality and the fragility are the same line of code.

Fix: make the strike CONDITIONAL and REVERSIBLE. Ambush already computes a sound launch trigger (strike when continued cooperation would bankrupt us or exhaust the bank). The bug is that it never asks the symmetric question on the way back. A disciplined predator strikes while defection is net-positive and capital is healthy, then STANDS DOWN before a strike turn would push it toward the same bankruptcy boundary that triggered the launch -- re-industrializes, rebuilds capital and C, and re-arms for a later strike. Raid-and-recover instead of raid-until-death. Never touches zero, so it stays tournament-eligible.

State machine:
    BUILDING  -- cooperate, convert C->D, accumulate capital and reserve (as before)
    STRIKING  -- defect while it pays and we stay solvent
    RECOVERING-- cooperate, rebuild C and capital, until safe to re-arm, then BUILDING
"""

from ..models import Action, GameView, Modification, Number
from ..player import Player


class DisciplinedAmbush(Player):

    BUILDING = "building"
    STRIKING = "striking"
    RECOVERING = "recovering"

    # Capital floor we refuse to strike below. The original's bug was effectively
    # floor = 0 with no way back; we stand down with a real buffer so a raid turn's
    # costs/clashes can never tip us into bankruptcy.
    SOLVENCY_FLOOR: Number = 20

    # While recovering, rebuild C back to at least this before considering a new buildup.
    REARM_C_TARGET = 5

    def __init__(
        self,
        name: str = "Disciplined Ambush",
        *,
        capital: Number = Player.STARTING_CAPITAL,
        c: int = 5,
        d: int = 5,
    ) -> None:
        super().__init__(name=name, capital=capital, c=c, d=d)
        self.phase = self.BUILDING

    # --- phase transitions -------------------------------------------------

    def choose_action(self, view: GameView) -> Action:
        if self.phase == self.BUILDING:
            return self._act_building(view)
        if self.phase == self.STRIKING:
            return self._act_striking(view)
        return self._act_recovering(view)

    def _act_building(self, view: GameView) -> Action:
        # Launch on the original trigger: continued cooperation would bankrupt us or
        # exhaust the bank, and we actually have a weapon.
        if view.own_d > 0 and (
            self._project_capital_after_cooperation(view) <= 0
            or self._cooperation_would_end_match(view)
        ):
            self.phase = self.STRIKING
            return Action.DEFECT
        return Action.COOPERATE

    def _act_striking(self, view: GameView) -> Action:
        # THE FIX: stand down before a strike turn risks our solvency, or once striking
        # has stopped paying (weapon spent / opponent disarmed to non-positive D).
        if view.own_capital - Player.OPERATING_COST <= self.SOLVENCY_FLOOR or view.own_d <= 0:
            self.phase = self.RECOVERING
            return Action.COOPERATE
        return Action.DEFECT

    def _act_recovering(self, view: GameView) -> Action:
        # Rebuild. Cooperate to harvest and re-industrialize until we are solvent and
        # re-armed, then resume a fresh buildup. If cooperation would bleed (C<=0), we
        # must still defect to avoid the abs(C) penalty.
        if view.own_c <= 0:
            return Action.DEFECT
        solvent = view.own_capital > self.SOLVENCY_FLOOR + Player.OPERATING_COST
        rearmed = view.own_c >= self.REARM_C_TARGET
        if solvent and rearmed:
            self.phase = self.BUILDING
        return Action.COOPERATE

    # --- structural modifications -----------------------------------------

    def choose_self_modification(self, view: GameView) -> Modification:
        if self.phase == self.BUILDING:
            return Modification.INCREASE_D   # convert C -> D, building the weapon
        if self.phase == self.RECOVERING:
            # Re-industrialize: rebuild productive capacity (and pull D back from any
            # negative excursion the clash drove us into).
            if view.own_c < self.REARM_C_TARGET:
                return Modification.INCREASE_C
            return Modification.NO_CHANGE
        return Modification.NO_CHANGE        # striking: hold the weapon

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # resist if we are attacked
        if view.opponent_previous_action is Action.DEFECT:
            return Modification.INCREASE_C
        
        # if we are under-armed, try to catch up
        if view.own_d < view.opponent_d:
            return Modification.INCREASE_D
        
        return Modification.NO_CHANGE

    # --- projections (same shape as the original) -------------------------

    @staticmethod
    def _project_capital_after_cooperation(view: GameView) -> Number:
        production_change = view.own_c if view.own_c >= 0 else -abs(view.own_c)
        return view.own_capital + production_change - Player.OPERATING_COST

    @staticmethod
    def _cooperation_would_end_match(view: GameView) -> bool:
        synergy = 2 if view.own_c + view.opponent_c > 2 else 0
        available = view.environment_bank + synergy
        total_request = max(0, view.own_c) + max(0, view.opponent_c)
        return total_request >= available