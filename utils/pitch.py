"""Pitch parsing and validation. Middle C is C4 = MIDI note 60."""

import re
from dataclasses import dataclass

MIN_OCTAVE = 0
MAX_OCTAVE = 8

# Semitones above C for each natural note.
NATURAL_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
ACCIDENTAL_OFFSET = {"": 0, "#": 1, "b": -1}

# Capital A-G, optional # or b, then the octave digits.
PITCH_PATTERN = re.compile(r"([A-G])([#b]?)(\d+)")


class InvalidPitchError(ValueError):
    """Raised with a ready-to-show reason when a pitch is not valid."""


@dataclass(frozen=True)
class Pitch:
    """A valid pitch, split into its parts."""
    letter: str        # "C" ... "B"
    accidental: str    # "", "#" or "b"
    octave: int        # 0 ... 8

    @property
    def midi(self) -> int:
        """MIDI note number (C4 = 60)."""
        offset = (NATURAL_SEMITONES[self.letter]
                  + ACCIDENTAL_OFFSET[self.accidental])
        return 12 * (self.octave + 1) + offset

    def __str__(self) -> str:
        return f"{self.letter}{self.accidental}{self.octave}"


def parse_pitch(text: str) -> Pitch:
    """Turn 'G#5' into a Pitch, or raise InvalidPitchError."""
    match = PITCH_PATTERN.fullmatch(text)
    if match is None:
        raise InvalidPitchError(f"Invalid pitch '{text}'.")
    letter, accidental, octave_text = match.groups()
    octave = int(octave_text)
    if not MIN_OCTAVE <= octave <= MAX_OCTAVE:
        raise InvalidPitchError(
            f"Invalid octave {octave} in pitch '{text}'. "
            f"Expected {MIN_OCTAVE} to {MAX_OCTAVE}."
        )
    return Pitch(letter, accidental, octave)