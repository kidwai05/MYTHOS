# Database schema (data files and SQLite)

The JSON files in `data/` are the canonical source of truth. The loader (`backend/seed/loader.py`) imports them into the relational schema (`backend/schema.sql`). Every JSON file has the shape `{ "meta": {...}, "records": [...] }`.

## Shared types

**SourceLink** (used in every `sources` array)

| Field | Type | Notes |
|---|---|---|
| `source_id` | string | Must exist in `sources.json` |
| `locator` | string or null | E.g. `ll. 453-491`. For the Theogony, ranges follow the Evelyn-White paragraph blocks |
| `relation` | enum | `attests`, `mentions`, `variant`, `context` |
| `claim` | string or null | One line saying what the passage supports. Required when `verified` is true |
| `note` | string, optional | Caveats, variants, editorial identifications |
| `verified` | boolean | True only after the passage is read in a named edition |

**mythology**: `greek`, `norse`, `egyptian`.

## traditions

Mythological traditions represent internal theological or regional traditions (such as Egyptian creation traditions or Greek philosophical/mystery schools).

| Field | Type | Notes |
|---|---|---|
| `slug` | string, unique | Slug, e.g. `heliopolitan`, `memphite`, `hesiodic` |
| `name` | string | Human-readable title, e.g. `Heliopolitan`, `Memphite` |
| `mythology_id` | integer FK | References `mythology(id)` |
| `description` | string | Summary of theological and cosmological focus |

Documented Egyptian traditions (`research/egyptian/creation-traditions.md`): `heliopolitan`, `hermopolitan`, `memphite`, `theban`, `esna`.

## sources.json and source_passage

| Field | Type | Notes |
|---|---|---|
| `id` | string, unique | `<gr/no/eg>-<slug>`, for example `gr-theogony` |
| `title`, `author` | string | `author` may be `Anonymous` or `Various` |
| `mythology` | string[] | First entry is the home folder. Extra entries for cross-listed sources |
| `tier` | enum | `primary`, `supplementary`, `scholarly` |
| `kind` | string | poem, epic, saga, text-collection, inscription, monograph, etc. |
| `collection` | string or null | E.g. `poetic-edda`, `prose-edda`, `heimskringla` |
| `period_or_origin` | string or null | Historical epoch or provenance |
| `subjects` | string[] | Subjects |
| `edition_used`, `url` | string or null | Filled in when read |
| `status` | enum | Entire-source lifecycle: `catalogued`, `edition-chosen`, `reading`, `extracted`, `verified` |
| `license` | string or null | Licence of the edition used |
| `edition_note` | string or null | Alternative host or format |
| `research_notes` | string[] | Paths to markdown notes under `research/` |
| `notes` | string or null | Flags and cautions |

**Source Passages (`source_passage` table)**:
Normalized representation of individual textual citations (`source_id`, `locator`, `original_locator`, `translation_edition`, `excerpt`, `notes`, `verified`). Allows independent exploration and cross-entity citation sharing.

## deities.json, creatures.json, heroes.json

| Field | Type | Notes |
|---|---|---|
| `id` | string, unique across all three files | Slug, for example `zeus` |
| `name` | string | Character name |
| `mythology` | enum | `greek`, `norse`, `egyptian` |
| `roles` | string[] | god, goddess, titan, monster, hero, legendary-figure |
| `domains` | string[] | Deities |
| `tradition` | string, optional | Theological tradition slug (e.g. `heliopolitan`) |
| `summary` | string, optional | 40 to 700 characters, plain prose written from the passages in `summary_basis` |
| `summary_basis` | {source_id, locator}[] | Required with a summary. Each entry must match a verified link on the same record |
| `sources` | SourceLink[] | At least one |

These three files all load into the `character` table; `tradition` resolves to `character.tradition_id`.

## stories.json

`id`, `title`, `mythology`, `tradition` (optional), `summary`, `locations` (optional), `participants` (character ids or `{character_id, role, notes}`), `sources`, and `body` for a written myth.

| Field | Type | Notes |
|---|---|---|
| `summary` | string | 60 to 420 characters. Required once there is a `body` |
| `locations` | string[] | Places named in the story. Each must appear in the text |
| `participants[].role` | string | `protagonist`, `antagonist`, `helper`, `parent`, `offspring`, `victim`, `adviser`, `instigator`, `abductor`, `companion`, `witness`, `setting` or `mentioned` |
| `participants[].notes` | string | One sentence saying what the figure does in this story, drawn from the retelling |
| `body` | Paragraph[] | The written retelling, in order |

**Paragraph**: `{ "text": "...", "kind": "narrative" | "variant" | "note", "basis": [{ "source_id", "locator" }] }`. `kind` defaults to `narrative`. A `variant` is another telling of the same event that differs from the main one. A `note` is an aside, such as a one-line version in another poem. `basis` lists the passages the paragraph rests on, and each must be a verified link in the story's own `sources`.

A story with no `body` is *unwritten*. The API reports `status: "unwritten"` and the page says so. Stories load into `myth`, `myth_paragraph`, `myth_paragraph_basis` and `character_myth` (with the participant `role` and `notes`).

## relationships.json

| Field | Type | Notes |
|---|---|---|
| `id` | string | Slug, e.g. `zeus-parent-of-athena` |
| `source`, `target` | character ids | Distinct character IDs |
| `type` | string | Relationship type slug |
| `tradition` | string, optional | Tradition qualification where applicable |
| `description` | string, optional | Detailed relationship context |
| `notes` | string, optional | Scholarly qualifications or variants |
| `sources` | SourceLink[] | At least one supporting source link |

**Relationship Categories**:
- **Genealogical**: `parent_of`, `child_of`, `ancestor_of`, `descendant_of`, `sibling_of`.
- **Social**: `spouse_of`, `lover_of`, `ally_of`, `enemy_of`, `rival_of`, `mentor_of`.
- **Narrative**: `creates`, `defeats`, `killer_of`, `rescues`, `transforms_into`, `gives_birth_to`, `born_from`.
- **Divine and symbolic**: `associated_with`, `worshipped_by`, `embodies`, `represents`, `shares_cult_with`.
- **Cross-cultural**: `equivalent_to`, `syncretized_with`, `parallels`, `similar_in_function_to`.

## Mapping to SQL

| JSON Entity / Concept | SQL Table | Notes |
|---|---|---|
| `sources.json` | `source` | Stores source bibliographic metadata and research status |
| `sources` locator entries | `source_passage` | Normalized unique passages (`source_id`, `locator`, `verified`) |
| every `sources` array | `source_link` | Links an entity (`character_id`, `relationship_id`, or `myth_id`) to a source and passage |
| `summary_basis` | `character_summary_basis` | Enforces that summaries rest exclusively on verified citations |
| `tradition` in JSON | `tradition` | Independent theological / regional tradition entity |
| `relationships.json` | `relationship`, `relationship_type` | Directed / reciprocal relationships with evidence |
| `stories.json` | `myth`, `myth_paragraph`, `myth_paragraph_basis`, `character_myth` | Story summaries, written retellings (each paragraph tied to verified passages) and participant roles |

## Validation rules (`scripts/validate_data.py`)

1. All JSON parses cleanly and entity IDs are unique.
2. Every `source_id` exists in `sources.json`.
3. Every record has at least one source link.
4. Relationship and story participant IDs refer to existing characters.
5. Every `research_notes` path exists in the repository.
6. Every source is located in the appropriate folder for its tier (`primary-sources/`, `supplementary-sources/`, `scholarly-references/`).
7. A verified link has an edition locator and claim, and its source has `edition_used`.
8. Character traditions match valid recognized traditions for that mythology.
9. Summaries require `summary_basis` pointing to verified links of that record.
10. With `--require-verified greek`, every Greek character, story, and relationship has at least one verified link.
11. A story `body` needs a summary, at least 180 words, a narrative first paragraph, and a `basis` on every paragraph. Every basis entry must be a verified link of that story, and every verified story link must be used by some paragraph.
12. Every story participant is named in the text, and every entry in `locations` appears in the text.
13. With `--require-story-text greek`, every Greek story must have a written `body`.
