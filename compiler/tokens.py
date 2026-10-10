"""Token types and the Token record for MusicDSL."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    TEMPO = auto()
    KEY = auto()
    TIME = auto()
    MELODY = auto()
    CHORDS = auto()
    MAJOR = auto()
    MINOR = auto()
    REST = auto()
    # Words and values
    NUMBER = auto()
    IDENT = auto()      # e.g. the C in "key C major"
    PITCH = auto()      # e.g. C4, G#5, Bb3
    DURATION = auto()   # the word after ':' (q, h, ...) - checked later
    ROMAN = auto()      # e.g. I, vi, vii°
    # Symbols
    COLON = auto()
    SLASH = auto()
    DASH = auto()
    BAR = auto()        # |
    LBRACE = auto()
    RBRACE = auto()
    EOF = auto()        # end of input


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: object
    line: int
    column: int


KEYWORDS = {
    "tempo": TokenType.TEMPO,
    "key": TokenType.KEY,
    "time": TokenType.TIME,
    "melody": TokenType.MELODY,
    "chords": TokenType.CHORDS,
    "major": TokenType.MAJOR,
    "minor": TokenType.MINOR,
}