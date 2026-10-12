# MusicDSL: A Compile-Time Music Generation DSL

A small domain-specific language that describes a song (tempo, key, time
signature, melody and chord progression) and a compiler that turns it into
a playable MIDI file, WAV audio and MusicXML sheet music.

Compiler Design Mini Project, B.Tech CSE, 2026-27.

## Pipeline

    source (.mdsl)
      -> Lexer           tokens
      -> Parser          AST (recursive descent)
      -> Semantic check  pitches, bar durations, chord resolution
      -> IR              timeline of timed note/chord events
      -> Backends        MIDI (.mid), MusicXML (.musicxml), WAV (.wav)

All work is done at compile time. Backends use only the Python standard library.

## Example

    tempo 100
    key C major
    time 4/4

    melody {
      C4:q E4:q G4:q E4:q
      A4:q C5:q E5:q C5:q
    }

    chords { I - vi - IV - V }

- `tempo`: beats per minute
- `key`: tonic and mode, used to resolve Roman-numeral chords
- `time`: time signature, used to validate bar lengths
- `melody { ... }`: notes written as pitch and duration (`C4:q` is a quarter note)
- `chords { ... }`: a progression of Roman numerals separated by `-`

## Setup

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

## Usage

Command line:

    python main.py examples\hello.mdsl
    python main.py examples\hello.mdsl --xml --wav --show-ir

Web UI:

    python -m streamlit run app.py

## Errors

Each compiler phase reports its own error type with a line number:

| File | Phase | Result |
|---|---|---|
| examples\error_lexical.mdsl | Lexer | Lexical Error |
| examples\error_syntax.mdsl | Parser | Syntax Error |
| examples\error_semantic.mdsl | Semantic analysis | Semantic Error |

## Tests

    pytest -q

## Limitations

- Single instrument; MIDI chords and melody use separate channels only
- WAV output is a plain sine-wave synthesis
- No key-signature event in the MIDI output
