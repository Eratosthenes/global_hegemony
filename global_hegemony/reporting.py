"""Console and CSV reporting for completed matches."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from .formatting import format_number
from .models import TurnRecord

if TYPE_CHECKING:
    from .match import Match


CSV_COLUMNS = list(TurnRecord.__dataclass_fields__)


def print_matchup(match: "Match") -> None:
    print(f"P1: {match.player_1.name} [{type(match.player_1).__name__}]")
    print(f"P2: {match.player_2.name} [{type(match.player_2).__name__}]")


def print_log_table(match: "Match") -> None:
    """Print only the state needed to follow the match at a glance."""
    if not match.turn_log:
        print("No turns have been played.")
        return

    headers = ("T", "A1", "P1 C/D", "K1", "A2", "P2 C/D", "K2", "ENV")
    rows = [
        (
            format_number(record.turn),
            record.p1_action,
            f"{format_number(record.p1_c)}/{format_number(record.p1_d)}",
            format_number(record.p1_capital),
            record.p2_action,
            f"{format_number(record.p2_c)}/{format_number(record.p2_d)}",
            format_number(record.p2_capital),
            format_number(record.environment),
        )
        for record in match.turn_log
    ]

    widths = [
        max(len(headers[index]), max(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    def format_row(values: tuple[str, ...]) -> str:
        return " | ".join(
            value.rjust(width)
            for value, width in zip(values, widths, strict=True)
        )

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))


def print_turn(record: TurnRecord) -> None:
    """Print one compact row when a match is run in verbose mode."""
    p1_structure = f"{format_number(record.p1_c)}/{format_number(record.p1_d)}"
    p2_structure = f"{format_number(record.p2_c)}/{format_number(record.p2_d)}"

    print(
        f"T={format_number(record.turn):>3}  "
        f"P1={record.p1_action} {p1_structure:>7} "
        f"K={format_number(record.p1_capital):>6}  "
        f"P2={record.p2_action} {p2_structure:>7} "
        f"K={format_number(record.p2_capital):>6}  "
        f"ENV={format_number(record.environment):>6}"
    )


def save_log_csv(match: "Match", filename: str | Path) -> Path:
    if not match.turn_log:
        raise RuntimeError("Cannot save an empty match log.")

    path = Path(filename)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(record.as_dict() for record in match.turn_log)

    return path
