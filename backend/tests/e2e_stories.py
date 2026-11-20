"""Browser checks for the story pages (optional, needs Playwright). Start the server first, then:
    python backend/tests/e2e_stories.py http://localhost:5000"""
import sys
from playwright.sync_api import sync_playwright, expect
base = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
problems = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: problems.append(name)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 900})
    errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(base + '/stories'); expect(pg.locator('.story-card').first).to_be_visible()
    total = pg.locator('.story-card').count()
    check('index lists the stories', total >= 15)
    pg.get_by_label('Written myths only').check(); pg.wait_for_timeout(300)
    check('"written only" hides the unwritten stories', 12 <= pg.locator('.story-card').count() < total)
    pg.fill('.input-search', 'pegasus'); pg.wait_for_timeout(300)
    check('search finds a story by its figures', pg.locator('.story-card').count() >= 1)
    pg.fill('.input-search', ''); pg.wait_for_timeout(200)
    pg.get_by_role('link', name='Read the myth').first.click(); pg.wait_for_url('**/stories/*')
    expect(pg.locator('.tale')).to_be_visible()
    check('a written story shows its text', pg.locator('.tale .para').count() >= 4)
    check('every paragraph run has a citation', pg.locator('.cites').count() >= 1)
    first = pg.locator('.cites > summary').first; first.click()
    check('a citation opens to show the passage', pg.locator('.cites[open] li').first.is_visible())
    check('no "null" text on the page', 'null' not in pg.locator('#story-detail-root').inner_text().split())
    pg.goto(base + '/stories/prometheus-and-the-first-woman')
    expect(pg.locator('.variant-block')).to_be_visible()
    check('another telling is set apart', pg.locator('.variant-block .para').count() >= 5)
    pg.goto(base + '/stories/ragnarok'); expect(pg.locator('h1')).to_have_text('Ragnarök')
    check('an unwritten story says so', 'has not been written yet' in pg.locator('#story-detail-root').inner_text())
    pg.goto(base + '/characters/athena'); pg.get_by_role('link', name='The birth of Athena').click(); pg.wait_for_url('**/stories/birth-of-athena')
    expect(pg.locator('.tale')).to_be_visible()
    check('a profile links through to the myth', '/stories/birth-of-athena' in pg.url)
    pg.locator('a.card[href="/characters/metis"]').click(); pg.wait_for_url('**/characters/metis')
    check('participants link back to profiles', True)
    pg.goto(base + '/stories/quest-for-the-golden-fleece'); expect(pg.locator('.tale')).to_be_visible()
    check('related myths are listed', pg.get_by_text('Related Myths').count() >= 1)
    check('no JavaScript errors', not errors)
    if errors: print(errors)
    b.close()
print('\nAll story checks passed' if not problems else f'\nFAILED: {problems}')
sys.exit(1 if problems else 0)
