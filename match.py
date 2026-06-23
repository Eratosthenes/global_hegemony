"""Run one example Global Hegemony match."""

from pathlib import Path

from global_hegemony import Match
from global_hegemony.reporting import print_log_table, print_matchup, save_log_csv
from global_hegemony.strategies import *

def main() -> None:
    player_one = Ambush("Ambush")
    player_two = TitForTat("Tit for Tat")

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
