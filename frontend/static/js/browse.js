import { api, h, label, plural, characterCard, autocomplete } from './common.js';

const DIMS = ['mythology', 'tradition', 'role', 'domain', 'gender'];
const DIM_TITLE = { mythology: 'Mythology', tradition: 'Tradition', role: 'Role', domain: 'Domain', gender: 'Gender' };
const PER_PAGE = 12;
const $ = (id) => document.getElementById(id);
let state = readUrl(), facets = null, token = 0;

function readUrl() {
  const p = new URLSearchParams(location.search), s = { q: p.get('q') || '', sort: p.get('sort') || '', page: Math.max(1, parseInt(p.get('page'), 10) || 1) };
  for (const d of DIMS) s[d] = (p.get(d) || '').split(',').filter(Boolean);
  return s;
}
function writeUrl(push) {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  for (const d of DIMS) if (state[d].length) p.set(d, state[d].join(','));
  if (state.sort) p.set('sort', state.sort);
  if (state.page > 1) p.set('page', state.page);
  const url = location.pathname + (p.toString() ? '?' + p : '');
  push ? history.pushState(null, '', url) : history.replaceState(null, '', url);
}
function params() {
  const p = { q: state.q, sort: state.sort, page: state.page, per_page: PER_PAGE, include: 'facets' };
  for (const d of DIMS) p[d] = state[d];
  return p;
}
function change(patch) { Object.assign(state, patch, { page: patch.page || 1 }); writeUrl(true); load(); }

async function load() {
  const mine = ++token;
  $('results').setAttribute('aria-busy', 'true');
  let data;
  try { data = await api('/characters', params()); }
  catch (e) { if (e.status === 400) { $('count').textContent = e.message; $('results').replaceChildren(); return; } $('count').textContent = `Could not load: ${e.message}`; return; }
  if (mine !== token) return;
  facets = data.facets;
  $('q').value = state.q;
  const sortEl = $('sort'); sortEl.value = data.sort;
  sortEl.querySelector('option[value=relevance]').disabled = !state.q;
  $('count').textContent = data.total ? `${plural(data.total, 'character')}${state.q ? ` for “${state.q}”` : ''}` : 'No characters match these filters.';
  $('results').replaceChildren(...data.items.map(characterCard));
  $('results').setAttribute('aria-busy', 'false');
  renderFacets(); renderActive(); renderPager(data);
  document.title = `${state.q ? state.q + ' · ' : ''}Browse characters | Mythos`;
}

function renderFacets() {
  const root = $('facets');
  root.replaceChildren(...DIMS.map((d) => {
    const rows = [...(facets[d] || [])];
    for (const v of state[d]) if (!rows.some((r) => r.value === v)) rows.push({ value: v, label: label(v), count: 0 });
    if (!rows.length) return null;
    return h('fieldset', {}, h('legend', {}, DIM_TITLE[d]), rows.map((r) => {
      const id = `f-${d}-${r.value}`;
      return h('label', { class: 'opt', for: id },
        h('input', { id, type: 'checkbox', checked: state[d].includes(r.value) || null, onchange: (e) => {
          const set = new Set(state[d]); e.target.checked ? set.add(r.value) : set.delete(r.value); change({ [d]: [...set] }); } }),
        h('span', {}, r.label), h('span', { class: 'n' }, r.count));
    }));
  }));
  root.setAttribute('aria-busy', 'false');
}
function renderActive() {
  const chips = [];
  if (state.q) chips.push(h('button', { type: 'button', 'aria-label': `Remove search ${state.q}`, onclick: () => change({ q: '' }) }, `Search: ${state.q} ×`));
  for (const d of DIMS) for (const v of state[d]) {
    const name = ((facets[d] || []).find((r) => r.value === v) || {}).label || label(v);
    chips.push(h('button', { type: 'button', 'aria-label': `Remove filter ${name}`, onclick: () => change({ [d]: state[d].filter((x) => x !== v) }) }, `${name} ×`));
  }
  $('active').replaceChildren(...chips);
}
function renderPager(data) {
  const pages = Math.ceil(data.total / data.per_page), cur = data.page, nav = $('pager');
  if (pages <= 1) { nav.replaceChildren(); return; }
  const link = (n, text, cls) => n === cur && !cls ? h('a', { href: '#', 'aria-current': 'page', onclick: (e) => e.preventDefault() }, text)
    : h('a', { href: '#', onclick: (e) => { e.preventDefault(); change({ page: n }); window.scrollTo({ top: 0 }); } }, text);
  const out = [cur > 1 ? link(cur - 1, '‹ Previous', true) : h('span', { class: 'off' }, '‹ Previous')];
  for (let n = 1; n <= pages; n++) out.push(link(n, String(n)));
  out.push(cur < pages ? link(cur + 1, 'Next ›', true) : h('span', { class: 'off' }, 'Next ›'));
  nav.replaceChildren(...out);
}

$('search-form').addEventListener('submit', (e) => { e.preventDefault(); change({ q: $('q').value.trim(), sort: '' }); });
$('sort').addEventListener('change', (e) => change({ sort: e.target.value }));
$('clear').addEventListener('click', () => change({ q: '', sort: '', mythology: [], tradition: [], role: [], domain: [], gender: [] }));
autocomplete($('q'), $('q-list'), (it) => { location.href = `/characters/${it.slug}`; });
addEventListener('popstate', () => { state = readUrl(); load(); });
if (matchMedia('(max-width: 860px)').matches) $('filters').open = false;
load();
