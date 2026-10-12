import pytest

from compiler.compiler import compile_file, compile_source
from utils.errors import LexicalError, ParserError, SemanticError

HELLO = """
tempo 100
key C major
time 4/4

melody {
  C4:q E4:q G4:q E4:q
  A4:q C5:q E5:q C5:q
  F4:q A4:q C5:q A4:q
  G4:q B4:q D5:q G4:q
}

chords { I - vi - IV - V }
"""


def test_full_pipeline_produces_midi():
    result = compile_source(HELLO)
    assert result.ir.tempo == 100
    assert result.ir.total_beats == 16
    assert result.midi[:4] == b"MThd"
    assert result.warnings == []


def test_length_mismatch_is_only_a_warning():
    result = compile_source(
        "melody { C4:q D4:q E4:q F4:q }\nchords { I - V }"
    )
    assert len(result.warnings) == 1
    assert result.midi[:4] == b"MThd"


def test_semantic_error_stops_compilation():
    with pytest.raises(SemanticError) as info:
        compile_source("melody { H4:q }")
    assert "Invalid pitch 'H4'." in str(info.value)


def test_syntax_error_stops_compilation():
    with pytest.raises(ParserError):
        compile_source("tempo C")


def test_lexical_error_stops_compilation():
    with pytest.raises(LexicalError):
        compile_source("melody {\n  C4:q $\n}")


def test_compile_file_writes_a_midi_file(tmp_path):
    source = tmp_path / "song.mdsl"
    source.write_text(HELLO, encoding="utf-8")
    target = tmp_path / "song.mid"
    compile_file(str(source), str(target))
    assert target.read_bytes()[:4] == b"MThd"
