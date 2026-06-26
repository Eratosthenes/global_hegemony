from global_hegemony.strategies import *
from global_hegemony.tournament import Tournament, TournamentEntry, TournamentMode, run_randomized_tournament_samples, print_randomized_tournament_statistics


def main() -> None:
    entries = [
        TournamentEntry.from_player_class(
            "Warrior",
            AlwaysDefect,
        ),
        TournamentEntry.from_player_class(
            "Spider",
            DisciplinedAmbush,
        ),
        TournamentEntry.from_player_class(
            "Strongman",
            AntiAmbush,
        ),
        TournamentEntry.from_player_class(
            "Prophet",
            Prophet,
        ),
        TournamentEntry.from_player_class(
            "SpaceBeam",
            CycleDefector,
        ),
        TournamentEntry.from_player_class(
            "Paperclip Maximizer",
            AlwaysCooperate,
        ),
        TournamentEntry.from_player_class(
            "Forager",
            Forager,
        ),
        TournamentEntry.from_player_class(
            "Tit for Tat",
            TitForTat,
        ),
        TournamentEntry.from_player_class(
            "Demagogue",
            Demagogue,
        ),
        TournamentEntry.from_player_class(
            "Raider",
            RaidAndHeal,
        )
    ]

    tournament = Tournament(entries, mode=TournamentMode.FRESH)
    tournament.run()
    tournament.print_summary()

    statistics = run_randomized_tournament_samples(
        entries,
        samples=500,
        mode=TournamentMode.PERSISTENT,
        # seed=42,
    )
    print()
    print_randomized_tournament_statistics(statistics)

if __name__ == "__main__":
    main()