#!/usr/bin/env python3
"""Load data/*.json into SQLite using backend/schema.sql. Minimal Phase 0 loader.
Usage: python backend/seed/loader.py [mythos.db]"""
import json, os, sqlite3, sys
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dbfile = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'mythos.db')
if os.path.exists(dbfile): os.remove(dbfile)
load = lambda n: json.load(open(os.path.join(root, 'data', n + '.json'), encoding='utf-8'))['records']
db = sqlite3.connect(dbfile); db.execute('PRAGMA foreign_keys=ON')
db.executescript(open(os.path.join(root, 'backend', 'schema.sql'), encoding='utf-8').read())
def one(sql, *a): return db.execute(sql, a).fetchone()[0]
def get_or_add(table, slug, name=None):
    r = db.execute(f'SELECT id FROM {table} WHERE slug=?', (slug,)).fetchone()
    return r[0] if r else db.execute(f'INSERT INTO {table}(slug,name) VALUES(?,?)', (slug, name or slug.replace('-', ' ').title())).lastrowid
for slug, name in (('greek','Greek'),('norse','Norse'),('egyptian','Egyptian')):
    db.execute('INSERT INTO mythology(slug,name) VALUES(?,?)', (slug, name))
src = {}
for s in load('sources'):
    src[s['id']] = db.execute('INSERT INTO source(slug,title,author,tier,kind,collection,period_or_origin,edition_used,url,license,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
        (s['id'], s['title'], s['author'], s['tier'], s['kind'], s['collection'], s['period_or_origin'], s.get('edition_used'), s.get('url'), s.get('license'), s['status'])).lastrowid
def links(r, col, rid):
    for l in r['sources']:
        db.execute(f'INSERT INTO source_link(source_id,{col},locator,relation,claim,note,verified) VALUES(?,?,?,?,?,?,?)',
            (src[l['source_id']], rid, l['locator'], l['relation'], l.get('claim'), l.get('note'), int(l['verified'])))
chars = {}
for fn in ('deities', 'creatures', 'heroes'):
    for r in load(fn):
        cid = db.execute('INSERT INTO character(slug,name,mythology_id,gender) VALUES(?,?,?,?)',
            (r['id'], r['name'], one('SELECT id FROM mythology WHERE slug=?', r['mythology']), r.get('gender'))).lastrowid
        chars[r['id']] = cid
        for a in r.get('aliases', []): db.execute('INSERT INTO character_alias(character_id,alias) VALUES(?,?)', (cid, a))
        for x in r.get('roles', []): db.execute('INSERT INTO character_role VALUES(?,?)', (cid, get_or_add('role', x)))
        for x in r.get('domains', []): db.execute('INSERT INTO character_domain VALUES(?,?)', (cid, get_or_add('domain', x)))
        links(r, 'character_id', cid)
TYPES = {'parent_of': ('family', 1, 'child_of'), 'spouse_of': ('family', 0, None), 'sibling_of': ('family', 0, None), 'rival_of': ('rivalry', 0, None),
         'ally_of': ('alliance', 0, None), 'killer_of': ('rivalry', 1, 'killed_by'), 'lover_of': ('romance', 0, None)}
for r in load('relationships'):
    cat, directed, inv = TYPES[r['type']]
    t = db.execute('SELECT id FROM relationship_type WHERE slug=?', (r['type'],)).fetchone()
    t = t[0] if t else db.execute('INSERT INTO relationship_type(slug,label,category,is_directed,inverse_label) VALUES(?,?,?,?,?)', (r['type'], r['type'].replace('_', ' '), cat, directed, inv)).lastrowid
    rid = db.execute('INSERT INTO relationship(slug,source_id,target_id,type_id) VALUES(?,?,?,?)', (r['id'], chars[r['source']], chars[r['target']], t)).lastrowid
    links(r, 'relationship_id', rid)
for r in load('stories'):
    mid = db.execute('INSERT INTO myth(slug,title,mythology_id) VALUES(?,?,?)', (r['id'], r['title'], one('SELECT id FROM mythology WHERE slug=?', r['mythology']))).lastrowid
    for p in r['participants']: db.execute('INSERT INTO character_myth VALUES(?,?)', (chars[p], mid))
    links(r, 'myth_id', mid)
db.commit()
for t in ('mythology','character','relationship','relationship_type','source','source_link','myth'): print(f'{t:18}', one(f'SELECT COUNT(*) FROM {t}'))
print('verified links:', one('SELECT COUNT(*) FROM source_link WHERE verified=1'))
