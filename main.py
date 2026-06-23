from global_hegemony.strategies import *
from global_hegemony.tournament import Tournament, TournamentEntry, TournamentMode


def main() -> None:
    entries = [
        TournamentEntry.from_player_class(
            "Ambush",
            Ambush,
        ),
        TournamentEntry.from_player_class(
            "Raid and Heal Predator",
            RaidAndHeal,
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
            "Peaceful Industrialist",
            AlwaysCooperate,
        ),
        TournamentEntry.from_player_class(
            "Cautious Industrialist",
            CautiousIndustrialist,
        ),
    ]

    tournament = Tournament(entries, mode=TournamentMode.PERSISTENT)
    tournament.run()
    tournament.print_summary()

if __name__ == "__main__":
    main()