"""Symbol table: the global settings the semantic analyzer collects."""

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass
class SymbolTable:
    """Tempo, key and time signature, with the defaults from design D4."""

    tempo: int = 120
    key_tonic: str = "C"
    key_mode: str = "major"
    time_numerator: int = 4
    time_denominator: int = 4
    declared: set = field(default_factory=set)

    def declare(self, name: str) -> bool:
        """Mark a setting ('tempo', 'key', 'time') as declared.

        Returns False if it was already declared, so the analyzer
        can report a duplicate-declaration Semantic Error.
        """
        if name in self.declared:
            return False
        self.declared.add(name)
        return True

    @property
    def beats_per_bar(self) -> Fraction:
        """Bar length in quarter-note beats (design D2)."""
        return Fraction(self.time_numerator * 4, self.time_denominator)