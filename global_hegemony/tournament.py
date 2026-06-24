"""Round-robin tournament runner for Global Hegemony.

Two tournament modes are supported:

FRESH
    Every matchup receives newly constructed player instances. Ending capital
    from every occupied seat is added to the strategy's tournament points.

PERSISTENT
    One live player instance is maintained for each strategy throughout the
    ordinary round robin. Capital, C/D structure, action memory, and any
    strategy-specific instance state carry from one match to the next. Each
    match still receives a fresh Environment through the Match constructor.

All distinct pairings are played first. Self-play matches are always last.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from random import Random
from statistics import fmean, stdev
from typing import Callable, Iterable

from .formatting import format_number
from .match import Match
from .models import Number
from .player import Player


PlayerFactory = Callable[[], Player]


class TournamentMode(Enum):
    """How player state is created and carried through the tournament."""

    FRESH = "fresh"
    PERSISTENT = "persistent"


@dataclass(frozen=True)
class TournamentEntry:
    """A named strategy and a factory that creates a player instance."""

    name: str
    factory: PlayerFactory

    @classmethod
    def from_player_class(
        cls,
        name: str,
        player_class: type[Player],
        **player_kwargs: object,
    ) -> "TournamentEntry":
        """Create an entry from a Player subclass."""

        def factory() -> Player:
            return player_class(name=name, **player_kwargs)

        return cls(name=name, factory=factory)

    def create_player(self) -> Player:
        player = self.factory()

        if not isinstance(player, Player):
            raise TypeError(
                f"Factory for {self.name!r} returned "
                f"{type(player).__name__}, not a Player instance."
            )

        return player


@dataclass(frozen=True)
class MatchResult:
    """Compact final result for one scheduled tournament matchup."""

    match_number: int
    p1: str
    p2: str
    k1: Number
    k2: Number
    outcome: str
    end_reason: str
    self_play: bool = False


@dataclass
class Standing:
    """Accumulated tournament record for one strategy."""

    name: str
    points: Number = 0
    matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    disqualification_reason: str | None = None

    @property
    def disqualified(self) -> bool:
        return self.disqualification_reason is not None

    @property
    def status(self) -> str:
        if self.disqualification_reason is None:
            return "Eligible"

        return f"DQ: {self.disqualification_reason}"


@dataclass(frozen=True)
class TournamentSampleStatistics:
    """Aggregate results for one strategy across randomized tournaments."""

    name: str
    samples: int
    average_points: float
    max_points: Number
    points_standard_deviation: float
    average_wins: float
    average_losses: float
    average_draws: float
    average_bankruptcies: float

class Tournament:
    """Run a complete Global Hegemony round-robin tournament.

    In both modes:

        1. Every distinct pair of strategies plays once.
        2. Every strategy plays itself after all distinct pairings.
        3. The highest-scoring eligible strategy wins.

    FRESH scoring:

        Every match uses fresh players. Each strategy receives the ending
        capital of every seat it occupies. Self-play therefore contributes
        both K1 and K2.

    PERSISTENT scoring:

        One live player per strategy carries state through all ordinary
        matches. Its capital is its running score; ordinary match-ending
        capital is not repeatedly added.

        During the final self-match, two deep copies of the accumulated player
        state are used. Their ending capitals are combined to produce the
        strategy's final point total.

        A player that goes bankrupt during an ordinary persistent match is
        disqualified and forfeits later scheduled matches. Bankruptcy by
        either copy during self-play also disqualifies the strategy.
    """

    def __init__(
        self,
        entries: Iterable[TournamentEntry],
        *,
        mode: TournamentMode = TournamentMode.FRESH,
        max_turns_per_match: int = 1_000,
    ) -> None:
        self.entries = list(entries)

        if not self.entries:
            raise ValueError("A tournament requires at least one entry.")

        if not isinstance(mode, TournamentMode):
            raise TypeError("mode must be a TournamentMode value.")

        names = [entry.name for entry in self.entries]

        duplicate_names = sorted(
            {
                name
                for name in names
                if names.count(name) > 1
            }
        )

        if duplicate_names:
            duplicates = ", ".join(
                repr(name)
                for name in duplicate_names
            )

            raise ValueError(
                f"Tournament entry names must be unique: {duplicates}"
            )

        if max_turns_per_match <= 0:
            raise ValueError("max_turns_per_match must be positive.")

        self.mode = mode
        self.max_turns_per_match = max_turns_per_match

        self.results: list[MatchResult] = []

        self.standings: dict[str, Standing] = {
            entry.name: Standing(name=entry.name)
            for entry in self.entries
        }

        self._live_players: dict[str, Player] = {}
        self._has_run = False
    
    @staticmethod
    def _round_robin_rounds(
        entries: list[TournamentEntry],
    ) -> list[list[tuple[TournamentEntry, TournamentEntry]]]:
        """
        Generate balanced round-robin pairings using the circle method.

        Every player appears exactly once per round. Consequently, both players
        in every matchup have completed the same number of previous matches.

        Exact balancing requires an even number of entries.
        """
        if len(entries) % 2 != 0:
            raise ValueError(
                "Balanced persistent tournaments require an even number of "
                "players. Add another strategy so nobody receives a bye."
            )

        rotation = list(entries)
        rounds: list[
            list[tuple[TournamentEntry, TournamentEntry]]
        ] = []

        for _ in range(len(rotation) - 1):
            pairings: list[
                tuple[TournamentEntry, TournamentEntry]
            ] = []

            for index in range(len(rotation) // 2):
                player_1 = rotation[index]
                player_2 = rotation[-1 - index]
                pairings.append((player_1, player_2))

            rounds.append(pairings)

            # Keep the first entry fixed and rotate every other entry.
            rotation = [
                rotation[0],
                rotation[-1],
                *rotation[1:-1],
            ]

        return rounds
    
    def run(self) -> None:
        """Play a balanced round robin, followed by self-play."""

        if self._has_run:
            raise RuntimeError(
                "This Tournament instance has already been run."
            )

        if self.mode is TournamentMode.PERSISTENT:
            self._live_players = {
                entry.name: entry.create_player()
                for entry in self.entries
            }

            rounds = self._round_robin_rounds(self.entries)

            for round_number, pairings in enumerate(rounds, start=1):
                for entry_1, entry_2 in pairings:
                    self._play_persistent_head_to_head(
                        entry_1,
                        entry_2,
                    )

        else:
            # Match order is irrelevant in fresh mode, but using the same
            # balanced schedule keeps the output consistent.
            if len(self.entries) % 2 == 0:
                rounds = self._round_robin_rounds(self.entries)

                for pairings in rounds:
                    for entry_1, entry_2 in pairings:
                        self._play_fresh_match(
                            entry_1,
                            entry_2,
                            self_play=False,
                        )
            else:
                # Fresh players have no inherited state, so ordinary combinations
                # remain fair even with an odd number of entries.
                for entry_1, entry_2 in combinations(self.entries, 2):
                    self._play_fresh_match(
                        entry_1,
                        entry_2,
                        self_play=False,
                    )

        # Self-play is the final round. At this point every strategy in a
        # balanced persistent tournament has faced the same number of opponents.
        for entry in self.entries:
            if self.mode is TournamentMode.FRESH:
                self._play_fresh_match(
                    entry,
                    entry,
                    self_play=True,
                )
            else:
                self._play_persistent_self_match(entry)

        self._has_run = True

    def get_live_player(self, entry_name: str) -> Player:
        """Return a live player from a persistent tournament."""

        if self.mode is not TournamentMode.PERSISTENT:
            raise RuntimeError(
                "Live players exist only in TournamentMode.PERSISTENT."
            )

        if entry_name not in self._live_players:
            raise KeyError(
                f"No persistent player named {entry_name!r}."
            )

        return self._live_players[entry_name]

    # ------------------------------------------------------------------
    # Fresh-player mode
    # ------------------------------------------------------------------

    def _play_fresh_match(
        self,
        entry_1: TournamentEntry,
        entry_2: TournamentEntry,
        *,
        self_play: bool,
    ) -> None:
        player_1 = entry_1.create_player()
        player_2 = entry_2.create_player()

        if player_1 is player_2:
            raise ValueError(
                f"Factory for {entry_1.name!r} returned the same object twice. "
                "A player factory must create a fresh instance on every call."
            )

        match = self._run_match(player_1, player_2)

        k1 = player_1.capital
        k2 = player_2.capital

        self._record_result(
            entry_1,
            entry_2,
            match,
            k1,
            k2,
            self_play=self_play,
        )

        if self_play:
            standing = self.standings[entry_1.name]

            standing.points += k1 + k2
            standing.matches += 1
            standing.draws += 1

            if player_1.is_bankrupt or player_2.is_bankrupt:
                standing.disqualification_reason = "self-bankruptcy"

            return

        self._score_fresh_head_to_head(
            entry_1,
            entry_2,
            match,
            k1,
            k2,
        )

    def _score_fresh_head_to_head(
        self,
        entry_1: TournamentEntry,
        entry_2: TournamentEntry,
        match: Match,
        k1: Number,
        k2: Number,
    ) -> None:
        standing_1 = self.standings[entry_1.name]
        standing_2 = self.standings[entry_2.name]

        standing_1.points += k1
        standing_2.points += k2

        self._score_record(
            standing_1,
            standing_2,
            match,
        )

    # ------------------------------------------------------------------
    # Persistent-player mode
    # ------------------------------------------------------------------

    def _play_persistent_head_to_head(
        self,
        entry_1: TournamentEntry,
        entry_2: TournamentEntry,
    ) -> None:
        standing_1 = self.standings[entry_1.name]
        standing_2 = self.standings[entry_2.name]

        player_1 = self._live_players[entry_1.name]
        player_2 = self._live_players[entry_2.name]

        if standing_1.disqualified or standing_2.disqualified:
            self._record_forfeit(
                entry_1,
                entry_2,
                player_1,
                player_2,
                standing_1,
                standing_2,
            )
            return

        match = self._run_match(
            player_1,
            player_2,
        )

        self._record_result(
            entry_1,
            entry_2,
            match,
            player_1.capital,
            player_2.capital,
            self_play=False,
        )

        self._score_record(
            standing_1,
            standing_2,
            match,
        )

        if player_1.is_bankrupt:
            standing_1.disqualification_reason = "bankruptcy"

        if player_2.is_bankrupt:
            standing_2.disqualification_reason = "bankruptcy"

        # The live player's capital is the running persistent score.
        # Do not repeatedly add full ending capital after each match.
        standing_1.points = player_1.capital
        standing_2.points = player_2.capital

    def _play_persistent_self_match(
        self,
        entry: TournamentEntry,
    ) -> None:
        standing = self.standings[entry.name]
        live_player = self._live_players[entry.name]

        if standing.disqualified:
            self.results.append(
                MatchResult(
                    match_number=len(self.results) + 1,
                    p1=entry.name,
                    p2=entry.name,
                    k1=live_player.capital,
                    k2=live_player.capital,
                    outcome="Not played",
                    end_reason="player already disqualified",
                    self_play=True,
                )
            )

            standing.matches += 1
            standing.draws += 1
            return

        # One Python object cannot occupy both seats.
        #
        # Deep copies preserve:
        # - accumulated capital,
        # - C/D allocation,
        # - previous action memory,
        # - and custom strategy instance fields.
        player_1 = deepcopy(live_player)
        player_2 = deepcopy(live_player)

        match = self._run_match(
            player_1,
            player_2,
        )

        k1 = player_1.capital
        k2 = player_2.capital

        self._record_result(
            entry,
            entry,
            match,
            k1,
            k2,
            self_play=True,
        )

        standing.matches += 1
        standing.draws += 1

        # The strategy occupies both seats during self-play.
        standing.points = (k1 + k2) // 2

        if player_1.is_bankrupt or player_2.is_bankrupt:
            standing.disqualification_reason = "self-bankruptcy"

    def _record_forfeit(
        self,
        entry_1: TournamentEntry,
        entry_2: TournamentEntry,
        player_1: Player,
        player_2: Player,
        standing_1: Standing,
        standing_2: Standing,
    ) -> None:
        if standing_1.disqualified and standing_2.disqualified:
            outcome = "No contest"

            standing_1.draws += 1
            standing_2.draws += 1

        elif standing_1.disqualified:
            outcome = entry_2.name

            standing_1.losses += 1
            standing_2.wins += 1

        else:
            outcome = entry_1.name

            standing_1.wins += 1
            standing_2.losses += 1

        standing_1.matches += 1
        standing_2.matches += 1

        self.results.append(
            MatchResult(
                match_number=len(self.results) + 1,
                p1=entry_1.name,
                p2=entry_2.name,
                k1=player_1.capital,
                k2=player_2.capital,
                outcome=outcome,
                end_reason="forfeit due to prior bankruptcy",
                self_play=False,
            )
        )

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _run_match(
        self,
        player_1: Player,
        player_2: Player,
    ) -> Match:
        match = Match(
            player_1,
            player_2,
        )

        match.play(
            max_turns=self.max_turns_per_match,
        )

        return match

    def _record_result(
        self,
        entry_1: TournamentEntry,
        entry_2: TournamentEntry,
        match: Match,
        k1: Number,
        k2: Number,
        *,
        self_play: bool,
    ) -> None:
        if match.winner is match.player_1:
            outcome = entry_1.name

        elif match.winner is match.player_2:
            outcome = entry_2.name

        else:
            outcome = "Draw"

        self.results.append(
            MatchResult(
                match_number=len(self.results) + 1,
                p1=entry_1.name,
                p2=entry_2.name,
                k1=k1,
                k2=k2,
                outcome=outcome,
                end_reason=match.end_reason or "unknown",
                self_play=self_play,
            )
        )

    @staticmethod
    def _score_record(
        standing_1: Standing,
        standing_2: Standing,
        match: Match,
    ) -> None:
        standing_1.matches += 1
        standing_2.matches += 1

        if match.winner is match.player_1:
            standing_1.wins += 1
            standing_2.losses += 1

        elif match.winner is match.player_2:
            standing_2.wins += 1
            standing_1.losses += 1

        else:
            standing_1.draws += 1
            standing_2.draws += 1

    def ranked_standings(self) -> list[Standing]:
        """Return eligible strategies first, ordered by descending points."""

        return sorted(
            self.standings.values(),
            key=lambda standing: (
                standing.disqualified,
                -float(standing.points),
                standing.name.casefold(),
            ),
        )

    def champions(self) -> list[Standing]:
        """Return every eligible strategy tied for the highest score."""

        eligible = [
            standing
            for standing in self.ranked_standings()
            if not standing.disqualified
        ]

        if not eligible:
            return []

        highest_points = eligible[0].points

        return [
            standing
            for standing in eligible
            if standing.points == highest_points
        ]

    def print_match_results(self) -> None:
        """Print one compact row for every scheduled matchup."""

        if not self.results:
            print("No tournament results are available.")
            return

        headers = (
            "#",
            "P1",
            "P2",
            "K1",
            "K2",
            "Outcome",
        )

        rows = [
            (
                str(result.match_number),
                result.p1,
                result.p2,
                format_number(result.k1),
                format_number(result.k2),
                result.outcome,
            )
            for result in self.results
        ]

        print(f"MATCH RESULTS ({self.mode.value})")

        _print_table(
            headers,
            rows,
            right_aligned={0, 3, 4},
        )

    def print_rankings(self) -> None:
        """Print final point totals and eligibility status."""

        ranked = self.ranked_standings()

        if not ranked:
            print("No tournament standings are available.")
            return

        headers = (
            "Rank",
            "Player",
            "Points",
            "M",
            "W",
            "L",
            "D",
            "Status",
        )

        rows: list[tuple[str, ...]] = []

        eligible_rank = 0
        previous_points: Number | None = None
        previous_rank = 0

        for standing in ranked:
            if standing.disqualified:
                rank = "—"

            else:
                eligible_rank += 1

                if (
                    previous_points is not None
                    and standing.points == previous_points
                ):
                    rank = str(previous_rank)

                else:
                    rank = str(eligible_rank)
                    previous_rank = eligible_rank

                previous_points = standing.points

            rows.append(
                (
                    rank,
                    standing.name,
                    format_number(standing.points),
                    str(standing.matches),
                    str(standing.wins),
                    str(standing.losses),
                    str(standing.draws),
                    standing.status,
                )
            )

        print("FINAL RANKING")

        _print_table(
            headers,
            rows,
            right_aligned={0, 2, 3, 4, 5, 6},
        )

    def print_summary(self) -> None:
        """Print matchup results, rankings, and tournament winner."""

        self.print_match_results()
        print()

        self.print_rankings()
        print()

        champions = self.champions()

        if not champions:
            print("Winner: None — every strategy was disqualified.")

        elif len(champions) == 1:
            champion = champions[0]

            print(
                f"Winner: {champion.name} "
                f"with {format_number(champion.points)} points"
            )

        else:
            names = ", ".join(
                champion.name
                for champion in champions
            )

            print(
                f"Winners: {names} "
                f"with {format_number(champions[0].points)} points each"
            )

def run_randomized_tournament_samples(
    entries: Iterable[TournamentEntry],
    *,
    samples: int = 100,
    mode: TournamentMode = TournamentMode.PERSISTENT,
    max_turns_per_match: int = 1_000,
    seed: int | None = None,
) -> list[TournamentSampleStatistics]:
    """Run randomized tournament schedules and aggregate player statistics.

    Each sample randomly permutes the entry list, then runs the normal
    balanced circle-method schedule. In persistent mode, this changes both
    matchup order and seat assignment while preserving equal rest: every
    strategy still plays exactly once per round.

    Random permutations are sampled independently, so the same permutation
    may occur more than once. Pass ``seed`` for reproducible results.
    """

    entry_list = list(entries)

    if samples <= 0:
        raise ValueError("samples must be positive.")

    if not entry_list:
        raise ValueError("At least one tournament entry is required.")

    rng = Random(seed)

    points_by_player: dict[str, list[Number]] = {
        entry.name: []
        for entry in entry_list
    }
    wins_by_player: dict[str, list[int]] = {
        entry.name: []
        for entry in entry_list
    }
    losses_by_player: dict[str, list[int]] = {
        entry.name: []
        for entry in entry_list
    }
    draws_by_player: dict[str, list[int]] = {
        entry.name: []
        for entry in entry_list
    }
    bankruptcy_by_player: dict[str, list[bool]] = {
        entry.name: []
        for entry in entry_list
    }

    for _ in range(samples):
        shuffled_entries = rng.sample(
            entry_list,
            k=len(entry_list),
        )

        tournament = Tournament(
            shuffled_entries,
            mode=mode,
            max_turns_per_match=max_turns_per_match,
        )
        tournament.run()

        for name, standing in tournament.standings.items():
            points_by_player[name].append(standing.points)
            wins_by_player[name].append(standing.wins)
            losses_by_player[name].append(standing.losses)
            draws_by_player[name].append(standing.draws)
            bankruptcy_by_player[name].append(standing.disqualified)

    statistics: list[TournamentSampleStatistics] = []

    for entry in entry_list:
        name = entry.name
        point_values = points_by_player[name]
        point_floats = [float(value) for value in point_values]

        statistics.append(
            TournamentSampleStatistics(
                name=name,
                samples=samples,
                average_points=fmean(point_floats),
                max_points=max(point_values),
                points_standard_deviation=(
                    stdev(point_floats)
                    if len(point_floats) > 1
                    else 0.0
                ),
                average_wins=fmean(wins_by_player[name]),
                average_losses=fmean(losses_by_player[name]),
                average_draws=fmean(draws_by_player[name]),
                average_bankruptcies=fmean([float(b) for b in bankruptcy_by_player[name]]),
            )
        )

    return sorted(
        statistics,
        key=lambda result: (
            -result.average_points,
            result.name.casefold(),
        ),
    )

def print_randomized_tournament_statistics(
    statistics: Iterable[TournamentSampleStatistics],
) -> None:
    """Print aggregate statistics from randomized tournament samples."""

    results = list(statistics)

    if not results:
        print("No randomized tournament statistics are available.")
        return

    sample_counts = {result.samples for result in results}
    if len(sample_counts) != 1:
        raise ValueError(
            "All statistics rows must have the same sample count."
        )

    samples = results[0].samples
    headers = (
        "Rank",
        "Player",
        "Avg Points",
        "Max Points",
        "Std Dev",
        "Avg W",
        "Avg L",
        "Avg D",
        "Avg B",
    )

    rows = [
        (
            str(rank),
            result.name,
            f"{result.average_points:.2f}",
            format_number(result.max_points),
            f"{result.points_standard_deviation:.2f}",
            f"{result.average_wins:.2f}",
            f"{result.average_losses:.2f}",
            f"{result.average_draws:.2f}",
            f"{result.average_bankruptcies:.2f}",
        )
        for rank, result in enumerate(results, start=1)
    ]

    print(
        f"RANDOMIZED TOURNAMENT STATISTICS "
        f"({samples} samples)"
    )
    _print_table(
        headers,
        rows,
        right_aligned={0, 2, 3, 4, 5, 6, 7, 8},
    )


def _print_table(
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    right_aligned: set[int] | None = None,
) -> None:
    """Render a compact dependency-free console table."""

    right_aligned = right_aligned or set()

    widths = [
        max(
            len(headers[index]),
            max(len(row[index]) for row in rows),
        )
        for index in range(len(headers))
    ]

    def format_row(values: tuple[str, ...]) -> str:
        cells: list[str] = []

        for index, (value, width) in enumerate(
            zip(values, widths, strict=True)
        ):
            if index in right_aligned:
                cells.append(value.rjust(width))
            else:
                cells.append(value.ljust(width))

        return " | ".join(cells)

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))

    for row in rows:
        print(format_row(row))
