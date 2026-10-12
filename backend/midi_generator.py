"""MIDI backend: writes a Standard MIDI File using only the standard library."""

import struct
from fractions import Fraction

from compiler.ir import CHORDS, IRProgram

TICKS_PER_BEAT = 480        # MIDI resolution: ticks in one quarter note
MELODY_CHANNEL = 0
CHORD_CHANNEL = 1
MELODY_VELOCITY = 90        # how hard the note is struck (0-127)
CHORD_VELOCITY = 60         # chords are quieter than the melody

# Sort order for events that happen at the same tick.
_META, _NOTE_OFF, _NOTE_ON = 0, 1, 2


def _vlq(value: int) -> bytes:
    """Encode an integer as a MIDI variable-length quantity."""
    chunks = [value & 0x7F]
    value >>= 7
    while value:
        chunks.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(chunks))


def _ticks(beats) -> int:
    return round(Fraction(beats) * TICKS_PER_BEAT)


def _meta(kind: int, payload: bytes) -> bytes:
    return bytes([0xFF, kind, len(payload)]) + payload


def generate_midi(program: IRProgram) -> bytes:
    """Convert an IRProgram into the bytes of a .mid file."""
    events = []   # (tick, order, raw_bytes)

    # Header events at tick 0: tempo and time signature.
    microseconds_per_beat = 60_000_000 // program.tempo
    events.append((0, _META, _meta(0x51, microseconds_per_beat.to_bytes(3, "big"))))
    denominator_power = program.time_denominator.bit_length() - 1   # 4 -> 2
    events.append((0, _META, _meta(
        0x58, bytes([program.time_numerator, denominator_power, 24, 8]),
    )))

    # Notes and chords.
    for event in program.events:
        if not event.midi:          # rests make no sound
            continue
        is_chord = event.track == CHORDS
        channel = CHORD_CHANNEL if is_chord else MELODY_CHANNEL
        velocity = CHORD_VELOCITY if is_chord else MELODY_VELOCITY
        start, end = _ticks(event.start), _ticks(event.end)
        for number in event.midi:
            events.append((start, _NOTE_ON,
                           bytes([0x90 | channel, number, velocity])))
            events.append((end, _NOTE_OFF,
                           bytes([0x80 | channel, number, 0])))

    # Note-offs sort before note-ons at the same tick.
    events.sort(key=lambda item: (item[0], item[1]))

    track = bytearray()
    previous = 0
    for tick, _, raw in events:
        track += _vlq(tick - previous) + raw
        previous = tick
    track += _vlq(0) + _meta(0x2F, b"")     # end of track

    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_PER_BEAT)
    return header + b"MTrk" + struct.pack(">I", len(track)) + bytes(track)


def write_midi(program: IRProgram, path: str) -> None:
    """Write the compiled song to a .mid file."""
    with open(path, "wb") as handle:
        handle.write(generate_midi(program))