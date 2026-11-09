#!/usr/bin/env python3
"""Rebuild 'Key passages' and 'Records linked' in every research note from data/*.json.
Run from the repo root after editing data. Never edit those two sections by hand."""
import json, os, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load = lambda n: json.load(open(os.path.join(root, 'data', n + '.json'), encoding='utf-8'))['records']
sources = {s['id']: s for s in load('sources')}
by = {}
for fn in ('deities', 'creatures', 'heroes', 'stories', 'relationships'):
    for r in load(fn):
        for l in r['sources']: by.setdefault(l['source_id'], []).append((fn, r['id'], l))
num = lambda loc: int(re.search(r'\d+', loc).group()) if loc and re.search(r'\d+', loc) else 10**9
def section(title, body): return f"## {title}\n{body}\n"
for sid, s in sources.items():
    rows = by.get(sid, [])
    ver = sorted([x for x in rows if x[2].get('verified')], key=lambda x: num(x[2]['locator']))
    tbl = "| Locator | What it attests | Record |\n|---|---|---|\n" + ''.join(
        f"| {l['locator']} | {l['claim']}{' (' + l['note'] + ')' if l.get('note') else ''} | `{fn}:{i}` |\n" for fn, i, l in ver) if ver else \
        "| Locator | What it attests | Record |\n|---|---|---|\n|  |  |  |\n"
    linked = ''.join(f"- `{fn}:{i}` ({'verified' if l.get('verified') else 'unverified'})\n" for fn, i, l in sorted(rows, key=lambda x: (x[0], x[1]))) or "_None yet._\n"
    for path in s['research_notes']:
        p = os.path.join(root, path); t = open(p, encoding='utf-8').read()
        if 'status: pointer' in t: continue
        parts = re.split(r'(?m)^(?=## )', t)
        out = []
        for part in parts:
            if part.startswith('## Key passages'): part = section('Key passages', tbl)
            elif part.startswith('## Records linked'): part = section('Records linked to this source', linked)
            elif part.startswith('## Edition and translation used') and s.get('edition_used'):
                part = section('Edition and translation used', f"{s['edition_used']}  \n{s['url']}  \n" + (f"{s['edition_note']}  \n" if s.get('edition_note') else '') + f"Licence: {s['license']}\n")
            out.append(part if part.endswith('\n') else part + '\n')
        t2 = ''.join(out)
        t2 = re.sub(r'(?m)^status: .*$', f"status: {s['status']}", t2, count=1)
        open(p, 'w', encoding='utf-8').write(t2)
print('notes refreshed')
