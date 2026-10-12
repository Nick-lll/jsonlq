# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- `keys` command: list every field path seen across a file, with a presence
  count, so an unfamiliar export can be explored without opening an editor.
- `--output csv` for `show`, so results can be pasted into a spreadsheet.
- Streaming aggregation, so `stats` does not need the whole file in memory.

## [0.1.0] - 2026-10-12

### Added

- `jsonlq show` — print records, with repeatable `--where` filters, field
  selection (`--field`), a record limit, and `--count`.
- `jsonlq stats` — per-field presence, distinct count, the ten most common
  values, and min/max/mean/median/sum when every present value is numeric.
- Filter operators: `=`, `!=`, `>`, `>=`, `<`, `<=`, `~` (case-insensitive
  substring). Numeric comparison is used when both sides parse as numbers.
- Dotted field paths, including list indexing: `errors.0.message`,
  `items.-1.id`.
- Unparsable lines are reported on stderr with their line number and skipped,
  so one bad line does not discard a file.
- Thirteen tests covering parsing, path traversal, filter semantics, the
  missing-field rule, summaries, and CLI exit codes.
- GitHub Actions CI across Python 3.10–3.13, including a CLI smoke test.
- MIT license.

### Notes

A record that does not contain the filtered field never matches — including for
`!=`. A missing value is not evidence of difference, and silently treating it
as one is the kind of quiet wrong answer this tool exists to avoid.
