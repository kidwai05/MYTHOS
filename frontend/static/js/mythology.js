import { api, h, label, plural, characterCard, sigil } from './common.js';

const root = document.getElementById('myth'), slug = root.dataset.slug;
const DESCRIPTIONS = {
  greek: 'Ancient Greek mythology arose in the Aegean basin, characterized by anthropomorphic pantheons, Hesiodic theogonies, epic Homeric literature, and dramatic explorations of fate, divine justice, and hubris.',
  norse: 'Norse and Germanic mythology flourished across Scandinavia and Iceland, preserved principally in the Poetic and Prose Eddas. It features a cyclical cosmology from Ymir to Ragnarök, centered on the Æsir and Vanir.',
  egyptian: 'Ancient Egyptian religion spans millennia along the Nile valley, comprising distinct theological traditions developed around major religious sanctuaries (Heliopolis, Hermopolis, Memphis, Thebes, and Esna).'
};

try {
  const m = await api(`/mythologies/${slug}`);
  const list = { items: [] };
  for (let page = 1; list.items.length < m.character_count; page++) {
    const res = await api('/characters', { mythology: slug, per_page: 100, page });
    list.items.push(...res.items);
    if (list.items.length >= res.total) break;
  }
  document.body.dataset.myth = slug;
  const tiers = Object.entries(m.sources_cited).map(([t, n]) => `${plural(n, t + ' source')}`).join(', ');

  const traditionElements = (m.traditions && m.traditions.length) ? h('section', { class: 'panel' },
    h('h2', {}, 'Theological & Regional Traditions'),
    h('p', { class: 'muted' }, 'Distinct theological frameworks, creation accounts, and cult centers within this mythology.'),
    h('div', { class: 'tradition-grid' }, m.traditions.map((t) => h('div', { class: 'tradition-card' },
      h('h3', {}, h('a', { href: `/characters?tradition=${t.slug}` }, t.name)),
      t.description ? h('p', { class: 'blurb' }, t.description) : null,
      h('a', { class: 'chip sm', href: `/characters?tradition=${t.slug}` }, `Browse ${t.name} records →`)
    )))
  ) : null;

  const storiesElements = (m.stories && m.stories.length) ? h('section', { class: 'panel' },
    h('h2', {}, `Narratives & Episodes (${m.stories.length})`),
    h('ul', { class: 'stories-list' }, m.stories.map((st) => h('li', { class: 'story-item' },
      h('a', { href: `/stories/${st.slug}`, class: 'story-link' }, st.title),
      st.summary ? h('p', { class: 'blurb' }, st.summary) : null
    )))
  ) : null;

  root.replaceChildren(
    h('p', { class: 'crumbs' }, h('a', { href: '/' }, 'Mythologies'), h('span', { class: 'crumb-sep' }, '›'), m.name),
    h('div', { class: 'myth-title' }, sigil(slug), h('h1', {}, `${m.name} mythology`)),
    h('p', { class: 'myth-intro' }, DESCRIPTIONS[slug] || `${m.name} mythological corpus.`),
    h('p', { class: 'muted' }, `${plural(m.character_count, 'character')}, ${m.verified_characters} with checked sources. Draws on ${tiers || 'no sources yet'}.`),
    h('div', { class: 'chips' }, m.roles.map((r) => h('a', { class: 'chip accent', href: `/characters?mythology=${slug}&role=${r.slug}` }, `${label(r.name)} · ${r.count}`))),
    traditionElements,
    storiesElements,
    h('h2', { class: 'sec-title myth-sec' }, 'Catalogued Characters'),
    h('div', { class: 'cards' }, list.items.map(characterCard)));
  document.title = `${m.name} mythology | Mythos`;
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, `Could not load: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
