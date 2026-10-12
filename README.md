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

## How I review code, including code an assistant wrote

This section exists because the way I judge a proposed change matters more
than the change itself, so it is worth writing down rather than leaving
implicit.

**I decide what would count as correct before I read the diff.** For a bug
fix, that means naming the input that is currently wrong and the output that
would be right; for a feature, the smallest example that must work. If I
cannot state the pass condition, I am not ready to judge the proposal, and
reading it first only makes me rationalise whatever it does.

**I read the failure path before the success path.** Most defects live where
the input is empty, missing, duplicated, malformed, or arrives twice. A patch
that handles the happy path and says nothing about those cases is incomplete
regardless of how clean it looks.

**I look for a case that should fail, and check that it still fails.** A test
that passes tells me very little; a test that passes when the cause is removed
tells me the test is not measuring what it claims. Behaviour demonstrated only
in the direction of success is not demonstrated.

**I check the description against the code.** Comments, docstrings, commit
messages and pull-request text are claims, and claims drift. When the prose
and the code disagree, that disagreement is itself the finding — it does not
matter which one the author intended.

**I distinguish "no evidence of a problem" from "evidence of no problem".**
These read the same in a summary and mean opposite things. "I did not see a
failure" is a statement about my testing; "there is no failure" is a statement
about the world. Only the first one is usually mine to make.

**I prefer the response that is honest about its own limits.** Given two
proposals that both work, the better one says what it does not handle. That is
not modesty, it is information I can act on: it tells me where to look next
and what the author actually verified.

**A concrete decision from this repository.** Filtering with `!=` on a field
that a record does not contain has two defensible behaviours: match, treating
absence as "not equal", or not match, treating absence as "unknown". The first
is convenient and silently wrong — it reports that a record differs from a
value it was never compared against, and the resulting list looks plausible.
The second is less convenient and states the truth. The implementation takes
the second, and `test_missing_field_never_matches_not_even_inequality` pins it
down so a later change cannot quietly reverse it.

## Development

    python -m pytest

## License

MIT
