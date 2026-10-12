"""Command-line interface for jsonlq."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import JsonlError, apply_filter, read_records, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jsonlq",
        description="Query and summarize JSONL files.",
    )
    parser.add_argument("--version", action="version", version=f"jsonlq {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="print records, optionally filtered")
    show.add_argument("path", type=Path)
    show.add_argument("-w", "--where", action="append", default=[],
                      help="filter, e.g. -w 'level=error' (repeatable, ANDed)")
    show.add_argument("-f", "--field", action="append", default=[],
                      help="only print these fields (repeatable)")
    show.add_argument("-n", "--limit", type=int, default=0, help="stop after N records")
    show.add_argument("--count", action="store_true", help="print only the match count")

    stats = sub.add_parser("stats", help="summarize one field")
    stats.add_argument("path", type=Path)
    stats.add_argument("field")
    stats.add_argument("-w", "--where", action="append", default=[])
    stats.add_argument("--json", action="store_true", help="machine-readable output")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        records, bad = read_records(args.path)
    except FileNotFoundError:
        print(f"jsonlq: no such file: {args.path}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"jsonlq: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    for item in bad:
        print(f"jsonlq: line {item.number} skipped ({item.reason})", file=sys.stderr)

    try:
        for expression in args.where:
            records = apply_filter(records, expression)
    except JsonlError as exc:
        print(f"jsonlq: {exc}", file=sys.stderr)
        return 2

    if args.command == "show":
        return _show(args, records)
    return _stats(args, records)


def _show(args: argparse.Namespace, records: list[dict]) -> int:
    if args.count:
        print(len(records))
        return 0
    emitted = 0
    for record in records:
        if args.field:
            record = {key: record[key] for key in args.field if key in record}
        print(json.dumps(record, ensure_ascii=False, default=str))
        emitted += 1
        if args.limit and emitted >= args.limit:
            break
    return 0


def _stats(args: argparse.Namespace, records: list[dict]) -> int:
    result = summarize(records, args.field)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    print(f"field    : {result['field']}")
    print(f"records  : {result['records']}  present {result['present']}  "
          f"missing {result['missing']}")
    print(f"distinct : {result['distinct']}")
    if result["top"]:
        print("top values:")
        for value, count in result["top"]:
            print(f"  {count:>6}  {value}")
    if "numeric" in result:
        num = result["numeric"]
        print("numeric:")
        print(f"  min {num['min']}  max {num['max']}  mean {num['mean']:.4g}  "
              f"median {num['median']}  sum {num['sum']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
