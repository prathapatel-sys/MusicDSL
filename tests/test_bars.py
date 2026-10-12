from fractions import Fraction

import pytest

from compiler.bars import BAR_LINE, Timed, check_bars
from utils.errors import SemanticError

FOUR = Fraction(4)


def quarters(count, first_line=1):
    """`count` quarter notes, one per line."""
    return [Timed(Fraction(1), first_line + i, 1) for i in range(count)]


def test_explicit_bars_correct():
    check_bars(quarters(4) + [BAR_LINE] + quarters(4), FOUR)


def test_trailing_bar_line_allowed():
    check_bars(quarters(4) + [BAR_LINE], FOUR)


def test_bar_with_five_beats():
    items = [
        Timed(Fraction(2), 1, 5),
        Timed(Fraction(2), 2, 5),
        Timed(Fraction(1), 3, 5),
        BAR_LINE,
    ]
    with pytest.raises(SemanticError) as info:
        check_bars(items, FOUR)
    assert "Bar 1 contains 5 beats, expected 4." in str(info.value)
    assert (info.value.line, info.value.column) == (1, 5)


def test_second_bar_is_reported_as_bar_2():
    items = quarters(4) + [BAR_LINE] + quarters(3) + [BAR_LINE]
    with pytest.raises(SemanticError) as info:
        check_bars(items, FOUR)
    assert "Bar 2 contains 3 beats, expected 4." in str(info.value)


def test_short_explicit_bar():
    items = [Timed(Fraction(2), 1, 1), BAR_LINE]
    with pytest.raises(SemanticError) as info:
        check_bars(items, FOUR)
    assert "Bar 1 contains 2 beats, expected 4." in str(info.value)


def test_auto_fill_correct():
    check_bars(quarters(8), FOUR)


def test_auto_incomplete_last_bar():
    with pytest.raises(SemanticError) as info:
        check_bars(quarters(5), FOUR)
    assert "Bar 2 is incomplete (1 of 4 beats)." in str(info.value)
    assert info.value.line == 5


def test_note_crossing_bar_line():
    items = quarters(3) + [Timed(Fraction(2), 4, 1)]
    with pytest.raises(SemanticError) as info:
        check_bars(items, FOUR)
    assert "crosses the bar line" in str(info.value)
    assert info.value.line == 4


def test_six_eight_has_three_beat_bars():
    eighths = [Timed(Fraction(1, 2), i + 1, 1) for i in range(6)]
    check_bars(eighths, Fraction(3))
    with pytest.raises(SemanticError) as info:
        check_bars(eighths[:5], Fraction(3))
    assert "incomplete (2.5 of 3 beats)" in str(info.value)


def test_empty_melody_is_fine():
    check_bars([], FOUR)