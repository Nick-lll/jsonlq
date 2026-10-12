"""Core reading and querying logic for jsonlq.

Kept free of argument-parsing concerns so it can be tested directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


class JsonlError(Exception):
    """Raised when a line cannot be parsed as a JSON object."""


@dataclass
class BadLine:
    """A line that failed to parse."""

    number: int
    text: str
    reason: str


def read_records(path: Path) -> tuple[list[dict[str, Any]], list[BadLine]]:
    """Read a JSONL file into records, collecting unparsable lines separately.

    Blank lines are skipped silently. A line that parses but is not a JSON
    object (for example a bare number or an array) is reported as bad, because
    the rest of this tool assumes field access on records.
    """
    records: list[dict[str, Any]] = []
    bad: list[BadLine] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                bad.append(BadLine(number, text, f"invalid JSON: {exc.msg}"))
                continue
            if not isinstance(value, dict):
                bad.append(BadLine(number, text, f"not a JSON object: {type(value).__name__}"))
                continue
            records.append(value)
    return records, bad


def iter_values(record: dict[str, Any], field: str) -> Iterator[Any]:
    """Yield the value(s) at a dotted ``field`` path.

    A missing key yields nothing rather than raising, so aggregates over a
    sparse field stay usable.
    """
    parts = field.split(".")
    current: Any = record
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return
            current = current[part]
        elif isinstance(current, list):
            # Allow indexing into a list, e.g. "errors.0.message".
            if not part.lstrip("-").isdigit():
                return
            index = int(part)
            if not -len(current) <= index < len(current):
                return
            current = current[index]
        else:
            return
    yield current


def apply_filter(records: Iterable[dict[str, Any]], expression: str) -> list[dict[str, Any]]:
    """Filter records by a simple ``field op value`` expression.

    Supported operators: ``=``, ``!=``, ``>``, ``>=``, ``<``, ``<=``, ``~``
    (substring, case-insensitive). Numeric comparison is used when both sides
    parse as numbers, otherwise the comparison falls back to string ordering.
    A record missing the field never matches, including for ``!=``.
    """
    field, op, wanted = _split_expression(expression)
    out: list[dict[str, Any]] = []
    for record in records:
        for value in iter_values(record, field):
            if _matches(value, op, wanted):
                out.append(record)
                break
    return out


_OPS = ("!=", ">=", "<=", "=", ">", "<", "~")


def _split_expression(expression: str) -> tuple[str, str, str]:
    for op in _OPS:
        if op in expression:
            field, _, wanted = expression.partition(op)
            field = field.strip()
            if not field:
                raise JsonlError(f"filter is missing a field name: {expression!r}")
            return field, op, wanted.strip()
    raise JsonlError(
        f"filter {expression!r} has no operator; use one of: " + ", ".join(_OPS)
    )


def _as_number(text: Any) -> float | None:
    if isinstance(text, bool):
        return None
    if isinstance(text, (int, float)):
        return float(text)
    try:
        return float(str(text).strip())
    except (TypeError, ValueError):
        return None


def _matches(value: Any, op: str, wanted: str) -> bool:
    if op == "~":
        return wanted.lower() in str(value).lower()
    if op == "=":
        return _equal(value, wanted)
    if op == "!=":
        return not _equal(value, wanted)
    left, right = _as_number(value), _as_number(wanted)
    if left is None or right is None:
        left, right = str(value), wanted
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    if op == "<":
        return left < right
    return left <= right


def _equal(value: Any, wanted: str) -> bool:
    if isinstance(value, bool):
        return str(value).lower() == wanted.lower()
    number = _as_number(value)
    other = _as_number(wanted)
    if number is not None and other is not None:
        return number == other
    return str(value) == wanted


def summarize(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    """Return counts and, when the values are numeric, basic statistics."""
    counts: dict[str, int] = {}
    numbers: list[float] = []
    present = 0
    for record in records:
        for value in iter_values(record, field):
            present += 1
            key = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            counts[key] = counts.get(key, 0) + 1
            number = _as_number(value)
            if number is not None:
                numbers.append(number)
            break
    result: dict[str, Any] = {
        "field": field,
        "records": len(records),
        "present": present,
        "missing": len(records) - present,
        "distinct": len(counts),
        "top": sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10],
    }
    if numbers and len(numbers) == present:
        ordered = sorted(numbers)
        result["numeric"] = {
            "count": len(ordered),
            "min": ordered[0],
            "max": ordered[-1],
            "sum": sum(ordered),
            "mean": sum(ordered) / len(ordered),
            "median": _median(ordered),
        }
    return result


def _median(ordered: list[float]) -> float:
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
