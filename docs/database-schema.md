# Database schema (data files)

The JSON files in `data/` are the source of truth. A loader (`seed/loader.py` in the app) imports them into the relational schema in the SRS (Section 6). Every file has the shape `{ "meta": {...}, "records": [...] }`.

## Shared types

**SourceLink** (used in every `sources` array)

| Field | Type | Notes |
|---|---|---|
| `source_id` | string | Must exist in `sources.json` |
| `locator` | string or null | For example `ll. 453-491`. For the Theogony, ranges follow the paragraph blocks of the Evelyn-White translation (see `sources.json` meta) |
| `relation` | enum | `attests`, `mentions`, `variant`, `context` |
| `claim` | string or null | One line, in your own words, saying what the passage supports. Required when `verified` is true |
| `note` | string, optional | Caveats, variants, editorial identifications |
| `verified` | boolean | True only after the passage is read in a named edition |

**mythology**: `greek`, `norse`, `egyptian`.

## sources.json

| Field | Type | Notes |
|---|---|---|
| `id` | string, unique | `<gr/no/eg>-<slug>`, for example `gr-theogony` |
| `title`, `author` | string | `author` may be `Anonymous` or `Various` |
| `mythology` | string[] | First entry is the home folder. Extra entries for cross-listed sources |
| `tier` | enum | `primary`, `supplementary`, `scholarly` |
| `kind` | string | poem, epic, saga, text-collection, inscription, monograph, and so on |
| `collection` | string or null | For example `poetic-edda`, `prose-edda`, `heimskringla` |
| `period_or_origin` | string or null | Only where known |
| `subjects` | string[] | |
| `edition_used`, `url` | string or null | Filled in when read |
| `status` | enum | `catalogued`, `edition-chosen`, `reading`, `extracted`, `verified` |
| `license` | string or null | Licence of the edition used |
| `edition_note` | string or null | Alternative host or format |
| `research_notes` | string[] | Paths to the markdown notes under `research/` |
| `notes` | string or null | Flags and cautions |

## deities.json, creatures.json, heroes.json

| Field | Type | Notes |
|---|---|---|
| `id` | string, unique across all three files | Slug, for example `zeus` |
| `name` | string | |
| `mythology` | enum | |
| `roles` | string[] | god, goddess, titan, monster, hero, legendary-figure |
| `domains` | string[] | Deities |
| `tradition` | string, optional | Egyptian creation tradition id |
| `summary` | string, optional | 40 to 700 characters, plain prose written from the passages in `summary_basis` |
| `summary_basis` | {source_id, locator}[] | Required with a summary. Each entry must match a verified link on the same record |
| `sources` | SourceLink[] | At least one |

These three files all load into the `character` table; `roles` map to `character_role`.

## stories.json

`id`, `title`, `mythology`, `participants` (character ids), `sources`. Loads into `myth` and `character_myth`.

## relationships.json

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `source`, `target` | character ids | Different characters |
| `type` | string | `parent_of`, `spouse_of`, `sibling_of`, `rival_of`, `ally_of`, and so on |
| `sources` | SourceLink[] | At least one |

Unique on (`source`, `target`, `type`).

## Mapping to SQL

| JSON | Table |
|---|---|
| `sources.json` | `source` |
| `summary_basis` | `character_summary_basis` (links a character to the `source_link` rows its summary rests on) |
| every `sources` array (characters, relationships, stories) | `source_link` (one table, exactly one of `character_id`, `relationship_id`, `myth_id` set) |
| `relationships.json` | `relationship`, `relationship_type` |
| `stories.json` | `myth`, `character_myth` |

The DDL is in `backend/schema.sql` and `backend/seed/loader.py` loads the JSON into SQLite.

## Validation rules (`scripts/validate_data.py`)

1. All JSON parses and ids are unique.
2. Every `source_id` exists in `sources.json`.
3. Every record has at least one source link.
4. Relationship and story ids refer to existing characters.
5. Every `research_notes` path exists.
6. Every source has the right folder for its tier.
7. A verified link has a locator and a claim, and its source has `edition_used`.
8. A summary needs a `summary_basis`, every basis entry is a verified link of that record, and a long summary rests on at least two passages. With `--require-summary greek`, every Greek character must have one.
9. With `--require-verified greek`, every Greek character, story and relationship has at least one verified link, and the script reports which Greek characters are not yet connected in the graph.
