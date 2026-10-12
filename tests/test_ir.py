from fractions import Fraction

from compiler.chords import resolve_chord
from compiler.ir import CHORDS, MELODY, format_ir
from compiler.ir_generator import generate_ir
from compiler.semantic import AnalyzedEvent, SemanticResult
from compiler.symbol_table import SymbolTable


def note(pitch, midi, beats):
    return AnalyzedEvent(midi, Fraction(beats), pitch)


def rest(beats):
    return AnalyzedEvent(None, Fraction(beats), None)


def build(melody=(), chords=(), symbols=None):
    return generate_ir(SemanticResult(
        symbols or SymbolTable(), list(melody), list(chords), []
    ))


def test_melody_start_times_follow_a_running_clock():
    ir = build([note("C4", 60, 1), note("D4", 62, 1), note("E4", 64, 2)])
    assert [e.start for e in ir.events] == [0, 1, 2]
    assert [e.midi for e in ir.events] == [(60,), (62,), (64,)]


def test_rest_has_no_notes_but_takes_time():
    ir = build([note("C4", 60, 1), rest(1), note("D4", 62, 2)])
    assert ir.events[1].kind == "rest"
    assert ir.events[1].midi == ()
    assert ir.events[2].start == 2


def test_each_chord_lasts_one_bar():
    chords = [resolve_chord(s, "C", "major") for s in ("I", "vi", "IV")]
    ir = build(chords=chords)
    assert [e.start for e in ir.events] == [0, 4, 8]
    assert all(e.duration == 4 for e in ir.events)
    assert ir.events[1].midi == (69, 72, 76)
    assert ir.events[1].names == ("A", "C", "E")


def test_chord_bar_length_follows_time_signature():
    symbols = SymbolTable(time_numerator=3, time_denominator=4)
    ir = build(chords=[resolve_chord("I", "C", "major")] * 2, symbols=symbols)
    assert [e.start for e in ir.events] == [0, 3]
    assert ir.events[0].duration == 3


def test_header_settings_are_copied():
    symbols = SymbolTable(tempo=90, key_tonic="G", key_mode="major")
    ir = build([note("G4", 67, 4)], symbols=symbols)
    assert (ir.tempo, ir.key_tonic, ir.key_mode) == (90, "G", "major")
    assert ir.beats_per_bar == 4


def test_total_beats():
    ir = build([note("C4", 60, 4), note("D4", 62, 4)])
    assert ir.total_beats == 8


def test_total_beats_of_empty_program_is_zero():
    assert build().total_beats == 0


def test_melody_and_chords_are_merged_in_time_order():
    ir = build(
        [note("C4", 60, 2), note("D4", 62, 2)],
        [resolve_chord("I", "C", "major")],
    )
    assert [e.start for e in ir.events] == [0, 0, 2]
    assert ir.events[0].track == MELODY      # melody first on a tie
    assert ir.events[1].track == CHORDS


def test_track_filter():
    ir = build([note("C4", 60, 4)], [resolve_chord("I", "C", "major")])
    assert len(ir.track(MELODY)) == 1
    assert len(ir.track(CHORDS)) == 1


def test_beats_to_seconds():
    ir = build([note("C4", 60, 4)])        # default tempo 120
    assert ir.beats_to_seconds(1) == 0.5
    assert ir.beats_to_seconds(Fraction(1, 2)) == 0.25


def test_eighth_notes_keep_exact_fractions():
    ir = build([note("C4", 60, Fraction(1, 2)), note("D4", 62, Fraction(1, 2))])
    assert ir.events[1].start == Fraction(1, 2)
    assert ir.events[1].end == 1


def test_format_ir_mentions_header_and_notes():
    text = format_ir(build([note("C4", 60, 4)]))
    assert "tempo=120" in text
    assert "C4" in text