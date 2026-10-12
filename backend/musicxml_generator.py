"""MusicXML backend: writes sheet-music XML using the standard library."""

import xml.etree.ElementTree as ET
from fractions import Fraction

from compiler.ir import CHORDS, MELODY, IRProgram

DIVISIONS = 8    # XML time units per quarter note (so a 32nd note = 1)

HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 '
    'Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
)

NATURAL_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# Length in beats -> (note type, number of dots).
NOTE_TYPES = {
    Fraction(4): ("whole", 0),
    Fraction(3): ("half", 1),
    Fraction(2): ("half", 0),
    Fraction(3, 2): ("quarter", 1),
    Fraction(1): ("quarter", 0),
    Fraction(3, 4): ("eighth", 1),
    Fraction(1, 2): ("eighth", 0),
    Fraction(3, 8): ("16th", 1),
    Fraction(1, 4): ("16th", 0),
    Fraction(1, 8): ("32nd", 0),
}

# Number of sharps (+) or flats (-) in each key signature.
MAJOR_FIFTHS = {
    "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
    "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7,
}
MINOR_FIFTHS = {
    "A": 0, "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7,
    "D": -1, "G": -2, "C": -3, "F": -4, "Bb": -5, "Eb": -6, "Ab": -7,
}


def _text(parent, tag, value):
    ET.SubElement(parent, tag).text = str(value)


def _add_duration(note, beats):
    _text(note, "duration", round(Fraction(beats) * DIVISIONS))
    kind = NOTE_TYPES.get(Fraction(beats))
    if kind is not None:
        _text(note, "type", kind[0])
        if kind[1]:
            ET.SubElement(note, "dot")


def _add_note(measure, name, midi, beats, chord=False):
    note = ET.SubElement(measure, "note")
    if chord:
        ET.SubElement(note, "chord")
    letter = name[0]
    accidental = name[1:].rstrip("0123456789")
    alter = accidental.count("#") - accidental.count("b")
    pitch = ET.SubElement(note, "pitch")
    _text(pitch, "step", letter)
    if alter:
        _text(pitch, "alter", alter)
    _text(pitch, "octave", (midi - NATURAL_PC[letter] - alter) // 12 - 1)
    _add_duration(note, beats)


def _add_rest(measure, beats):
    note = ET.SubElement(measure, "note")
    ET.SubElement(note, "rest")
    _add_duration(note, beats)


def _add_attributes(measure, program):
    attributes = ET.SubElement(measure, "attributes")
    _text(attributes, "divisions", DIVISIONS)
    table = MAJOR_FIFTHS if program.key_mode == "major" else MINOR_FIFTHS
    key = ET.SubElement(attributes, "key")
    _text(key, "fifths", table.get(program.key_tonic, 0))
    _text(key, "mode", program.key_mode)
    time = ET.SubElement(attributes, "time")
    _text(time, "beats", program.time_numerator)
    _text(time, "beat-type", program.time_denominator)
    clef = ET.SubElement(attributes, "clef")
    _text(clef, "sign", "G")
    _text(clef, "line", 2)


def _add_tempo(measure, tempo):
    direction = ET.SubElement(measure, "direction", placement="above")
    ET.SubElement(direction, "direction-type")
    ET.SubElement(direction, "sound", tempo=str(tempo))


def _build_part(root, part_id, events, program, with_tempo):
    part = ET.SubElement(root, "part", id=part_id)
    bar = program.beats_per_bar
    grouped = {}
    for event in events:
        grouped.setdefault(int(event.start // bar), []).append(event)
    for position, index in enumerate(sorted(grouped), start=1):
        measure = ET.SubElement(part, "measure", number=str(position))
        if position == 1:
            _add_attributes(measure, program)
            if with_tempo:
                _add_tempo(measure, program.tempo)
        for event in grouped[index]:
            if event.kind == "rest":
                _add_rest(measure, event.duration)
                continue
            for i, (name, midi) in enumerate(zip(event.names, event.midi)):
                _add_note(measure, name, midi, event.duration, chord=i > 0)


def generate_musicxml(program: IRProgram) -> str:
    """Convert an IRProgram into a MusicXML document (as text)."""
    root = ET.Element("score-partwise", version="3.1")
    tracks = [("P1", "Melody", MELODY), ("P2", "Chords", CHORDS)]
    used = [(pid, name, program.track(track)) for pid, name, track in tracks
            if program.track(track)]

    part_list = ET.SubElement(root, "part-list")
    for pid, name, _ in used:
        score_part = ET.SubElement(part_list, "score-part", id=pid)
        _text(score_part, "part-name", name)
    for number, (pid, _, events) in enumerate(used):
        _build_part(root, pid, events, program, with_tempo=(number == 0))

    ET.indent(root)
    return HEADER + ET.tostring(root, encoding="unicode")


def write_musicxml(program: IRProgram, path: str) -> None:
    """Write the compiled song to a .musicxml file."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(generate_musicxml(program))
