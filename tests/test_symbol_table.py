from fractions import Fraction

from compiler.symbol_table import SymbolTable


def test_defaults():
    table = SymbolTable()
    assert table.tempo == 120
    assert (table.key_tonic, table.key_mode) == ("C", "major")
    assert table.beats_per_bar == Fraction(4)


def test_bar_length_for_common_time_signatures():
    for num, den, expected in [(4, 4, 4), (3, 4, 3), (6, 8, 3), (2, 4, 2)]:
        table = SymbolTable(time_numerator=num, time_denominator=den)
        assert table.beats_per_bar == Fraction(expected)


def test_duplicate_declaration_is_detected():
    table = SymbolTable()
    assert table.declare("tempo") is True
    assert table.declare("tempo") is False
    assert table.declare("key") is True


def test_tables_do_not_share_declarations():
    first, second = SymbolTable(), SymbolTable()
    first.declare("tempo")
    assert second.declare("tempo") is True