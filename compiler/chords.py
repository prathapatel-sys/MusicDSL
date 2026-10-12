"""Chord resolution: Roman numerals to real notes (design D7)."""

import re
from dataclasses import dataclass

LETTERS = "CDEFGAB"
NATURAL_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# Semitones above the tonic for each scale degree 1..7.
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]   # natural minor

# Semitones above the chord root for each triad quality.
TRIAD_STEPS = {
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
    "diminished": (0, 3, 6),
}

# Which quality each degree must have (diatonic chords).
DIATONIC_QUALITY = {
    "major": ["major", "minor", "minor", "major", "major", "minor", "diminished"],
    "minor": ["minor", "diminished", "major", "minor", "minor", "major", "major"],
}

ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII"]
NUMERAL_PATTERN = re.compile("([IViv]+)(\u00b0|dim)?")   # \u00b0 is the degree sign
KEY_PATTERN = re.compile("([A-G])([#b]?)")
CHORD_OCTAVE_BASE = 60   # MIDI number of C4


class ChordError(ValueError):
    """Raised with a ready-to-show reason when a chord can't be resolved."""


@dataclass(frozen=True)
class Chord:
    numeral: str        # as written, e.g. "vi"
    degree: int         # 1..7
    quality: str        # "major", "minor" or "diminished"
    names: tuple        # e.g. ("A", "C", "E")
    midi: tuple         # e.g. (69, 72, 76)


def _numeral_for(degree: int, quality: str) -> str:
    """The correct way to write a chord, used in error messages."""
    base = ROMANS[degree - 1]
    if quality == "major":
        return base
    if quality == "minor":
        return base.lower()
    return base.lower() + "\u00b0"


def _parse_key(tonic: str) -> int:
    """Return the pitch class (0-11) of the tonic, e.g. 'F#' -> 6."""
    match = KEY_PATTERN.fullmatch(tonic)
    if match is None:
        raise ChordError(f"Invalid key '{tonic}'. Expected a note from A to G.")
    letter, accidental = match.groups()
    offset = {"": 0, "#": 1, "b": -1}[accidental]
    return (NATURAL_PC[letter] + offset) % 12


def _parse_numeral(text: str):
    """Return (degree, written_quality) from a numeral like 'vii\u00b0'."""
    match = NUMERAL_PATTERN.fullmatch(text)
    if match is None:
        raise ChordError(f"Invalid chord '{text}'.")
    core, suffix = match.groups()
    if core.upper() not in ROMANS:
        raise ChordError(f"Invalid chord '{text}'. Expected I to VII.")
    if not (core.isupper() or core.islower()):
        raise ChordError(f"Invalid chord '{text}'. Do not mix upper and lower case.")
    degree = ROMANS.index(core.upper()) + 1
    if suffix:
        if core.isupper():
            raise ChordError(
                f"Invalid chord '{text}'. A diminished chord is written in lower case."
            )
        return degree, "diminished"
    return degree, "major" if core.isupper() else "minor"


def _spell(letter_index: int, target_pc: int) -> str:
    """Spell a pitch class using a given letter, e.g. letter F + pc 6 -> 'F#'."""
    letter = LETTERS[letter_index % 7]
    accidental = (target_pc - NATURAL_PC[letter] + 6) % 12 - 6
    if accidental > 0:
        return letter + "#" * accidental
    return letter + "b" * (-accidental)


def resolve_chord(text: str, tonic: str, mode: str) -> Chord:
    """Turn a Roman numeral into real notes in the given key."""
    tonic_pc = _parse_key(tonic)
    degree, written = _parse_numeral(text)

    expected = DIATONIC_QUALITY[mode][degree - 1]
    harmonic_dominant = (mode == "minor" and degree == 5 and written == "major")
    if written != expected and not harmonic_dominant:
        raise ChordError(
            f"Chord '{text}' is not compatible with key {tonic} {mode}. "
            f"Degree {degree} should be written '{_numeral_for(degree, expected)}'."
        )

    steps = MAJOR_STEPS if mode == "major" else MINOR_STEPS
    root_pc = (tonic_pc + steps[degree - 1]) % 12
    tonic_letter_index = LETTERS.index(tonic[0])

    midi, names = [], []
    for position, interval in enumerate(TRIAD_STEPS[written]):
        midi.append(CHORD_OCTAVE_BASE + root_pc + interval)
        letter_index = tonic_letter_index + (degree - 1) + 2 * position
        names.append(_spell(letter_index, (root_pc + interval) % 12))

    return Chord(text, degree, written, tuple(names), tuple(midi))