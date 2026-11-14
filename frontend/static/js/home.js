import { api, h, label, plural } from './common.js';

const box = document.getElementById('mythologies');
if (box) {
  try {
    const { items } = await api('/mythologies');
    box.replaceChildren(...items.map((m) => h('a', { class: 'myth-card', href: `/characters?mythology=${m.slug}`, 'data-myth': m.slug },
      h('h3', {}, m.name),
      h('div', { class: 'big' }, m.character_count),
      h('div', { class: 'muted' }, plural(m.character_count, 'character'), m.verified_characters ? ` · ${m.verified_characters} with checked sources` : ' · sources not yet checked'),
      h('div', { class: 'chips' }, m.roles.slice(0, 4).map((r) => h('span', { class: 'chip' }, `${label(r.name)} ${r.count}`))))));
    box.setAttribute('aria-busy', 'false');
    const { items: srcs } = await api('/sources');
    const links = srcs.reduce((a, s) => a + s.links, 0), ok = srcs.reduce((a, s) => a + s.verified_links, 0);
    const stats = document.getElementById('stats');
    if (stats) stats.textContent = `${ok} of ${links} source links are checked against a named edition. ${srcs.length} sources are catalogued.`;
  } catch (e) { box.replaceChildren(h('p', { class: 'error' }, `Could not load mythologies: ${e.message}`)); }
}
const random = document.getElementById('random');
if (random) random.addEventListener('click', async () => {
  const { total } = await api('/characters', { per_page: 1, fields: 'slug' });
  const { items } = await api('/characters', { per_page: 1, page: 1 + Math.floor(Math.random() * total), fields: 'slug' });
  location.href = `/characters/${items[0].slug}`;
});
