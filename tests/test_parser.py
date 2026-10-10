import pytest

from compiler.ast_nodes import (
    BarLineNode,
    ChordNode,
    ChordProgressionNode,
    KeyNode,
    MelodyNode,
    NoteNode,
    RestNode,
    TempoNode,
    TimeSignatureNode,
)
from compiler.lexer import tokenize
from compiler.parser import Parser
from utils.errors import ParserError


def parse(source):
    """Source text -> AST (lexer and parser together)."""
    return Parser(tokenize(source)).parse()


def test_empty_program_has_no_statements():
    assert parse("").statements == []


def test_tempo():
    node = parse("tempo 120").statements[0]
    assert isinstance(node, TempoNode)
    assert node.bpm == 120


def test_key_major_and_minor():
    major = parse("key F# major").statements[0]
    minor = parse("key A minor").statements[0]
    assert isinstance(major, KeyNode)
    assert (major.tonic, major.mode) == ("F#", "major")
    assert (minor.tonic, minor.mode) == ("A", "minor")


def test_time_signature():
    node = parse("time 6/8").statements[0]
    assert isinstance(node, TimeSignatureNode)
    assert (node.numerator, node.denominator) == (6, 8)


def test_melody_notes_and_rests():
    melody = parse("melody {\n  C4:q\n  R:h\n}").statements[0]
    assert isinstance(melody, MelodyNode)
    note, rest = melody.events
    assert isinstance(note, NoteNode)
    assert (note.pitch, note.duration) == ("C4", "q")
    assert isinstance(rest, RestNode)
    assert rest.duration == "h"


def test_melody_bar_lines():
    melody = parse("melody { C4:h D4:h | E4:w }").statements[0]
    kinds = [type(e) for e in melody.events]
    assert kinds == [NoteNode, NoteNode, BarLineNode, NoteNode]


def test_chords_separated_by_dashes():
    chords = parse("chords { I - V - vi - IV }").statements[0]
    assert isinstance(chords, ChordProgressionNode)
    assert all(isinstance(c, ChordNode) for c in chords.chords)
    assert [c.symbol for c in chords.chords] == ["I", "V", "vi", "IV"]


def test_chords_on_separate_lines():
    chords = parse("chords {\n  I\n  IV\n  V\n  I\n}").statements[0]
    assert [c.symbol for c in chords.chords] == ["I", "IV", "V", "I"]


def test_full_program_keeps_statement_order():
    source = """tempo 120
key C major
time 4/4
melody { C4:q }
chords { I - V }
"""
    kinds = [type(s) for s in parse(source).statements]
    assert kinds == [TempoNode, KeyNode, TimeSignatureNode,
                     MelodyNode, ChordProgressionNode]


def test_nodes_remember_their_position():
    note = parse("melody {\n  C4:q\n}").statements[0].events[0]
    assert (note.line, note.column) == (2, 3)


def parse_error(source):
    """Parse a broken program and return the ParserError it raises."""
    with pytest.raises(ParserError) as info:
        parse(source)
    return info.value


def test_missing_colon_after_pitch():
    err = parse_error("melody {\n  C4 q\n}")
    assert (err.line, err.column) == (2, 6)
    assert "Expected ':' after pitch" in str(err)


def test_missing_closing_brace_in_melody():
    err = parse_error("melody {\n  C4:q")
    assert (err.line, err.column) == (2, 7)
    assert "Missing '}'" in str(err)


def test_missing_closing_brace_in_chords():
    err = parse_error("chords { I")
    assert "Missing '}'" in str(err)


def test_error_reports_position_and_what_was_found():
    err = parse_error("tempo C")
    assert (err.line, err.column) == (1, 7)
    assert err.found == "'C'"


@pytest.mark.parametrize("source, message", [
    ("tempo C", "Expected a number after 'tempo'"),
    ("key C", "Expected 'major' or 'minor'"),
    ("key major", "Expected a key name"),
    ("time 4", "Expected '/'"),
    ("time 4 4", "Expected '/'"),
    ("time 4/", "Expected a number after '/'"),
    ("melody C4:q", "Expected '{' after 'melody'"),
    ("melody { C4: }", "Expected a duration"),
    ("melody { 120 }", "Expected a note"),
    ("chords { }", "Expected a chord symbol"),
    ("chords { I - }", "Expected a chord symbol"),
    ("hello", "Expected a statement"),
])
def test_malformed_programs_give_clear_errors(source, message):
    assert message in str(parse_error(source))