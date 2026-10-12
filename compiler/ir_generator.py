"""IR generator: turns the analyzer's result into an IRProgram."""

from fractions import Fraction

from compiler.ir import CHORDS, MELODY, IREvent, IRProgram
from compiler.semantic import SemanticResult


def generate_ir(result: SemanticResult) -> IRProgram:
    symbols = result.symbols
    events = []

    # Melody: events follow one another, so keep a running clock.
    cursor = Fraction(0)
    for item in result.melody:
        if item.midi is None:
            events.append(IREvent(MELODY, "rest", cursor, item.beats))
        else:
            events.append(IREvent(
                MELODY, "note", cursor, item.beats,
                (item.midi,), (item.pitch,),
            ))
        cursor += item.beats

    # Chords: each one lasts exactly one bar (design D7).
    bar = symbols.beats_per_bar
    for index, chord in enumerate(result.chords):
        events.append(IREvent(
            CHORDS, "chord", index * bar, bar, chord.midi, chord.names,
        ))

    # Stable sort: equal start times keep melody-before-chords order.
    events.sort(key=lambda event: event.start)

    return IRProgram(
        tempo=symbols.tempo,
        key_tonic=symbols.key_tonic,
        key_mode=symbols.key_mode,
        time_numerator=symbols.time_numerator,
        time_denominator=symbols.time_denominator,
        events=tuple(events),
    )