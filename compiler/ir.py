"""Intermediate representation: one flat timeline of events."""

from dataclasses import dataclass
from fractions import Fraction

MELODY = "melody"
CHORDS = "chords"


@dataclass(frozen=True)
class IREvent:
    """One thing that happens on the timeline."""
    track: str              # MELODY or CHORDS
    kind: str               # "note", "rest" or "chord"
    start: Fraction         # in quarter-note beats
    duration: Fraction      # in quarter-note beats
    midi: tuple = ()        # MIDI numbers (empty for a rest)
    names: tuple = ()       # e.g. ("C4",) or ("C", "E", "G")

    @property
    def end(self) -> Fraction:
        return self.start + self.duration


@dataclass(frozen=True)
class IRProgram:
    """The whole compiled song: settings plus the event timeline."""
    tempo: int
    key_tonic: str
    key_mode: str
    time_numerator: int
    time_denominator: int
    events: tuple

    @property
    def beats_per_bar(self) -> Fraction:
        return Fraction(self.time_numerator * 4, self.time_denominator)

    @property
    def total_beats(self) -> Fraction:
        return max((e.end for e in self.events), default=Fraction(0))

    def track(self, name: str) -> list:
        """All events belonging to one track, in time order."""
        return [e for e in self.events if e.track == name]

    def beats_to_seconds(self, beats) -> float:
        """Convert a length in beats to seconds at this tempo."""
        return float(Fraction(beats) * 60 / self.tempo)


def _num(value: Fraction) -> str:
    return f"{float(value):g}"


def format_ir(program: IRProgram) -> str:
    """Readable text dump of the IR (used in the demo and the Streamlit UI)."""
    lines = [
        f"IR  tempo={program.tempo}  key={program.key_tonic} {program.key_mode}"
        f"  time={program.time_numerator}/{program.time_denominator}"
        f"  total={_num(program.total_beats)} beats",
        "start  track   kind  duration  notes",
    ]
    for e in program.events:
        lines.append(
            f"{_num(e.start):>5}  {e.track:<7} {e.kind:<5} "
            f"{_num(e.duration):<9} {' '.join(e.names)}"
        )
    return "\n".join(lines)