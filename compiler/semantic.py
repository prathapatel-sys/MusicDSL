"""Semantic analyzer: checks that a parsed program makes musical sense."""

from dataclasses import dataclass, field
from fractions import Fraction

from compiler import ast_nodes as nodes
from compiler.bars import BAR_LINE, Timed, check_bars
from compiler.chords import KEY_PATTERN, ChordError, resolve_chord
from compiler.symbol_table import SymbolTable
from utils.errors import SemanticError
from utils.pitch import InvalidPitchError, parse_pitch

# Design D2: durations in quarter-note beats.
DURATION_BEATS = {
    "w": Fraction(4),
    "h": Fraction(2),
    "q": Fraction(1),
    "e": Fraction(1, 2),
    "s": Fraction(1, 4),
}
VALID_DENOMINATORS = (1, 2, 4, 8, 16, 32)


@dataclass(frozen=True)
class AnalyzedEvent:
    """A checked note or rest, ready for the IR stage."""
    midi: int | None        # None means a rest
    beats: Fraction
    pitch: str | None       # e.g. "C4", None for a rest


@dataclass
class SemanticResult:
    """Everything later stages need from the analyzer."""
    symbols: SymbolTable
    melody: list = field(default_factory=list)    # list of AnalyzedEvent
    chords: list = field(default_factory=list)    # list of Chord
    warnings: list = field(default_factory=list)  # list of str


def _fmt(value: Fraction) -> str:
    return f"{float(value):g}"


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.warnings = []
        self.melody_node = None
        self.chords_node = None

    # ---------- public API ----------
    def analyze(self, program: nodes.ProgramNode) -> SemanticResult:
        # Pass 1: collect declarations.
        for statement in program.statements:
            self._collect(statement)

        if self.melody_node is None and self.chords_node is None:
            raise SemanticError(
                "The program has no melody and no chord progression, "
                "so there is nothing to play.",
                1, 1,
            )

        # Pass 2: check the content, now that tempo/key/time are known.
        melody = self._check_melody()
        chords = self._check_chords()
        self._compare_lengths(melody, chords)
        return SemanticResult(self.symbols, melody, chords, self.warnings)

    # ---------- pass 1 ----------
    def _declare(self, name: str, node):
        if not self.symbols.declare(name):
            raise SemanticError(
                f"Duplicate {name} declaration.", node.line, node.column
            )

    def _collect(self, node):
        if isinstance(node, nodes.TempoNode):
            self._declare("tempo", node)
            if node.bpm <= 0:
                raise SemanticError(
                    f"Invalid tempo {node.bpm}. Tempo must be positive.",
                    node.line, node.column,
                )
            self.symbols.tempo = node.bpm
        elif isinstance(node, nodes.KeyNode):
            self._declare("key", node)
            if KEY_PATTERN.fullmatch(node.tonic) is None:
                raise SemanticError(
                    f"Invalid key '{node.tonic}'.",
                    node.line, node.column,
                    expected="A note from A to G, optionally with # or b",
                    found=node.tonic,
                )
            self.symbols.key_tonic = node.tonic
            self.symbols.key_mode = node.mode
        elif isinstance(node, nodes.TimeSignatureNode):
            self._declare("time", node)
            if (node.numerator < 1
                    or node.denominator not in VALID_DENOMINATORS):
                raise SemanticError(
                    f"Invalid time signature "
                    f"{node.numerator}/{node.denominator}.",
                    node.line, node.column,
                    expected="A positive top number and a bottom number "
                             "of 1, 2, 4, 8, 16 or 32",
                )
            self.symbols.time_numerator = node.numerator
            self.symbols.time_denominator = node.denominator
        elif isinstance(node, nodes.MelodyNode):
            self._declare("melody", node)
            self.melody_node = node
        elif isinstance(node, nodes.ChordProgressionNode):
            self._declare("chords", node)
            self.chords_node = node
        else:
            raise SemanticError(
                f"Unknown statement {type(node).__name__}.",
                node.line, node.column,
            )

    # ---------- pass 2 ----------
    def _duration(self, node) -> Fraction:
        beats = DURATION_BEATS.get(node.duration)
        if beats is None:
            raise SemanticError(
                f"Invalid duration '{node.duration}'.",
                node.line, node.column,
                expected="w, h, q, e or s",
                found=node.duration,
            )
        return beats

    def _check_melody(self) -> list:
        if self.melody_node is None:
            return []
        items, events = [], []
        for event in self.melody_node.events:
            if isinstance(event, nodes.BarLineNode):
                items.append(BAR_LINE)
                continue
            if isinstance(event, nodes.NoteNode):
                try:
                    pitch = parse_pitch(event.pitch)
                except InvalidPitchError as problem:
                    raise SemanticError(
                        str(problem), event.line, event.column
                    ) from None
                beats = self._duration(event)
                events.append(AnalyzedEvent(pitch.midi, beats, str(pitch)))
            else:  # RestNode
                beats = self._duration(event)
                events.append(AnalyzedEvent(None, beats, None))
            items.append(Timed(beats, event.line, event.column))
        check_bars(items, self.symbols.beats_per_bar)
        return events

    def _check_chords(self) -> list:
        if self.chords_node is None:
            return []
        resolved = []
        for chord in self.chords_node.chords:
            try:
                resolved.append(resolve_chord(
                    chord.symbol,
                    self.symbols.key_tonic,
                    self.symbols.key_mode,
                ))
            except ChordError as problem:
                raise SemanticError(
                    str(problem), chord.line, chord.column
                ) from None
        return resolved

    def _compare_lengths(self, melody, chords):
        """Design D8: a length mismatch is a warning, not an error."""
        if not melody or not chords:
            return
        melody_beats = sum((e.beats for e in melody), Fraction(0))
        chord_beats = len(chords) * self.symbols.beats_per_bar
        if melody_beats != chord_beats:
            self.warnings.append(
                f"The melody lasts {_fmt(melody_beats)} beats but the "
                f"chord progression lasts {_fmt(chord_beats)} beats."
            )


def analyze(program: nodes.ProgramNode) -> SemanticResult:
    """Convenience function: AST in, checked result out."""
    return SemanticAnalyzer().analyze(program)