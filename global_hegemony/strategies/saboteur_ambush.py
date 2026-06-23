"""SaboteurAmbush: farm the wallet, but also cripple the victim's PERSISTENT structure.

Tournament insight (persistence on the structure axis):
    A normal DisciplinedAmbush strikes, banks capital, and stands down -- but it lets the
    victim's C/D run away. Against AC that means AC EXITS the match at C=20/D=-10 and
    carries that monstrous economy into every later opponent. We farmed AC's wallet but
    left its economy STRONGER than we found it -- a gift to the rest of the field.

    In a tournament you are not only playing your opponent, you are setting the state they
    bring to everyone after you. Crippling a victim's C/D is an investment that pays out
    across all their downstream matches: they arrive at the next opponent deep in negative
    C, bleeding abs(C) on every cooperation. That is often worth MORE than the capital,
    because capital is a one-time steal while structural damage is a persistent debuff.

SaboteurAmbush keeps DisciplinedAmbush's solvency discipline (reversible strike, never
self-bankrupt, exit with a balanced C/D so OUR character stays healthy for later matches)
and adds the sabotage objective: during the strike, relentlessly drive the victim's C DOWN
so it leaves the match crippled.

Self-discipline note: we still must not wreck our OWN persistent structure. We strike from
the standing/ built reserve, stand down before bankruptcy, and recover toward a balanced
split -- our character must arrive at the next match solvent and armed, while the victim
arrives broke and crippled.
"""

from ..models import Action, GameView, Modification, Number
from ..player import Player


class SaboteurAmbush(Player):

    BUILDING = "building"
    STRIKING = "striking"
    RECOVERING = "recovering"

    SOLVENCY_FLOOR: Number = 20
    REARM_C_TARGET = 5
    # Later launch than vanilla Ambush: let the victim over-extend its C (so there is more
    # to strip) and bank a bigger reserve before striking. Tunable; higher = more patient.
    LAUNCH_PATIENCE = 1  # strike when projected cooperation capital margin <= this

    def __init__(
        self,
        name: str = "Saboteur Ambush",
        *,
        capital: Number = Player.STARTING_CAPITAL,
        c: int = 7,
        d: int = 3,
    ) -> None:
        super().__init__(name=name, capital=capital, c=c, d=d)
        self.phase = self.BUILDING

    # --- actions ----------------------------------------------------------

    def choose_action(self, view: GameView) -> Action:
        if self.phase == self.BUILDING:
            return self._act_building(view)
        if self.phase == self.STRIKING:
            return self._act_striking(view)
        return self._act_recovering(view)

    def _act_building(self, view: GameView) -> Action:
        if view.own_d > 0 and (
            self._project_capital_after_cooperation(view) <= self.LAUNCH_PATIENCE
            or self._cooperation_would_end_match(view)
            or view.own_d >= 11
        ):
            self.phase = self.STRIKING
            return Action.DEFECT
        return Action.COOPERATE

    def _act_striking(self, view: GameView) -> Action:
        # Stand down before risking solvency or once the weapon is spent -- protect OUR
        # persistent character. (We keep sabotaging via opponent-mod whenever we defect.)
        if view.own_capital - Player.OPERATING_COST <= self.SOLVENCY_FLOOR or view.own_d <= 0:
            self.phase = self.RECOVERING
            return Action.COOPERATE
        return Action.DEFECT

    def _act_recovering(self, view: GameView) -> Action:
        if view.own_c <= 0:
            return Action.DEFECT
        solvent = view.own_capital > self.SOLVENCY_FLOOR + Player.OPERATING_COST
        rearmed = view.own_c >= self.REARM_C_TARGET
        if solvent and rearmed:
            self.phase = self.BUILDING
        return Action.COOPERATE

    # --- modifications ----------------------------------------------------

    def choose_self_modification(self, view: GameView) -> Modification:
        if self.phase == self.BUILDING:
            return Modification.DECREASE_C   # build the weapon
        if self.phase == self.RECOVERING:
            if view.own_c < self.REARM_C_TARGET:
                return Modification.INCREASE_C   # rebuild production / pull D back to balance
            return Modification.NO_CHANGE
        return Modification.NO_CHANGE            # striking: hold the weapon

    def choose_opponent_modification(self, view: GameView) -> Modification:
        # SABOTAGE: whenever we defect (strike phase), drive the victim's C DOWN so it
        # exits the match crippled and carries negative C into its next opponent. This is
        # the persistent-state weapon -- a debuff on the victim's whole remaining tournament.
        return Modification.DECREASE_C

    # --- projections ------------------------------------------------------

    @staticmethod
    def _project_capital_after_cooperation(view: GameView) -> Number:
        production_change = view.own_c if view.own_c >= 0 else -abs(view.own_c)
        return view.own_capital + production_change - Player.OPERATING_COST

    @staticmethod
    def _cooperation_would_end_match(view: GameView) -> bool:
        drain = view.own_c + view.opponent_c - 2
        return drain > 0 and view.environment_bank <= drain