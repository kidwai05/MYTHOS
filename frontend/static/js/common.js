// Shared helpers: API client, DOM builder, autocomplete.
import { sigil } from './fx.js';
export { sigil, icon, countUp } from './fx.js';
export function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) { if (kid == null || kid === false) continue; el.append(kid.nodeType ? kid : document.createTextNode(String(kid))); }
  return el;
}

export async function api(path, params) {
  const url = new URL('/api/v1' + path, location.origin);
  for (const [k, v] of Object.entries(params || {})) {
    if (v == null || v === '' || (Array.isArray(v) && !v.length)) continue;
    url.searchParams.set(k, Array.isArray(v) ? v.join(',') : v);
  }
  const res = await fetch(url);
  if (!res.ok) {
    let msg = 'Request failed';
    try { msg = (await res.json()).error.message; } catch { /* keep default */ }
    throw Object.assign(new Error(msg), { status: res.status });
  }
  return res.json();
}

export const label = (s) => s.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
export const plural = (n, one, many) => `${n} ${n === 1 ? one : many || one + 's'}`;

export function characterCard(c) {
  const hit = c.match && c.match.on !== 'name' ? (c.match.on === 'alias' ? `Also known as ${c.match.text}` : 'Matches the sources text') : null;
  const sourced = c.sources.verified ? `${plural(c.sources.verified, 'checked source link')}` : 'No checked sources yet';
  const metaParts = [c.mythology.name];
  if (c.tradition) metaParts.push(c.tradition.name);
  if (c.roles && c.roles.length) metaParts.push(...c.roles.slice(0, 2).map(label));

  return h('a', { class: 'card', href: `/characters/${c.slug}`, 'data-myth': c.mythology.slug },
    h('span', { class: 'mono', 'aria-hidden': 'true' }, c.name[0]),
    h('span', {},
      h('h3', {}, c.name),
      h('span', { class: 'meta' }, metaParts.join(' · ')),
      c.summary ? h('span', { class: 'blurb' }, c.summary) : (c.domains && c.domains.length ? h('span', { class: 'meta' }, h('br'), c.domains.slice(0, 3).map(label).join(', ')) : null),
      h('span', { class: 'meta' }, h('br'), sourced),
      hit ? h('div', { class: 'hit' }, hit) : null));
}

// Autocomplete on a search input. onPick(item) is called for a chosen suggestion; otherwise the form submits normally.
export function autocomplete(input, list, onPick) {
  let items = [], active = -1, timer = 0, seq = 0;
  const close = () => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1; };
  const render = () => {
    list.replaceChildren(...items.map((it, i) => h('li', { id: `${list.id}-${i}`, role: 'option', 'aria-selected': String(i === active), onmousedown: (e) => { e.preventDefault(); onPick(it); } },
      h('span', {}, it.name), h('small', {}, it.matched.on === 'alias' ? `${it.matched.text} · ${it.mythology.name}` : it.mythology.name))));
    list.hidden = !items.length; input.setAttribute('aria-expanded', String(!!items.length));
    if (active >= 0) input.setAttribute('aria-activedescendant', `${list.id}-${active}`);
  };
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { items = []; close(); return; }
    timer = setTimeout(async () => {
      const mine = ++seq;
      try { const r = await api('/search/suggest', { q }); if (mine === seq) { items = r.items; active = -1; render(); } } catch { close(); }
    }, 150);
  });
  input.addEventListener('keydown', (e) => {
    if (list.hidden) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); active = (active + 1) % items.length; render(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); active = (active - 1 + items.length) % items.length; render(); }
    else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); onPick(items[active]); }
    else if (e.key === 'Escape') close();
  });
  input.addEventListener('blur', () => setTimeout(close, 120));
}

export function initHeaderSearch() {
  const input = document.getElementById('hs'), list = document.getElementById('hs-list');
  if (input && list) autocomplete(input, list, (it) => { location.href = `/characters/${it.slug}`; });
}
initHeaderSearch();
