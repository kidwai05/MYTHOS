import { api, h, label, plural, icon, sigil } from './common.js';
import { MythosGraph } from './graph.js';

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
      withSource ? h('span', { class: 'note' },
        l.source ? h('a', { href: `/sources/${l.source.slug}` }, `${l.source.title}${l.source.author ? ', ' + l.source.author : ''}`) : null
      ) : null,
      l.note ? h('span', { class: 'note' }, l.note) : null),
    badge(l));
}

function sourcesSection(p) {
  const groups = new Map();
  for (const l of p.sources) {
    if (!groups.has(l.source.slug)) groups.set(l.source.slug, { source: l.source, links: [] });
    groups.get(l.source.slug).links.push(l);
  }
  return h('section', { class: 'panel', 'aria-labelledby': 'say' },
    h('h2', { id: 'say' }, 'Textual Evidence & Ancient Sources'),
    h('p', { class: 'muted' }, `${plural(p.counts.sources, 'passage')} across ${plural(groups.size, 'source')}. Each record is linked directly to the ancient textual witness.`),
    [...groups.values()].map(({ source, links }) => h('div', { class: 'src-group' },
      h('h3', {}, h('a', { href: `/sources/${source.slug}` }, source.title)),
      h('p', { class: 'src-meta' }, [
        TIER[source.tier] || source.tier,
        source.author,
        source.edition_used ? `Edition: ${source.edition_used}` : 'Edition not chosen yet'
      ].filter(Boolean).join(' · ')),
      h('ul', { class: 'passages' }, links.map((l) => passage(l, false))))));
}

function relationshipsSection(p) {
  if (!p.relationships.length) return null;
  return h('section', { class: 'panel', 'aria-labelledby': 'rel' },
    h('h2', { id: 'rel' }, 'Relationships & Connections'),
    p.relationships.map((g) => h('div', { class: 'rel-group' },
      h('h3', {}, g.group),
      h('ul', { class: 'rel-list' }, g.items.map((i) => h('li', {},
        h('a', { href: `/characters/${i.other.slug}` }, i.other.name), ' ',
        h('span', { class: 'chip' }, i.other.mythology.name), ' ',
        i.verified ? checkedBadge() : h('span', { class: 'badge no' }, 'unchecked'),
        h('details', {},
          h('summary', {}, `${plural(i.sources.length, 'source passage')}`),
          h('ul', {}, i.sources.map((l) => h('li', {},
            h('span', { class: 'loc' },
              h('a', { href: `/sources/${l.source.slug}` }, l.source.title), ` ${l.locator || ''}`
            ), ' ',
            l.claim || '',
            l.relation === 'variant' ? ' (variant)' : '',
            l.note ? h('span', { class: 'note' }, l.note) : null
          )))
        )
      ))))));
}

function storiesSection(p) {
  if (!p.stories.length) return null;
  return h('section', { class: 'panel', 'aria-labelledby': 'story-head' },
    h('h2', { id: 'story-head' }, 'Narrative Appearances'),
    h('ul', { class: 'stories-list' }, p.stories.map((s) => h('li', { class: 'story-item' },
      h('a', { href: `/stories/${s.slug}`, class: 'story-link' }, s.title),
      s.role ? h('span', { class: 'chip sm' }, label(s.role)) : null
    ))));
}

function sidebar(p, onShowGraph) {
  const uniq = new Map();
  for (const l of p.sources) {
    const e = uniq.get(l.source.slug) || { source: l.source, n: 0 };
    e.n++;
    uniq.set(l.source.slug, e);
  }
  return h('aside', { class: 'side', 'aria-label': 'Related Information' },
    h('section', { class: 'panel' },
      h('h2', {}, 'Primary Sources Cited'),
      h('ul', {}, [...uniq.values()].map(({ source, n }) => h('li', {},
        h('a', { href: `/sources/${source.slug}` }, source.title), ` (${n})`
      ))),
      h('p', { class: 'muted' }, 'Click any source to inspect all recorded passages and supported entities.')),
    h('section', { class: 'panel' },
      h('h2', {}, 'Tradition & Context'),
      p.tradition ? h('p', {}, h('strong', {}, p.tradition.name), ' theological tradition.') :
        h('p', { class: 'muted' }, `Canonical ${p.mythology.name} corpus.`),
      p.counts.passages ? h('p', { class: 'muted' }, `${p.counts.passages} distinct passages cited across ancient editions.`) : null
    ),
    h('section', { class: 'panel' },
      h('h2', {}, 'Equivalents in Other Cultures'),
      h('p', { class: 'muted' }, p.equivalents.length ? '' : 'None yet. Cross-cultural syncretisms and parallels will be mapped with verified citations as additional mythologies expand.')),
    h('section', { class: 'panel' },
      h('h2', {}, 'Interactive Tools'),
      h('p', {}, h('button', {
        class: 'btn primary block',
        type: 'button',
        onclick: onShowGraph
      }, 'Explore in Graph View')),
      h('p', { class: 'muted' }, 'Open the interactive knowledge graph to explore connections, paths, and supporting evidence.')
    ));
}

function summaryBlock(p) {
  if (!p.summary) return h('p', { class: 'muted summary' }, p.counts.verified_sources ? 'No summary has been written yet.' : 'No summary yet: the passages for this character have not been checked against the texts.');
  return h('div', { class: 'summary-wrap' },
    h('p', { class: 'summary' }, p.summary),
    h('details', { class: 'basis' },
      h('summary', {}, `Based on ${plural(p.summary_basis.length, 'passage')} listed below`),
      h('ul', {}, p.summary_basis.map((l) => h('li', {},
        h('span', { class: 'loc' },
          h('a', { href: `/sources/${l.source.slug}` }, l.source.title), ` ${l.locator}`
        ), ' ', l.claim
      )))));
}

try {
  const p = await api(`/characters/${slug}`);
  document.body.dataset.myth = p.mythology.slug;
  const tradTitle = p.tradition ? ` · ${p.tradition.name}` : '';
  document.title = `${p.name} (${p.mythology.name}${tradTitle}) | Mythos`;

  // Segmented Tabs Header
  let activeTab = 'overview';
  const tabOverview = h('button', { class: 'tab-btn active', type: 'button', onclick: () => setTab('overview') }, 'Overview & Evidence');
  const tabGraph = h('button', { class: 'tab-btn', type: 'button', onclick: () => setTab('graph') }, 'Interactive Graph');
  const tabsNav = h('nav', { class: 'profile-tabs', 'aria-label': 'Character Profile Views' }, tabOverview, tabGraph);

  // Tab View Panes
  const overviewPane = h('div', { class: 'tab-pane active' });
  const graphPane = h('div', { class: 'tab-pane' });
  let graphInstance = null;

  function setTab(tabName) {
    activeTab = tabName;
    tabOverview.classList.toggle('active', tabName === 'overview');
    tabGraph.classList.toggle('active', tabName === 'graph');
    overviewPane.classList.toggle('active', tabName === 'overview');
    graphPane.classList.toggle('active', tabName === 'graph');

    if (tabName === 'graph') {
      if (!graphInstance) {
        graphInstance = new MythosGraph(graphPane, { rootSlug: slug });
      } else {
        graphInstance.resizeCanvas();
        graphInstance.render();
      }
    }
  }

  // Populate overview pane
  overviewPane.append(
    h('div', { class: 'profile' },
      h('div', {},
        sourcesSection(p),
        relationshipsSection(p),
        storiesSection(p)
      ),
      sidebar(p, () => setTab('graph'))
    )
  );

  root.replaceChildren(
    sigil(p.mythology.slug, 'profile-sigil'),
    h('p', { class: 'crumbs' },
      h('a', { href: '/' }, 'Mythologies'),
      h('span', { class: 'crumb-sep' }, '›'),
      h('a', { href: `/mythologies/${p.mythology.slug}` }, p.mythology.name),
      p.tradition ? h('span', { class: 'crumb-sep' }, '›') : null,
      p.tradition ? h('span', {}, p.tradition.name) : null,
      h('span', { class: 'crumb-sep' }, '›'),
      p.name
    ),
    h('div', { class: 'profile-head' },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, p.name[0]),
      h('div', {},
        h('h1', {}, p.name),
        p.aliases.length ? h('p', { class: 'aka' }, 'Also called ', p.aliases.join(', ')) : null
      )
    ),
    h('div', { class: 'chips' },
      h('a', { class: 'chip accent', href: `/characters?mythology=${p.mythology.slug}` }, p.mythology.name),
      p.tradition ? h('a', { class: 'chip highlight', href: `/characters?tradition=${p.tradition.slug}` }, p.tradition.name) : null,
      p.roles.map((r) => h('a', { class: 'chip', href: `/characters?role=${r.slug}` }, label(r.name))),
      p.domains.map((d) => h('a', { class: 'chip', href: `/characters?domain=${d.slug}` }, label(d.name))),
      p.gender ? h('span', { class: 'chip' }, p.gender === 'f' ? 'Female' : 'Male') : null
    ),
    summaryBlock(p),
    tabsNav,
    overviewPane,
    graphPane
  );
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, e.status === 404 ? 'No such character.' : `Could not load: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
