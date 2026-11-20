# MYTHOS
### An Atlas of Comparative Mythology

<p align="center">
  <em>Three civilizations. Countless stories. One interconnected world.</em>
</p>

<p align="center">
  <strong>GREEK · NORSE · EGYPTIAN</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-BC9A59?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.x-BC9A59?style=flat-square&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Database-SQLite-BC9A59?style=flat-square&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Frontend-Vanilla%20JS-BC9A59?style=flat-square&logo=javascript&logoColor=white" />
  <img src="https://img.shields.io/badge/Architecture-Local--First-BC9A59?style=flat-square" />
</p>

---

<p align="center">
  <strong>✦ EXPLORE · DISCOVER · TRACE · VERIFY ✦</strong>
</p>

MYTHOS is a local-first, research-oriented atlas of comparative mythology, bringing together the gods, heroes, monsters, genealogies, narratives, and ancient texts of Greek, Norse, and Egyptian traditions.

More than a mythology encyclopedia, MYTHOS is an interconnected knowledge system. Characters are connected through relationships, stories are grounded in primary textual evidence, and individual claims can be traced back to specific source passages.

Its central principle is simple:

**Every factual claim should have a source. Every source should have a traceable passage. Every verification should be explicit.**

> Greek characters, summaries, relationships, and written stories currently contain verified primary-text citations. Norse and Egyptian records form an expanding seed corpus and may remain unverified until their passages have been individually reviewed.

---

## Ⅰ. THE ARCHIVE

| | |
|:---|:---|
| **Mythologies** | Greek, Norse, Egyptian |
| **Core experience** | Comparative mythology exploration |
| **Knowledge model** | Interconnected relational graph |
| **Research philosophy** | Source-grounded, passage-level verification |
| **Architecture** | Local-first Flask application |
| **Canonical data** | Structured JSON |
| **Database** | Rebuildable SQLite |

### The collection at a glance

<p align="center">
  <table>
    <tr>
      <td align="center"><strong>03</strong><br/>Mythologies</td>
      <td align="center"><strong>104</strong><br/>Characters</td>
      <td align="center"><strong>071</strong><br/>Sources</td>
      <td align="center"><strong>229</strong><br/>Relationships</td>
      <td align="center"><strong>015</strong><br/>Stories</td>
    </tr>
  </table>
</p>

---

## Ⅱ. EXPLORE THE MYTHOLOGIES

### ⚜ The Greek Tradition

Gods, Titans, Olympians, heroes, monsters, and the intricate genealogies and narratives of the ancient Greek world.

### ᛟ The Norse Tradition

The gods, giants, legendary figures, cosmology, and interconnected narratives of the Norse mythological tradition.

### 𓂀 The Egyptian Tradition

The deities, divine relationships, creation traditions, and complex religious narratives of ancient Egypt.

*The three traditions share a common research framework while retaining their own distinct historical, textual, and cultural contexts.*

---

## Ⅲ. FEATURES

### ◈ Character Catalogue
Browse an expanding collection of mythological figures.

- Explore gods, goddesses, heroes, monsters, and other figures.
- Filter by mythology, tradition, role, domain, and gender.
- Search using primary names and alternative aliases.
- Navigate directly from individual characters to their connected records.

### ◈ Detailed Character Profiles
A centralized record of each mythological figure.

- Names, epithets, and aliases.
- Research-grounded character summaries.
- Categorized relationships and genealogies.
- Associated stories and narrative appearances.
- Linked primary sources and individual passages.
- Explicit passage-verification status.

### ◈ Interactive Knowledge Graph
Explore mythology as a network rather than a collection of isolated biographies.

- Trace genealogical relationships.
- Discover divine, familial, and social connections.
- Follow narrative and symbolic associations.
- Explore cross-cultural connections.
- Navigate outward from individual characters.

### ◈ Source-Grounded Stories
Read structured mythological narratives with traceable textual foundations.

- Source-grounded written retellings.
- Paragraph-level passage citations.
- Links between stories, characters, and sources.
- Documentation of variant traditions.
- Explicit separation between textual evidence and narrative interpretation.

### ◈ Primary Source Library
A dedicated catalogue of the texts behind the mythology.

- Primary ancient texts.
- Supplementary historical accounts.
- Scholarly references.
- Source editions and bibliographic information.
- Individual passages linked to the claims they support.

### ◈ Unified Search
A single search system spanning the entire collection.

Search across:
- Character names and aliases.
- Character summaries.
- Mythologies and traditions.
- Source titles and passages.
- Stories and narrative content.
- Textual claims.

### ◈ REST API
A versioned, read-only JSON API for accessing the underlying catalogue.

- Character retrieval and filtering.
- Categorized relationship data.
- Character-centered graph data.
- Multi-entity search and suggestions.
- Story and passage retrieval.
- Source and mythology endpoints.

### ◈ Interface and Themes
- Dark theme.
- Parchment-inspired theme.
- Locally bundled fonts.
- Responsive layouts.
- Accessible interface elements.
- Browser-rendered interactive visualizations.

---

## Ⅳ. RESEARCH & VERIFICATION

MYTHOS distinguishes between the existence of a source, a citation to that source, and the actual verification of the cited passage.

These are not interchangeable.

**The research model**

| Concept | Meaning |
|:---|:---|
| Source | A catalogued textual or scholarly work |
| Passage | A specific, identifiable section of a source |
| Citation | A link between a factual record and its evidence |
| Verification | Confirmation that the cited passage was directly checked |
| Claim | The particular information supported by the passage |

### Verification principles

1. Every character, relationship, and story record must cite at least one source.
2. A verified source link requires a locator, an explicit claim, and a named edition.
3. Character summaries must be supported exclusively by verified source links.
4. Story paragraphs must identify the verified passages on which they are based.
5. Unverified records may exist in the expanding corpus, but must never be presented as verified.
6. Source status and individual passage verification are tracked separately.

**The distinction matters:** a record can reference a legitimate ancient text without its particular passage having been reviewed.

This makes research progress visible instead of disguising incomplete verification as established evidence.

---

## Ⅴ. TECHNOLOGY

| Layer | Technology |
|:---|:---|
| Backend | Python, Flask 3.x |
| Database | SQLite |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Data format | JSON |
| Data architecture | Normalized relational tables |
| Visualization | Browser-rendered knowledge graph |
| Testing | Python `unittest` |

### Architecture

```text
                 MYTHOS
                   │
          ┌────────┴────────┐
          │                 │
      FRONTEND           BACKEND
          │                 │
    HTML / CSS / JS       Flask
          │                 │
          │          Application Layer
          │                 │
          │        ┌────────┴────────┐
          │        │                 │
          │    Repository         Search
          │        │                 │
          │        └────────┬────────┘
          │                 │
          │              SQLite
          │
          └──── REST API / Web Routes

          CANONICAL DATA LAYER
                   │
              JSON Files
                   │
             Seed Loader
                   │
                 SQLite
```

**JSON is the source of truth.** SQLite is a derived, rebuildable representation of the canonical data.

---

## Ⅵ. GETTING STARTED

### Requirements

- Python 3.10 or later
- Flask 3.x
- A modern web browser

### Windows (PowerShell)

Clone the repository and navigate to its root directory.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

python backend\run.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

python backend/run.py
```

### Open MYTHOS

Once the development server starts, visit:

**http://127.0.0.1:5000**

The application automatically creates and seeds `mythos.db` if the configured database does not exist.

---

## Ⅶ. CONFIGURATION

MYTHOS supports environment-based configuration.

| Variable | Default | Description |
|:---|:---|:---|
| `PORT` | `5000` | Development server port |
| `DEBUG` | Unset | Set to `1` to enable Flask debug mode |
| `MYTHOS_DB` | `mythos.db` | SQLite database path |

### Example: Custom configuration

```powershell
$env:PORT="8080"
$env:DEBUG="1"
$env:MYTHOS_DB="C:\Data\mythos.db"

python backend\run.py
```

A missing custom database path causes the application to create and seed a new database.

Existing databases are not automatically overwritten.

---

## Ⅷ. DATABASE MANAGEMENT

### Rebuilding the database

The JSON files under `data/` are canonical.

Rebuild SQLite using:

```powershell
python backend\seed\loader.py mythos.db
```

For a custom database location:

```powershell
python backend\seed\loader.py C:\Data\mythos.db
```

If using a custom location, ensure that `MYTHOS_DB` points to the same path when launching the application.

> **Important:** Rebuilding recreates the requested database. Back up existing databases before running the loader.

---

## Ⅸ. APPLICATION ROUTES

| Route | Description |
|:---|:---|
| `/` | Mythologies overview |
| `/characters` | Character catalogue, search, and filtering |
| `/characters/{slug}` | Individual character profile |
| `/mythologies/{slug}` | Mythology detail |
| `/stories` | Story catalogue |
| `/stories/{slug}` | Story and passage citations |
| `/sources` | Primary source library |
| `/sources/{slug}` | Source details and linked passages |
| `/graph?root={character_slug}` | Interactive relationship graph |

---

## Ⅹ. REST API

The read-only REST API is available under:

`/api/v1`

### Character endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/v1/characters` | Search and filter characters |
| GET | `/api/v1/characters/zeus` | Retrieve a character profile |
| GET | `/api/v1/characters/zeus/relationships` | Retrieve categorized relationships |
| GET | `/api/v1/characters/zeus/graph?depth=2` | Retrieve character-centered graph data |

### Search endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/v1/search?q=sea&limit=15` | Multi-entity search |
| GET | `/api/v1/search/suggest?q=cyth` | Search suggestions |

### Stories and sources

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/v1/stories/birth-of-zeus` | Story, participants, and cited paragraphs |
| GET | `/api/v1/sources/gr-theogony` | Source metadata and passages |
| GET | `/api/v1/passages/{id}` | Individual source passage |
| GET | `/api/v1/mythologies/greek` | Mythology details |
| GET | `/api/v1/traditions` | Tradition catalogue |

### Example request

```powershell
curl "http://127.0.0.1:5000/api/v1/characters?q=zeus&per_page=10"
```

### Response conventions

Paginated endpoints normally return:

- `items`
- `page`
- `per_page`
- `total`

API errors follow a consistent structure:

```json
{
  "error": {
    "code": "not_found",
    "message": "Character 'nobody' does not exist"
  }
}
```

For complete parameter definitions and response structures, consult:

[`docs/api.md`](docs/api.md)

---

## Ⅺ. TESTING & VALIDATION

MYTHOS includes automated tests and research-data validation tools.

### Run the test suite

From the repository root:

```powershell
python -m unittest discover -s backend\tests -t .
```

The tests create an isolated temporary SQLite database and load the canonical JSON corpus.

They cover application behavior, API endpoints, search functionality, profiles, and page rendering.

### Validate the research corpus

```powershell
python scripts\validate_data.py
```

For stricter Greek corpus verification:

```powershell
python scripts\validate_data.py --require-verified greek --require-summary greek --require-story-text greek
```

### Refresh research notes

After editing source links:

```powershell
python scripts\refresh_notes.py
```

This refreshes generated sections in the research notes.

---

## Ⅻ. PROJECT STRUCTURE

```text
MYTHOS/
│
├── backend/
│   ├── app/
│   │   ├── Flask application
│   │   ├── Routes
│   │   ├── Repository
│   │   ├── Search
│   │   └── SQLite setup
│   │
│   ├── seed/
│   │   └── JSON-to-SQLite loader
│   │
│   ├── tests/
│   │   └── API, search, profile, and page tests
│   │
│   └── run.py
│
├── data/
│   ├── Canonical character records
│   ├── Story records
│   ├── Relationship records
│   └── Source catalogue
│
├── docs/
│   ├── API documentation
│   ├── Database schema
│   ├── Research methodology
│   ├── Source bibliography
│   └── Wireframes
│
├── frontend/
│   ├── static/
│   │   ├── CSS
│   │   ├── JavaScript
│   │   ├── SVG
│   │   └── Bundled fonts
│   │
│   └── templates/
│       └── Server-rendered HTML pages
│
├── research/
│   ├── greek/
│   ├── norse/
│   └── egyptian/
│
├── scripts/
│   ├── validate_data.py
│   └── refresh_notes.py
│
└── README.md
```

---

## ⅩⅢ. RESEARCH LIBRARY

The research directory contains tradition-specific source notes and supporting documentation.

| Collection | Contents |
|:---|:---|
| [Greek Research](research/greek/README.md) | Greek primary-text research and documentation |
| [Norse Research](research/norse/README.md) | Norse source research and corpus development |
| [Egyptian Research](research/egyptian/README.md) | Egyptian source research and creation traditions |
| [Source Bibliography](docs/source-bibliography.md) | Catalogue of referenced sources |
| [Egyptian Creation Traditions](research/egyptian/creation-traditions.md) | Research into Egyptian creation narratives |

### Further documentation

- [Database Schema](docs/database-schema.md)
- [Research Methodology](docs/research-methodology.md)
- [API Documentation](docs/api.md)

---

## ⅩⅣ. CONTRIBUTING & DATA INTEGRITY

Contributions should preserve the distinction between documented information and verified evidence.

### Research workflow

1. Edit the canonical JSON files under `data/`.
2. Add or update source notes under `research/`.
3. Run `python scripts\refresh_notes.py`.
4. Validate the corpus:

   ```powershell
   python scripts\validate_data.py --require-verified greek --require-summary greek --require-story-text greek
   ```

5. Run the automated unit tests.
6. Review the changes before rebuilding the database.

### Non-negotiable research principles

- Never mark a passage as verified unless the named passage has been directly checked in the selected edition.
- Never treat a source citation as automatic proof of verification.
- Keep source status and passage verification separate.
- Preserve distinctions between competing versions of a myth.
- Ensure factual summaries are supported by verified evidence.
- Keep the canonical JSON dataset consistent with its supporting research notes.

**Research integrity takes precedence over corpus size.**

---

## ⅩⅤ. LICENSING

No license file is currently present in the repository.

The licensing of the application code and that of bundled or referenced source editions may differ.

An explicit license should be added before redistribution or reuse. Copyright and licensing conditions for individual source editions must be considered separately.

---

<p align="center">

  **✦ THE END OF ONE STORY IS THE BEGINNING OF ANOTHER ✦**

  <em>MYTHOS — An Atlas of Comparative Mythology</em>

  <sub>Greek · Norse · Egyptian</sub>

</p>
