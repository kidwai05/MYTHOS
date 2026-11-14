#!/usr/bin/env python3
"""Load data/*.json into SQLite using backend/schema.sql.
Usage: python backend/seed/loader.py [mythos.db]"""
import json, os, sqlite3, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Canonical taxonomy of relationship types: category, is_directed, inverse_label
TYPES = {
    # Genealogical
    'parent_of': ('genealogical', 1, 'child_of'),
    'child_of': ('genealogical', 1, 'parent_of'),
    'ancestor_of': ('genealogical', 1, 'descendant_of'),
    'descendant_of': ('genealogical', 1, 'ancestor_of'),
    'sibling_of': ('genealogical', 0, None),
    # Social
    'spouse_of': ('social', 0, None),
    'lover_of': ('social', 0, None),
    'ally_of': ('social', 0, None),
    'enemy_of': ('social', 0, None),
    'rival_of': ('social', 0, None),
    'mentor_of': ('social', 1, 'mentee_of'),
    # Narrative
    'creates': ('narrative', 1, 'created_by'),
    'defeats': ('narrative', 1, 'defeated_by'),
    'killer_of': ('narrative', 1, 'killed_by'),
    'rescues': ('narrative', 1, 'rescued_by'),
    'transforms_into': ('narrative', 1, 'transformed_from'),
    'gives_birth_to': ('narrative', 1, 'born_from'),
    'born_from': ('narrative', 1, 'gives_birth_to'),
    # Divine and symbolic
    'associated_with': ('divine_symbolic', 0, None),
    'worshipped_by': ('divine_symbolic', 1, 'worships'),
    'embodies': ('divine_symbolic', 1, 'embodied_by'),
    'represents': ('divine_symbolic', 1, 'represented_by'),
    'shares_cult_with': ('divine_symbolic', 0, None),
    # Cross-cultural
    'equivalent_to': ('cross_cultural', 0, None),
    'syncretized_with': ('cross_cultural', 0, None),
    'parallels': ('cross_cultural', 0, None),
    'similar_in_function_to': ('cross_cultural', 0, None),
}

TRADITIONS = [
    # Egyptian theological traditions
    ('heliopolitan', 'Heliopolitan', 'egyptian', 'Ennead theology centered on Atum and divine genealogy.'),
    ('hermopolitan', 'Hermopolitan', 'egyptian', 'Ogdoad theology of primeval forces and primordial waters.'),
    ('memphite', 'Memphite', 'egyptian', 'Theology of Ptah creating the cosmos through mind and speech.'),
    ('theban', 'Theban', 'egyptian', 'Amun theology of divine sovereignty and creative transcendence.'),
    ('esna', 'Esna', 'egyptian', 'Khnum theology of cosmic potter shaping deities and humanity.'),
    # Greek traditions
    ('hesiodic', 'Hesiodic', 'greek', 'Archaic genealogical tradition focused on the succession of cosmic orders.'),
    ('homeric', 'Homeric', 'greek', 'Epic tradition reflecting the Olympian order and heroic narrative.'),
    ('orphic', 'Orphic', 'greek', 'Mystery tradition of cosmic egg, Phanes, Zagreus, and rebirth.'),
    ('eleusinian', 'Eleusinian', 'greek', 'Mystery cult tradition centered on Demeter and Persephone.'),
    # Norse traditions
    ('eddic', 'Eddic', 'norse', 'Classical mythological tradition preserved in the Poetic and Prose Eddas.'),
    ('skaldic', 'Skaldic', 'norse', 'Courtly and poetic verse preservation of mythological kennings.'),
]

def build(dbfile=None, root=ROOT):
    """(Re)create the database at dbfile from the JSON in data/. Returns a dict of row counts."""
    dbfile = dbfile or os.path.join(root, 'mythos.db')
    if os.path.exists(dbfile): os.remove(dbfile)
    def load(n):
        with open(os.path.join(root, 'data', n + '.json'), encoding='utf-8') as f: return json.load(f)['records']
    db = sqlite3.connect(dbfile); db.execute('PRAGMA foreign_keys=ON')
    with open(os.path.join(root, 'backend', 'schema.sql'), encoding='utf-8') as f: db.executescript(f.read())
    def one(sql, *a): return db.execute(sql, a).fetchone()[0]
    def get_or_add(table, slug, name=None):
        r = db.execute(f'SELECT id FROM {table} WHERE slug=?', (slug,)).fetchone()
        return r[0] if r else db.execute(f'INSERT INTO {table}(slug,name) VALUES(?,?)', (slug, name or slug.replace('-', ' ').title())).lastrowid

    # Populate core mythologies
    myth_map = {}
    for slug, name in (('greek', 'Greek'), ('norse', 'Norse'), ('egyptian', 'Egyptian')):
        mid = db.execute('INSERT INTO mythology(slug,name) VALUES(?,?)', (slug, name)).lastrowid
        myth_map[slug] = mid

    # Populate predefined traditions
    trad_map = {}
    for tslug, tname, myth_slug, tdesc in TRADITIONS:
        if myth_slug in myth_map:
            tid = db.execute('INSERT INTO tradition(slug,name,mythology_id,description) VALUES(?,?,?,?)',
                             (tslug, tname, myth_map[myth_slug], tdesc)).lastrowid
            trad_map[tslug] = tid

    def get_or_add_tradition(slug, myth_slug, name=None):
        if not slug: return None
        if slug in trad_map: return trad_map[slug]
        mid = myth_map.get(myth_slug) or one('SELECT id FROM mythology WHERE slug=?', myth_slug)
        tname = name or slug.replace('-', ' ').title()
        tid = db.execute('INSERT INTO tradition(slug,name,mythology_id) VALUES(?,?,?)', (slug, tname, mid)).lastrowid
        trad_map[slug] = tid
        return tid

    # Pre-populate all relationship types from TYPES catalog
    for slug, (cat, directed, inv) in TYPES.items():
        db.execute('INSERT OR IGNORE INTO relationship_type(slug,label,category,is_directed,inverse_label) VALUES(?,?,?,?,?)',
                   (slug, slug.replace('_', ' '), cat, directed, inv))

    src = {}
    src_editions = {}
    for s in load('sources'):
        src_id = db.execute('INSERT INTO source(slug,title,author,tier,kind,collection,period_or_origin,edition_used,url,license,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (s['id'], s['title'], s['author'], s['tier'], s['kind'], s['collection'], s['period_or_origin'], s.get('edition_used'), s.get('url'), s.get('license'), s['status'])).lastrowid
        src[s['id']] = src_id
        src_editions[src_id] = s.get('edition_used')

    passages = {}  # (source_id, locator) -> passage_id

    def get_or_add_passage(source_db_id, locator, verified=0, note=None):
        if not locator: return None
        key = (source_db_id, locator)
        if key in passages:
            pid = passages[key]
            if verified:
                db.execute('UPDATE source_passage SET verified=1 WHERE id=? AND verified=0', (pid,))
            return pid
        pid = db.execute('INSERT INTO source_passage(source_id,locator,translation_edition,notes,verified) VALUES(?,?,?,?,?)',
                         (source_db_id, locator, src_editions.get(source_db_id), note, int(verified))).lastrowid
        passages[key] = pid
        return pid

    def links(r, col, rid):
        for l in r['sources']:
            s_db_id = src[l['source_id']]
            loc = l.get('locator')
            ver = int(bool(l.get('verified')))
            pid = get_or_add_passage(s_db_id, loc, verified=ver, note=l.get('note'))
            db.execute(f'INSERT INTO source_link(source_id,{col},passage_id,locator,relation,claim,note,verified) VALUES(?,?,?,?,?,?,?,?)',
                (s_db_id, rid, pid, loc, l['relation'], l.get('claim'), l.get('note'), ver))

    chars = {}
    for fn in ('deities', 'creatures', 'heroes'):
        for r in load(fn):
            myth_id = myth_map.get(r['mythology']) or one('SELECT id FROM mythology WHERE slug=?', r['mythology'])
            trad_id = get_or_add_tradition(r.get('tradition'), r['mythology'])
            cid = db.execute('INSERT INTO character(slug,name,mythology_id,tradition_id,gender,summary,description) VALUES(?,?,?,?,?,?,?)',
                (r['id'], r['name'], myth_id, trad_id, r.get('gender'), r.get('summary'), r.get('description'))).lastrowid
            chars[r['id']] = cid
            for a in r.get('aliases', []): db.execute('INSERT INTO character_alias(character_id,alias) VALUES(?,?)', (cid, a))
            for x in r.get('roles', []): db.execute('INSERT INTO character_role VALUES(?,?)', (cid, get_or_add('role', x)))
            for x in r.get('domains', []): db.execute('INSERT INTO character_domain VALUES(?,?)', (cid, get_or_add('domain', x)))
            links(r, 'character_id', cid)
            for b in r.get('summary_basis', []):
                row = db.execute('SELECT id FROM source_link WHERE character_id=? AND source_id=? AND locator=? AND verified=1', (cid, src[b['source_id']], b['locator'])).fetchone()
                if row is None: raise ValueError(f"{r['id']}: summary basis {b} is not a verified link")
                db.execute('INSERT INTO character_summary_basis VALUES(?,?)', (cid, row[0]))

    for r in load('relationships'):
        rel_type = r['type']
        if rel_type in TYPES:
            cat, directed, inv = TYPES[rel_type]
        else:
            cat, directed, inv = ('other', 1, None)
        t = db.execute('SELECT id FROM relationship_type WHERE slug=?', (rel_type,)).fetchone()
        t = t[0] if t else db.execute('INSERT INTO relationship_type(slug,label,category,is_directed,inverse_label) VALUES(?,?,?,?,?)',
                                      (rel_type, rel_type.replace('_', ' '), cat, directed, inv)).lastrowid
        r_trad_id = get_or_add_tradition(r.get('tradition'), None) if r.get('tradition') else None
        rid = db.execute('INSERT INTO relationship(slug,source_id,target_id,type_id,tradition_id,description,notes) VALUES(?,?,?,?,?,?,?)',
                         (r['id'], chars[r['source']], chars[r['target']], t, r_trad_id, r.get('description'), r.get('notes'))).lastrowid
        links(r, 'relationship_id', rid)

    for r in load('stories'):
        myth_id = myth_map.get(r['mythology']) or one('SELECT id FROM mythology WHERE slug=?', r['mythology'])
        s_trad_id = get_or_add_tradition(r.get('tradition'), r['mythology']) if r.get('tradition') else None
        mid = db.execute('INSERT INTO myth(slug,title,summary,mythology_id,tradition_id,locations,episodes,notes) VALUES(?,?,?,?,?,?,?,?)',
                         (r['id'], r['title'], r.get('summary'), myth_id, s_trad_id,
                          json.dumps(r['locations']) if 'locations' in r else None,
                          json.dumps(r['episodes']) if 'episodes' in r else None,
                          r.get('notes'))).lastrowid
        for p in r['participants']:
            if isinstance(p, dict):
                p_slug = p.get('character_id') or p.get('id') or p.get('character')
                p_role = p.get('role', 'participant')
                p_note = p.get('notes')
            else:
                p_slug = p
                p_role = 'participant'
                p_note = None
            db.execute('INSERT INTO character_myth(character_id,myth_id,role,notes) VALUES(?,?,?,?)',
                       (chars[p_slug], mid, p_role, p_note))
        links(r, 'myth_id', mid)

    db.commit()
    counts = {t: one(f'SELECT COUNT(*) FROM {t}') for t in ('mythology', 'tradition', 'character', 'relationship', 'relationship_type', 'source', 'source_passage', 'source_link', 'myth')}
    counts['verified_links'] = one('SELECT COUNT(*) FROM source_link WHERE verified=1')
    counts['verified_passages'] = one('SELECT COUNT(*) FROM source_passage WHERE verified=1')
    db.close()
    return counts

if __name__ == '__main__':
    for k, v in build(sys.argv[1] if len(sys.argv) > 1 else None).items(): print(f'{k:20}', v)
