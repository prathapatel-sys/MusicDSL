"""Note durations and bar lengths, measured in quarter-note beats."""

from fractions import Fraction

# Length of each duration symbol, in quarter-note beats.
DURATION_BEATS = {
    "w": Fraction(4),      # whole
    "h": Fraction(2),      # half
    "q": Fraction(1),      # quarter
    "e": Fraction(1, 2),   # eighth
    "s": Fraction(1, 4),   # sixteenth
}

VALID_DURATIONS = list(DURATION_BEATS)   # ['w', 'h', 'q', 'e', 's']

VALID_BEAT_UNITS = (2, 4, 8, 16)         # allowed bottoms of a time signature
MAX_BEATS_PER_BAR = 32


def is_valid_duration(symbol: str) -> bool:
    """True for w, h, q, e, s (lowercase only)."""
    return symbol in DURATION_BEATS


def duration_to_beats(symbol: str) -> Fraction:
    """Beats for a duration symbol. Call is_valid_duration first."""
    return DURATION_BEATS[symbol]


def is_valid_time_signature(numerator: int, denominator: int) -> bool:
    """4/4, 3/4, 6/8 ... are valid; 4/3 or 0/4 are not."""
    return (1 <= numerator <= MAX_BEATS_PER_BAR
            and denominator in VALID_BEAT_UNITS)


def bar_length(numerator: int, denominator: int) -> Fraction:
    """Length of one bar in quarter-note beats (4/4 -> 4, 6/8 -> 3)."""
    return Fraction(4 * numerator, denominator)


def format_beats(beats: Fraction) -> str:
    """Friendly text for error messages: 5 -> '5', 3/2 -> '1.5'."""
    return f"{float(beats):g}"