"""API and search tests. Run from the repo root:  python -m unittest discover -s backend/tests -t .
They build a throwaway database from data/*.json, so they also check that the data loads."""
import os, tempfile, unittest
from backend.app import create_app
from backend.app.search import norm, distance, score_doc

class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = create_app({'DATABASE': os.path.join(cls.tmp.name, 'test.db'), 'TESTING': True})
        cls.c = cls.app.test_client()
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def get(self, url, status=200):
        r = self.c.get(url); self.assertEqual(r.status_code, status, r.get_data(as_text=True)[:300]); return r.get_json()
    def all_characters(self, query='', fields='slug,name'):
        out, page = [], 1
        while True:
            j = self.get(f'/api/v1/characters?per_page=100&page={page}&fields={fields}' + (('&' + query) if query else ''))
            out += j['items']
            if len(out) >= j['total']: return out
            page += 1

class VocabularyTests(ApiTest):
    def test_mythologies(self):
        j = self.get('/api/v1/mythologies')
        self.assertEqual([m['slug'] for m in j['items']], ['greek', 'norse', 'egyptian'])
        self.assertEqual(sum(m['character_count'] for m in j['items']), self.get('/api/v1/characters')['total'])
    def test_mythology_detail_and_404(self):
        self.assertGreater(self.get('/api/v1/mythologies/greek')['character_count'], 90)
        self.assertEqual(self.get('/api/v1/mythologies/nope', 404)['error']['code'], 'not_found')
    def test_vocabularies(self):
        self.assertIn('god', [r['slug'] for r in self.get('/api/v1/roles')['items']])
        self.assertIn('sea', [r['slug'] for r in self.get('/api/v1/domains')['items']])
        self.assertIn('parent_of', [r['slug'] for r in self.get('/api/v1/relationship-types')['items']])
    def test_sources_and_stories(self):
        self.assertEqual(len(self.get('/api/v1/sources')['items']), 71)
        s = self.get('/api/v1/stories/birth-of-zeus')
        self.assertIn('zeus', [p['slug'] for p in s['participants']])
        self.get('/api/v1/stories/nope', 404)

class ListTests(ApiTest):
    def test_pagination(self):
        a = self.get('/api/v1/characters?per_page=10&page=1'); b = self.get('/api/v1/characters?per_page=10&page=2')
        self.assertEqual((a['per_page'], len(a['items'])), (10, 10))
        self.assertFalse({i['slug'] for i in a['items']} & {i['slug'] for i in b['items']})
        self.assertEqual(self.get('/api/v1/characters?page=999')['items'], [])
    def test_bad_paging_is_400(self):
        for q in ('page=0', 'page=x', 'per_page=0', 'per_page=101'):
            self.assertEqual(self.get('/api/v1/characters?' + q, 400)['error']['code'], 'invalid_parameter')
    def test_sorting(self):
        names = [i['name'] for i in self.all_characters()]
        self.assertEqual(names, sorted(names, key=norm))
        rev = [i['name'] for i in self.all_characters('sort=-name')]
        self.assertEqual(rev, names[::-1])
        self.get('/api/v1/characters?sort=bogus', 400)
    def test_filters_and(self):
        greek = self.get('/api/v1/characters?mythology=greek&per_page=100')
        self.assertTrue(all(i['mythology']['slug'] == 'greek' for i in greek['items']))
        sea = self.get('/api/v1/characters?mythology=greek&role=god&domain=sea')
        self.assertEqual({i['slug'] for i in sea['items']}, {'poseidon', 'pontus', 'nereus', 'phorcys', 'triton'})
        self.assertTrue(all('sea' in i['domains'] and 'god' in i['roles'] for i in sea['items']))
        self.assertEqual(self.get('/api/v1/characters?mythology=norse&domain=sea')['total'], 0)
    def test_filters_or_within_one_filter(self):
        both = self.get('/api/v1/characters?mythology=greek,norse')['total']
        self.assertEqual(both, self.get('/api/v1/characters?mythology=greek')['total'] + self.get('/api/v1/characters?mythology=norse')['total'])
        self.assertEqual(both, self.get('/api/v1/characters?mythology=greek&mythology=norse')['total'])
    def test_unknown_filter_value(self):
        self.assertEqual(self.get('/api/v1/characters?role=wizard', 400)['error']['code'], 'unknown_filter_value')
    def test_fields(self):
        i = self.get('/api/v1/characters?fields=slug,name&per_page=1')['items'][0]
        self.assertEqual(set(i), {'slug', 'name'})
        self.get('/api/v1/characters?fields=password', 400)
    def test_facets_never_hide_own_alternatives(self):
        f = self.get('/api/v1/characters?mythology=greek&include=facets')['facets']
        self.assertEqual({m['value'] for m in f['mythology']}, {'greek', 'norse', 'egyptian'})
        self.assertEqual(sum(m['count'] for m in f['mythology']), self.get('/api/v1/characters')['total'])

class SearchTests(ApiTest):
    def first(self, q): return self.get('/api/v1/characters?q=' + q)['items']
    def test_exact_alias_typo_accent(self):
        self.assertEqual(self.first('Zeus')[0]['slug'], 'zeus')
        self.assertEqual(self.first('zues')[0]['slug'], 'zeus')            # transposition
        self.assertEqual(self.first('Cytherea')[0]['slug'], 'aphrodite')   # alias
        self.assertEqual(self.first('Cytherea')[0]['match']['on'], 'alias')
        self.assertEqual(self.first('jormungandr')[0]['slug'], 'jormungandr')  # no diacritics typed
        self.assertEqual(self.first('Jörmungandr')[0]['slug'], 'jormungandr')
    def test_multiword_and_text(self):
        self.assertEqual(self.first('lernaean hydra')[0]['slug'], 'hydra')
        self.assertIn('poseidon', [i['slug'] for i in self.first('sea')])
    def test_name_beats_text_match(self):
        r = self.first('hera'); self.assertEqual(r[0]['slug'], 'hera')
    def test_no_match(self):
        self.assertEqual(self.get('/api/v1/characters?q=qqqqzzzz')['total'], 0)
    def test_filters_apply_to_search(self):
        self.assertEqual(self.get('/api/v1/characters?q=zeus&mythology=norse')['total'], 0)
    def test_suggest(self):
        self.assertEqual(self.get('/api/v1/search/suggest?q=a')['items'], [])  # needs two characters
        s = self.get('/api/v1/search/suggest?q=cyth')['items']
        self.assertEqual((s[0]['slug'], s[0]['matched']['on']), ('aphrodite', 'alias'))

class ProfileTests(ApiTest):
    def test_profile_shape(self):
        z = self.get('/api/v1/characters/zeus')
        self.assertEqual(z['mythology']['slug'], 'greek')
        self.assertGreater(len(z['sources']), 10)
        for l in z['sources']:
            self.assertIn(l['source']['tier'], ('primary', 'supplementary', 'scholarly'))
            if l['verified']: self.assertTrue(l['locator'] and l['claim'])
        self.assertEqual([g['group'] for g in z['relationships']][:2], ['Parents', 'Children'])
    def test_sources_sorted_by_tier_then_locator(self):
        z = self.get('/api/v1/characters/zeus')['sources']
        order = {'primary': 0, 'supplementary': 1, 'scholarly': 2}
        tiers = [order[l['source']['tier']] for l in z]; self.assertEqual(tiers, sorted(tiers))
    def test_relationships_are_symmetric(self):
        # If A lists B, B must list A.
        names = [i['slug'] for i in self.all_characters(fields='slug')]
        seen = {}
        for s in names:
            seen[s] = {i['other']['slug'] for g in self.get(f'/api/v1/characters/{s}/relationships')['groups'] for i in g['items']}
        for a, others in seen.items():
            for b in others: self.assertIn(a, seen[b], f'{a} lists {b} but not the other way round')
    def test_direction_labels(self):
        z = {g['group']: [i['other']['slug'] for i in g['items']] for g in self.get('/api/v1/characters/zeus')['relationships']}
        self.assertIn('cronus', z['Parents']); self.assertIn('athena', z['Children'])
        h = {g['group']: [i['other']['slug'] for i in g['items']] for g in self.get('/api/v1/characters/hydra')['relationships']}
        self.assertIn('heracles', h['Slain by'])
    def test_variant_is_kept(self):
        a = self.get('/api/v1/characters/aphrodite')
        self.assertIn('variant', {l['relation'] for l in a['sources']})
    def test_404(self):
        self.assertEqual(self.get('/api/v1/characters/nobody', 404)['error']['code'], 'not_found')
        self.get('/api/v1/characters/nobody/relationships', 404)
        self.assertEqual(self.get('/api/v1/nothing', 404)['error']['code'], 'not_found')

class SummaryTests(ApiTest):
    def greek(self): return self.all_characters('mythology=greek', 'slug,summary')
    def test_every_greek_character_has_a_summary(self):
        self.assertEqual(len(self.greek()), self.get('/api/v1/mythologies/greek')['character_count'])
        self.assertGreater(len(self.greek()), 90)
        self.assertTrue(all(i['summary'] and len(i['summary']) > 40 for i in self.greek()))
    def test_unchecked_mythologies_have_none(self):
        items = self.all_characters('mythology=norse,egyptian', 'slug,summary')
        self.assertTrue(all(i['summary'] is None for i in items))
    def test_profile_summary_rests_on_verified_passages(self):
        for slug in ('zeus', 'hestia', 'jason', 'cerberus'):
            p = self.get(f'/api/v1/characters/{slug}')
            self.assertTrue(p['summary']); self.assertGreaterEqual(len(p['summary_basis']), 1)
            self.assertTrue(all(b['verified'] and b['locator'] and b['claim'] for b in p['summary_basis']))
            own = {(s['source']['slug'], s['locator']) for s in p['sources']}
            self.assertTrue(all((b['source']['slug'], b['locator']) in own for b in p['summary_basis']))
    def test_summary_text_is_searchable(self):
        self.assertIn('hydra', [i['slug'] for i in self.get('/api/v1/characters?q=nine-headed')['items']])
    def test_description_meta_uses_summary(self):
        html = self.c.get('/characters/hestia').get_data(as_text=True)
        self.assertIn('first-named child of Cronus and Rhea', html)

class NewEntityTests(ApiTest):
    def rels(self, slug): return {g['group']: [i['other']['slug'] for i in g['items']] for g in self.get(f'/api/v1/characters/{slug}')['relationships']}
    def test_family_trees_run_through_the_titans(self):
        self.assertTrue({'gaia', 'uranus'} <= set(self.rels('oceanus')['Parents']))
        self.assertIn('metis', self.rels('athena')['Parents'])
        self.assertTrue({'hyperion', 'theia'} <= set(self.rels('helios')['Parents']))
        self.assertTrue({'helios', 'perseis'} <= set(self.rels('circe')['Parents']))
    def test_the_fates_have_both_parentages(self):
        m = self.get('/api/v1/characters/moerae')
        self.assertTrue({'nyx', 'zeus', 'themis'} <= {i['other']['slug'] for g in m['relationships'] for i in g['items']})
        self.assertIn('variant', {l['relation'] for l in m['sources']})
    def test_jason_and_odysseus_are_still_connected(self):
        self.assertIn('circe', self.rels('odysseus')['Lovers'])
    def test_no_unchecked_greek_link(self):
        for c in self.all_characters('mythology=greek', 'slug'):
            p = self.get('/api/v1/characters/' + c['slug'])
            self.assertTrue(all(s['verified'] for s in p['sources']), c['slug'])
    def test_search_finds_new_entities(self):
        self.assertEqual(self.get('/api/v1/characters?q=pegassus')['items'][0]['slug'], 'pegasus')   # typo
        self.assertEqual(self.get('/api/v1/characters?q=Hecatoncheires')['items'][0]['slug'], 'hundred-handers')  # alias
        self.assertEqual(self.get('/api/v1/characters?q=tartarus')['items'][0]['slug'], 'tartarus')

class PageTests(ApiTest):
    def test_pages_render(self):
        for url in ('/', '/characters', '/characters/zeus', '/mythologies/greek',
                    '/sources', '/sources/gr-theogony', '/stories', '/stories/birth-of-zeus', '/graph'):
            self.assertEqual(self.c.get(url).status_code, 200, url)
    def test_clean_url_has_meta(self):
        html = self.c.get('/characters/zeus').get_data(as_text=True)
        self.assertIn('<title>Zeus (Greek) | Mythos</title>', html); self.assertIn('name="description"', html)
    def test_missing_page_404(self):
        self.assertEqual(self.c.get('/characters/nobody').status_code, 404)
        self.assertEqual(self.c.get('/mythologies/atlantis').status_code, 404)
        self.assertEqual(self.c.get('/sources/nobody').status_code, 404)
        self.assertEqual(self.c.get('/stories/nobody').status_code, 404)

class SearchUnitTests(unittest.TestCase):
    def test_norm(self): self.assertEqual(norm('Völuspá'), 'voluspa'); self.assertEqual(norm('Þrymskviða'), 'thrymskvida')
    def test_distance(self):
        self.assertEqual(distance('zeus', 'zues'), 1); self.assertEqual(distance('zeus', 'zeus'), 0); self.assertEqual(distance('abc', 'abcdef'), 3)
    def test_score_requires_every_token(self):
        doc = dict(name='Lernaean Hydra', aliases=[], text='')
        self.assertIsNotNone(score_doc('lernaean hydra', doc)); self.assertIsNone(score_doc('lernaean zeus', doc))

if __name__ == '__main__': unittest.main()
