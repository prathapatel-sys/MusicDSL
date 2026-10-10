import pytest

from compiler.lexer import tokenize
from compiler.tokens import TokenType as T
from utils.errors import LexicalError


def types(source):
    """Token types only, without the final EOF."""
    return [t.type for t in tokenize(source)][:-1]


def values(source):
    """Token values only, without the final EOF."""
    return [t.value for t in tokenize(source)][:-1]


def test_header_keywords_and_numbers():
    assert types("tempo 120\nkey C major\ntime 4/4") == [
        T.TEMPO, T.NUMBER,
        T.KEY, T.IDENT, T.MAJOR,
        T.TIME, T.NUMBER, T.SLASH, T.NUMBER,
    ]


def test_minor_keyword():
    assert types("key A minor") == [T.KEY, T.IDENT, T.MINOR]


def test_pitches_with_accidentals():
    src = "C4 G#5 Db4"
    assert types(src) == [T.PITCH, T.PITCH, T.PITCH]
    assert values(src) == ["C4", "G#5", "Db4"]


def test_note_with_duration():
    assert types("C4:q") == [T.PITCH, T.COLON, T.DURATION]


def test_rest():
    assert types("R:q") == [T.REST, T.COLON, T.DURATION]


def test_bad_pitch_letter_is_left_for_semantic_analysis():
    assert types("H4:q")[0] == T.PITCH
    assert values("H4:q")[0] == "H4"


def test_bad_duration_is_left_for_semantic_analysis():
    assert types("C4:x") == [T.PITCH, T.COLON, T.DURATION]
    assert values("C4:x")[2] == "x"


def test_roman_numerals_and_dashes():
    assert types("I - vi - IV - V") == [
        T.ROMAN, T.DASH, T.ROMAN, T.DASH, T.ROMAN, T.DASH, T.ROMAN,
    ]


def test_diminished_chord_symbols():
    assert types("vii\u00b0 viidim") == [T.ROMAN, T.ROMAN]


def test_sharp_key_is_not_a_comment():
    assert values("key F# major") == ["key", "F#", "major"]


def test_comments_are_skipped_and_lines_counted():
    tokens = tokenize("C4:q # a comment\nD4:q")
    assert [t.value for t in tokens if t.type == T.PITCH] == ["C4", "D4"]
    assert tokens[3].line == 2  # D4 is on line 2


def test_bar_line_and_braces():
    assert types("melody { C4:q | }") == [
        T.MELODY, T.LBRACE, T.PITCH, T.COLON, T.DURATION, T.BAR, T.RBRACE,
    ]


def test_positions_are_one_based():
    tokens = tokenize("tempo 120")
    assert (tokens[0].line, tokens[0].column) == (1, 1)
    assert (tokens[1].line, tokens[1].column) == (1, 7)


def test_empty_source_gives_only_eof():
    tokens = tokenize("")
    assert [t.type for t in tokens] == [T.EOF]


def test_unexpected_character_reports_position():
    with pytest.raises(LexicalError) as info:
        tokenize("melody {\n  C4:q $\n}")
    err = info.value
    assert (err.line, err.column) == (2, 8)
    assert "Unexpected character '$'" in str(err)