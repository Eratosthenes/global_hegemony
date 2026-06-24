"""Run one example Global Hegemony match."""

from pathlib import Path

from global_hegemony import Match
from global_hegemony.reporting import print_log_table, print_matchup, save_log_csv
from global_hegemony.strategies import *

def main() -> None:
    # player_one = CycleDefector("Cycle Defector")
    # player_one = AntiAmbush("Anti-Ambush Predator")
    # player_one = AntiAmbush("Strongman")
    # player_two = AntiAmbush("Strongman")
    # player_two = Forager("Forager")
    # player_two = TitForTat("Tit for Tat")
    # player_two = AlwaysCooperate("Peaceful Industrialist")
    player_one = DisciplinedAmbush("Spider")
    player_two = DisciplinedAmbush("Spider")
    # player_one = DisciplinedAmbush("Disciplined Ambush")
    # player_two = Ambush("Ambusher")
    # player_two = AlwaysDefect("Defector")
    # player_two = RaidAndHeal("Raid and Heal Predator")

    match = Match(player_one, player_two)
    match.play()

    print_matchup(match)
    print()
    print_log_table(match)

    print("\nFinal result:")
    print(f"Winner: {match.winner.name if match.winner else 'Draw'}")
    print(f"Reason: {match.end_reason}")

if __name__ == "__main__":
    main()
