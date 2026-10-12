import io
import wave
from fractions import Fraction

from backend.wav_generator import (
    SAMPLE_RATE, generate_wav, midi_to_frequency, render_samples, write_wav,
)
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


def test_riff_wave_header_and_format():
    data = generate_wav(build([note("C4", 60, 4)]))
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WAVE"
    with wave.open(io.BytesIO(data)) as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == SAMPLE_RATE


def test_length_matches_tempo():
    # 4 beats at 120 BPM = 2 seconds
    data = generate_wav(build([note("C4", 60, 4)]))
    with wave.open(io.BytesIO(data)) as handle:
        assert handle.getnframes() == 2 * SAMPLE_RATE


def test_rest_is_silent():
    samples = render_samples(build([rest(1)]))
    assert len(samples) == SAMPLE_RATE // 2
    assert all(s == 0.0 for s in samples)


def test_note_makes_sound():
    samples = render_samples(build([note("A4", 69, 1)]))
    assert max(abs(s) for s in samples) > 0.2


def test_midi_to_frequency():
    assert midi_to_frequency(69) == 440.0
    assert abs(midi_to_frequency(60) - 261.63) < 0.01
    assert abs(midi_to_frequency(81) - 880.0) < 0.001


def test_note_fades_out_to_silence():
    samples = render_samples(build([note("C4", 60, 1)]))
    assert samples[0] == 0.0
    assert abs(samples[-1]) < 0.01


def test_melody_plus_chord_does_not_clip():
    ir = build([note("C4", 60, 4)], [resolve_chord("I", "C", "major")])
    assert max(abs(s) for s in render_samples(ir)) <= 1.0


def test_empty_program_gives_empty_audio():
    data = generate_wav(build())
    with wave.open(io.BytesIO(data)) as handle:
        assert handle.getnframes() == 0


def test_write_wav_creates_file(tmp_path):
    path = tmp_path / "song.wav"
    write_wav(build([note("C4", 60, 1)]), str(path))
    assert path.read_bytes()[:4] == b"RIFF"
