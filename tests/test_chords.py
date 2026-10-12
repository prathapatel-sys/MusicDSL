import pytest

from compiler.chords import ChordError, resolve_chord


def test_c_major_tonic():
    chord = resolve_chord("I", "C", "major")
    assert chord.names == ("C", "E", "G")
    assert chord.midi == (60, 64, 67)


def test_c_major_dominant():
    assert resolve_chord("V", "C", "major").midi == (67, 71, 74)


def test_c_major_vi_is_a_minor():
    chord = resolve_chord("vi", "C", "major")
    assert chord.names == ("A", "C", "E")
    assert chord.midi == (69, 72, 76)


def test_diminished_with_degree_sign():
    chord = resolve_chord("vii\u00b0", "C", "major")
    assert chord.names == ("B", "D", "F")
    assert chord.midi == (71, 74, 77)


def test_diminished_ascii_alternative():
    assert resolve_chord("viidim", "C", "major").midi == (71, 74, 77)


def test_a_minor_tonic():
    chord = resolve_chord("i", "A", "minor")
    assert chord.names == ("A", "C", "E")
    assert chord.midi == (69, 72, 76)


def test_minor_harmonic_dominant_is_allowed():
    chord = resolve_chord("V", "A", "minor")
    assert chord.names == ("E", "G#", "B")
    assert chord.midi == (64, 68, 71)


def test_minor_key_III():
    assert resolve_chord("III", "A", "minor").midi == (60, 64, 67)


def test_g_major_dominant_is_spelled_with_sharp():
    chord = resolve_chord("V", "G", "major")
    assert chord.names == ("D", "F#", "A")
    assert chord.midi == (62, 66, 69)


def test_wrong_case_is_a_compatibility_error():
    with pytest.raises(ChordError) as info:
        resolve_chord("II", "C", "major")
    assert "not compatible" in str(info.value)
    assert "'ii'" in str(info.value)


def test_major_chord_on_minor_tonic_is_rejected():
    with pytest.raises(ChordError):
        resolve_chord("I", "A", "minor")


def test_numeral_out_of_range():
    with pytest.raises(ChordError):
        resolve_chord("VIII", "C", "major")


def test_mixed_case_numeral():
    with pytest.raises(ChordError):
        resolve_chord("Iv", "C", "major")


def test_invalid_key_tonic():
    with pytest.raises(ChordError):
        resolve_chord("I", "H", "major")


def test_diminished_must_be_lowercase():
    with pytest.raises(ChordError):
        resolve_chord("VII\u00b0", "C", "major")