"""Authoritative match engine and payoff resolution."""

from __future__ import annotations

from typing import Optional

from .environment import Environment
from .models import Action, GameView, Modification, Number, TurnRecord
from .player import Player


class Match:
    def __init__(
        self,
        player_1: Player,
        player_2: Player,
        environment: Optional[Environment] = None,
    ) -> None:
        self.player_1 = player_1
        self.player_2 = player_2
        self.environment = environment or Environment()

        self.turn_number = 0
        self.finished = False
        self.winner: Optional[Player] = None
        self.end_reason: Optional[str] = None
        self.turn_log: list[TurnRecord] = []
        self.append_initial_turn_record()
    
    def append_initial_turn_record(self) -> None:
        """Append a turn record for turn 0, before any actions have been taken."""
        record = TurnRecord(
            turn=0,
            p1_action="-",
            p1_mod_dc="",
            p1_c=self.player_1.c,
            p1_d=self.player_1.d,
            p1_capital_delta=0,
            p1_vulture_prize=0,
            p1_capital=self.player_1.capital,
            p2_action="-",
            p2_mod_dc="",
            p2_c=self.player_2.c,
            p2_d=self.player_2.d,
            p2_capital_delta=0,
            p2_vulture_prize=0,
            p2_capital=self.player_2.capital,
            environment_delta=0,
            environment=self.environment.bank,
        )
        self.turn_log.append(record)

    @property
    def is_over(self) -> bool:
        return self.finished

    def play(self, max_turns: int = 1_000, verbose: bool = False) -> None:
        while not self.is_over:
            if self.turn_number >= max_turns:
                raise RuntimeError(
                    f"Match did not terminate within {max_turns} turns."
                )
            self.play_turn(verbose=verbose)

    def play_turn(self, verbose: bool = False) -> TurnRecord:
        if self.is_over:
            raise RuntimeError("Cannot play a turn after the match has ended.")

        self.turn_number += 1

        start_p1_capital = self.player_1.capital
        start_p2_capital = self.player_2.capital
        start_environment = self.environment.bank

        view_1 = self._make_view(self.player_1, self.player_2)
        view_2 = self._make_view(self.player_2, self.player_1)

        # Both actions are selected from the same pre-turn state.
        action_1 = self.player_1.choose_action(view_1)
        action_2 = self.player_2.choose_action(view_2)
        self._validate_action(action_1, self.player_1)
        self._validate_action(action_2, self.player_2)

        self._resolve_actions(action_1, action_2)

        self.player_1.pay_operating_cost()
        self.player_2.pay_operating_cost()

        self.player_1.previous_action = action_1
        self.player_1.opponent_previous_action = action_2
        self.player_2.previous_action = action_2
        self.player_2.opponent_previous_action = action_1

        p1_vulture_prize, p2_vulture_prize = self._resolve_terminal_state()

        p1_mod = Modification.NO_CHANGE
        p2_mod = Modification.NO_CHANGE
        if not self.is_over:
            p1_mod, p2_mod = self._resolve_modifications(action_1, action_2)

        record = TurnRecord(
            turn=self.turn_number,
            p1_action=action_1.value,
            p1_mod_dc=p1_mod.value,
            p1_c=self.player_1.c,
            p1_d=self.player_1.d,
            p1_capital_delta=self.player_1.capital - start_p1_capital,
            p1_vulture_prize=p1_vulture_prize,
            p1_capital=self.player_1.capital,
            p2_action=action_2.value,
            p2_mod_dc=p2_mod.value,
            p2_c=self.player_2.c,
            p2_d=self.player_2.d,
            p2_capital_delta=self.player_2.capital - start_p2_capital,
            p2_vulture_prize=p2_vulture_prize,
            p2_capital=self.player_2.capital,
            environment_delta=self.environment.bank - start_environment,
            environment=self.environment.bank,
        )
        self.turn_log.append(record)

        if verbose:
            from .reporting import print_turn

            print_turn(record)

        return record

    def _resolve_actions(self, action_1: Action, action_2: Action) -> None:
        if action_1 is Action.COOPERATE and action_2 is Action.COOPERATE:
            self._resolve_mutual_cooperation()
        elif action_1 is Action.DEFECT and action_2 is Action.DEFECT:
            self._resolve_mutual_defection()
        elif action_1 is Action.DEFECT:
            self._resolve_unilateral_defection(self.player_1, self.player_2)
        else:
            self._resolve_unilateral_defection(self.player_2, self.player_1)

    def _apply_cooperation_capacity(self, player: Player) -> Number:
        """Return extraction request, charging capital when C is negative."""
        if player.c >= 0:
            return player.c

        player.capital -= abs(player.c)
        return 0

    def _resolve_mutual_cooperation(self) -> None:
        self.environment.apply_synergy(self.player_1.c, self.player_2.c)

        requested_1 = self._apply_cooperation_capacity(self.player_1)
        requested_2 = self._apply_cooperation_capacity(self.player_2)
        extraction_1, extraction_2 = self._allocate_simultaneous_extraction(
            requested_1,
            requested_2,
        )

        self.player_1.capital += extraction_1
        self.player_2.capital += extraction_2

    def _allocate_simultaneous_extraction(
        self,
        requested_1: Number,
        requested_2: Number,
    ) -> tuple[int, int]:
        requested_1 = int(requested_1)
        requested_2 = int(requested_2)
        available = int(self.environment.bank)

        total_requested = requested_1 + requested_2

        if total_requested <= 0 or available <= 0:
            return 0, 0

        if total_requested <= available:
            self.environment.bank -= total_requested
            return requested_1, requested_2

        # Compute each player's proportional allocation using integer arithmetic.
        numerator_1 = available * requested_1
        numerator_2 = available * requested_2

        extraction_1, remainder_1 = divmod(numerator_1, total_requested)
        extraction_2, remainder_2 = divmod(numerator_2, total_requested)

        # Flooring may leave one environmental point unallocated.
        leftover = available - extraction_1 - extraction_2

        if leftover:
            if remainder_1 > remainder_2:
                extraction_1 += leftover
            elif remainder_2 > remainder_1:
                extraction_2 += leftover
            elif self.turn_number % 2 == 1:
                # Alternate exact ties so neither player position is privileged.
                extraction_1 += leftover
            else:
                extraction_2 += leftover

        self.environment.bank = 0
        return extraction_1, extraction_2
        
    def _resolve_unilateral_defection(
        self,
        attacker: Player,
        cooperator: Player,
    ) -> None:
        requested = self._apply_cooperation_capacity(cooperator)
        extracted = self.environment.extract(requested)

        if attacker.d >= 0:
            intercepted = min(extracted, attacker.d)
            retained_by_cooperator = extracted - intercepted
            vault_raid = attacker.d

            cooperator.capital += retained_by_cooperator - vault_raid
            attacker.capital += intercepted + vault_raid
        else:
            charity = abs(attacker.d)
            cooperator.capital += extracted + charity
            attacker.capital -= charity

        self.environment.apply_defection_cost()

    def _resolve_mutual_defection(self) -> None:
        difference = self.player_1.d - self.player_2.d

        if difference > 0:
            self.player_1.capital += difference
            self.player_2.capital -= difference
        elif difference < 0:
            transfer = abs(difference)
            self.player_2.capital += transfer
            self.player_1.capital -= transfer

        self.environment.apply_defection_cost()

    def _resolve_modifications(
        self,
        action_1: Action,
        action_2: Action,
    ) -> tuple[Modification, Modification]:
        if action_1 is Action.DEFECT and action_2 is Action.DEFECT:
            return Modification.NO_CHANGE, Modification.NO_CHANGE

        if action_1 is Action.COOPERATE and action_2 is Action.COOPERATE:
            view_1 = self._make_view(self.player_1, self.player_2)
            view_2 = self._make_view(self.player_2, self.player_1)

            mod_1 = self.player_1.choose_self_modification(view_1)
            mod_2 = self.player_2.choose_self_modification(view_2)
            self._validate_modification(mod_1, self.player_1)
            self._validate_modification(mod_2, self.player_2)

            self.player_1.apply_modification(mod_1)
            self.player_2.apply_modification(mod_2)
            return mod_1, mod_2

        if action_1 is Action.DEFECT:
            attacker, victim = self.player_1, self.player_2
            p1_is_attacker = True
        else:
            attacker, victim = self.player_2, self.player_1
            p1_is_attacker = False

        attacker_view = self._make_view(attacker, victim)
        victim_view = self._make_view(victim, attacker)

        conquest = attacker.choose_opponent_modification(attacker_view)
        retaliation = victim.choose_opponent_modification(victim_view)
        self._validate_modification(conquest, attacker)
        self._validate_modification(retaliation, victim)

        # Both choices are selected before either structural edit occurs.
        victim.apply_modification(conquest)
        attacker.apply_modification(retaliation)

        if p1_is_attacker:
            return conquest, retaliation
        return retaliation, conquest

    def _resolve_terminal_state(self) -> tuple[Number, Number]:
        p1_bankrupt = self.player_1.is_bankrupt
        p2_bankrupt = self.player_2.is_bankrupt

        if p1_bankrupt and p2_bankrupt:
            self.finished = True
            self.winner = None
            self.end_reason = "simultaneous bankruptcy"
            self.environment.bank = 0
            return 0, 0

        if p1_bankrupt or p2_bankrupt:
            prize = max(0, self.environment.bank)

            if p1_bankrupt:
                self.player_2.capital += prize
                self.winner = self.player_2
                p1_prize, p2_prize = 0, prize
                self.end_reason = f"{self.player_1.name} went bankrupt"
            else:
                self.player_1.capital += prize
                self.winner = self.player_1
                p1_prize, p2_prize = prize, 0
                self.end_reason = f"{self.player_2.name} went bankrupt"

            self.environment.bank = 0
            self.finished = True
            return p1_prize, p2_prize

        if self.environment.is_exhausted:
            self.finished = True
            self.end_reason = "environmental exhaustion"

            if self.player_1.capital > self.player_2.capital:
                self.winner = self.player_1
            elif self.player_2.capital > self.player_1.capital:
                self.winner = self.player_2
            else:
                self.winner = None

        return 0, 0

    def _make_view(self, player: Player, opponent: Player) -> GameView:
        return GameView(
            turn_number=self.turn_number,
            environment_bank=self.environment.bank,
            own_capital=player.capital,
            own_c=player.c,
            own_d=player.d,
            opponent_capital=opponent.capital,
            opponent_c=opponent.c,
            opponent_d=opponent.d,
            own_previous_action=player.previous_action,
            opponent_previous_action=player.opponent_previous_action,
        )

    @staticmethod
    def _validate_action(action: Action, player: Player) -> None:
        if not isinstance(action, Action):
            raise TypeError(f"{player.name} returned invalid action {action!r}.")

    @staticmethod
    def _validate_modification(
        modification: Modification,
        player: Player,
    ) -> None:
        if not isinstance(modification, Modification):
            raise TypeError(
                f"{player.name} returned invalid modification {modification!r}."
            )
