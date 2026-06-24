from global_hegemony.strategies import *
from global_hegemony.tournament import Tournament, TournamentEntry, TournamentMode


def main() -> None:
    entries = [
        TournamentEntry.from_player_class(
            "Disciplined Ambush",
            DisciplinedAmbush,
        ),
        TournamentEntry.from_player_class(
            "Ambush",
            Ambush,
        ),
        TournamentEntry.from_player_class(
            "Peaceful Industrialist",
            AlwaysCooperate,
        ),
        TournamentEntry.from_player_class(
            "Cautious Industrialist",
            CautiousIndustrialist,
        ),
        TournamentEntry.from_player_class(
            "Raid and Heal",
            RaidAndHeal,
        ),
        TournamentEntry.from_player_class(
            "Forager",
            Forager,
        ),
        TournamentEntry.from_player_class(
            "Counter Raider",
            CounterRaider,
        ),
        TournamentEntry.from_player_class(
            "Tit for Tat",
            TitForTat,
        ),
        TournamentEntry.from_player_class(
            "Always Defect",
            AlwaysDefect,
        ),
        TournamentEntry.from_player_class(
            "Anti-Ambush Predator",
            AntiAmbush,
        ),
    ]

    tournament = Tournament(entries, mode=TournamentMode.PERSISTENT)
    tournament.run()
    tournament.print_summary()

if __name__ == "__main__":
    main()