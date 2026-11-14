"""All SQL for the read API. Row dictionaries in, plain dictionaries out."""
import re

TIER_ORDER = {'primary': 0, 'supplementary': 1, 'scholarly': 2}

GROUPS = {  # (type, am_i_source) -> (group heading, label for the other character)
    ('parent_of', True): ('Children', 'child'), ('parent_of', False): ('Parents', 'parent'),
    ('child_of', True): ('Parents', 'parent'), ('child_of', False): ('Children', 'child'),
    ('ancestor_of', True): ('Descendants', 'descendant'), ('ancestor_of', False): ('Ancestors', 'ancestor'),
    ('descendant_of', True): ('Ancestors', 'ancestor'), ('descendant_of', False): ('Descendants', 'descendant'),
    ('spouse_of', True): ('Spouses', 'spouse'), ('spouse_of', False): ('Spouses', 'spouse'),
    ('sibling_of', True): ('Siblings', 'sibling'), ('sibling_of', False): ('Siblings', 'sibling'),
    ('lover_of', True): ('Lovers', 'lover'), ('lover_of', False): ('Lovers', 'lover'),
    ('ally_of', True): ('Allies', 'ally'), ('ally_of', False): ('Allies', 'ally'),
    ('enemy_of', True): ('Enemies', 'enemy'), ('enemy_of', False): ('Enemies', 'enemy'),
    ('rival_of', True): ('Rivals', 'rival'), ('rival_of', False): ('Rivals', 'rival'),
    ('mentor_of', True): ('Mentees', 'mentee'), ('mentor_of', False): ('Mentors', 'mentor'),
    ('creates', True): ('Creations', 'created entity'), ('creates', False): ('Creator', 'creator'),
    ('defeats', True): ('Defeated', 'defeated entity'), ('defeats', False): ('Defeated by', 'defeater'),
    ('killer_of', True): ('Slayer of', 'victim'), ('killer_of', False): ('Slain by', 'slayer'),
    ('rescues', True): ('Rescued', 'rescued entity'), ('rescues', False): ('Rescued by', 'rescuer'),
    ('transforms_into', True): ('Transforms Into', 'form'), ('transforms_into', False): ('Transformed From', 'original form'),
    ('gives_birth_to', True): ('Offspring', 'offspring'), ('gives_birth_to', False): ('Borne by', 'mother'),
    ('born_from', True): ('Borne by', 'mother'), ('born_from', False): ('Offspring', 'offspring'),
    ('associated_with', True): ('Associated With', 'associated entity'), ('associated_with', False): ('Associated With', 'associated entity'),
    ('worshipped_by', True): ('Worshippers', 'worshipper'), ('worshipped_by', False): ('Worships', 'deity'),
    ('embodies', True): ('Embodies', 'embodied concept'), ('embodies', False): ('Embodied by', 'entity'),
    ('represents', True): ('Represents', 'represented domain'), ('represents', False): ('Represented by', 'entity'),
    ('shares_cult_with', True): ('Shared Cults', 'cult partner'), ('shares_cult_with', False): ('Shared Cults', 'cult partner'),
    ('equivalent_to', True): ('Cross-Cultural Equivalents', 'equivalent'), ('equivalent_to', False): ('Cross-Cultural Equivalents', 'equivalent'),
    ('syncretized_with', True): ('Syncretisms', 'syncretized entity'), ('syncretized_with', False): ('Syncretisms', 'syncretized entity'),
    ('parallels', True): ('Parallels', 'parallel figure'), ('parallels', False): ('Parallels', 'parallel figure'),
    ('similar_in_function_to', True): ('Similar In Function', 'comparable entity'), ('similar_in_function_to', False): ('Similar In Function', 'comparable entity'),
}

GROUP_ORDER = [
    'Parents', 'Children', 'Ancestors', 'Descendants', 'Spouses', 'Siblings', 'Lovers',
    'Allies', 'Rivals', 'Enemies', 'Mentors', 'Mentees',
    'Creations', 'Creator', 'Defeated', 'Defeated by', 'Slayer of', 'Slain by', 'Rescued', 'Rescued by',
    'Transforms Into', 'Transformed From', 'Offspring', 'Borne by',
    'Associated With', 'Worshippers', 'Worships', 'Embodies', 'Embodied by', 'Represents', 'Represented by', 'Shared Cults',
    'Cross-Cultural Equivalents', 'Syncretisms', 'Parallels', 'Similar In Function'
]

def locator_key(loc):
    return tuple(int(x) for x in re.findall(r'\d+', loc or '')) or (10 ** 9,)

def _link(r):
    return {
        'id': r['id'] if 'id' in r.keys() else None,
        'passage_id': r['passage_id'] if 'passage_id' in r.keys() else None,
        'source': {
            'slug': r['sslug'], 'title': r['stitle'], 'author': r['sauthor'],
            'tier': r['stier'], 'edition_used': r['sedition'], 'url': r['surl'], 'license': r['slicense']
        },
        'locator': r['locator'], 'relation': r['relation'], 'claim': r['claim'], 'note': r['note'], 'verified': bool(r['verified'])
    }

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

def get_rel_group(rel_type, is_source, inv_label=None):
    if (rel_type, is_source) in GROUPS:
        return GROUPS[(rel_type, is_source)]
    if is_source:
        return (rel_type.replace('_', ' ').title(), rel_type.replace('_', ' '))
    label = inv_label or f"related ({rel_type.replace('_', ' ')})"
    return (label.title(), label)

def character_profile(db, cat, slug):
    c = cat.by_slug.get(slug)
    if not c: return None
    cid = c['id']
    rels = db.execute('''SELECT r.id, r.slug, rt.slug type, rt.category, rt.inverse_label, r.source_id, r.target_id,
            o.slug oslug, o.name oname, om.slug omyth, om.name omythname
        FROM relationship r JOIN relationship_type rt ON rt.id = r.type_id
        JOIN character o ON o.id = CASE WHEN r.source_id = ? THEN r.target_id ELSE r.source_id END
        JOIN mythology om ON om.id = o.mythology_id
        WHERE r.source_id = ? OR r.target_id = ?''', (cid, cid, cid)).fetchall()
    rlinks = _links(db, 'relationship_id', [r['id'] for r in rels])
    groups = {}
    for r in rels:
        is_src = (r['source_id'] == cid)
        heading, label = get_rel_group(r['type'], is_src, r['inverse_label'])
        links = rlinks[r['id']]
        groups.setdefault(heading, []).append({
            'id': r['slug'], 'type': r['type'], 'category': r['category'], 'as': label,
            'other': {'slug': r['oslug'], 'name': r['oname'], 'mythology': {'slug': r['omyth'], 'name': r['omythname']}},
            'verified': any(l['verified'] for l in links), 'sources': links})

    sorted_groups = []
    # Known priority order first
    for g in GROUP_ORDER:
        if g in groups:
            sorted_groups.append({'group': g, 'items': sorted(groups[g], key=lambda i: i['other']['name'])})
    # Any other dynamic groups
    for g in sorted(groups):
        if g not in GROUP_ORDER:
            sorted_groups.append({'group': g, 'items': sorted(groups[g], key=lambda i: i['other']['name'])})

    stories = [dict(slug=r['slug'], title=r['title'], role=r['role']) for r in db.execute(
        'SELECT m.slug, m.title, cm.role FROM myth m JOIN character_myth cm ON cm.myth_id = m.id WHERE cm.character_id = ? ORDER BY m.title', (cid,))]
    sources = _links(db, 'character_id', [cid])[cid]
    basis = [_link(r) for r in db.execute('''SELECT sl.*, s.slug sslug, s.title stitle, s.author sauthor, s.tier stier, s.edition_used sedition, s.url surl, s.license slicense
        FROM character_summary_basis b JOIN source_link sl ON sl.id = b.source_link_id JOIN source s ON s.id = sl.source_id WHERE b.character_id = ?''', (cid,))]
    basis.sort(key=lambda l: (TIER_ORDER[l['source']['tier']], l['source']['title'], locator_key(l['locator'])))

    unique_passages = {l['locator'] for l in sources if l['locator']}

    return {
        'slug': c['slug'], 'name': c['name'], 'mythology': c['mythology'],
        'tradition': c.get('tradition'),
        'gender': c['gender'], 'summary': c['summary'], 'summary_basis': basis, 'aliases': c['aliases'],
        'roles': [{'slug': x, 'name': cat.role_names.get(x, x)} for x in c['roles']],
        'domains': [{'slug': x, 'name': cat.domain_names.get(x, x)} for x in c['domains']],
        'sources': sources, 'relationships': sorted_groups, 'stories': stories,
        'equivalents': [],
        'counts': {
            'sources': len(sources),
            'verified_sources': sum(1 for s in sources if s['verified']),
            'passages': len(unique_passages),
            'relationships': len(rels),
            'stories': len(stories)
        }
    }

def character_relationships(db, cat, slug):
    p = character_profile(db, cat, slug)
    return None if p is None else {'character': p['slug'], 'groups': p['relationships']}

def character_graph(db, cat, slug, depth=1, categories=None, tradition=None, include_stories=True, include_sources=False, include_passages=False):
    """Generate structured nodes and edges for graph exploration centered on a character."""
    root = cat.by_slug.get(slug)
    if not root: return None
    depth = max(1, min(int(depth or 1), 3))
    categories_set = set(categories) if categories else None

    nodes_by_id = {}
    edges_by_id = {}
    visited_char_ids = {root['id']}
    frontier = {root['id']}

    def make_char_node(c, deg, is_root=False):
        node_type = 'deity' if any(r in ('god', 'goddess', 'titan', 'primordial') for r in c['roles']) else (
            'creature' if 'monster' in c['roles'] else ('hero' if 'hero' in c['roles'] else 'character'))
        return {
            'id': f"c:{c['slug']}",
            'slug': c['slug'],
            'label': c['name'],
            'entity_type': 'character',
            'node_type': node_type,
            'mythology': c['mythology']['slug'],
            'mythology_name': c['mythology']['name'],
            'tradition': c['tradition']['slug'] if c.get('tradition') else None,
            'tradition_name': c['tradition']['name'] if c.get('tradition') else None,
            'roles': [cat.role_names.get(r, r) for r in c['roles']],
            'domains': [cat.domain_names.get(d, d) for d in c['domains']],
            'summary': c['summary'],
            'verified': c['sources']['verified'] > 0,
            'degree': deg,
            'is_root': is_root
        }

    nodes_by_id[f"c:{root['slug']}"] = make_char_node(root, 0, is_root=True)

    for level in range(1, depth + 1):
        if not frontier: break
        placeholders = ','.join('?' * len(frontier))
        q = f'''SELECT r.id, r.slug, rt.slug type_slug, rt.label type_label, rt.category, rt.is_directed, rt.inverse_label,
                       r.source_id, r.target_id,
                       sc.slug src_slug, tc.slug tgt_slug
                FROM relationship r
                JOIN relationship_type rt ON rt.id = r.type_id
                JOIN character sc ON sc.id = r.source_id
                JOIN character tc ON tc.id = r.target_id
                WHERE r.source_id IN ({placeholders}) OR r.target_id IN ({placeholders})'''
        rows = db.execute(q, list(frontier) + list(frontier)).fetchall()
        rlinks = _links(db, 'relationship_id', [r['id'] for r in rows])

        next_frontier = set()
        for r in rows:
            if categories_set and r['category'] not in categories_set:
                continue
            src_cid, tgt_cid = r['source_id'], r['target_id']
            # Determine which end is new
            for cid in (src_cid, tgt_cid):
                if cid not in visited_char_ids:
                    char_obj = cat.by_id.get(cid)
                    if char_obj:
                        if tradition and (not char_obj.get('tradition') or char_obj['tradition']['slug'] != tradition):
                            continue
                        visited_char_ids.add(cid)
                        next_frontier.add(cid)
                        nodes_by_id[f"c:{char_obj['slug']}"] = make_char_node(char_obj, level)

            # Add edge if both endpoints exist in nodes_by_id
            src_node_id = f"c:{r['src_slug']}"
            tgt_node_id = f"c:{r['tgt_slug']}"
            if src_node_id in nodes_by_id and tgt_node_id in nodes_by_id:
                edge_id = f"r:{r['slug']}"
                links = rlinks.get(r['id'], [])
                edges_by_id[edge_id] = {
                    'id': edge_id,
                    'source': src_node_id,
                    'target': tgt_node_id,
                    'type': r['type_slug'],
                    'category': r['category'],
                    'label': r['type_label'],
                    'directed': bool(r['is_directed']),
                    'inverse_label': r['inverse_label'],
                    'verified': any(l['verified'] for l in links),
                    'evidence': links
                }
        frontier = next_frontier

    # Include Stories
    if include_stories and visited_char_ids:
        placeholders = ','.join('?' * len(visited_char_ids))
        sq = f'''SELECT m.id, m.slug, m.title, m.summary, mm.slug ms, mm.name mn, cm.character_id, cm.role, c.slug cslug
                 FROM myth m
                 JOIN character_myth cm ON cm.myth_id = m.id
                 JOIN character c ON c.id = cm.character_id
                 JOIN mythology mm ON mm.id = m.mythology_id
                 WHERE cm.character_id IN ({placeholders})'''
        for r in db.execute(sq, list(visited_char_ids)):
            story_node_id = f"m:{r['slug']}"
            if story_node_id not in nodes_by_id:
                nodes_by_id[story_node_id] = {
                    'id': story_node_id,
                    'slug': r['slug'],
                    'label': r['title'],
                    'entity_type': 'story',
                    'node_type': 'story',
                    'mythology': r['ms'],
                    'mythology_name': r['mn'],
                    'summary': r['summary'],
                    'degree': 1
                }
            edge_id = f"cm:{r['cslug']}:{r['slug']}"
            edges_by_id[edge_id] = {
                'id': edge_id,
                'source': f"c:{r['cslug']}",
                'target': story_node_id,
                'type': 'appears_in',
                'category': 'narrative',
                'label': (r['role'] or 'participant').replace('_', ' ').title(),
                'directed': True,
                'verified': True,
                'evidence': []
            }

    # Include Sources
    if include_sources and visited_char_ids:
        placeholders = ','.join('?' * len(visited_char_ids))
        sq = f'''SELECT s.id, s.slug, s.title, s.author, s.tier, s.edition_used, sl.character_id, sl.relation, sl.locator, sl.claim, sl.verified, c.slug cslug
                 FROM source_link sl
                 JOIN source s ON s.id = sl.source_id
                 JOIN character c ON c.id = sl.character_id
                 WHERE sl.character_id IN ({placeholders})'''
        for r in db.execute(sq, list(visited_char_ids)):
            src_node_id = f"s:{r['slug']}"
            if src_node_id not in nodes_by_id:
                nodes_by_id[src_node_id] = {
                    'id': src_node_id,
                    'slug': r['slug'],
                    'label': r['title'],
                    'entity_type': 'source',
                    'node_type': 'source',
                    'author': r['author'],
                    'tier': r['tier'],
                    'edition_used': r['edition_used'],
                    'degree': 1
                }
            edge_id = f"sl:c:{r['cslug']}:{r['slug']}"
            edges_by_id[edge_id] = {
                'id': edge_id,
                'source': f"c:{r['cslug']}",
                'target': src_node_id,
                'type': r['relation'],
                'category': 'evidence',
                'label': r['relation'].title(),
                'directed': True,
                'verified': bool(r['verified']),
                'evidence': [{'locator': r['locator'], 'claim': r['claim']}]
            }

    # Include Passages
    if include_passages and visited_char_ids:
        placeholders = ','.join('?' * len(visited_char_ids))
        pq = f'''SELECT sp.id, sp.locator, sp.translation_edition, sp.verified, s.slug sslug, s.title stitle,
                        sl.character_id, sl.relation, sl.claim, c.slug cslug
                 FROM source_link sl
                 JOIN source_passage sp ON sp.id = sl.passage_id
                 JOIN source s ON s.id = sp.source_id
                 JOIN character c ON c.id = sl.character_id
                 WHERE sl.character_id IN ({placeholders})'''
        for r in db.execute(pq, list(visited_char_ids)):
            pass_node_id = f"p:{r['id']}"
            if pass_node_id not in nodes_by_id:
                nodes_by_id[pass_node_id] = {
                    'id': pass_node_id,
                    'passage_id': r['id'],
                    'label': f"{r['stitle']} {r['locator']}",
                    'entity_type': 'passage',
                    'node_type': 'passage',
                    'source_slug': r['sslug'],
                    'locator': r['locator'],
                    'verified': bool(r['verified']),
                    'degree': 2
                }
            edge_id = f"splink:c:{r['cslug']}:p:{r['id']}"
            edges_by_id[edge_id] = {
                'id': edge_id,
                'source': f"c:{r['cslug']}",
                'target': pass_node_id,
                'type': 'attested_by',
                'category': 'evidence',
                'label': r['relation'].title(),
                'directed': True,
                'verified': bool(r['verified']),
                'evidence': [{'claim': r['claim']}]
            }

    return {
        'root': f"c:{root['slug']}",
        'nodes': list(nodes_by_id.values()),
        'edges': list(edges_by_id.values()),
        'counts': {
            'nodes': len(nodes_by_id),
            'edges': len(edges_by_id),
            'characters': sum(1 for n in nodes_by_id.values() if n.get('entity_type') == 'character'),
            'stories': sum(1 for n in nodes_by_id.values() if n.get('entity_type') == 'story'),
            'sources': sum(1 for n in nodes_by_id.values() if n.get('entity_type') == 'source'),
            'passages': sum(1 for n in nodes_by_id.values() if n.get('entity_type') == 'passage')
        }
    }

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
    traditions = [dict(slug=t['slug'], name=t['name'], description=t['description']) for t in cat.traditions.values() if t['mythology'] == slug]
    stories = [dict(slug=r['slug'], title=r['title'], summary=r['summary']) for r in cat.stories if r['mythology']['slug'] == slug]
    return {
        **m,
        'character_count': len(chars),
        'roles': sorted(({'slug': k, 'name': cat.role_names.get(k, k), 'count': v} for k, v in roles.items()), key=lambda x: (-x['count'], x['name'])),
        'sources_cited': tiers,
        'traditions': traditions,
        'stories': stories,
        'verified_characters': sum(1 for c in chars if c['sources']['verified'] > 0)
    }

def vocab(db, table, cat=None):
    if table == 'relationship_type':
        return [dict(slug=r['slug'], label=r['label'], category=r['category'], directed=bool(r['is_directed']), inverse_label=r['inverse_label'], count=r['n'])
                for r in db.execute('SELECT rt.*, (SELECT COUNT(*) FROM relationship r WHERE r.type_id = rt.id) n FROM relationship_type rt ORDER BY n DESC, rt.label')]
    link = {'role': 'character_role', 'domain': 'character_domain'}[table]
    return [dict(slug=r['slug'], name=r['name'], count=r['n']) for r in db.execute(
        f'SELECT t.slug, t.name, COUNT(l.character_id) n FROM {table} t LEFT JOIN {link} l ON l.{table}_id = t.id GROUP BY t.id ORDER BY n DESC, t.name')]

def sources_list(db):
    rows = db.execute('''SELECT s.*,
        (SELECT COUNT(*) FROM source_link sl WHERE sl.source_id = s.id) links,
        (SELECT COALESCE(SUM(verified),0) FROM source_link sl WHERE sl.source_id = s.id) verified,
        (SELECT COUNT(*) FROM source_passage sp WHERE sp.source_id = s.id) passages
        FROM source s''').fetchall()
    out = [dict(slug=r['slug'], title=r['title'], author=r['author'], tier=r['tier'], kind=r['kind'], collection=r['collection'], status=r['status'],
                edition_used=r['edition_used'], url=r['url'], license=r['license'], links=r['links'], verified_links=r['verified'], passages=r['passages']) for r in rows]
    return sorted(out, key=lambda s: (TIER_ORDER[s['tier']], s['title']))

def source_detail(db, slug):
    r = db.execute('''SELECT s.* FROM source s WHERE s.slug = ?''', (slug,)).fetchone()
    if not r: return None
    sid = r['id']
    passages = []
    for p in db.execute('''SELECT sp.*,
            (SELECT COUNT(*) FROM source_link sl WHERE sl.passage_id = sp.id AND sl.character_id IS NOT NULL) char_count,
            (SELECT COUNT(*) FROM source_link sl WHERE sl.passage_id = sp.id AND sl.relationship_id IS NOT NULL) rel_count,
            (SELECT COUNT(*) FROM source_link sl WHERE sl.passage_id = sp.id AND sl.myth_id IS NOT NULL) myth_count
        FROM source_passage sp WHERE sp.source_id = ? ORDER BY sp.id''', (sid,)).fetchall():
        passages.append({
            'id': p['id'],
            'locator': p['locator'],
            'original_locator': p['original_locator'],
            'translation_edition': p['translation_edition'],
            'excerpt': p['excerpt'],
            'notes': p['notes'],
            'verified': bool(p['verified']),
            'usage_count': p['char_count'] + p['rel_count'] + p['myth_count'],
            'counts': {'characters': p['char_count'], 'relationships': p['rel_count'], 'stories': p['myth_count']}
        })
    passages.sort(key=lambda p: locator_key(p['locator']))

    chars = [dict(slug=row['slug'], name=row['name'], mythology=dict(slug=row['ms'], name=row['mn']),
                  relation=row['relation'], locator=row['locator'], claim=row['claim'], verified=bool(row['verified']))
             for row in db.execute('''SELECT c.slug, c.name, m.slug ms, m.name mn, sl.relation, sl.locator, sl.claim, sl.verified
                 FROM source_link sl JOIN character c ON c.id = sl.character_id
                 JOIN mythology m ON m.id = c.mythology_id WHERE sl.source_id = ? ORDER BY c.name, sl.locator''', (sid,))]

    stories = [dict(slug=row['slug'], title=row['title'], mythology=dict(slug=row['ms'], name=row['mn']),
                    relation=row['relation'], locator=row['locator'], claim=row['claim'], verified=bool(row['verified']))
               for row in db.execute('''SELECT m.slug, m.title, mm.slug ms, mm.name mn, sl.relation, sl.locator, sl.claim, sl.verified
                   FROM source_link sl JOIN myth m ON m.id = sl.myth_id
                   JOIN mythology mm ON mm.id = m.mythology_id WHERE sl.source_id = ? ORDER BY m.title''', (sid,))]

    relationships = [dict(id=row['slug'], type=row['type'], label=row['label'], category=row['category'],
                          source=dict(slug=row['src_slug'], name=row['src_name']),
                          target=dict(slug=row['tgt_slug'], name=row['tgt_name']),
                          locator=row['locator'], claim=row['claim'], verified=bool(row['verified']))
                     for row in db.execute('''SELECT r.slug, rt.slug type, rt.label, rt.category,
                             sc.slug src_slug, sc.name src_name, tc.slug tgt_slug, tc.name tgt_name,
                             sl.locator, sl.claim, sl.verified
                         FROM source_link sl JOIN relationship r ON r.id = sl.relationship_id
                         JOIN relationship_type rt ON rt.id = r.type_id
                         JOIN character sc ON sc.id = r.source_id
                         JOIN character tc ON tc.id = r.target_id
                         WHERE sl.source_id = ? ORDER BY sc.name, tc.name''', (sid,))]

    return {
        'id': r['id'],
        'slug': r['slug'],
        'title': r['title'],
        'author': r['author'],
        'tier': r['tier'],
        'kind': r['kind'],
        'collection': r['collection'],
        'period_or_origin': r['period_or_origin'],
        'edition_used': r['edition_used'],
        'url': r['url'],
        'license': r['license'],
        'status': r['status'],
        'passages': passages,
        'characters_mentioned': chars,
        'stories_associated': stories,
        'relationships_supported': relationships,
        'counts': {
            'passages': len(passages),
            'verified_passages': sum(1 for p in passages if p['verified']),
            'characters': len({c['slug'] for c in chars}),
            'stories': len({s['slug'] for s in stories}),
            'relationships': len({rel['id'] for rel in relationships}),
            'links': len(chars) + len(stories) + len(relationships)
        }
    }

def source_passages(db, slug):
    src = db.execute('SELECT id, slug, title, author, tier, edition_used FROM source WHERE slug = ?', (slug,)).fetchone()
    if not src: return None
    passages = []
    for p in db.execute('''SELECT sp.* FROM source_passage sp WHERE sp.source_id = ? ORDER BY sp.id''', (src['id'],)).fetchall():
        chars = [dict(slug=c['slug'], name=c['name'], relation=c['relation'], claim=c['claim']) for c in db.execute(
            '''SELECT c.slug, c.name, sl.relation, sl.claim FROM source_link sl JOIN character c ON c.id = sl.character_id WHERE sl.passage_id = ?''', (p['id'],))]
        stories = [dict(slug=m['slug'], title=m['title'], relation=m['relation'], claim=m['claim']) for m in db.execute(
            '''SELECT m.slug, m.title, sl.relation, sl.claim FROM source_link sl JOIN myth m ON m.id = sl.myth_id WHERE sl.passage_id = ?''', (p['id'],))]
        relationships = [dict(id=r['slug'], type=r['type'], source=r['src_slug'], target=r['tgt_slug'], claim=r['claim']) for r in db.execute(
            '''SELECT rel.slug, rt.slug type, sc.slug src_slug, tc.slug tgt_slug, sl.claim
               FROM source_link sl JOIN relationship rel ON rel.id = sl.relationship_id
               JOIN relationship_type rt ON rt.id = rel.type_id
               JOIN character sc ON sc.id = rel.source_id
               JOIN character tc ON tc.id = rel.target_id
               WHERE sl.passage_id = ?''', (p['id'],))]
        passages.append({
            'id': p['id'],
            'locator': p['locator'],
            'original_locator': p['original_locator'],
            'translation_edition': p['translation_edition'],
            'excerpt': p['excerpt'],
            'notes': p['notes'],
            'verified': bool(p['verified']),
            'characters': chars,
            'stories': stories,
            'relationships': relationships
        })
    passages.sort(key=lambda p: locator_key(p['locator']))
    return {'source': dict(slug=src['slug'], title=src['title'], author=src['author'], tier=src['tier'], edition_used=src['edition_used']), 'passages': passages}

def passage_detail(db, passage_id):
    p = db.execute('''SELECT sp.*, s.slug sslug, s.title stitle, s.author sauthor, s.tier stier, s.edition_used sedition, s.url surl, s.license slicense
        FROM source_passage sp JOIN source s ON s.id = sp.source_id WHERE sp.id = ?''', (passage_id,)).fetchone()
    if not p: return None
    chars = [dict(slug=row['slug'], name=row['name'], mythology=dict(slug=row['ms'], name=row['mn']),
                  relation=row['relation'], claim=row['claim'], note=row['note'], verified=bool(row['verified']))
             for row in db.execute('''SELECT c.slug, c.name, m.slug ms, m.name mn, sl.relation, sl.claim, sl.note, sl.verified
                 FROM source_link sl JOIN character c ON c.id = sl.character_id
                 JOIN mythology m ON m.id = c.mythology_id WHERE sl.passage_id = ? ORDER BY c.name''', (passage_id,))]
    stories = [dict(slug=row['slug'], title=row['title'], mythology=dict(slug=row['ms'], name=row['mn']),
                    relation=row['relation'], claim=row['claim'], note=row['note'], verified=bool(row['verified']))
               for row in db.execute('''SELECT m.slug, m.title, mm.slug ms, mm.name mn, sl.relation, sl.claim, sl.note, sl.verified
                   FROM source_link sl JOIN myth m ON m.id = sl.myth_id
                   JOIN mythology mm ON mm.id = m.mythology_id WHERE sl.passage_id = ? ORDER BY m.title''', (passage_id,))]
    relationships = [dict(id=row['slug'], type=row['type'], label=row['label'], category=row['category'],
                          source=dict(slug=row['src_slug'], name=row['src_name']),
                          target=dict(slug=row['tgt_slug'], name=row['tgt_name']),
                          relation=row['relation'], claim=row['claim'], note=row['note'], verified=bool(row['verified']))
                     for row in db.execute('''SELECT r.slug, rt.slug type, rt.label, rt.category,
                             sc.slug src_slug, sc.name src_name, tc.slug tgt_slug, tc.name tgt_name,
                             sl.relation, sl.claim, sl.note, sl.verified
                         FROM source_link sl JOIN relationship r ON r.id = sl.relationship_id
                         JOIN relationship_type rt ON rt.id = r.type_id
                         JOIN character sc ON sc.id = r.source_id
                         JOIN character tc ON tc.id = r.target_id
                         WHERE sl.passage_id = ? ORDER BY sc.name''', (passage_id,))]
    return {
        'id': p['id'],
        'locator': p['locator'],
        'original_locator': p['original_locator'],
        'translation_edition': p['translation_edition'],
        'excerpt': p['excerpt'],
        'notes': p['notes'],
        'verified': bool(p['verified']),
        'source': {
            'slug': p['sslug'],
            'title': p['stitle'],
            'author': p['sauthor'],
            'tier': p['stier'],
            'edition_used': p['sedition'],
            'url': p['surl'],
            'license': p['slicense']
        },
        'supported_entities': {
            'characters': chars,
            'stories': stories,
            'relationships': relationships
        }
    }

def traditions_list(db):
    rows = db.execute('''SELECT t.*, m.slug ms, m.name mn,
        (SELECT COUNT(*) FROM character c WHERE c.tradition_id = t.id) char_count,
        (SELECT COUNT(*) FROM myth my WHERE my.tradition_id = t.id) myth_count
        FROM tradition t JOIN mythology m ON m.id = t.mythology_id ORDER BY m.name, t.name''').fetchall()
    return [dict(slug=r['slug'], name=r['name'], mythology=dict(slug=r['ms'], name=r['mn']),
                 description=r['description'], character_count=r['char_count'], story_count=r['myth_count']) for r in rows]

def tradition_detail(db, slug):
    r = db.execute('''SELECT t.*, m.slug ms, m.name mn FROM tradition t JOIN mythology m ON m.id = t.mythology_id WHERE t.slug = ?''', (slug,)).fetchone()
    if not r: return None
    tid = r['id']
    chars = [dict(slug=c['slug'], name=c['name'], summary=c['summary']) for c in db.execute(
        'SELECT slug, name, summary FROM character WHERE tradition_id = ? ORDER BY name', (tid,))]
    stories = [dict(slug=m['slug'], title=m['title'], summary=m['summary']) for m in db.execute(
        'SELECT slug, title, summary FROM myth WHERE tradition_id = ? ORDER BY title', (tid,))]
    return {
        'slug': r['slug'],
        'name': r['name'],
        'mythology': dict(slug=r['ms'], name=r['mn']),
        'description': r['description'],
        'characters': chars,
        'stories': stories,
        'character_count': len(chars),
        'story_count': len(stories)
    }

def story_detail(db, cat, slug):
    r = db.execute('''SELECT m.id, m.slug, m.title, m.summary, m.locations, m.episodes, m.notes,
                             mm.slug ms, mm.name mn, t.slug ts, t.name tn
                      FROM myth m
                      JOIN mythology mm ON mm.id = m.mythology_id
                      LEFT JOIN tradition t ON t.id = m.tradition_id
                      WHERE m.slug = ?''', (slug,)).fetchone()
    if not r: return None
    parts = [dict(slug=x['slug'], name=x['name'], role=x['role'], notes=x['notes']) for x in db.execute(
        'SELECT c.slug, c.name, cm.role, cm.notes FROM character c JOIN character_myth cm ON cm.character_id = c.id WHERE cm.myth_id = ? ORDER BY c.name', (r['id'],))]
    sources = _links(db, 'myth_id', [r['id']])[r['id']]
    return {
        'slug': r['slug'],
        'title': r['title'],
        'summary': r['summary'],
        'mythology': {'slug': r['ms'], 'name': r['mn']},
        'tradition': {'slug': r['ts'], 'name': r['tn']} if r['ts'] else None,
        'participants': parts,
        'sources': sources
    }

def stories_list(db):
    return [dict(slug=r['slug'], title=r['title'], summary=r['summary'],
                 mythology=dict(slug=r['ms'], name=r['mn']), participants=r['n']) for r in db.execute(
        '''SELECT m.slug, m.title, m.summary, mm.slug ms, mm.name mn, (SELECT COUNT(*) FROM character_myth cm WHERE cm.myth_id = m.id) n
           FROM myth m JOIN mythology mm ON mm.id = m.mythology_id ORDER BY m.title''')]
