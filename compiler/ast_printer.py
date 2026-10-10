"""Draws an AST as a readable text tree."""

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

TEE = "\u251c\u2500\u2500 "      # ├──  (more siblings below)
ELBOW = "\u2514\u2500\u2500 "    # └──  (last sibling)
PIPE = "\u2502   "               # │    (line continues down)
SPACE = "    "                   # nothing to continue


def _label(node) -> str:
    """The one-line description of a node."""
    if isinstance(node, ProgramNode):
        return "Program"
    if isinstance(node, TempoNode):
        return f"Tempo({node.bpm})"
    if isinstance(node, KeyNode):
        return f"Key({node.tonic}, {node.mode})"
    if isinstance(node, TimeSignatureNode):
        return f"TimeSignature({node.numerator}, {node.denominator})"
    if isinstance(node, MelodyNode):
        return "Melody"
    if isinstance(node, NoteNode):
        return f"Note({node.pitch}, {node.duration})"
    if isinstance(node, RestNode):
        return f"Rest({node.duration})"
    if isinstance(node, BarLineNode):
        return "BarLine"
    if isinstance(node, ChordProgressionNode):
        return "ChordProgression"
    if isinstance(node, ChordNode):
        return f"Chord({node.symbol})"
    return type(node).__name__


def _children(node) -> list:
    """The child nodes of a node (leaf nodes have none)."""
    if isinstance(node, ProgramNode):
        return node.statements
    if isinstance(node, MelodyNode):
        return node.events
    if isinstance(node, ChordProgressionNode):
        return node.chords
    return []


def _add_children(node, prefix: str, lines: list) -> None:
    children = _children(node)
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        lines.append(prefix + (ELBOW if is_last else TEE) + _label(child))
        # Children of this child are indented one level deeper.
        _add_children(child, prefix + (SPACE if is_last else PIPE), lines)


def format_ast(node) -> str:
    """Return the whole tree below `node` as a multi-line string."""
    lines = [_label(node)]
    _add_children(node, "", lines)
    return "\n".join(lines)