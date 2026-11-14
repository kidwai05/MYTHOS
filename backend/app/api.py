"""REST API, version 1 (read-only). Lists use ?page and ?per_page and return {items, page, per_page, total}."""
from flask import Blueprint, jsonify, request, current_app
from .db import get_db
from . import repository as repo
from .catalog import Catalog, DIMENSIONS, GENDER_LABELS
from .search import norm

bp = Blueprint('api', __name__)
CHAR_FIELDS = ('slug', 'name', 'mythology', 'gender', 'summary', 'roles', 'domains', 'aliases', 'sources', 'match')
SORTS = ('relevance', 'name', '-name', 'mythology')
MAX_PER_PAGE = 100

class ApiError(Exception):
    def __init__(self, status, code, message): self.status, self.code, self.message = status, code, message

@bp.errorhandler(ApiError)
def _api_error(e):
    return jsonify({'error': {'code': e.code, 'message': e.message}}), e.status

def catalog():
    cat = current_app.extensions.get('catalog')
    if cat is None:
        cat = current_app.extensions['catalog'] = Catalog(current_app.config['DATABASE'])
    return cat.fresh()

def int_param(name, default, lo, hi):
    raw = request.args.get(name)
    if raw is None or raw == '': return default
    try: v = int(raw)
    except ValueError: raise ApiError(400, 'invalid_parameter', f'{name} must be an integer')
    if v < lo or v > hi: raise ApiError(400, 'invalid_parameter', f'{name} must be between {lo} and {hi}')
    return v

def list_param(name):
    vals = []
    for raw in request.args.getlist(name):
        vals += [v.strip() for v in raw.split(',') if v.strip()]
    return vals

def shape(c, score, on, txt, fields, with_match):
    full = {'slug': c['slug'], 'name': c['name'], 'mythology': c['mythology'], 'gender': c['gender'], 'summary': c['summary'], 'roles': c['roles'], 'domains': c['domains'],
            'aliases': c['aliases'], 'sources': c['sources']}
    if with_match: full['match'] = {'on': on, 'text': txt, 'score': round(score, 3)}
    return {k: full[k] for k in fields if k in full}

@bp.get('/characters')
def characters():
    cat = catalog()
    filters = {}
    for dim in DIMENSIONS:
        vals = list_param(dim)
        bad = [v for v in vals if v not in cat.valid(dim)]
        if bad: raise ApiError(400, 'unknown_filter_value', f"Unknown {dim} value(s): {', '.join(bad)}. Valid: {', '.join(sorted(cat.valid(dim)))}")
        filters[dim] = vals
    q = (request.args.get('q') or '').strip() or None
    if q and len(q) > 100: raise ApiError(400, 'invalid_parameter', 'q must be at most 100 characters')
    sort = request.args.get('sort') or ('relevance' if q else 'name')
    if sort not in SORTS: raise ApiError(400, 'invalid_parameter', f"sort must be one of: {', '.join(SORTS)}")
    if sort == 'relevance' and not q: sort = 'name'
    page = int_param('page', 1, 1, 10 ** 6); per_page = int_param('per_page', 20, 1, MAX_PER_PAGE)
    fields = [f.strip() for f in (request.args.get('fields') or '').split(',') if f.strip()] or [f for f in CHAR_FIELDS if f != 'match']
    bad = [f for f in fields if f not in CHAR_FIELDS]
    if bad: raise ApiError(400, 'invalid_parameter', f"Unknown field(s): {', '.join(bad)}. Valid: {', '.join(CHAR_FIELDS)}")
    hits = cat.search(filters, q)
    if sort == 'relevance': hits.sort(key=lambda h: (-h[1], norm(h[0]['name'])))
    elif sort == 'name': hits.sort(key=lambda h: norm(h[0]['name']))
    elif sort == '-name': hits.sort(key=lambda h: norm(h[0]['name']), reverse=True)
    else: hits.sort(key=lambda h: (h[0]['mythology']['name'], norm(h[0]['name'])))
    total = len(hits)
    window = hits[(page - 1) * per_page: page * per_page]
    if q and 'match' not in fields and request.args.get('fields') is None: fields.append('match')
    out = {'items': [shape(*h, fields, 'match' in fields) for h in window], 'page': page, 'per_page': per_page, 'total': total, 'query': q, 'sort': sort}
    if request.args.get('include') == 'facets': out['facets'] = cat.facets(filters, q)
    return jsonify(out)

@bp.get('/characters/<slug>')
def character(slug):
    p = repo.character_profile(get_db(), catalog(), slug)
    if p is None: raise ApiError(404, 'not_found', f"Character '{slug}' does not exist")
    return jsonify(p)

@bp.get('/characters/<slug>/relationships')
def character_relationships(slug):
    p = repo.character_relationships(get_db(), catalog(), slug)
    if p is None: raise ApiError(404, 'not_found', f"Character '{slug}' does not exist")
    return jsonify(p)

@bp.get('/search/suggest')
def suggest():
    q = (request.args.get('q') or '').strip()
    if len(q) < 2: return jsonify({'items': [], 'query': q})
    items = [{'slug': c['slug'], 'name': c['name'], 'mythology': c['mythology'], 'matched': {'on': on, 'text': txt}} for _, c, on, txt in catalog().suggest(q)]
    return jsonify({'items': items, 'query': q})

@bp.get('/mythologies')
def mythologies():
    cat = catalog()
    items = [repo.mythology_detail(get_db(), cat, s) for s in cat.mythologies]
    return jsonify({'items': items, 'total': len(items)})

@bp.get('/mythologies/<slug>')
def mythology(slug):
    m = repo.mythology_detail(get_db(), catalog(), slug)
    if m is None: raise ApiError(404, 'not_found', f"Mythology '{slug}' does not exist")
    return jsonify(m)

@bp.get('/roles')
def roles(): return jsonify({'items': repo.vocab(get_db(), 'role')})

@bp.get('/domains')
def domains(): return jsonify({'items': repo.vocab(get_db(), 'domain')})

@bp.get('/relationship-types')
def relationship_types(): return jsonify({'items': repo.vocab(get_db(), 'relationship_type')})

@bp.get('/sources')
def sources(): return jsonify({'items': repo.sources_list(get_db())})

@bp.get('/stories')
def stories(): return jsonify({'items': repo.stories_list(get_db())})

@bp.get('/stories/<slug>')
def story(slug):
    s = repo.story_detail(get_db(), catalog(), slug)
    if s is None: raise ApiError(404, 'not_found', f"Story '{slug}' does not exist")
    return jsonify(s)

@bp.errorhandler(404)
def _nf(_e): return jsonify({'error': {'code': 'not_found', 'message': 'No such endpoint'}}), 404
