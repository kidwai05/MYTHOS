"""Text search: accent-insensitive, typo-tolerant, ranked. Pure Python so it is easy to test.
For thousands of characters swap this for SQLite FTS5 / PostgreSQL trigram search behind the same interface."""
import re, unicodedata

def norm(s):
    s = (s or '').replace('Þ', 'Th').replace('þ', 'th').replace('ð', 'd').replace('Ð', 'D').replace('æ', 'ae')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

def tokens(s): return norm(s).split()

def distance(a, b):
    """Optimal string alignment distance (Levenshtein plus adjacent transpositions)."""
    if abs(len(a) - len(b)) > 2: return 3
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1): d[i][0] = i
    for j in range(len(b) + 1): d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]

def token_score(qt, targets, fuzzy=True):
    """Best score (0..1) of a query token against a list of target tokens."""
    best = 0.0
    for t in targets:
        if qt == t: return 1.0
        if len(qt) >= 2 and t.startswith(qt): best = max(best, 0.85)
        elif len(qt) >= 3 and qt in t: best = max(best, 0.55)
        elif fuzzy and len(qt) >= 4 and len(t) >= 3:
            dist = distance(qt, t)
            if dist <= 1 or (len(qt) >= 7 and dist <= 2): best = max(best, 0.7 if dist <= 1 else 0.6)
        # a prefix of the target within one typo ("zeu" vs "zeus" handled by startswith; "zues" handled by distance)
    return best

FIELD_WEIGHT = {'name': 1.0, 'alias': 0.9, 'text': 0.3}

def score_doc(q, doc):
    """doc: {'name': str, 'aliases': [str], 'text': str}. Returns (score, matched_on, matched_text) or None.
    Every query token must match something; the score is the mean of the best field score per token."""
    qts = tokens(q)
    if not qts: return None
    name_t = tokens(doc['name'])
    alias_t = [(a, tokens(a)) for a in doc['aliases']]
    text_t = set(tokens(doc['text']))
    total, matched_on, matched_text = 0.0, 'name', doc['name']
    for qt in qts:
        opts = [(token_score(qt, name_t) * FIELD_WEIGHT['name'], 'name', doc['name'])]
        for a, at in alias_t: opts.append((token_score(qt, at) * FIELD_WEIGHT['alias'], 'alias', a))
        opts.append((token_score(qt, text_t, fuzzy=False) * FIELD_WEIGHT['text'], 'text', None))
        s, on, txt = max(opts, key=lambda o: o[0])
        if s <= 0: return None
        total += s
        if on != 'name' and matched_on == 'name': matched_on, matched_text = on, txt
    score = total / len(qts)
    nq = ' '.join(qts)
    if norm(doc['name']) == nq: score += 0.5
    elif norm(doc['name']).startswith(nq): score += 0.2
    for a in doc['aliases']:
        if norm(a) == nq: score += 0.4; matched_on, matched_text = 'alias', a; break
    return score, matched_on, matched_text
