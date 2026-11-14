-- Mythos relational schema (SQLite and PostgreSQL compatible core).
-- Mirrors SRS Section 6. In production use Alembic migrations generated from the SQLAlchemy models.
CREATE TABLE mythology (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  region TEXT, era TEXT, description TEXT, accent_color TEXT);

CREATE TABLE tradition (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  mythology_id INTEGER NOT NULL REFERENCES mythology(id) ON DELETE CASCADE,
  description TEXT);

CREATE TABLE character (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  mythology_id INTEGER NOT NULL REFERENCES mythology(id),
  tradition_id INTEGER REFERENCES tradition(id) ON DELETE SET NULL,
  gender TEXT, summary TEXT, description TEXT, image_url TEXT, image_credit TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE character_alias (
  id INTEGER PRIMARY KEY, character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  alias TEXT NOT NULL, language TEXT);

CREATE TABLE role (id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL);

CREATE TABLE character_role (
  character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  role_id INTEGER NOT NULL REFERENCES role(id), PRIMARY KEY (character_id, role_id));

CREATE TABLE domain (id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL);

CREATE TABLE character_domain (
  character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  domain_id INTEGER NOT NULL REFERENCES domain(id), PRIMARY KEY (character_id, domain_id));

CREATE TABLE relationship_type (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, label TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN (
    'genealogical', 'family',
    'social', 'alliance', 'rivalry', 'romance', 'mentorship',
    'narrative',
    'divine_symbolic',
    'cross_cultural',
    'other'
  )),
  is_directed INTEGER NOT NULL DEFAULT 1, inverse_label TEXT);

CREATE TABLE relationship (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE,
  source_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  target_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  type_id INTEGER NOT NULL REFERENCES relationship_type(id),
  tradition_id INTEGER REFERENCES tradition(id) ON DELETE SET NULL,
  description TEXT, notes TEXT, myth_reference TEXT,
  CHECK (source_id <> target_id), UNIQUE (source_id, target_id, type_id));

CREATE TABLE equivalence (
  id INTEGER PRIMARY KEY,
  character_a_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  character_b_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('identical','syncretic','similar_role')),
  confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1), note TEXT,
  CHECK (character_a_id < character_b_id), UNIQUE (character_a_id, character_b_id));

CREATE TABLE myth (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, summary TEXT,
  mythology_id INTEGER NOT NULL REFERENCES mythology(id),
  tradition_id INTEGER REFERENCES tradition(id) ON DELETE SET NULL,
  locations TEXT, episodes TEXT, notes TEXT);

CREATE TABLE character_myth (
  character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  myth_id INTEGER NOT NULL REFERENCES myth(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'participant',
  notes TEXT,
  PRIMARY KEY (character_id, myth_id));

CREATE TABLE source (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, author TEXT,
  tier TEXT NOT NULL CHECK (tier IN ('primary','supplementary','scholarly')),
  kind TEXT, collection TEXT, period_or_origin TEXT, edition_used TEXT, url TEXT, license TEXT, status TEXT NOT NULL);

CREATE TABLE source_passage (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
  locator TEXT NOT NULL,
  original_locator TEXT,
  translation_edition TEXT,
  excerpt TEXT,
  notes TEXT,
  verified INTEGER NOT NULL DEFAULT 0,
  UNIQUE (source_id, locator));

-- One table holds every link from a record to a source. Exactly one target column is set.
CREATE TABLE source_link (
  id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES source(id),
  character_id INTEGER REFERENCES character(id) ON DELETE CASCADE,
  relationship_id INTEGER REFERENCES relationship(id) ON DELETE CASCADE,
  myth_id INTEGER REFERENCES myth(id) ON DELETE CASCADE,
  passage_id INTEGER REFERENCES source_passage(id) ON DELETE SET NULL,
  locator TEXT, relation TEXT NOT NULL CHECK (relation IN ('attests','mentions','variant','context')),
  claim TEXT, note TEXT, verified INTEGER NOT NULL DEFAULT 0,
  CHECK ((character_id IS NOT NULL) + (relationship_id IS NOT NULL) + (myth_id IS NOT NULL) = 1),
  CHECK (verified = 0 OR (locator IS NOT NULL AND claim IS NOT NULL)));

-- The passages a character's summary rests on. Every row must point at a verified link of the same character.
CREATE TABLE character_summary_basis (
  character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  source_link_id INTEGER NOT NULL REFERENCES source_link(id) ON DELETE CASCADE,
  PRIMARY KEY (character_id, source_link_id));

CREATE TABLE app_user (
  id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  display_name TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE bookmark (
  user_id INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, character_id));

CREATE TABLE collection (
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  name TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE collection_item (
  collection_id INTEGER NOT NULL REFERENCES collection(id) ON DELETE CASCADE,
  character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  position INTEGER, added_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (collection_id, character_id));

CREATE INDEX ix_character_mythology ON character(mythology_id);
CREATE INDEX ix_character_tradition ON character(tradition_id);
CREATE INDEX ix_relationship_source ON relationship(source_id);
CREATE INDEX ix_relationship_target ON relationship(target_id);
CREATE INDEX ix_source_link_source ON source_link(source_id);
CREATE INDEX ix_source_link_character ON source_link(character_id);
CREATE INDEX ix_source_link_passage ON source_link(passage_id);
CREATE INDEX ix_source_passage_source ON source_passage(source_id);
CREATE INDEX ix_alias_character ON character_alias(character_id);
