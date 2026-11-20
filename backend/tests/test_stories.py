"""Written myths: data rules, API shape and pages. Run: python -m unittest discover -s backend/tests -t ."""
import json, os, re, tempfile, unittest
from backend.app import create_app

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = create_app({'DATABASE': os.path.join(cls.tmp.name, 't.db'), 'TESTING': True}); cls.c = cls.app.test_client()
        cls.stories = {s['slug']: s for s in cls.get('/api/v1/stories')['items']}
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    @classmethod
    def get(cls, url, status=200):
        r = cls.c.get(url); assert r.status_code == status, (url, r.status_code); return r.get_json()

    def test_every_greek_story_is_written(self):
        greek = [s for s in self.stories.values() if s['mythology']['slug'] == 'greek']
        self.assertGreaterEqual(len(greek), 12)
        self.assertTrue(all(s['status'] == 'written' and s['reading_minutes'] >= 1 for s in greek))

    def test_unchecked_mythologies_stay_unwritten(self):
        for slug in ('ragnarok', 'thor-and-the-serpent', 'contendings-of-horus-and-seth'):
            s = self.get(f'/api/v1/stories/{slug}')
            self.assertEqual((s['status'], s['paragraphs'], s['reading_minutes']), ('unwritten', [], 0))

    def test_every_paragraph_rests_on_verified_passages_of_that_story(self):
        for slug, meta in self.stories.items():
            s = self.get(f'/api/v1/stories/{slug}')
            own = {(l['source']['slug'], l['locator']) for l in s['sources']}
            for i, p in enumerate(s['paragraphs'], 1):
                self.assertTrue(p['basis'], f'{slug} paragraph {i} has no basis')
                for b in p['basis']:
                    self.assertTrue(b['verified'] and b['claim'] and b['locator'], f'{slug} {i}')
                    self.assertIn((b['source']['slug'], b['locator']), own)
            if s['paragraphs']: self.assertEqual(s['paragraphs'][0]['kind'], 'narrative')

    def test_every_participant_is_named_in_the_text(self):
        for slug in self.stories:
            s = self.get(f'/api/v1/stories/{slug}')
            if not s['paragraphs']: continue
            text = ' '.join(p['text'] for p in s['paragraphs']).lower()
            for part in s['participants']:
                c = self.get(f"/api/v1/characters/{part['slug']}")
                names = {re.sub(r'\s*\(.*\)', '', c['name']).strip().lower()} | {a.lower() for a in c['aliases']}
                names |= {n[4:] for n in names if n.startswith('the ')}
                self.assertTrue(any(n in text for n in names if len(n) > 2), f"{slug}: {part['slug']} never named")
                self.assertTrue(part['role'], f"{slug}: {part['slug']} has no role")

    def test_places_appear_in_the_text(self):
        s = self.get('/api/v1/stories/quest-for-the-golden-fleece')
        text = ' '.join(p['text'] for p in s['paragraphs'])
        self.assertIn('Colchis', s['locations']); self.assertTrue(all(l in text for l in s['locations']))

    def test_variants_are_kept_and_marked(self):
        s = self.get('/api/v1/stories/prometheus-and-the-first-woman')
        kinds = [p['kind'] for p in s['paragraphs']]
        self.assertIn('variant', kinds); self.assertEqual(kinds[0], 'narrative')
        self.assertIn('gr-works-and-days', {b['source']['slug'] for p in s['paragraphs'] if p['kind'] == 'variant' for b in p['basis']})
        a = self.get('/api/v1/stories/birth-of-athena')
        self.assertIn('variant', [p['kind'] for p in a['paragraphs']])

    def test_related_stories_share_figures(self):
        s = self.get('/api/v1/stories/yoking-of-the-bronze-bulls')
        self.assertIn('quest-for-the-golden-fleece', [r['slug'] for r in s['related']])
        self.assertTrue(all(r['shared'] for r in s['related']))

    def test_profile_and_mythology_carry_story_status(self):
        z = self.get('/api/v1/characters/zeus')['stories']
        self.assertTrue(z and all(x['status'] in ('written', 'unwritten') for x in z))
        m = self.get('/api/v1/mythologies/greek')
        self.assertTrue(all(x['status'] == 'written' for x in m['stories']))

    def test_cast_lists_main_figures_first(self):
        hydra = self.stories['the-lernaean-hydra']['cast']
        self.assertEqual(hydra[0]['slug'], 'heracles')

    def test_story_text_is_searchable(self):
        r = self.get('/api/v1/search?q=pomegranate')
        self.assertIn('abduction-of-persephone', [x.get('slug') for x in r.get('stories', r.get('items', []))])

    def test_pages(self):
        self.assertEqual(self.c.get('/stories/titanomachy').status_code, 200)
        html = self.c.get('/stories/titanomachy').get_data(as_text=True)
        self.assertIn('Titanomachy', html) if 'Titanomachy' in html else self.assertIn('titanomachy', html)
        self.assertEqual(self.c.get('/stories/nonexistent').status_code, 404)

if __name__ == '__main__': unittest.main()
