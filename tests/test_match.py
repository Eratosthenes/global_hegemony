"""Basic regression tests for the match engine."""

import unittest

from global_hegemony import Environment, Match
from global_hegemony.strategies import AlwaysCooperate, AlwaysDefect


class MatchTests(unittest.TestCase):
    def test_example_match_terminates(self) -> None:
        match = Match(
            AlwaysCooperate("Cooperator"),
            AlwaysDefect("Defector"),
        )
        match.play()

        self.assertTrue(match.is_over)
        self.assertIsNotNone(match.end_reason)
        self.assertGreater(len(match.turn_log), 0)

    def test_actions_are_logged_as_letters(self) -> None:
        match = Match(
            AlwaysCooperate("Cooperator"),
            AlwaysDefect("Defector"),
        )
        record = match.play_turn()

        self.assertEqual(record.p1_action, "C")
        self.assertEqual(record.p2_action, "D")

    def test_environment_can_be_injected(self) -> None:
        environment = Environment(100)
        added = environment.apply_synergy(7, 3)

        self.assertEqual(added, 2)
        self.assertEqual(environment.bank, 102)


if __name__ == "__main__":
    unittest.main()
