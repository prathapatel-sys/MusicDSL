import pytest

from compiler.ast_nodes import (
    BarLineNode, ChordNode, ChordProgressionNode, KeyNode, MelodyNode,
    NoteNode, ProgramNode, RestNode, TempoNode, TimeSignatureNode,
)
from compiler.semantic import analyze
from utils.errors import SemanticError


def program(*statements):
    return ProgramNode(statements=list(statements))


def note(pitch, duration, line=1, column=1):
    return NoteNode(pitch=pitch, duration=duration, line=line, column=column)


def quarters(count):
    return [note("C4", "q", line=i + 1) for i in range(count)]


def melody(*events, line=1, column=1):
    return MelodyNode(events=list(events), line=line, column=column)


def test_defaults_and_simple_melody():
    events = [note("C4", "q"), note("D4", "q"), note("E4", "q"), note("G4", "q")]
    result = analyze(program(melody(*events)))
    assert result.symbols.tempo == 120
    assert (result.symbols.key_tonic, result.symbols.key_mode) == ("C", "major")
    assert [e.midi for e in result.melody] == [60, 62, 64, 67]
    assert result.warnings == []


def test_header_values_are_stored():
    result = analyze(program(
        TempoNode(bpm=90),
        KeyNode(tonic="G", mode="major"),
        TimeSignatureNode(numerator=3, denominator=4),
        melody(*quarters(3)),
    ))
    assert result.symbols.tempo == 90
    assert result.symbols.key_tonic == "G"
    assert result.symbols.beats_per_bar == 3


def test_invalid_pitch_letter():
    with pytest.raises(SemanticError) as info:
        analyze(program(melody(note("H4", "q", line=3, column=5))))
    assert "Invalid pitch 'H4'." in str(info.value)
    assert (info.value.line, info.value.column) == (3, 5)


def test_invalid_octave():
    with pytest.raises(SemanticError) as info:
        analyze(program(melody(note("C9", "q"))))
    assert "Invalid octave 9" in str(info.value)


def test_invalid_duration():
    with pytest.raises(SemanticError) as info:
        analyze(program(melody(note("C4", "x", line=2, column=4))))
    assert "Invalid duration 'x'." in str(info.value)
    assert (info.value.line, info.value.column) == (2, 4)


def test_rest_has_no_midi():
    events = [note("C4", "h"), RestNode(duration="h")]
    result = analyze(program(melody(*events)))
    assert result.melody[1].midi is None
    assert result.melody[1].beats == 2


def test_duplicate_tempo():
    with pytest.raises(SemanticError) as info:
        analyze(program(TempoNode(bpm=100), TempoNode(bpm=120, line=2),
                        melody(*quarters(4))))
    assert "Duplicate tempo declaration." in str(info.value)
    assert info.value.line == 2


def test_duplicate_melody():
    with pytest.raises(SemanticError) as info:
        analyze(program(melody(*quarters(4)), melody(*quarters(4))))
    assert "Duplicate melody declaration." in str(info.value)


def test_invalid_key_tonic():
    with pytest.raises(SemanticError) as info:
        analyze(program(KeyNode(tonic="H", mode="major"),
                        melody(*quarters(4))))
    assert "Invalid key 'H'." in str(info.value)


def test_invalid_time_denominator():
    with pytest.raises(SemanticError) as info:
        analyze(program(TimeSignatureNode(numerator=4, denominator=5),
                        melody(*quarters(4))))
    assert "Invalid time signature 4/5." in str(info.value)


def test_bar_with_five_beats_with_bar_lines():
    events = [note("C4", "h", column=5), note("D4", "h"), note("E4", "q"),
              BarLineNode()]
    with pytest.raises(SemanticError) as info:
        analyze(program(melody(*events)))
    assert "Bar 1 contains 5 beats, expected 4." in str(info.value)


def test_time_declared_after_melody_still_applies():
    # 3 quarter notes only fit because time 3/4 comes AFTER the melody.
    result = analyze(program(
        melody(*quarters(3)),
        TimeSignatureNode(numerator=3, denominator=4),
    ))
    assert len(result.melody) == 3


def test_chords_are_resolved():
    chords = ChordProgressionNode(chords=[
        ChordNode(symbol="I"), ChordNode(symbol="vi"),
        ChordNode(symbol="IV"), ChordNode(symbol="V"),
    ])
    result = analyze(program(chords))
    assert len(result.chords) == 4
    assert result.chords[1].midi == (69, 72, 76)


def test_incompatible_chord():
    chords = ChordProgressionNode(chords=[
        ChordNode(symbol="I"), ChordNode(symbol="II", line=2, column=9),
    ])
    with pytest.raises(SemanticError) as info:
        analyze(program(chords))
    assert "not compatible" in str(info.value)
    assert (info.value.line, info.value.column) == (2, 9)


def test_matching_lengths_give_no_warning():
    chords = ChordProgressionNode(chords=[ChordNode(symbol="I")])
    result = analyze(program(melody(*quarters(4)), chords))
    assert result.warnings == []


def test_length_mismatch_gives_warning():
    chords = ChordProgressionNode(
        chords=[ChordNode(symbol="I"), ChordNode(symbol="V")])
    result = analyze(program(melody(*quarters(4)), chords))
    assert len(result.warnings) == 1
    assert "4 beats" in result.warnings[0]
    assert "8 beats" in result.warnings[0]


def test_empty_program_is_rejected():
    with pytest.raises(SemanticError) as info:
        analyze(program(TempoNode(bpm=120)))
    assert "nothing to play" in str(info.value)


def test_chords_only_program_is_fine():
    chords = ChordProgressionNode(chords=[ChordNode(symbol="I")])
    result = analyze(program(chords))
    assert result.melody == []
    assert len(result.chords) == 1