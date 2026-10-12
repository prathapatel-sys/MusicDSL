"""Compiler driver: runs every stage from source text to MIDI bytes."""

from dataclasses import dataclass

from backend.midi_generator import generate_midi
from compiler.ir import IRProgram
from compiler.ir_generator import generate_ir
from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.semantic import SemanticResult, analyze


@dataclass
class CompileResult:
    """Every stage's output, so the demo and the UI can show each one."""
    source: str
    tokens: list
    ast: object
    analysis: SemanticResult
    ir: IRProgram
    midi: bytes

    @property
    def warnings(self) -> list:
        return self.analysis.warnings


def compile_source(source: str) -> CompileResult:
    """Lexer -> parser -> semantic analyzer -> IR -> MIDI."""
    tokens = tokenize(source)
    ast = Parser(tokens).parse()
    analysis = analyze(ast)
    ir = generate_ir(analysis)
    midi = generate_midi(ir)
    return CompileResult(source, tokens, ast, analysis, ir, midi)


def compile_file(source_path: str, midi_path: str) -> CompileResult:
    """Compile a .mdsl file and write the .mid file."""
    # utf-8-sig quietly drops the BOM that PowerShell/Notepad may add.
    with open(source_path, encoding="utf-8-sig") as handle:
        source = handle.read()
    result = compile_source(source)
    with open(midi_path, "wb") as handle:
        handle.write(result.midi)
    return result
