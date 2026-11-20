#!/usr/bin/env python3
"""Check that data/ and research/ agree. Run from the repo root.
Usage: python scripts/validate_data.py [--require-verified greek] [--require-summary greek] [--require-story-text greek]"""
import json, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]
require = args[args.index('--require-verified') + 1] if '--require-verified' in args else None
require_summary = args[args.index('--require-summary') + 1] if '--require-summary' in args else None
require_story = args[args.index('--require-story-text') + 1] if '--require-story-text' in args else None
load = lambda n: json.load(open(os.path.join(root, 'data', n + '.json'), encoding='utf-8'))['records']
errors, info = [], []

VALID_MYTHOLOGIES = {'greek', 'norse', 'egyptian'}
VALID_TRADITIONS = {
    'egyptian': {'heliopolitan', 'hermopolitan', 'memphite', 'theban', 'esna'},
    'greek': {'hesiodic', 'homeric', 'orphic', 'eleusinian'},
    'norse': {'eddic', 'skaldic'}
}

sources = load('sources'); sid = {}
tier_dir = {'primary': 'primary-sources', 'supplementary': 'supplementary-sources', 'scholarly': 'scholarly-references'}
source_cites = {s['id']: 0 for s in sources}

for s in sources:
    if s['id'] in sid: errors.append(f"duplicate source id {s['id']}")
    sid[s['id']] = s
    for m in s.get('mythology', []):
        if m not in VALID_MYTHOLOGIES: errors.append(f"{s['id']}: invalid mythology '{m}'")
    for p in s['research_notes']:
        if not os.path.exists(os.path.join(root, p)): errors.append(f"{s['id']}: missing note {p}")
        elif tier_dir[s['tier']] not in p: errors.append(f"{s['id']}: {p} is in the wrong tier folder")

chars = {}
for f in ('deities', 'creatures', 'heroes'):
    for r in load(f):
        if r['id'] in chars: errors.append(f"duplicate character id {r['id']}")
        chars[r['id']] = r
        m = r.get('mythology')
        if m not in VALID_MYTHOLOGIES: errors.append(f"{f}:{r['id']} has invalid mythology '{m}'")
        trad = r.get('tradition')
        if trad and m in VALID_TRADITIONS and trad not in VALID_TRADITIONS[m]:
            errors.append(f"{f}:{r['id']} unknown tradition '{trad}' for {m}")

def check_links(name, r):
    if not r.get('sources'): errors.append(f"{name}:{r['id']} has no sources")
    for l in r.get('sources', []):
        source_id = l.get('source_id')
        s = sid.get(source_id)
        if not s:
            errors.append(f"{name}:{r['id']} cites unknown source {source_id}")
            continue
        source_cites[source_id] = source_cites.get(source_id, 0) + 1
        if l.get('verified'):
            if not l.get('locator'): errors.append(f"{name}:{r['id']} verified link to {source_id} has no locator")
            if not l.get('claim'): errors.append(f"{name}:{r['id']} verified link to {source_id} has no claim")
            if not s.get('edition_used'): errors.append(f"{name}:{r['id']} verified against {source_id} but the source has no edition_used")

def check_summary(r):
    s, basis = r.get('summary'), r.get('summary_basis', [])
    if require_summary and r.get('mythology') == require_summary and not s: errors.append(f"{r['id']} ({require_summary}) has no summary")
    if not s:
        if basis: errors.append(f"{r['id']} has summary_basis but no summary")
        return
    if not basis: errors.append(f"{r['id']} has a summary with no summary_basis")
    verified = {(l['source_id'], l['locator']) for l in r['sources'] if l.get('verified')}
    for b in basis:
        if (b['source_id'], b['locator']) not in verified: errors.append(f"{r['id']}: summary basis {b['source_id']} {b['locator']} is not a verified link")
    used = {(b['source_id'], b['locator']) for b in basis}
    if len(used) < 2 and len(s) > 120: errors.append(f"{r['id']}: a long summary should rest on at least two passages")
    if not (40 <= len(s) <= 700): errors.append(f"{r['id']}: summary length {len(s)} is outside 40-700 characters")

def needs_verified(r):
    if require and r.get('mythology') == require and not any(l.get('verified') for l in r['sources']):
        errors.append(f"{r['id']} ({require}) has no verified source link")

for f in ('deities', 'creatures', 'heroes'):
    for r in load(f): check_links(f, r); needs_verified(r); check_summary(r)

import re
def _pid(p): return (p.get('character_id') or p.get('id') or p.get('character')) if isinstance(p, dict) else p
def _names(c):
    out = {re.sub(r'\s*\(.*\)', '', c['name']).strip()} | set(c.get('aliases', []))
    out |= {n[4:] for n in list(out) if n.lower().startswith('the ')}
    return {n.lower() for n in out if len(n) > 2}
def check_story(r):
    """A written myth (a `body`) must be traceable: every paragraph rests on verified passages of the story, every participant is named."""
    body, summary = r.get('body', []), r.get('summary')
    if require_story and r['mythology'] == require_story and not body: errors.append(f"story {r['id']} ({require_story}) has no written text")
    if not body: return
    if not summary or not (60 <= len(summary) <= 420): errors.append(f"story {r['id']}: needs a summary of 60-420 characters")
    verified = {(l['source_id'], l['locator']) for l in r['sources'] if l.get('verified')}
    words = sum(len(p['text'].split()) for p in body)
    if words < 180: errors.append(f"story {r['id']}: only {words} words; a written myth needs at least 180")
    if body[0].get('kind', 'narrative') != 'narrative': errors.append(f"story {r['id']}: the first paragraph must be narrative")
    for i, p in enumerate(body, 1):
        if p.get('kind', 'narrative') not in ('narrative', 'variant', 'note'): errors.append(f"story {r['id']} paragraph {i}: unknown kind")
        if len(p['text']) < 60: errors.append(f"story {r['id']} paragraph {i}: too short")
        if not p.get('basis'): errors.append(f"story {r['id']} paragraph {i}: no basis")
        for b in p.get('basis', []):
            if (b['source_id'], b['locator']) not in verified: errors.append(f"story {r['id']} paragraph {i}: basis {b['source_id']} {b['locator']} is not a verified link of the story")
    text = ' '.join(p['text'] for p in body).lower()
    for part in r.get('participants', []):
        c = chars.get(_pid(part))
        if c and not any(n in text for n in _names(c)): errors.append(f"story {r['id']}: participant {_pid(part)} is never named in the text")
    used = {(b['source_id'], b['locator']) for p in body for b in p.get('basis', [])}
    for l in r['sources']:
        if l.get('verified') and (l['source_id'], l['locator']) not in used: errors.append(f"story {r['id']}: verified link {l['source_id']} {l['locator']} is not used by any paragraph")
    if r.get('locations') is not None and not isinstance(r['locations'], list): errors.append(f"story {r['id']}: locations must be a list")
    for loc in r.get('locations', []):
        if loc.lower() not in text: errors.append(f"story {r['id']}: location '{loc}' is never named in the text")
stories = load('stories')
for r in stories:
    check_links('stories', r); needs_verified(r)
    m = r.get('mythology')
    if m not in VALID_MYTHOLOGIES: errors.append(f"stories:{r['id']} has invalid mythology '{m}'")
    trad = r.get('tradition')
    if trad and m in VALID_TRADITIONS and trad not in VALID_TRADITIONS[m]:
        errors.append(f"stories:{r['id']} unknown tradition '{trad}' for {m}")
    for p in r.get('participants', []):
        p_id = p.get('character_id') or p.get('id') or p.get('character') if isinstance(p, dict) else p
        if p_id not in chars: errors.append(f"stories:{r['id']} unknown participant {p_id}")
    check_story(r)

seen, edges = set(), {}
for r in load('relationships'):
    check_links('relationships', r)
    for k in ('source', 'target'):
        if r[k] not in chars: errors.append(f"relationships:{r['id']} unknown {k} {r[k]}")
    if r['source'] == r['target']: errors.append(f"relationships:{r['id']} links a character to itself")
    key = (r['source'], r['target'], r['type'])
    if key in seen: errors.append(f"relationships:{r['id']} duplicates {key}")
    seen.add(key)
    edges.setdefault(r['source'], set()).add(r['target']); edges.setdefault(r['target'], set()).add(r['source'])
    if require:
        ms = {chars[r[k]]['mythology'] for k in ('source', 'target') if r[k] in chars}
        if require in ms and not any(l.get('verified') for l in r['sources']):
            errors.append(f"relationships:{r['id']} has no verified source link")

if require:
    ids = [i for i, c in chars.items() if c['mythology'] == require]
    left, comps = set(ids), []
    while left:
        stack = [left.pop()]; comp = set(stack)
        while stack:
            for n in edges.get(stack.pop(), ()):
                if n in left: left.discard(n); comp.add(n); stack.append(n)
        comps.append(sorted(comp))
    comps.sort(key=len, reverse=True)
    info.append(f"{require}: {len(ids)} characters in {len(comps)} connected group(s); largest has {len(comps[0])}")
    for c in comps[1:]: info.append(f"  not yet connected: {', '.join(c)}")

uncited = [sid for sid, c in source_cites.items() if c == 0]
if uncited:
    info.append(f"Note: {len(uncited)} sources currently catalogued without direct link in data/*.json (seed corpus).")

print(f"{len(sources)} sources, {len(chars)} characters, {len(stories)} stories, {len(seen)} relationships")
print('\n'.join(info))
if errors:
    print('\n'.join('ERROR ' + e for e in errors)); sys.exit(1)
print('OK')
