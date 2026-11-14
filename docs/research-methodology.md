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

## 3. Source status lifecycle vs passage verification

MYTHOS maintains a rigorous distinction between the research status of an entire source work and the verification status of an individual passage:

- **Source-level status** (`sources.json` and `source.status`):
  `catalogued` (listed, not read) → `edition-chosen` (edition, URL and licence recorded) → `reading` → `extracted` (passages logged in the note) → `verified` (thoroughly read and linked).
- **Passage-level verification** (`source_passage.verified` and `source_link.verified`):
  Indicates whether that specific passage has been directly consulted and checked in the chosen translation or critical text.
- **Integrity Rule**: An entire ancient text is never marked as `verified` merely because a subset of passages from it have been extracted.

## 3.1 Relationship taxonomy and grounding

Relationships must be grounded in recorded textual evidence or qualified scholarly comparative analysis:
- **Genealogical**: `parent_of`, `child_of`, `ancestor_of`, `descendant_of`, `sibling_of`.
- **Social**: `spouse_of`, `lover_of`, `ally_of`, `enemy_of`, `rival_of`, `mentor_of`.
- **Narrative**: `creates`, `defeats`, `killer_of`, `rescues`, `transforms_into`, `gives_birth_to`, `born_from`.
- **Divine and symbolic**: `associated_with`, `worshipped_by`, `embodies`, `represents`, `shares_cult_with`.
- **Cross-cultural**: `equivalent_to` (formal historical syncretism or direct equation), `syncretized_with` (historical Hellenistic/Roman blending), `parallels` (typological motif similarity), `similar_in_function_to` (structural role similarity without genetic link).

Never treat functional similarity as proof of historical equivalence. All relationships require supporting citation links.

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

Every Greek link is verified (684 of 684), across 93 characters. What has been read, per source:

| Source id | Read so far |
|---|---|
| `gr-theogony`, `gr-works-and-days` | Whole poems. Most of the Greek characters beyond the first 34 come straight from the Theogony's genealogies |
| `gr-homeric-hymns` | Hymns 1 to 3 (Dionysus, Demeter, Apollo) |
| `gr-iliad`, `gr-odyssey` | Book 1 of each |
| `gr-argonautica` | Books 1 and 3 (Book 3 to line 1407) |
| `gr-bibliotheca` | 1.9.13-1.9.28, 2.4.2-2.4.8, 2.5.1-2.5.8 |

Everything else in those works is unread. Norse and Egyptian records are still unverified seeds. Locator formats: `ll. 453-491` for the Theogony and *Works and Days*, `Hymn 3, ll. 1-18`, `Book 1, ll. 44-62` for the epics, and `Library 2.4.2` for Apollodorus.

## 11. Locators and editorial identifications

Theogony ranges follow the paragraph blocks of the Evelyn-White text as numbered on Theoi, so check the Greek before quoting exact line ends. Where this database identifies two names as one figure (Typhaon and Typhoeus) or follows a translator's note (the Dark-haired One as Poseidon), the link carries a `note`.

## 12. Variants recorded so far

Where sources disagree, each version is its own link with `relation: variant` and a `note`:

- Aphrodite: born from the foam around Heaven's severed members (Theogony 176-206) or a daughter of Zeus (Hymn 3, ll. 182-206).
- Typhon: son of Earth and Tartarus (Theogony 820-868) or son of Hera alone (Hymn 3, ll. 340-361).
- The first woman: made by Hephaestus and Athena (Theogony 560-584), with Hermes and Aphrodite also taking part and a jar of ills (Works and Days 42-105).
- Medea's marriage: promised in Argonautica 3.1118-1130, arranged by Arete in the Library (1.9.25).

## 13. Writing summaries

A summary is two to five sentences of plain prose for the top of a profile. Rules:

1. Say only what the character's verified passages say. No outside knowledge, no tidying up of disagreements.
2. List every passage the summary uses in `summary_basis`. The validator rejects a basis entry that is not a verified link of the same character, and the profile shows the list under "Based on".
3. Name the source when a statement comes from one version only ("In the Theogony ...", "In the Hymn to Apollo ..."). Where versions disagree, say so in the summary, as for Aphrodite, Typhon, Hephaestus's wife and Calypso's father.
4. When little has been read, say so ("The passages read so far say little else about her"). Do not pad.
5. Write in your own words. Do not copy phrases from the translation.
6. A character with no verified passages gets no summary. Norse and Egyptian characters have none yet.
7. When a summary changes, or a passage it uses is corrected, re-check its basis. Summaries are part of the data, so they are reviewed like the links.

All 93 Greek characters have summaries.

## 14. Order of work for new Greek entities

Add them from texts already read, so every link can be checked at once. The Theogony alone supplies a family tree from Chaos to the heroes, so it comes first. Add stories later, after the characters in them exist. Next candidates are the rest of the Theogony's catalogues (the Nereids, the rivers, the Hesperides) and the characters in the Iliad, Odyssey and Apollodorus passages not yet read.
