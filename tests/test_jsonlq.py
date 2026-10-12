"""Tests for jsonlq.core and the CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jsonlq.cli import main
from jsonlq.core import JsonlError, apply_filter, iter_values, read_records, summarize


def write(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "data.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_read_records_collects_bad_lines_separately(tmp_path):
    path = write(tmp_path, [
        '{"a": 1}',
        'not json',
        '[1, 2]',
        '',
        '{"a": 2}',
    ])
    records, bad = read_records(path)
    assert records == [{"a": 1}, {"a": 2}]
    assert [item.number for item in bad] == [2, 3]
    assert "invalid JSON" in bad[0].reason
    assert "not a JSON object" in bad[1].reason


def test_iter_values_walks_nested_and_list_paths():
    record = {"a": {"b": {"c": 7}}, "xs": [{"m": 1}, {"m": 2}]}
    assert list(iter_values(record, "a.b.c")) == [7]
    assert list(iter_values(record, "xs.1.m")) == [2]
    assert list(iter_values(record, "xs.-1.m")) == [2]
    assert list(iter_values(record, "nope")) == []
    assert list(iter_values(record, "xs.9.m")) == []


def test_filter_numeric_and_string_and_substring():
    records = [{"n": 1, "s": "Alpha"}, {"n": 10, "s": "beta"}, {"n": 2, "s": "gamma"}]
    assert apply_filter(records, "n>5") == [records[1]]
    assert apply_filter(records, "n<=2") == [records[0], records[2]]
    assert apply_filter(records, "s=alpha") == []
    assert apply_filter(records, "s~ALP") == [records[0]]
    assert apply_filter(records, "n=1") == [records[0]]


def test_missing_field_never_matches_not_even_inequality():
    records = [{"n": 1}, {"m": 2}]
    assert apply_filter(records, "n!=1") == []
    assert apply_filter(records, "n=1") == [records[0]]


def test_filter_requires_an_operator():
    with pytest.raises(JsonlError):
        apply_filter([{"n": 1}], "n")
    with pytest.raises(JsonlError):
        apply_filter([{"n": 1}], "=1")


def test_summarize_counts_missing_and_numeric_stats():
    records = [{"v": 1}, {"v": 3}, {"other": 9}]
    result = summarize(records, "v")
    assert result["records"] == 3
    assert result["present"] == 2
    assert result["missing"] == 1
    assert result["distinct"] == 2
    assert result["numeric"]["min"] == 1
    assert result["numeric"]["max"] == 3
    assert result["numeric"]["median"] == 2


def test_summarize_without_numbers_omits_numeric_block():
    result = summarize([{"v": "x"}, {"v": "y"}], "v")
    assert "numeric" not in result
    assert result["distinct"] == 2


def test_cli_show_count_and_limit(tmp_path, capsys):
    path = write(tmp_path, ['{"n": 1}', '{"n": 2}', '{"n": 3}'])
    assert main(["show", str(path), "--count"]) == 0
    assert capsys.readouterr().out.strip() == "3"

    assert main(["show", str(path), "-w", "n>=2", "-n", "1"]) == 0
    printed = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert printed == [{"n": 2}]


def test_cli_reports_bad_lines_on_stderr_but_still_succeeds(tmp_path, capsys):
    path = write(tmp_path, ['{"n": 1}', 'oops'])
    assert main(["show", str(path), "--count"]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "1"
    assert "line 2 skipped" in captured.err


def test_cli_missing_file_returns_two(tmp_path, capsys):
    assert main(["show", str(tmp_path / "nope.jsonl")]) == 2
    assert "no such file" in capsys.readouterr().err


def test_cli_bad_filter_returns_two(tmp_path, capsys):
    path = write(tmp_path, ['{"n": 1}'])
    assert main(["show", str(path), "-w", "n"]) == 2
    assert "no operator" in capsys.readouterr().err


def test_cli_stats_json(tmp_path, capsys):
    path = write(tmp_path, ['{"v": 2}', '{"v": 4}'])
    assert main(["stats", str(path), "v", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["numeric"]["mean"] == 3
