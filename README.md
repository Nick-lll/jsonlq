# jsonlq

Query and summarize JSONL files from the command line.

JSONL (one JSON object per line) is the default output format of most logging
and data-export pipelines, but inspecting it usually means writing a throwaway
Python snippet. `jsonlq` covers the common cases with two commands.

## Install

    python -m pip install -e .

## Usage

    jsonlq show   app.jsonl --where level=error --limit 20
    jsonlq show   app.jsonl --where duration_ms>500 --field id --field duration_ms
    jsonlq show   app.jsonl --where message~timeout --count
    jsonlq stats  app.jsonl duration_ms
    jsonlq stats  app.jsonl status --json

### `show`

Prints matching records. Filters (`-w/--where`) are repeatable and combined
with AND. Supported operators:

| operator | meaning |
|---|---|
| `=`  | equal (numeric when both sides look numeric) |
| `!=` | not equal |
| `>` `>=` `<` `<=` | ordered comparison, numeric when possible |
| `~`  | case-insensitive substring |

Field paths are dotted and may index into lists: `errors.0.message`,
`items.-1.id`. A record that does not contain the field never matches, not
even for `!=` — a missing value is not evidence of difference.

### `stats`

Reports presence, distinct-value count, the ten most common values, and basic
statistics when every present value is numeric.

## Exit codes

| code | meaning |
|---|---|
| 0 | success (unparsable lines are reported on stderr and skipped) |
| 2 | file not found, unreadable, or the filter expression is malformed |

## Development

    python -m pytest

## License

MIT
