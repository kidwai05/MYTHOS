import { api, h, label, plural, icon, sigil } from './common.js';

const root = document.getElementById('profile'), slug = root.dataset.slug;
const TIER = { primary: 'Primary source', supplementary: 'Supplementary source', scholarly: 'Scholarly reference' };

const checkedBadge = (title) => h('span', { class: 'badge ok', title: title || 'The passage was read in the named edition' }, icon('check'), 'checked');
const checked = (l) => l.verified ? checkedBadge()
  : h('span', { class: 'badge no', title: 'Listed but the passage has not been read yet' }, 'unchecked');
const badge = (l) => h('span', { class: 'badges' }, checked(l),
  l.relation === 'variant' ? h('span', { class: 'badge var', title: 'A version that differs from other sources' }, 'variant') : null);

function passage(l, withSource) {
  return h('li', {},
    h('span', { class: 'loc' }, l.locator || 'no locator'),
    h('span', {}, l.claim || h('em', { class: 'muted' }, 'Passage not read yet'),
      withSource ? h('span', { class: 'note' }, `${l.source.title}${l.source.author ? ', ' + l.source.author : ''}`) : null,
      l.note ? h('span', { class: 'note' }, l.note) : null),
    badge(l));
}

function sourcesSection(p) {
  const groups = new Map();
  for (const l of p.sources) { if (!groups.has(l.source.slug)) groups.set(l.source.slug, { source: l.source, links: [] }); groups.get(l.source.slug).links.push(l); }
  return h('section', { class: 'panel', 'aria-labelledby': 'say' },
    h('h2', { id: 'say' }, 'What the sources say'),
    h('p', { class: 'muted' }, `${plural(p.counts.sources, 'passage')} across ${plural(groups.size, 'source')}. Each line is a short paraphrase with the place it comes from.`),
    [...groups.values()].map(({ source, links }) => h('div', { class: 'src-group' },
      h('h3', {}, source.title),
      h('p', { class: 'src-meta' }, [TIER[source.tier], source.author, source.edition_used ? `Edition: ${source.edition_used}` : 'Edition not chosen yet'].filter(Boolean).join(' · ')),
      h('ul', { class: 'passages' }, links.map((l) => passage(l, false))))));
}

function relationshipsSection(p) {
  if (!p.relationships.length) return null;
  return h('section', { class: 'panel', 'aria-labelledby': 'rel' }, h('h2', { id: 'rel' }, 'Relationships'),
    p.relationships.map((g) => h('div', { class: 'rel-group' }, h('h3', {}, g.group),
      h('ul', { class: 'rel-list' }, g.items.map((i) => h('li', {},
        h('a', { href: `/characters/${i.other.slug}` }, i.other.name), ' ',
        h('span', { class: 'chip' }, i.other.mythology.name), ' ',
        i.verified ? checkedBadge() : h('span', { class: 'badge no' }, 'unchecked'),
        h('details', {}, h('summary', {}, `${plural(i.sources.length, 'source passage')}`),
          h('ul', {}, i.sources.map((l) => h('li', {}, h('span', { class: 'loc' }, `${l.source.title} ${l.locator || ''}`), ' ', l.claim || '', l.relation === 'variant' ? ' (variant)' : '', l.note ? h('span', { class: 'note' }, l.note) : null))))))))));
}

function sidebar(p) {
  const uniq = new Map();
  for (const l of p.sources) { const e = uniq.get(l.source.slug) || { source: l.source, n: 0 }; e.n++; uniq.set(l.source.slug, e); }
  return h('aside', { class: 'side', 'aria-label': 'Related' },
    h('section', { class: 'panel' }, h('h2', {}, 'Sources'),
      h('ul', {}, [...uniq.values()].map(({ source, n }) => h('li', {}, source.url ? h('a', { href: source.url, target: '_blank', rel: 'noopener' }, source.title) : source.title, ` (${n})`))),
      h('p', { class: 'muted' }, 'Links open a public-domain translation. Passage counts are in brackets.')),
    h('section', { class: 'panel' }, h('h2', {}, 'Equivalents in other cultures'),
      h('p', { class: 'muted' }, p.equivalents.length ? '' : 'None yet. Cross-cultural links arrive when a second mythology is complete.')),
    h('section', { class: 'panel' }, h('h2', {}, 'Explore'),
      h('p', {}, h('button', { class: 'btn ghost', disabled: true, 'aria-disabled': 'true', title: 'Coming in the next phase' }, 'Relationship graph')),
      h('p', {}, h('button', { class: 'btn ghost', disabled: true, 'aria-disabled': 'true', title: 'Accounts come later' }, 'Bookmark')),
      h('p', { class: 'muted' }, 'The graph and bookmarks are planned for later phases.')));
}

function summaryBlock(p) {
  if (!p.summary) return h('p', { class: 'muted summary' }, p.counts.verified_sources ? 'No summary has been written yet.' : 'No summary yet: the passages for this character have not been checked against the texts.');
  return h('div', { class: 'summary-wrap' },
    h('p', { class: 'summary' }, p.summary),
    h('details', { class: 'basis' }, h('summary', {}, `Based on ${plural(p.summary_basis.length, 'passage')} listed below`),
      h('ul', {}, p.summary_basis.map((l) => h('li', {}, h('span', { class: 'loc' }, `${l.source.title} ${l.locator}`), ' ', l.claim)))));
}

try {
  const p = await api(`/characters/${slug}`);
  document.body.dataset.myth = p.mythology.slug;
  document.title = `${p.name} (${p.mythology.name}) | Mythos`;
  root.replaceChildren(
    sigil(p.mythology.slug, 'profile-sigil'),
    h('p', { class: 'crumbs' }, h('a', { href: '/' }, 'Mythologies'), h('span', { class: 'crumb-sep' }, '›'), h('a', { href: `/mythologies/${p.mythology.slug}` }, p.mythology.name), h('span', { class: 'crumb-sep' }, '›'), p.name),
    h('div', { class: 'profile-head' }, h('span', { class: 'mono', 'aria-hidden': 'true' }, p.name[0]),
      h('div', {}, h('h1', {}, p.name), p.aliases.length ? h('p', { class: 'aka' }, 'Also called ', p.aliases.join(', ')) : null)),
    h('div', { class: 'chips' }, h('a', { class: 'chip accent', href: `/characters?mythology=${p.mythology.slug}` }, p.mythology.name),
      p.roles.map((r) => h('a', { class: 'chip', href: `/characters?role=${r.slug}` }, label(r.name))),
      p.domains.map((d) => h('a', { class: 'chip', href: `/characters?domain=${d.slug}` }, label(d.name))),
      p.gender ? h('span', { class: 'chip' }, p.gender === 'f' ? 'Female' : 'Male') : null),
    summaryBlock(p),
    h('div', { class: 'profile' },
      h('div', {}, sourcesSection(p), relationshipsSection(p),
        p.stories.length ? h('section', { class: 'panel' }, h('h2', {}, 'Appears in'), h('ul', { class: 'stories' }, p.stories.map((s) => h('li', {}, s.title)))) : null),
      sidebar(p)));
} catch (e) { root.replaceChildren(h('p', { class: 'error' }, e.status === 404 ? 'No such character.' : `Could not load: ${e.message}`)); }
root.setAttribute('aria-busy', 'false');
