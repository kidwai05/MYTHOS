# Research methodology

## 1. Source tiers

| Tier | Folder | What belongs here | How it is used |
|---|---|---|---|
| Primary | `primary-sources/` | Ancient texts, inscriptions and religious compositions that tell or record the myth | Evidence for every factual claim in `data/` |
| Supplementary | `supplementary-sources/` | Later ancient or classical accounts, and related traditions (sagas, chronicles, travel writers) | Corroboration, variants, local traditions. Never the only source for a core fact if a primary source exists |
| Scholarly | `scholarly-references/` | Modern reference works, handbooks and studies | Interpretation, dating, translation guidance. Not evidence for what a myth says |

Modern retellings are useful for orientation. Cite the Eddas, Hesiod, the Pyramid Texts and the other historical sources, not the retelling.

## 2. Linking records to sources

1. Every record in `data/` (deities, creatures, heroes, stories, relationships) has a `sources` array with at least one entry.
2. Each entry points to a source by `source_id` from `data/sources.json`.
3. Each entry has a `locator` (book and line, poem and stanza, spell number, section) and a `relation`: `attests`, `mentions`, `variant` or `context`.
4. `verified` stays `false` until someone has read the passage in a named edition and filled in the locator.
5. At least one linked source for a core fact should be primary or supplementary. A scholarly source alone is not enough.
6. The back-link also lives in each source note, under "Records linked to this source".

## 3. Source status lifecycle

`catalogued` (listed, not read) → `edition-chosen` (edition, URL and licence recorded) → `reading` → `extracted` (passages logged in the note) → `verified` (records linked with locators). Set `status` in `sources.json`.

## 4. Workflow for adding a character

1. Find the character in a primary source. Log the passage in that source's note (locator, what it attests).
2. Create the record in the right `data/*.json` file with `verified: false`.
3. Add a supplementary or scholarly source for context.
4. Fill in the locator and a one-line claim, set `verified: true`, then run `python scripts/refresh_notes.py` and `python scripts/validate_data.py --require-verified greek`.

## 5. Variants and disagreements

Sources disagree, and that is data. Do not pick a winner silently. Record each version as its own `sources` entry with `relation: "variant"`, and describe the difference in the "Variants and disagreements" section of the relevant source note.

## 6. Egyptian specifics

Egyptian cosmology was not uniform. Heliopolitan, Hermopolitan, Memphite, Theban and Esna traditions are kept as separate records (`research/egyptian/creation-traditions.md`). Deity records carry a `tradition` field. Plutarch, Herodotus and Diodorus are later classical accounts and are filed as supplementary.

## 7. Norse specifics

The Poetic Edda is a collection, so each poem is its own source. The Prose Edda is catalogued by section (Prologue, Gylfaginning, Skáldskaparmál, Háttatal). Ynglinga saga is the opening section of Heimskringla, so cite the section when you can.

## 8. Issues found in the original source list

- Your Greek list has a second "Theogony" row ("other ancient genealogical traditions"). It is not a distinct work, so it was left out. Add specific works if you meant any.
- Diodorus Siculus appears as "Library" and as "Bibliotheca Historica". These are the same work, so it is one source, tagged Greek and Egyptian.
- "Greek Mythology: A Guide to the Gods, Heroes, and Legends — various scholarly editions" is not a single identifiable book. It is flagged in `sources.json` for you to pick a specific edition.
- Authors, periods and editions were taken only from your list. Nothing was added.

## 9. Citation format

Cite as `source_id` plus locator, for example `gr-theogony` with locator "ll. 116-138" once you have verified it in your chosen edition.

## 10. Editions chosen for Greek (Phase 1)

All are older Loeb translations that are public domain in the US and are hosted online. Locators in `data/` refer to these editions.

| Source id | Edition |
|---|---|
| `gr-theogony`, `gr-works-and-days`, `gr-homeric-hymns` | Evelyn-White, Loeb 57 (1914) |
| `gr-iliad` | Murray, Loeb (1924) |
| `gr-odyssey` | Murray, Loeb (1919) |
| `gr-bibliotheca` | Frazer, Loeb 121-122 (1921) |
| `gr-argonautica` | Seaton, Loeb (1912) |

Only the Theogony links are verified so far. Links to the other five have no locators yet and stay `verified: false`.

## 11. Locators and editorial identifications

Theogony ranges follow the paragraph blocks of the Evelyn-White text as numbered on Theoi, so check the Greek before quoting exact line ends. Where this database identifies two names as one figure (Typhaon and Typhoeus) or follows a translator's note (the Dark-haired One as Poseidon), the link carries a `note`.
