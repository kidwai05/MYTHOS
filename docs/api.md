# REST API (v1, read-only)

Base path `/api/v1`. All responses are JSON. Lists return `{items, page, per_page, total}`. Errors return `{"error": {"code": "...", "message": "..."}}` with HTTP status 400, 404, or 500.

## Characters

`GET /characters`

| Parameter | Meaning |
|---|---|
| `q` | Free text. Matches names, aliases, summaries, traditions, and claims. Ignores accents and tolerates minor typos. Every word must match |
| `mythology`, `tradition`, `role`, `domain`, `gender` | Filters. Comma-separate or repeat to allow several values (OR). Different filters combine with AND. Unknown values return 400 |
| `sort` | `name` (default), `-name`, `mythology`, `relevance` (default when `q` is set) |
| `page`, `per_page` | Default 1 and 20. `per_page` is at most 100 |
| `fields` | Comma list from `slug,name,mythology,tradition,gender,roles,domains,aliases,sources,match` |
| `include=facets` | Adds count facets for each filter dimension |

`GET /characters/{slug}`
Returns the full profile: `slug`, `name`, `mythology`, `tradition` (slug and name), `gender`, `summary`, `summary_basis`, `aliases`, `roles`, `domains`, `sources` (passages with source, locator, claim, relation, note, verified), `relationships` (categorized groups with supporting source passages), `stories` (with participant narrative roles), `counts`.

`GET /characters/{slug}/relationships`
Returns character relationship groups with directionality, inverse labels, and citation links.

`GET /characters/{slug}/graph`
Returns structured node and edge data centered on the character for graph visualization.
- **Query parameters**:
  - `depth`: integer (1 to 3, default 1).
  - `category`: comma-separated relationship categories (`genealogical`, `social`, `narrative`, `divine_symbolic`, `cross_cultural`, etc.).
  - `tradition`: filter neighbors by tradition slug.
  - `include_stories`: boolean (default true).
  - `include_sources`: boolean (default false).
  - `include_passages`: boolean (default false).
- **Response**: `{root, nodes, edges, counts}` where nodes contain entity types (`deity`, `hero`, `creature`, `story`, `source`, `passage`), degrees, and summaries, and edges contain categories, typed labels, directionality, and supporting source evidence.

`GET /graph`
General graph query endpoint taking `root` parameter (delegates to `/characters/{root}/graph`).

## Sources & Passages

`GET /sources`
Lists every catalogued source with author, tier, kind, collection, research status, passage count, and verified link count.

`GET /sources/{slug}`
Returns full source metadata, publication period, edition used, license, research status lifecycle, all recorded passages, characters mentioned, stories documented, and relationships supported.

`GET /sources/{slug}/passages`
Returns all unique `source_passage` records for this text, including locators, translation edition, notes, verification status, and supported entities.

`GET /passages/{id}`
Returns a specific passage locator, source edition metadata, excerpt, notes, and the full list of characters, relationships, and stories grounded in this passage.

## Traditions

`GET /traditions`
Lists all theological and regional traditions across mythologies with character and story counts.

`GET /traditions/{slug}`
Returns tradition details, mythology, description, associated deities/characters, and associated stories.

## Stories

`GET /stories`
Lists all narratives and myths with mythology, tradition, summary, and participant count.

`GET /stories/{slug}`
Returns story details: title, summary, mythology, tradition, supporting textual citations, and participants with explicit narrative roles (`protagonist`, `antagonist`, `victim`, `creator`, `participant`).

## Multi-Entity Search & Autocomplete

`GET /search?q={query}`
Unified multi-category search returning `{characters: [...], stories: [...], sources: [...], total: ...}`.

`GET /search/suggest?q={query}`
Fast autocomplete suggestions matching names and aliases.

## Vocabularies

| Path | Returns |
|---|---|
| `/mythologies`, `/mythologies/{slug}` | Counts, role breakdown, traditions, and sources cited |
| `/roles`, `/domains`, `/relationship-types` | Vocabularies with active usage counts |
