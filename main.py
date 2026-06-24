from global_hegemony.strategies import *
from global_hegemony.tournament import Tournament, TournamentEntry, TournamentMode


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
            "Raider",
            RaidAndHeal,
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
    ]

    tournament = Tournament(entries, mode=TournamentMode.PERSISTENT)
    tournament.run()
    tournament.print_summary()

if __name__ == "__main__":
    main()