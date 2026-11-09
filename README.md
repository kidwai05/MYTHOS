# Mythos

An interactive encyclopedia of world mythology. Every fact in `data/` links back to a source catalogued in `research/`.

```
mythos/
├── research/
│   ├── greek/ | norse/ | egyptian/
│   │   ├── primary-sources/
│   │   ├── supplementary-sources/
│   │   └── scholarly-references/
│   └── egyptian/creation-traditions.md
├── data/        deities, creatures, heroes, stories, relationships, sources (JSON)
├── docs/        research-methodology, database-schema, source-bibliography
├── backend/     schema.sql and seed/loader.py
└── scripts/     validate_data.py, refresh_notes.py
```

Run `python scripts/validate_data.py` after every edit. See `docs/research-methodology.md` to add a character.

Workflow: edit `data/*.json`, run `python scripts/refresh_notes.py`, then `python scripts/validate_data.py --require-verified greek`. Load into SQLite with `python backend/seed/loader.py`. Wireframes: `docs/wireframes.html`.
