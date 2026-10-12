import xml.etree.ElementTree as ET
from fractions import Fraction

from backend.musicxml_generator import generate_musicxml, write_musicxml
from compiler.chords import resolve_chord
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


def xml_of(ir):
    return ET.fromstring(generate_musicxml(ir))


def test_root_and_two_parts():
    root = xml_of(build([note("C4", 60, 4)], [resolve_chord("I", "C", "major")]))
    assert root.tag == "score-partwise"
    assert [p.get("id") for p in root.findall("part")] == ["P1", "P2"]


def test_melody_only_has_one_part():
    root = xml_of(build([note("C4", 60, 4)]))
    assert len(root.findall("part")) == 1


def test_first_note_pitch_and_duration():
    first = xml_of(build([note("C4", 60, 1)])).find(".//note")
    assert first.findtext("pitch/step") == "C"
    assert first.findtext("pitch/octave") == "4"
    assert first.findtext("duration") == "8"
    assert first.findtext("type") == "quarter"


def test_sharp_note_has_alter():
    first = xml_of(build([note("F#4", 66, 1)])).find(".//note")
    assert first.findtext("pitch/step") == "F"
    assert first.findtext("pitch/alter") == "1"
    assert first.findtext("pitch/octave") == "4"


def test_rest_element():
    notes = xml_of(build([rest(1), note("C4", 60, 1)])).findall(".//note")
    assert notes[0].find("rest") is not None
    assert notes[0].find("pitch") is None


def test_chord_notes_are_stacked():
    root = xml_of(build(chords=[resolve_chord("I", "C", "major")]))
    notes = root.findall(".//note")
    assert [n.findtext("pitch/step") for n in notes] == ["C", "E", "G"]
    assert [n.find("chord") is not None for n in notes] == [False, True, True]


def test_chord_octaves_come_from_midi_numbers():
    root = xml_of(build(chords=[resolve_chord("vi", "C", "major")]))
    octaves = [n.findtext("pitch/octave") for n in root.findall(".//note")]
    assert octaves == ["4", "5", "5"]          # A4 C5 E5


def test_measures_are_split_by_bar_length():
    root = xml_of(build([note("C4", 60, 1)] * 8))
    measures = root.find("part").findall("measure")
    assert len(measures) == 2
    assert all(len(m.findall("note")) == 4 for m in measures)


def test_attributes_and_tempo():
    symbols = SymbolTable(tempo=90, key_tonic="G", key_mode="major",
                          time_numerator=3, time_denominator=4)
    root = xml_of(build([note("G4", 67, 3)], symbols=symbols))
    assert root.findtext(".//divisions") == "8"
    assert root.findtext(".//key/fifths") == "1"
    assert root.findtext(".//key/mode") == "major"
    assert root.findtext(".//time/beats") == "3"
    assert root.findtext(".//time/beat-type") == "4"
    assert root.find(".//sound").get("tempo") == "90"


def test_minor_key_signatures():
    a_minor = xml_of(build([note("A4", 69, 4)], symbols=SymbolTable(
        key_tonic="A", key_mode="minor")))
    d_minor = xml_of(build([note("D4", 62, 4)], symbols=SymbolTable(
        key_tonic="D", key_mode="minor")))
    assert a_minor.findtext(".//key/fifths") == "0"
    assert d_minor.findtext(".//key/fifths") == "-1"


def test_dotted_half_chord_in_three_four():
    symbols = SymbolTable(time_numerator=3, time_denominator=4)
    root = xml_of(build(chords=[resolve_chord("I", "C", "major")],
                        symbols=symbols))
    first = root.find(".//note")
    assert first.findtext("duration") == "24"
    assert first.findtext("type") == "half"
    assert first.find("dot") is not None


def test_write_musicxml_creates_file(tmp_path):
    path = tmp_path / "song.musicxml"
    write_musicxml(build([note("C4", 60, 1)]), str(path))
    assert path.read_text(encoding="utf-8").startswith("<?xml")
