from fractions import Fraction

from backend.midi_generator import _vlq, generate_midi, write_midi
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


def read_vlq(data, pos):
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, pos


def parse_events(midi_bytes):
    """Tiny MIDI reader: returns (tick, kind, a, b) tuples."""
    track = midi_bytes[22:]          # skip 14-byte header + 8-byte track header
    pos, tick, events = 0, 0, []
    while pos < len(track):
        delta, pos = read_vlq(track, pos)
        tick += delta
        status = track[pos]
        if status == 0xFF:
            kind, length = track[pos + 1], track[pos + 2]
            events.append((tick, "meta", kind, bytes(track[pos + 3:pos + 3 + length])))
            pos += 3 + length
        else:
            name = "on" if status & 0xF0 == 0x90 else "off"
            events.append((tick, name, status & 0x0F, track[pos + 1]))
            pos += 3
    return events


def notes_only(midi_bytes):
    return [e for e in parse_events(midi_bytes) if e[1] in ("on", "off")]


def test_variable_length_quantities():
    assert _vlq(0) == b"\x00"
    assert _vlq(127) == b"\x7f"
    assert _vlq(128) == b"\x81\x00"
    assert _vlq(480) == b"\x83\x60"


def test_header_is_format_0_with_480_ticks():
    data = generate_midi(build([note("C4", 60, 4)]))
    assert data[:4] == b"MThd"
    assert data[8:14] == b"\x00\x00\x00\x01\x01\xe0"   # format 0, 1 track, 480
    assert data[14:18] == b"MTrk"


def test_tempo_meta_event():
    data = generate_midi(build([note("C4", 60, 4)]))          # tempo 120
    tempo = [e for e in parse_events(data) if e[1] == "meta" and e[2] == 0x51]
    assert tempo[0][3] == (500000).to_bytes(3, "big")


def test_time_signature_meta_event():
    symbols = SymbolTable(time_numerator=6, time_denominator=8)
    data = generate_midi(build([note("C4", 60, 3)], symbols=symbols))
    sig = [e for e in parse_events(data) if e[1] == "meta" and e[2] == 0x58]
    assert sig[0][3][:2] == bytes([6, 3])                      # 6/8, 2**3 = 8


def test_single_note_on_and_off():
    data = generate_midi(build([note("C4", 60, 1)]))
    assert notes_only(data) == [(0, "on", 0, 60), (480, "off", 0, 60)]


def test_rest_delays_the_next_note():
    data = generate_midi(build([rest(1), note("C4", 60, 1)]))
    assert notes_only(data)[0] == (480, "on", 0, 60)


def test_note_off_comes_before_next_note_on():
    data = generate_midi(build([note("C4", 60, 1), note("D4", 62, 1)]))
    events = notes_only(data)
    off_index = events.index((480, "off", 0, 60))
    on_index = events.index((480, "on", 0, 62))
    assert off_index < on_index


def test_chord_notes_sound_together_on_channel_1():
    data = generate_midi(build(chords=[resolve_chord("I", "C", "major")]))
    ons = [e for e in notes_only(data) if e[1] == "on"]
    assert [(e[0], e[2], e[3]) for e in ons] == [(0, 1, 60), (0, 1, 64), (0, 1, 67)]


def test_track_ends_with_end_of_track():
    data = generate_midi(build([note("C4", 60, 1)]))
    assert data.endswith(b"\xff\x2f\x00")


def test_write_midi_creates_file(tmp_path):
    path = tmp_path / "song.mid"
    write_midi(build([note("C4", 60, 1)]), str(path))
    assert path.read_bytes()[:4] == b"MThd"
