"""In-memory catalogue of characters built from the database. Filtering, facets, sorting and search live here.
The data is read-only in Phase 2, so the catalogue reloads only when the database file changes."""
import os, sqlite3
from .search import score_doc, norm

DIMENSIONS = ('mythology', 'role', 'domain', 'gender')
GENDER_LABELS = {'f': 'Female', 'm': 'Male'}

class Catalog:
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.mtime = None
        self.reload()

    def reload(self):
        db = sqlite3.connect(self.dbfile); db.row_factory = sqlite3.Row
        self.mythologies = {r['slug']: dict(slug=r['slug'], name=r['name']) for r in db.execute('SELECT slug,name FROM mythology ORDER BY id')}
        self.role_names = {r['slug']: r['name'] for r in db.execute('SELECT slug,name FROM role')}
        self.domain_names = {r['slug']: r['name'] for r in db.execute('SELECT slug,name FROM domain')}
        chars = {}
        for r in db.execute('SELECT c.id,c.slug,c.name,c.gender,c.summary,m.slug ms,m.name mn FROM character c JOIN mythology m ON m.id=c.mythology_id'):
            chars[r['id']] = dict(id=r['id'], slug=r['slug'], name=r['name'], gender=r['gender'], summary=r['summary'],
                mythology=dict(slug=r['ms'], name=r['mn']), aliases=[], roles=[], domains=[], sources=dict(total=0, verified=0), _text=[])
        for r in db.execute('SELECT character_id,alias FROM character_alias ORDER BY id'): chars[r['character_id']]['aliases'].append(r['alias'])
        for r in db.execute('SELECT cr.character_id,r.slug FROM character_role cr JOIN role r ON r.id=cr.role_id ORDER BY r.slug'): chars[r['character_id']]['roles'].append(r['slug'])
        for r in db.execute('SELECT cd.character_id,d.slug FROM character_domain cd JOIN domain d ON d.id=cd.domain_id ORDER BY d.slug'): chars[r['character_id']]['domains'].append(r['slug'])
        for r in db.execute('SELECT character_id,verified,claim FROM source_link WHERE character_id IS NOT NULL'):
            c = chars[r['character_id']]; c['sources']['total'] += 1; c['sources']['verified'] += r['verified']
            if r['claim']: c['_text'].append(r['claim'])
        db.close()
        for c in chars.values():
            c['_doc'] = dict(name=c['name'], aliases=c['aliases'],
                text=' '.join(([c['summary']] if c['summary'] else []) + c['_text'] + [self.role_names.get(x, x) for x in c['roles']] + [self.domain_names.get(x, x) for x in c['domains']]))
        self.chars = sorted(chars.values(), key=lambda c: norm(c['name']))
        self.by_slug = {c['slug']: c for c in self.chars}
        self.mtime = os.path.getmtime(self.dbfile)

    def fresh(self):
        if os.path.getmtime(self.dbfile) != self.mtime: self.reload()
        return self

    # ---- vocabularies ----
    def valid(self, dim):
        if dim == 'mythology': return set(self.mythologies)
        if dim == 'role': return set(self.role_names)
        if dim == 'domain': return set(self.domain_names)
        return set(GENDER_LABELS)

    @staticmethod
    def _values(c, dim):
        if dim == 'mythology': return [c['mythology']['slug']]
        if dim == 'gender': return [c['gender']] if c['gender'] else []
        return c['roles'] if dim == 'role' else c['domains']

    # ---- query ----
    def search(self, filters, q=None, skip=None):
        """filters: {dim: [values]}. Values within one filter are OR, different filters are AND.
        Returns [(character, score, matched_on, matched_text)] unsorted."""
        out = []
        for c in self.chars:
            if any(vals and dim != skip and not (set(vals) & set(self._values(c, dim))) for dim, vals in filters.items()): continue
            if q:
                m = score_doc(q, c['_doc'])
                if m: out.append((c, m[0], m[1], m[2]))
            else: out.append((c, 0.0, None, None))
        return out

    def facets(self, filters, q=None):
        """Counts per value for each dimension, with every other filter applied (so a dimension never hides its own alternatives)."""
        res = {}
        for dim in DIMENSIONS:
            counts = {}
            for c, *_ in self.search(filters, q, skip=dim):
                for v in self._values(c, dim): counts[v] = counts.get(v, 0) + 1
            names = {'mythology': {k: v['name'] for k, v in self.mythologies.items()}, 'role': self.role_names, 'domain': self.domain_names, 'gender': GENDER_LABELS}[dim]
            res[dim] = sorted(({'value': v, 'label': names.get(v, v), 'count': n} for v, n in counts.items()), key=lambda x: (-x['count'], x['label']))
        return res

    def suggest(self, q, limit=8):
        res = []
        for c in self.chars:
            m = score_doc(q, dict(name=c['name'], aliases=c['aliases'], text=''))
            if m: res.append((m[0], c, m[1], m[2]))
        res.sort(key=lambda x: (-x[0], norm(x[1]['name'])))
        return res[:limit]
