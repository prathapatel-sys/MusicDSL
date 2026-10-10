"""Hand-written lexer for MusicDSL."""

import re
import sys

from compiler.tokens import KEYWORDS, Token, TokenType
from utils.errors import LexicalError

# Shape only: a letter, optional # or b, then digits. Validity is checked later.
PITCH_SHAPE = re.compile(r"^[A-Za-z][#b]?\d+$")
ROMAN_SHAPE = re.compile(r"^[IViv]+(\u00b0|dim)?$")

SYMBOLS = {
    ":": TokenType.COLON,
    "/": TokenType.SLASH,
    "-": TokenType.DASH,
    "|": TokenType.BAR,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
}


class Lexer:
    """Turns MusicDSL source text into a list of tokens."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0        # which character we are looking at
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    # ---------- public API ----------
    def tokenize(self) -> list[Token]:
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "#":
                self._skip_comment()
            elif self._is_digit(ch):
                self._read_number()
            elif self._is_letter(ch):
                self._read_word()
            elif ch in SYMBOLS:
                self._read_symbol()
            else:
                raise LexicalError(
                    f"Unexpected character '{ch}'.",
                    self.line, self.column,
                )
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    # ---------- character helpers ----------
    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        """Current character, or '' at end of input."""
        return "" if self._at_end() else self.source[self.pos]

    def _advance(self) -> str:
        """Consume one character and keep line/column up to date."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    @staticmethod
    def _is_digit(ch: str) -> bool:
        return ch.isascii() and ch.isdigit()

    @staticmethod
    def _is_letter(ch: str) -> bool:
        return ch.isascii() and ch.isalpha()

    # ---------- token readers ----------
    def _add(self, token_type, value, line, column):
        self.tokens.append(Token(token_type, value, line, column))

    def _skip_comment(self):
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _read_number(self):
        line, column = self.line, self.column
        text = ""
        while self._is_digit(self._peek()):
            text += self._advance()
        self._add(TokenType.NUMBER, int(text), line, column)

    def _read_symbol(self):
        line, column = self.line, self.column
        ch = self._advance()
        self._add(SYMBOLS[ch], ch, line, column)

    def _read_word(self):
        line, column = self.line, self.column
        text = self._advance()  # first letter

        # A '#' stuck directly to a note letter is a sharp, not a comment.
        if text in "ABCDEFG" and self._peek() == "#":
            text += self._advance()

        while self._is_letter(self._peek()) or self._is_digit(self._peek()):
            text += self._advance()

        # The degree sign belongs to Roman numerals like vii°
        if self._peek() == "\u00b0" and re.fullmatch(r"[IViv]+", text):
            text += self._advance()

        self._add(self._classify(text), text, line, column)

    def _classify(self, text: str) -> TokenType:
        previous = self.tokens[-1].type if self.tokens else None
        if previous == TokenType.COLON:
            return TokenType.DURATION
        if PITCH_SHAPE.match(text):
            return TokenType.PITCH
        if text in KEYWORDS:
            return KEYWORDS[text]
        if text == "R":
            return TokenType.REST
        if ROMAN_SHAPE.match(text):
            return TokenType.ROMAN
        return TokenType.IDENT

def tokenize(source: str) -> list[Token]:
    """Convenience function: source text in, tokens out."""
    return Lexer(source).tokenize()


if __name__ == "__main__":
    # Dev helper:  python -m compiler.lexer examples/simple_melody.mus
    with open(sys.argv[1], encoding="utf-8") as f:
        source = f.read()
    try:
        for t in tokenize(source):
            print(t.type.name, repr(t.value), f"{t.line}:{t.column}")
    except LexicalError as err:
        print(err)