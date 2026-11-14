# REST API (v1, read-only)

Base path `/api/v1`. All responses are JSON. Lists return `{items, page, per_page, total}`. Errors return `{"error": {"code": "...", "message": "..."}}` with status 400, 404 or 500.

## Characters

`GET /characters`

| Parameter | Meaning |
|---|---|
| `q` | Free text. Matches names, aliases, summaries and the text of the source claims, ignores accents, tolerates one or two typos. Every word must match |
| `mythology`, `role`, `domain`, `gender` | Filters. Comma-separate or repeat to allow several values (OR). Different filters combine with AND. Unknown values give 400 |
| `sort` | `name` (default), `-name`, `mythology`, `relevance` (default when `q` is set) |
| `page`, `per_page` | Default 1 and 20. `per_page` is at most 100 |
| `fields` | Comma list from `slug,name,mythology,gender,roles,domains,aliases,sources,match` |
| `include=facets` | Adds counts for each filter value. Each dimension is counted with the other filters applied, so options never disappear when you pick one |

Each item has `summary` (or null when the character's sources are not checked yet) and `sources: {total, verified}`. When `q` is set, `match` says what matched: `{on: name|alias|text, text, score}`.

`GET /characters/{slug}` returns the full profile: `summary`, `summary_basis` (the verified passages the summary rests on), `aliases`, `roles`, `domains`, `sources` (every passage with `source`, `locator`, `claim`, `relation`, `note`, `verified`), `relationships` (grouped as Parents, Children, Spouses, Siblings, Lovers, Allies, Rivals, Slayer of, Slain by, each item with its own source passages), `stories`, `equivalents` (empty until Phase 5) and `counts`.

`GET /characters/{slug}/relationships` returns just the relationship groups.

`GET /search/suggest?q=` gives up to 8 name or alias matches for autocomplete (needs at least 2 characters).

## Other endpoints

| Path | Returns |
|---|---|
| `/mythologies`, `/mythologies/{slug}` | Counts, role breakdown, how many sources of each tier are cited |
| `/roles`, `/domains`, `/relationship-types` | Vocabularies with usage counts |
| `/sources` | Every catalogued source with edition, licence and how many links are verified |
| `/stories`, `/stories/{slug}` | Stories with participants and source passages |

## Meaning of the source fields

- `locator`: where in the text, for example `ll. 453-491`, `Book 3, ll. 36-54` or `Library 2.4.2`.
- `verified`: true only if the passage was read in the named `edition_used`.
- `relation`: `attests`, `mentions`, `context` or `variant` (a version that differs from other sources).

## Notes on the implementation

Filtering, facets and search run in memory over a catalogue loaded from the database at start-up (`backend/app/catalog.py`, `search.py`). That is comfortable for a few thousand characters. For more, swap `search.py` for SQLite FTS5 or PostgreSQL trigram search behind the same functions. Profile and vocabulary endpoints use SQL directly (`repository.py`).
