"""Compiler error types. Every stage raises one of these."""


class CompilerError(Exception):
    """Base class for all MusicDSL compiler errors."""

    kind = "Compiler Error"

    def __init__(self, message, line=None, column=None,
                 expected=None, found=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.expected = expected
        self.found = found

    def __str__(self):
        where = ""
        if self.line is not None:
            where = f" at line {self.line}, column {self.column}"
        text = f"{self.kind}{where}:\n{self.message}"
        if self.expected is not None:
            text += f"\n\nExpected:\n{self.expected}"
        if self.found is not None:
            text += f"\n\nFound:\n{self.found}"
        return text


class LexicalError(CompilerError):
    kind = "Lexical Error"


class ParserError(CompilerError):
    kind = "Parser Error"


class SemanticError(CompilerError):
    kind = "Semantic Error"


class CodeGenerationError(CompilerError):
    kind = "Code Generation Error"