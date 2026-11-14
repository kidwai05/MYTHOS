import { api, h, label, plural, sigil, countUp } from './common.js';

const box = document.getElementById('mythologies');
if (box) {
  try {
    const { items } = await api('/mythologies');
    box.replaceChildren(...items.map((m) => h('a', { class: 'myth-card', href: `/characters?mythology=${m.slug}`, 'data-myth': m.slug },
      sigil(m.slug),
      h('h3', {}, m.name),
      h('div', { class: 'big' }, String(m.character_count)),
      h('div', { class: 'muted' }, plural(m.character_count, 'character'), m.verified_characters ? ` · ${m.verified_characters} with checked sources` : ' · sources not yet checked'),
      h('div', { class: 'chips' }, m.roles.slice(0, 4).map((r) => h('span', { class: 'chip' }, `${label(r.name)} ${r.count}`))))));
    box.setAttribute('aria-busy', 'false');
    const nums = box.querySelectorAll('.big');
    const seen = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { seen.unobserve(e.target); countUp(e.target, Number(e.target.dataset.n)); } }), { threshold: .4 });
    items.forEach((m, i) => { nums[i].dataset.n = m.character_count; seen.observe(nums[i]); });
    const { items: srcs } = await api('/sources');
    const links = srcs.reduce((a, s) => a + s.links, 0), ok = srcs.reduce((a, s) => a + s.verified_links, 0);
    const passages = srcs.reduce((a, s) => a + (s.passages || 0), 0);
    const stats = document.getElementById('stats');
    if (stats) stats.textContent = `${ok} of ${links} citations are verified against named translations across ${passages} distinct passages. ${srcs.length} sources are catalogued.`;
  } catch (e) { box.replaceChildren(h('p', { class: 'error' }, `Could not load mythologies: ${e.message}`)); }
}
const random = document.getElementById('random');
if (random) random.addEventListener('click', async () => {
  const { total } = await api('/characters', { per_page: 1, fields: 'slug' });
  const { items } = await api('/characters', { per_page: 1, page: 1 + Math.floor(Math.random() * total), fields: 'slug' });
  location.href = `/characters/${items[0].slug}`;
});
