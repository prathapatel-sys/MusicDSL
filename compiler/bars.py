"""Bar-duration validation (design D3)."""

from dataclasses import dataclass
from fractions import Fraction

from utils.errors import SemanticError

BAR_LINE = "|"   # marker placed in the item list where the program wrote '|'


@dataclass(frozen=True)
class Timed:
    """A note or rest: how long it lasts and where it was written."""
    beats: Fraction
    line: int
    column: int


def _num(value: Fraction) -> str:
    """4 -> '4', Fraction(5, 2) -> '2.5'."""
    return f"{float(value):g}"


def _beats(value: Fraction) -> str:
    return f"{_num(value)} {'beat' if value == 1 else 'beats'}"


def check_bars(items, bar_length: Fraction) -> None:
    """Raise SemanticError if the melody does not fit its bars."""
    if BAR_LINE in items:
        _check_explicit(items, bar_length)
    else:
        _check_auto(items, bar_length)


def _check_explicit(items, bar_length):
    bars, current = [], []
    for item in items:
        if item == BAR_LINE:
            if current:                 # ignore empty segments like "| |"
                bars.append(current)
                current = []
        else:
            current.append(item)
    if current:
        bars.append(current)

    for number, bar in enumerate(bars, start=1):
        total = sum((event.beats for event in bar), Fraction(0))
        if total != bar_length:
            first = bar[0]
            raise SemanticError(
                f"Bar {number} contains {_beats(total)}, "
                f"expected {_num(bar_length)}.",
                first.line, first.column,
            )


def _check_auto(items, bar_length):
    bar_number = 1
    filled = Fraction(0)
    bar_start = None
    for event in items:
        if filled == 0:
            bar_start = event
        if filled + event.beats > bar_length:
            raise SemanticError(
                f"Note crosses the bar line in bar {bar_number}: "
                f"only {_beats(bar_length - filled)} left, "
                f"but the note lasts {_beats(event.beats)}.",
                event.line, event.column,
            )
        filled += event.beats
        if filled == bar_length:
            bar_number += 1
            filled = Fraction(0)

    if filled != 0:
        raise SemanticError(
            f"Bar {bar_number} is incomplete "
            f"({_num(filled)} of {_num(bar_length)} beats).",
            bar_start.line, bar_start.column,
        )