"""AST node classes for MusicDSL.

The parser builds a tree of these nodes. Every node remembers the
line and column where it started, for good error messages later.
"""

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Node:
    """Base class: every node knows where it is in the source."""
    line: int = 0
    column: int = 0


@dataclass
class TempoNode(Node):
    bpm: int


@dataclass
class KeyNode(Node):
    tonic: str   # e.g. "C", "F#", "Bb" (checked later by semantic analysis)
    mode: str    # "major" or "minor"


@dataclass
class TimeSignatureNode(Node):
    numerator: int
    denominator: int


@dataclass
class NoteNode(Node):
    pitch: str      # e.g. "C4" (validity checked later)
    duration: str   # e.g. "q" (validity checked later)


@dataclass
class RestNode(Node):
    duration: str


@dataclass
class BarLineNode(Node):
    """The optional '|' that separates bars inside a melody."""


@dataclass
class MelodyNode(Node):
    events: list = field(default_factory=list)   # notes, rests, bar lines


@dataclass
class ChordNode(Node):
    symbol: str     # Roman numeral, e.g. "vi" (validity checked later)


@dataclass
class ChordProgressionNode(Node):
    chords: list = field(default_factory=list)   # list of ChordNode


@dataclass
class ProgramNode(Node):
    statements: list = field(default_factory=list)   # in source order