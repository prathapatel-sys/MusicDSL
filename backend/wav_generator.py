"""WAV backend: synthesizes audio from the IR using only the standard library."""

import io
import math
import struct
import wave

from compiler.ir import CHORDS, IRProgram

SAMPLE_RATE = 22050          # samples per second (CD quality is 44100)
MELODY_AMPLITUDE = 0.35      # loudness of the melody (max is 1.0)
CHORD_AMPLITUDE = 0.12       # each chord note is quieter, so 3 together stay below 1.0
ATTACK = 0.01                # fade-in, seconds
RELEASE = 0.03               # fade-out, seconds


def midi_to_frequency(number: int) -> float:
    """MIDI note number to Hz: A4 (69) is 440 Hz, each semitone is x 2**(1/12)."""
    return 440.0 * 2 ** ((number - 69) / 12)


def _envelope(index: int, length: int) -> float:
    """Volume from 0 to 1: fades in at the start and out at the end."""
    attack = int(SAMPLE_RATE * ATTACK)
    release = int(SAMPLE_RATE * RELEASE)
    gain = 1.0
    if index < attack:
        gain = index / attack
    if index >= length - release:
        gain = min(gain, (length - index) / release)
    return gain


def render_samples(program: IRProgram) -> list:
    """Mix every note and chord into one list of floats between -1 and 1."""
    total = math.ceil(program.beats_to_seconds(program.total_beats) * SAMPLE_RATE)
    buffer = [0.0] * total
    for event in program.events:
        if not event.midi:               # rests stay silent
            continue
        amplitude = CHORD_AMPLITUDE if event.track == CHORDS else MELODY_AMPLITUDE
        start = int(program.beats_to_seconds(event.start) * SAMPLE_RATE)
        length = int(program.beats_to_seconds(event.duration) * SAMPLE_RATE)
        length = min(length, total - start)
        for number in event.midi:
            step = 2 * math.pi * midi_to_frequency(number) / SAMPLE_RATE
            for i in range(length):
                buffer[start + i] += (
                    amplitude * _envelope(i, length) * math.sin(step * i)
                )
    return buffer


def generate_wav(program: IRProgram) -> bytes:
    """Convert an IRProgram into the bytes of a mono 16-bit .wav file."""
    samples = render_samples(program)
    ints = [int(max(-1.0, min(1.0, s)) * 32767) for s in samples]
    pcm = struct.pack(f"<{len(ints)}h", *ints)
    stream = io.BytesIO()
    with wave.open(stream, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)           # 2 bytes = 16 bits
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm)
    return stream.getvalue()


def write_wav(program: IRProgram, path: str) -> None:
    """Write the compiled song to a .wav file."""
    with open(path, "wb") as handle:
        handle.write(generate_wav(program))
