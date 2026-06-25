"""Run one example Global Hegemony match."""

from pathlib import Path

from global_hegemony import Match
from global_hegemony.reporting import print_log_table, print_matchup, save_log_csv
from global_hegemony.strategies import *

def main() -> None:
    # player_one = AntiAmbush("Anti-Ambush Predator")
    # player_one = AntiAmbush("Strongman")
    # player_one = AlwaysDefect("Warrior")
    player_one = AntiAmbush("Strongman")
    # player_one = Forager("Forager")
    # player_two = TitForTat("Tit for Tat")
    # player_one = AlwaysCooperate("Paperclip Maximizer")
    # player_two = AlwaysCooperate("Paperclip Maximizer")
    # player_one = DisciplinedAmbush("Spider")
    # player_two = DisciplinedAmbush("Spider")
    # player_two = Ambush("Ambusher")
    # player_two = AlwaysDefect("Warrior")
    player_two = RaidAndHeal("Raider")
    # player_two = CycleDefector("SpaceBeam")

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
