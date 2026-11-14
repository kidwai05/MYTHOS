"""Tests for enhanced MYTHOS features: traditions, source passages, graph endpoints, stories, and unified search."""
import os, tempfile, unittest
from backend.app import create_app

class EnhancedApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = create_app({'DATABASE': os.path.join(cls.tmp.name, 'test.db'), 'TESTING': True})
        cls.c = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def get(self, url, status=200):
        r = self.c.get(url)
        self.assertEqual(r.status_code, status, r.get_data(as_text=True)[:300])
        return r.get_json()

class TraditionTests(EnhancedApiTest):
    def test_osiris_tradition_persisted(self):
        o = self.get('/api/v1/characters/osiris')
        self.assertIsNotNone(o['tradition'])
        self.assertEqual(o['tradition']['slug'], 'heliopolitan')
        self.assertEqual(o['tradition']['name'], 'Heliopolitan')

    def test_tradition_list_and_detail(self):
        trads = self.get('/api/v1/traditions')['items']
        slugs = [t['slug'] for t in trads]
        self.assertIn('heliopolitan', slugs)
        self.assertIn('memphite', slugs)
        self.assertIn('theban', slugs)

        det = self.get('/api/v1/traditions/heliopolitan')
        self.assertEqual(det['slug'], 'heliopolitan')
        self.assertEqual(det['mythology']['slug'], 'egyptian')
        self.assertIn('osiris', [c['slug'] for c in det['characters']])

    def test_tradition_filter(self):
        res = self.get('/api/v1/characters?tradition=heliopolitan')
        self.assertGreaterEqual(res['total'], 1)
        self.assertEqual(res['items'][0]['slug'], 'osiris')

    def test_tradition_404(self):
        self.assertEqual(self.get('/api/v1/traditions/nonexistent', 404)['error']['code'], 'not_found')

class PassageAndSourceTests(EnhancedApiTest):
    def test_source_detail(self):
        s = self.get('/api/v1/sources/gr-theogony')
        self.assertEqual(s['slug'], 'gr-theogony')
        self.assertEqual(s['status'], 'verified')
        self.assertGreater(s['counts']['passages'], 50)
        self.assertGreater(s['counts']['characters'], 50)
        self.assertTrue(any(c['slug'] == 'zeus' for c in s['characters_mentioned']))

    def test_source_passages_list(self):
        sp = self.get('/api/v1/sources/gr-theogony/passages')
        self.assertEqual(sp['source']['slug'], 'gr-theogony')
        self.assertGreater(len(sp['passages']), 10)
        p = sp['passages'][0]
        self.assertIn('locator', p)
        self.assertIn('verified', p)

    def test_passage_detail(self):
        sp = self.get('/api/v1/sources/gr-theogony/passages')
        pid = sp['passages'][0]['id']
        p = self.get(f'/api/v1/passages/{pid}')
        self.assertEqual(p['id'], pid)
        self.assertEqual(p['source']['slug'], 'gr-theogony')
        self.assertIn('supported_entities', p)

    def test_source_and_passage_404(self):
        self.get('/api/v1/sources/unknown-source', 404)
        self.get('/api/v1/sources/unknown-source/passages', 404)
        self.get('/api/v1/passages/999999', 404)

class GraphTests(EnhancedApiTest):
    def test_character_graph_structure(self):
        g = self.get('/api/v1/characters/zeus/graph')
        self.assertEqual(g['root'], 'c:zeus')
        self.assertGreater(len(g['nodes']), 5)
        self.assertGreater(len(g['edges']), 5)
        self.assertIn('counts', g)

        root_node = next(n for n in g['nodes'] if n['id'] == 'c:zeus')
        self.assertEqual(root_node['slug'], 'zeus')
        self.assertTrue(root_node['is_root'])
        self.assertEqual(root_node['degree'], 0)

    def test_graph_edge_evidence(self):
        g = self.get('/api/v1/characters/zeus/graph')
        # Check that edges include type, category, label, and evidence
        for edge in g['edges']:
            self.assertIn('type', edge)
            self.assertIn('category', edge)
            self.assertIn('label', edge)
            self.assertIn('evidence', edge)
            if edge['category'] != 'narrative':
                self.assertIsInstance(edge['evidence'], list)

    def test_graph_expansion_depth(self):
        g1 = self.get('/api/v1/characters/zeus/graph?depth=1')
        g2 = self.get('/api/v1/characters/zeus/graph?depth=2')
        self.assertGreaterEqual(len(g2['nodes']), len(g1['nodes']))

    def test_graph_include_options(self):
        with_stories = self.get('/api/v1/characters/zeus/graph?include_stories=true')
        no_stories = self.get('/api/v1/characters/zeus/graph?include_stories=false')
        self.assertGreaterEqual(with_stories['counts']['stories'], no_stories['counts']['stories'])

        with_sources = self.get('/api/v1/characters/zeus/graph?include_sources=true')
        self.assertGreater(with_sources['counts']['sources'], 0)

    def test_graph_root_endpoint(self):
        g = self.get('/api/v1/graph?root=zeus')
        self.assertEqual(g['root'], 'c:zeus')
        self.get('/api/v1/graph', 400)

class StoryTests(EnhancedApiTest):
    def test_story_detail_roles(self):
        s = self.get('/api/v1/stories/birth-of-zeus')
        self.assertEqual(s['slug'], 'birth-of-zeus')
        self.assertIn('participants', s)
        for p in s['participants']:
            self.assertIn('role', p)
            self.assertIn('name', p)

    def test_character_profile_story_roles(self):
        p = self.get('/api/v1/characters/zeus')
        self.assertGreater(len(p['stories']), 0)
        self.assertIn('role', p['stories'][0])

class SearchTests(EnhancedApiTest):
    def test_unified_search(self):
        res = self.get('/api/v1/search?q=zeus')
        self.assertIn('characters', res)
        self.assertIn('stories', res)
        self.assertIn('sources', res)
        self.assertGreaterEqual(res['total'], 1)
        self.assertTrue(any(c['slug'] == 'zeus' for c in res['characters']))

    def test_unified_search_theogony(self):
        res = self.get('/api/v1/search?q=theogony')
        self.assertTrue(any(s['slug'] == 'gr-theogony' for s in res['sources']))

if __name__ == '__main__':
    unittest.main()
