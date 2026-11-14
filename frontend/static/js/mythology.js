import { api, h, label, plural, characterCard } from './common.js';

const root = document.getElementById('myth'), slug = root.dataset.slug;
try {
  const m = await api(`/mythologies/${slug}`);
  const list = { items: [] };
  for (let page = 1; list.items.length < m.character_count; page++) list.items.push(...(await api('/characters', { mythology: slug, per_page: 100, page })).items);
  document.body.dataset.myth = slug;
  const tiers = Object.entries(m.sources_cited).map(([t, n]) => `${plural(n, t + ' source')}`).join(', ');
  root.replaceChildren(
    h('p', { class: 'crumbs' }, h('a', { href: '/' }, 'Mythologies'), h('span', { class: 'crumb-sep' }, '›'), m.name),
    h('h1', {}, `${m.name} mythology`),
    h('p', { class: 'muted' }, `${plural(m.character_count, 'character')}, ${m.verified_characters} with checked sources. Draws on ${tiers || 'no sources yet'}.`),
    h('div', { class: 'chips' }, m.roles.map((r) => h('a', { class: 'chip accent', href: `/characters?mythology=${slug}&role=${r.slug}` }, `${label(r.name)} · ${r.count}`))),
    h('h2', {}, 'Characters'),
    h('div', { class: 'cards' }, list.items.map(characterCard)));
  document.title = `${m.name} mythology | Mythos`;
} catch (e) { root.replaceChildren(h('p', { class: 'error' }, `Could not load: ${e.message}`)); }
root.setAttribute('aria-busy', 'false');
