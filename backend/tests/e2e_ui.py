"""Browser checks with Playwright (optional). Start the server first:  PORT=5055 python backend/run.py
Then:  python backend/tests/e2e_ui.py http://localhost:5055"""
import sys
import json, urllib.request
from playwright.sync_api import sync_playwright, expect
base = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5055'
problems = []
def count(query=''): return json.load(urllib.request.urlopen(f'{base}/api/v1/characters?per_page=1&fields=slug&{query}'))['total']
TOTAL, NORSE, MONSTERS, NORSE_MONSTERS = count(), count('mythology=norse'), count('role=monster'), count('mythology=norse&role=monster')
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: problems.append(name)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 900})
    js_errors = []; pg.on('pageerror', lambda e: js_errors.append(str(e)))
    pg.goto(base + '/characters'); expect(pg.locator('#count')).to_have_text(f'{TOTAL} characters')
    # filter by checkbox updates results, facets and URL
    pg.get_by_label('Norse', exact=False).first.check()
    expect(pg.locator('#count')).to_have_text(f'{NORSE} characters')
    check('filter updates URL', 'mythology=norse' in pg.url)
    check('active chip shown', pg.locator('#active button').count() == 1)
    # combine filters, then remove the chip
    pg.get_by_label('Monster').check(); expect(pg.locator('#count')).to_have_text(f'{NORSE_MONSTERS} characters')
    pg.locator('#active button').first.click()
    expect(pg.locator('#count')).not_to_have_text(f'{NORSE_MONSTERS} characters')   # waits for the reload
    check('removing a chip widens results', pg.locator('#count').inner_text() == f'{MONSTERS} characters')  # monsters of every mythology
    # back button restores previous state
    pg.go_back(); pg.wait_for_timeout(400)
    check('back button restores filters', 'mythology=norse' in pg.url and 'role=monster' in pg.url)
    # search + typo + clear
    pg.goto(base + '/characters'); pg.fill('#q', 'zues'); pg.press('#q', 'Enter')
    expect(pg.locator('#count')).to_contain_text('1 character for')
    check('typo search finds Zeus', pg.locator('.card h3').first.inner_text() == 'Zeus')
    pg.click('#clear'); expect(pg.locator('#count')).to_have_text(f'{TOTAL} characters')
    # pagination
    pg.get_by_role('link', name='2', exact=True).click(); expect(pg.locator('#count')).to_have_text(f'{TOTAL} characters')
    check('page 2 in URL', 'page=2' in pg.url)
    # autocomplete with keyboard
    pg.goto(base + '/characters'); pg.fill('#q', 'cyth')
    expect(pg.locator('#q-list li').first).to_be_visible()
    pg.press('#q', 'ArrowDown'); pg.press('#q', 'Enter'); pg.wait_for_url('**/characters/aphrodite')
    check('autocomplete navigates to profile', True)
    # profile
    expect(pg.locator('h1')).to_have_text('Aphrodite')
    check('variant badge visible', pg.locator('.badge.var').count() >= 1)
    check('checked badge visible', pg.locator('.badge.ok').count() >= 3)
    pg.goto(base + '/characters/zeus'); pg.get_by_role('link', name='Cronus').first.click(); pg.wait_for_url('**/characters/cronus')
    check('relationship link navigates', True)
    pg.goto(base + '/characters/nobody'); check('missing character shows 404 page', 'no character called' in pg.content())
    # header search on a profile page
    pg.goto(base + '/characters/zeus'); pg.fill('#hs', 'athe'); expect(pg.locator('#hs-list li').first).to_be_visible()
    # mythology page and home
    pg.goto(base + '/mythologies/egyptian'); expect(pg.locator('h1')).to_have_text('Egyptian mythology')
    pg.goto(base + '/'); expect(pg.locator('.myth-card')).to_have_count(3)
    pg.click('#random'); pg.wait_for_url('**/characters/*')
    check('random character works', '/characters/' in pg.url)
    check('no JavaScript errors', not js_errors)
    if js_errors: print(js_errors)
    b.close()
print('\nAll browser checks passed' if not problems else f'\nFAILED: {problems}')
sys.exit(1 if problems else 0)
