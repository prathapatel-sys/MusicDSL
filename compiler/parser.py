"""Recursive-descent parser for MusicDSL.

One method per grammar rule. Turns a token list into an AST.
"""

from compiler.ast_nodes import (
    BarLineNode,
    ChordNode,
    ChordProgressionNode,
    KeyNode,
    MelodyNode,
    NoteNode,
    ProgramNode,
    RestNode,
    TempoNode,
    TimeSignatureNode,
)
from compiler.tokens import Token, TokenType as T
from utils.errors import ParserError


class Parser:
    """Builds an AST from the tokens produced by the lexer."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ---------- public API ----------
    def parse(self) -> ProgramNode:
        first = self._peek()
        program = ProgramNode(line=first.line, column=first.column)
        while not self._check(T.EOF):
            program.statements.append(self._statement())
        return program

    # ---------- token helpers ----------
    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _check(self, token_type: T) -> bool:
        return self._peek().type == token_type

    def _advance(self) -> Token:
        token = self._peek()
        if token.type != T.EOF:
            self.pos += 1
        return token

    def _expect(self, token_type: T, message: str) -> Token:
        """Consume a token of the given type, or raise a Parser Error."""
        if self._check(token_type):
            return self._advance()
        bad = self._peek()
        raise ParserError(message, bad.line, bad.column,
                          found=self._describe(bad))

    @staticmethod
    def _describe(token: Token) -> str:
        if token.type == T.EOF:
            return "end of input"
        return f"'{token.value}'"

    # ---------- grammar rules ----------
    def _statement(self):
        token = self._peek()
        if token.type == T.TEMPO:
            return self._tempo()
        if token.type == T.KEY:
            return self._key()
        if token.type == T.TIME:
            return self._time_signature()
        if token.type == T.MELODY:
            return self._melody()
        if token.type == T.CHORDS:
            return self._chords()
        raise ParserError(
            "Expected a statement: 'tempo', 'key', 'time', "
            "'melody' or 'chords'.",
            token.line, token.column, found=self._describe(token),
        )

    def _tempo(self) -> TempoNode:
        keyword = self._advance()  # the word 'tempo'
        number = self._expect(T.NUMBER, "Expected a number after 'tempo'.")
        return TempoNode(bpm=number.value,
                         line=keyword.line, column=keyword.column)

    def _key(self) -> KeyNode:
        keyword = self._advance()  # the word 'key'
        tonic = self._expect(
            T.IDENT, "Expected a key name (like C or F#) after 'key'.")
        if self._check(T.MAJOR) or self._check(T.MINOR):
            mode = self._advance()
        else:
            bad = self._peek()
            raise ParserError(
                "Expected 'major' or 'minor' after the key name.",
                bad.line, bad.column, found=self._describe(bad))
        return KeyNode(tonic=tonic.value, mode=mode.value,
                       line=keyword.line, column=keyword.column)

    def _time_signature(self) -> TimeSignatureNode:
        keyword = self._advance()  # the word 'time'
        top = self._expect(
            T.NUMBER, "Expected a number after 'time' (like 4/4).")
        self._expect(T.SLASH, "Expected '/' in the time signature (like 4/4).")
        bottom = self._expect(
            T.NUMBER, "Expected a number after '/' in the time signature.")
        return TimeSignatureNode(numerator=top.value, denominator=bottom.value,
                                 line=keyword.line, column=keyword.column)

    def _melody(self) -> MelodyNode:
        keyword = self._advance()  # the word 'melody'
        self._expect(T.LBRACE, "Expected '{' after 'melody'.")
        melody = MelodyNode(line=keyword.line, column=keyword.column)
        while not self._check(T.RBRACE):
            if self._check(T.EOF):
                end = self._peek()
                raise ParserError(
                    "Missing '}' to close the 'melody' block that starts "
                    f"at line {keyword.line}.",
                    end.line, end.column, found="end of input")
            melody.events.append(self._melody_event())
        self._advance()  # the closing '}'
        return melody

    def _melody_event(self):
        token = self._peek()
        if token.type == T.PITCH:
            self._advance()
            duration = self._colon_and_duration("pitch")
            return NoteNode(pitch=token.value, duration=duration.value,
                            line=token.line, column=token.column)
        if token.type == T.REST:
            self._advance()
            duration = self._colon_and_duration("rest")
            return RestNode(duration=duration.value,
                            line=token.line, column=token.column)
        if token.type == T.BAR:
            self._advance()
            return BarLineNode(line=token.line, column=token.column)
        raise ParserError(
            "Expected a note (like C4:q), a rest (like R:q) or '|' "
            "inside the melody block.",
            token.line, token.column, found=self._describe(token))

    def _colon_and_duration(self, what: str) -> Token:
        """Read the ':' and the duration that must follow a pitch or rest."""
        self._expect(T.COLON, f"Expected ':' after {what}.")
        return self._expect(
            T.DURATION, "Expected a duration (like q) after ':'.")

    def _chords(self) -> ChordProgressionNode:
        keyword = self._advance()  # the word 'chords'
        self._expect(T.LBRACE, "Expected '{' after 'chords'.")
        progression = ChordProgressionNode(line=keyword.line,
                                           column=keyword.column)
        while True:
            chord = self._expect(
                T.ROMAN, "Expected a chord symbol (like I, vi or IV).")
            progression.chords.append(
                ChordNode(symbol=chord.value,
                          line=chord.line, column=chord.column))
            if self._check(T.DASH):
                self._advance()      # a chord must follow the dash
            elif self._check(T.RBRACE):
                break
            elif self._check(T.EOF):
                end = self._peek()
                raise ParserError(
                    "Missing '}' to close the 'chords' block that starts "
                    f"at line {keyword.line}.",
                    end.line, end.column, found="end of input")
        self._advance()  # the closing '}'
        return progression

if __name__ == "__main__":
    # Dev helper:  python -m compiler.parser examples\simple_melody.mus
    import sys

    from compiler.ast_printer import format_ast
    from compiler.lexer import tokenize
    from utils.errors import CompilerError

    with open(sys.argv[1], encoding="utf-8") as f:
        source = f.read()
    try:
        print(format_ast(Parser(tokenize(source)).parse()))
    except CompilerError as err:
        print(err)