#!/usr/bin/env python3
"""Check that data/ and research/ agree. Run from the repo root.
Usage: python scripts/validate_data.py [--require-verified greek] [--require-summary greek]"""
import json, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]
require = args[args.index('--require-verified') + 1] if '--require-verified' in args else None
require_summary = args[args.index('--require-summary') + 1] if '--require-summary' in args else None
load = lambda n: json.load(open(os.path.join(root, 'data', n + '.json'), encoding='utf-8'))['records']
errors, info = [], []
sources = load('sources'); sid = {}
tier_dir = {'primary': 'primary-sources', 'supplementary': 'supplementary-sources', 'scholarly': 'scholarly-references'}
for s in sources:
    if s['id'] in sid: errors.append(f"duplicate source id {s['id']}")
    sid[s['id']] = s
    for p in s['research_notes']:
        if not os.path.exists(os.path.join(root, p)): errors.append(f"{s['id']}: missing note {p}")
        elif tier_dir[s['tier']] not in p: errors.append(f"{s['id']}: {p} is in the wrong tier folder")
chars = {}
for f in ('deities', 'creatures', 'heroes'):
    for r in load(f):
        if r['id'] in chars: errors.append(f"duplicate character id {r['id']}")
        chars[r['id']] = r
def check_links(name, r):
    if not r.get('sources'): errors.append(f"{name}:{r['id']} has no sources")
    for l in r.get('sources', []):
        s = sid.get(l['source_id'])
        if not s: errors.append(f"{name}:{r['id']} cites unknown source {l['source_id']}"); continue
        if l.get('verified'):
            if not l.get('locator'): errors.append(f"{name}:{r['id']} verified link to {l['source_id']} has no locator")
            if not l.get('claim'): errors.append(f"{name}:{r['id']} verified link to {l['source_id']} has no claim")
            if not s.get('edition_used'): errors.append(f"{name}:{r['id']} verified against {l['source_id']} but the source has no edition_used")
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
stories = load('stories')
for r in stories:
    check_links('stories', r); needs_verified(r)
    for p in r['participants']:
        if p not in chars: errors.append(f"stories:{r['id']} unknown participant {p}")
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
print(f"{len(sources)} sources, {len(chars)} characters, {len(stories)} stories, {len(seen)} relationships")
print('\n'.join(info))
if errors:
    print('\n'.join('ERROR ' + e for e in errors)); sys.exit(1)
print('OK')
