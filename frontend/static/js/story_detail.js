import { api, h, label, plural, icon } from './common.js';

const root = document.getElementById('story-detail-root');
const initial = (t) => t.replace(/^(the|a|an)\s+/i, '')[0].toUpperCase();
const slug = root.dataset.slug;

const checked = (l) => (l.verified
  ? h('span', { class: 'badge ok', title: 'The passage was read in the named edition' }, icon('check'), 'checked')
  : h('span', { class: 'badge no', title: 'Listed, but the passage has not been read yet' }, 'unchecked'));

// The passages one paragraph rests on, folded away until asked for.
const sig = (p) => p.basis.map((b) => `${b.source.slug}|${b.locator}`).sort().join(';');

function citations(basis, span = 1) {
  if (!basis.length) return null;
  const sameSource = new Set(basis.map((b) => b.source.slug)).size === 1;
  const shown = basis.slice(0, 3).map((b) => h('span', { class: 'loc' }, sameSource ? b.locator : `${b.source.title}: ${b.locator}`));
  return h('details', { class: 'cites' },
    h('summary', {}, h('span', { class: 'cites-label' }, span > 1 ? `${plural(basis.length, 'passage')} for the last ${span} paragraphs` : plural(basis.length, 'passage')), shown, basis.length > 3 ? h('span', { class: 'cites-more' }, `+${basis.length - 3} more`) : null),
    h('ul', {}, basis.map((b) => h('li', {},
      h('span', { class: 'cite-ref' }, h('a', { href: `/sources/${b.source.slug}` }, b.source.title), ' ', h('span', { class: 'loc' }, b.locator)),
      h('span', { class: 'cite-claim' }, b.claim || '', b.note ? h('span', { class: 'note' }, b.note) : null),
      checked(b)))));
}

function paragraph(p, cite) {
  return h('div', { class: `para${p.kind === 'note' ? ' tale-note' : ''}` },
    p.kind === 'note' ? h('span', { class: 'badge' }, 'Note') : null,
    h('p', {}, p.text), cite);
}

function mythSection(s) {
  if (s.status !== 'written') {
    return h('section', { class: 'panel', 'aria-labelledby': 'tale-h' }, h('h2', { id: 'tale-h' }, 'The Myth'),
      h('p', { class: 'muted' }, 'This myth has not been written yet. The texts that tell it have not been read for this project, so the passages listed below are references only and are marked as unchecked.'));
  }
  const nodes = [];
  let block = null, run = 1;
  s.paragraphs.forEach((p, i) => {
    const next = s.paragraphs[i + 1];
    const sameNext = next && next.kind === p.kind && sig(next) === sig(p);
    run = (i > 0 && s.paragraphs[i - 1].kind === p.kind && sig(s.paragraphs[i - 1]) === sig(p)) ? run + 1 : 1;
    const cite = sameNext ? null : citations(p.basis, run);
    if (p.kind === 'variant') {
      if (!block) { block = h('aside', { class: 'variant-block', 'aria-label': 'Another telling' }, h('p', { class: 'variant-label' }, h('span', { class: 'badge var' }, 'Another telling'))); nodes.push(block); }
      block.append(paragraph(p, cite));
    } else {
      block = null;
      nodes.push(paragraph(p, cite));
    }
  });
  const books = new Set(s.paragraphs.flatMap((p) => p.basis.map((b) => b.source.title)));
  return h('section', { class: 'panel', 'aria-labelledby': 'tale-h' },
    h('h2', { id: 'tale-h' }, 'The Myth'),
    h('p', { class: 'muted tale-intro' }, `${s.reading_minutes} minute read. A close paraphrase of ${[...books].join(', ')}, keeping its order of events. Under each paragraph, open its passages to see the line numbers and what each passage says.`),
    h('div', { class: 'tale' }, nodes));
}

function sourcesSection(s) {
  if (!s.sources.length) return h('p', { class: 'empty' }, 'No supporting textual citations recorded yet.');
  const groups = new Map();
  for (const l of s.sources) { if (!groups.has(l.source.slug)) groups.set(l.source.slug, { source: l.source, links: [] }); groups.get(l.source.slug).links.push(l); }
  return h('div', { class: 'sources-block' }, [...groups.values()].map(({ source, links }) => h('div', { class: 'src-group' },
    h('h3', {}, h('a', { href: `/sources/${source.slug}` }, source.title)),
    h('p', { class: 'src-meta' }, [source.author, source.tier ? `${label(source.tier)} source` : null, source.edition_used ? `Edition: ${source.edition_used}` : null].filter(Boolean).join(' · ')),
    h('ul', { class: 'passages' }, links.map((l) => h('li', {},
      h('span', { class: 'loc' }, l.locator || 'Unspecified section'),
      h('span', {}, l.claim || h('em', { class: 'muted' }, 'Passage awaiting detailed extraction'), l.note ? h('span', { class: 'note' }, l.note) : null),
      h('span', { class: 'badges' }, checked(l), l.relation === 'variant' ? h('span', { class: 'badge var' }, 'variant') : null)))))));
}

try {
  const s = await api(`/stories/${slug}`);
  document.body.dataset.myth = s.mythology.slug;
  document.title = `${s.title} | Stories | Mythos`;

  const participantsList = s.participants.length ? h('div', { class: 'cards' },
    s.participants.map((p) => h('a', { class: 'card', href: `/characters/${p.slug}` },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, p.name[0]),
      h('span', {}, h('h3', {}, p.name),
        h('span', { class: 'meta' }, p.role ? `Role: ${label(p.role)}` : 'Participant'),
        p.notes ? h('span', { class: 'blurb' }, p.notes) : null)))) : h('p', { class: 'empty' }, 'No participants catalogued for this story.');

  const related = s.related.length ? h('section', { class: 'panel', 'aria-labelledby': 'rel-h' },
    h('h2', { id: 'rel-h' }, 'Related Myths'),
    h('p', { class: 'muted' }, 'Other stories that share figures with this one.'),
    h('div', { class: 'cards' }, s.related.map((r) => h('a', { class: 'card story-card', href: `/stories/${r.slug}`, 'data-myth': r.mythology.slug },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, initial(r.title)),
      h('span', {}, h('h3', {}, r.title),
        h('span', { class: 'meta' }, `Shares ${r.shared.slice(0, 3).join(', ')}${r.shared.length > 3 ? ` and ${r.shared.length - 3} more` : ''}`),
        r.status === 'written' ? (r.summary ? h('span', { class: 'blurb' }, r.summary) : null) : h('span', { class: 'meta' }, 'Not yet written')))))) : null;

  root.replaceChildren(...[
    h('p', { class: 'crumbs' }, h('a', { href: '/' }, 'Home'), h('span', { class: 'crumb-sep' }, '›'), h('a', { href: '/stories' }, 'Stories'), h('span', { class: 'crumb-sep' }, '›'), s.title),
    h('div', { class: 'profile-head' },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, initial(s.title)),
      h('div', {}, h('h1', {}, s.title),
        h('p', { class: 'aka' }, [s.mythology.name, s.tradition ? `${s.tradition.name} tradition` : null, plural(s.participants.length, 'participant')].filter(Boolean).join(' · ')))),
    h('div', { class: 'chips' },
      h('a', { class: 'chip accent', href: `/characters?mythology=${s.mythology.slug}` }, s.mythology.name),
      s.tradition ? h('a', { class: 'chip highlight', href: `/characters?tradition=${s.tradition.slug}` }, s.tradition.name) : null,
      s.status === 'written' ? h('span', { class: 'chip' }, `${s.reading_minutes} min read`) : h('span', { class: 'chip' }, 'Not yet written'),
      s.locations.map((l) => h('span', { class: 'chip place', title: 'A place named in the story' }, l))),
    s.summary ? h('div', { class: 'summary-wrap' }, h('p', { class: 'summary' }, s.summary))
      : h('p', { class: 'muted summary' }, 'Narrative summary has not yet been drafted from verified textual witnesses.'),
    mythSection(s),
    h('section', { class: 'panel' }, h('h2', {}, `Story Participants (${s.participants.length})`),
      h('p', { class: 'muted' }, 'Catalogued figures in this episode and their narrative roles.'), participantsList),
    h('section', { class: 'panel' }, h('h2', {}, `Ancient Textual Sources & Attestations (${s.sources.length})`),
      h('p', { class: 'muted' }, 'Every passage used above, grouped by text.'), sourcesSection(s)),
    related].filter(Boolean));
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, e.status === 404 ? 'Story not found.' : `Could not load: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
