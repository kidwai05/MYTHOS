"""All SQL for the read API. Row dictionaries in, plain dictionaries out."""
import re

TIER_ORDER = {'primary': 0, 'supplementary': 1, 'scholarly': 2}
GROUPS = {  # (type, am_i_source) -> (group heading, label for the other character)
    ('parent_of', True): ('Children', 'child'), ('parent_of', False): ('Parents', 'parent'),
    ('spouse_of', True): ('Spouses', 'spouse'), ('spouse_of', False): ('Spouses', 'spouse'),
    ('sibling_of', True): ('Siblings', 'sibling'), ('sibling_of', False): ('Siblings', 'sibling'),
    ('lover_of', True): ('Lovers', 'lover'), ('lover_of', False): ('Lovers', 'lover'),
    ('ally_of', True): ('Allies', 'ally'), ('ally_of', False): ('Allies', 'ally'),
    ('rival_of', True): ('Rivals', 'rival'), ('rival_of', False): ('Rivals', 'rival'),
    ('killer_of', True): ('Slayer of', 'victim'), ('killer_of', False): ('Slain by', 'slayer'),
}
GROUP_ORDER = ['Parents', 'Children', 'Spouses', 'Siblings', 'Lovers', 'Allies', 'Rivals', 'Slayer of', 'Slain by']

def locator_key(loc):
    return tuple(int(x) for x in re.findall(r'\d+', loc or '')) or (10 ** 9,)

def _link(r):
    return {'source': {'slug': r['sslug'], 'title': r['stitle'], 'author': r['sauthor'], 'tier': r['stier'], 'edition_used': r['sedition'], 'url': r['surl'], 'license': r['slicense']},
            'locator': r['locator'], 'relation': r['relation'], 'claim': r['claim'], 'note': r['note'], 'verified': bool(r['verified'])}

LINK_SQL = '''SELECT sl.*, s.slug sslug, s.title stitle, s.author sauthor, s.tier stier, s.edition_used sedition, s.url surl, s.license slicense
              FROM source_link sl JOIN source s ON s.id = sl.source_id WHERE sl.{col} IN ({marks})'''

def _links(db, col, ids):
    out = {i: [] for i in ids}
    if not ids: return out
    for r in db.execute(LINK_SQL.format(col=col, marks=','.join('?' * len(ids))), list(ids)):
        out[r[col]].append(_link(r))
    for v in out.values():
        v.sort(key=lambda l: (TIER_ORDER[l['source']['tier']], l['source']['title'], locator_key(l['locator'])))
    return out

def character_profile(db, cat, slug):
    c = cat.by_slug.get(slug)
    if not c: return None
    cid = c['id']
    rels = db.execute('''SELECT r.id, r.slug, rt.slug type, rt.category, r.source_id, r.target_id,
            o.slug oslug, o.name oname, om.slug omyth, om.name omythname
        FROM relationship r JOIN relationship_type rt ON rt.id = r.type_id
        JOIN character o ON o.id = CASE WHEN r.source_id = ? THEN r.target_id ELSE r.source_id END
        JOIN mythology om ON om.id = o.mythology_id
        WHERE r.source_id = ? OR r.target_id = ?''', (cid, cid, cid)).fetchall()
    rlinks = _links(db, 'relationship_id', [r['id'] for r in rels])
    groups = {}
    for r in rels:
        heading, label = GROUPS[(r['type'], r['source_id'] == cid)]
        links = rlinks[r['id']]
        groups.setdefault(heading, []).append({
            'id': r['slug'], 'type': r['type'], 'category': r['category'], 'as': label,
            'other': {'slug': r['oslug'], 'name': r['oname'], 'mythology': {'slug': r['omyth'], 'name': r['omythname']}},
            'verified': any(l['verified'] for l in links), 'sources': links})
    relationships = [{'group': g, 'items': sorted(groups[g], key=lambda i: i['other']['name'])} for g in GROUP_ORDER if g in groups]
    stories = [dict(slug=r['slug'], title=r['title']) for r in db.execute(
        'SELECT m.slug, m.title FROM myth m JOIN character_myth cm ON cm.myth_id = m.id WHERE cm.character_id = ? ORDER BY m.title', (cid,))]
    sources = _links(db, 'character_id', [cid])[cid]
    basis = [_link(r) for r in db.execute('''SELECT sl.*, s.slug sslug, s.title stitle, s.author sauthor, s.tier stier, s.edition_used sedition, s.url surl, s.license slicense
        FROM character_summary_basis b JOIN source_link sl ON sl.id = b.source_link_id JOIN source s ON s.id = sl.source_id WHERE b.character_id = ?''', (cid,))]
    basis.sort(key=lambda l: (TIER_ORDER[l['source']['tier']], l['source']['title'], locator_key(l['locator'])))
    return {'slug': c['slug'], 'name': c['name'], 'mythology': c['mythology'], 'gender': c['gender'], 'summary': c['summary'], 'summary_basis': basis, 'aliases': c['aliases'],
            'roles': [{'slug': x, 'name': cat.role_names.get(x, x)} for x in c['roles']],
            'domains': [{'slug': x, 'name': cat.domain_names.get(x, x)} for x in c['domains']],
            'sources': sources, 'relationships': relationships, 'stories': stories,
            'equivalents': [],  # filled in once a second mythology exists (Phase 5)
            'counts': {'sources': len(sources), 'verified_sources': sum(1 for s in sources if s['verified']),
                       'relationships': len(rels), 'stories': len(stories)}}

def character_relationships(db, cat, slug):
    p = character_profile(db, cat, slug)
    return None if p is None else {'character': p['slug'], 'groups': p['relationships']}

def mythology_detail(db, cat, slug):
    m = cat.mythologies.get(slug)
    if not m: return None
    chars = [c for c in cat.chars if c['mythology']['slug'] == slug]
    roles, tiers = {}, {}
    for c in chars:
        for r in c['roles']: roles[r] = roles.get(r, 0) + 1
    for r in db.execute('''SELECT s.tier, COUNT(DISTINCT s.id) n FROM source s JOIN source_link sl ON sl.source_id = s.id
            LEFT JOIN character c ON c.id = sl.character_id LEFT JOIN myth my ON my.id = sl.myth_id
            LEFT JOIN relationship rel ON rel.id = sl.relationship_id LEFT JOIN character rc ON rc.id = rel.source_id
            JOIN mythology mm ON mm.id = COALESCE(c.mythology_id, my.mythology_id, rc.mythology_id)
            WHERE mm.slug = ? GROUP BY s.tier''', (slug,)):
        tiers[r['tier']] = r['n']
    return {**m, 'character_count': len(chars),
            'roles': sorted(({'slug': k, 'name': cat.role_names.get(k, k), 'count': v} for k, v in roles.items()), key=lambda x: (-x['count'], x['name'])),
            'sources_cited': tiers,
            'verified_characters': sum(1 for c in chars if c['sources']['verified'] > 0)}

def vocab(db, table, cat=None):
    if table == 'relationship_type':
        return [dict(slug=r['slug'], label=r['label'], category=r['category'], directed=bool(r['is_directed']), inverse_label=r['inverse_label'], count=r['n'])
                for r in db.execute('SELECT rt.*, (SELECT COUNT(*) FROM relationship r WHERE r.type_id = rt.id) n FROM relationship_type rt ORDER BY n DESC, rt.label')]
    link = {'role': 'character_role', 'domain': 'character_domain'}[table]
    return [dict(slug=r['slug'], name=r['name'], count=r['n']) for r in db.execute(
        f'SELECT t.slug, t.name, COUNT(l.character_id) n FROM {table} t LEFT JOIN {link} l ON l.{table}_id = t.id GROUP BY t.id ORDER BY n DESC, t.name')]

def sources_list(db):
    rows = db.execute('''SELECT s.*, (SELECT COUNT(*) FROM source_link sl WHERE sl.source_id = s.id) links,
        (SELECT COALESCE(SUM(verified),0) FROM source_link sl WHERE sl.source_id = s.id) verified FROM source s''').fetchall()
    out = [dict(slug=r['slug'], title=r['title'], author=r['author'], tier=r['tier'], kind=r['kind'], collection=r['collection'], status=r['status'],
                edition_used=r['edition_used'], url=r['url'], license=r['license'], links=r['links'], verified_links=r['verified']) for r in rows]
    return sorted(out, key=lambda s: (TIER_ORDER[s['tier']], s['title']))

def story_detail(db, cat, slug):
    r = db.execute('SELECT m.id, m.slug, m.title, mm.slug ms, mm.name mn FROM myth m JOIN mythology mm ON mm.id = m.mythology_id WHERE m.slug = ?', (slug,)).fetchone()
    if not r: return None
    parts = [dict(slug=x['slug'], name=x['name']) for x in db.execute(
        'SELECT c.slug, c.name FROM character c JOIN character_myth cm ON cm.character_id = c.id WHERE cm.myth_id = ? ORDER BY c.name', (r['id'],))]
    return {'slug': r['slug'], 'title': r['title'], 'mythology': {'slug': r['ms'], 'name': r['mn']}, 'participants': parts, 'sources': _links(db, 'myth_id', [r['id']])[r['id']]}

def stories_list(db):
    return [dict(slug=r['slug'], title=r['title'], mythology=dict(slug=r['ms'], name=r['mn']), participants=r['n']) for r in db.execute(
        '''SELECT m.slug, m.title, mm.slug ms, mm.name mn, (SELECT COUNT(*) FROM character_myth cm WHERE cm.myth_id = m.id) n
           FROM myth m JOIN mythology mm ON mm.id = m.mythology_id ORDER BY m.title''')]
