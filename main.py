"""Command-line entry point: python main.py examples\hello.mdsl"""

import argparse
import os
import sys

from compiler.compiler import compile_file
from compiler.ir import format_ir
from utils.errors import LexicalError, ParserError, SemanticError


def main() -> int:
    cli = argparse.ArgumentParser(description="MusicDSL compiler")
    cli.add_argument("source", help="path to a .mdsl file")
    cli.add_argument("-o", "--output", help="path of the .mid file to write")
    cli.add_argument("--show-ir", action="store_true",
                     help="print the intermediate representation")
    args = cli.parse_args()

    output = args.output or os.path.splitext(args.source)[0] + ".mid"

    try:
        result = compile_file(args.source, output)
    except FileNotFoundError:
        print(f"File not found: {args.source}")
        return 1
    except LexicalError as error:
        print(f"Lexical Error: {error}")
        return 1
    except ParserError as error:
        print(f"Syntax Error: {error}")
        return 1
    except SemanticError as error:
        print(f"Semantic Error: {error}")
        return 1

    for warning in result.warnings:
        print(f"Warning: {warning}")
    if args.show_ir:
        print(format_ir(result.ir))
    print(f"Compiled {args.source} -> {output} "
          f"({len(result.ir.events)} events, "
          f"{result.ir.total_beats} beats)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
