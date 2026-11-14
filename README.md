<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=230&color=0:2a1a14,45:a8321f,80:d9a441,100:8a9a5b&text=MYTHOS&fontColor=f3e6c8&fontSize=70&fontAlign=50&fontAlignY=40&desc=every%20myth%2C%20every%20source%2C%20every%20connection&descColor=f3e6c8&descSize=19&descAlignY=64" width="100%" alt="MYTHOS" />

`α` &nbsp; `β` &nbsp; `γ` &nbsp; `δ` &nbsp; `ε` &nbsp; `ζ` &nbsp; `η` &nbsp; `θ`

*a comparative mythology atlas, grounded in primary sources*

</div>

<br/>

## α &nbsp;About

**MYTHOS** is an interactive atlas of world mythology. It starts with Greek myth and grows outward, mapping how the characters, stories and ideas of different traditions **connect, echo and differ**, with every claim traced back to its **primary source**.

Each mythology is researched from its original texts first, then linked to the others, so you can follow a single figure across stories, sources and cultures.

<br/>

## β &nbsp;Explore

- **Search and browse** characters by name, alias, source text, mythology, role and domain. Sort results, use filter facets and follow name suggestions.
- **Open character profiles** with summaries, roles, domains, stories and sourced relationships.
- **Inspect citations** including the source edition, passage locator, claim and whether the passage has been checked.
- **Browse mythology pages** for an overview of each tradition and its catalogued material.
- **Use the read-only JSON API** for characters, relationships, stories, sources, vocabularies and mythologies.

## γ &nbsp;Research status

Greek mythology is the most developed corpus: its character summaries and links are grounded in the cited passages, and Greek records are marked verified. Norse and Egyptian records are catalogued as research seeds; their links have not yet been verified. Cross-mythology equivalents are not yet implemented.

MYTHOS keeps primary sources distinct from supplementary ancient accounts and modern scholarly references. When sources disagree, their variants are recorded rather than merged into a single account. See the [research methodology](docs/research-methodology.md) for verification rules and current coverage.

<br/>

## δ &nbsp;Repository

```text
MYTHOS/
├── backend/     Flask app, JSON API, SQLite schema and tests
├── data/        characters, stories, sources and relationships (JSON)
├── docs/        API, schema, methodology and source bibliography
├── frontend/    Flask templates, styles, fonts and browser scripts
├── research/    source notes organized by mythology and tier
└── scripts/     research-note and data-validation helpers
```

<br/>

## δ &nbsp;Sources

The data is grounded in primary texts, with supplementary ancient accounts and scholarly works clearly identified. The full list of sources, editions and translations is in [`docs/source-bibliography.md`](docs/source-bibliography.md).

<br/>

## ε &nbsp;Run locally

```bash
git clone https://github.com/kidwai05/MYTHOS.git
cd MYTHOS
python -m venv .venv
```

Activate the environment, then install the backend dependency:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate with `source .venv/bin/activate` instead. Then run:

```bash
pip install -r backend/requirements.txt
python backend/run.py
```

Open <http://127.0.0.1:5000>. On first startup, MYTHOS builds `mythos.db` in the repository root from the JSON files in `data/`. Set `MYTHOS_DB` to use a different database path. The development server uses port `5000` by default; set `PORT` to change it.

## ζ &nbsp;Check the project

Run the API and UI tests from the repository root:

```bash
python -m unittest discover -s backend/tests -t .
```

Validate the research data and its source-note links:

```bash
python scripts/validate_data.py
python scripts/validate_data.py --require-verified greek --require-summary greek
```

## η &nbsp;Documentation

- [API reference](docs/api.md)
- [Database and JSON schema](docs/database-schema.md)
- [Research methodology](docs/research-methodology.md)
- [Source bibliography](docs/source-bibliography.md)

<br/>

<div align="center">

<sub><i>made by <a href="https://github.com/kidwai05">Fatema Kidwai</a></i></sub>

<img src="https://capsule-render.vercel.app/api?type=waving&height=100&color=0:8a9a5b,40:d9a441,75:a8321f,100:2a1a14&section=footer" width="100%" alt="footer" />

</div>