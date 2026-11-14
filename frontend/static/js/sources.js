import { api, h, label, plural } from './common.js';

const root = document.getElementById('sources-root');
const TIER_LABELS = { primary: 'Primary source', supplementary: 'Supplementary source', scholarly: 'Scholarly reference' };

let allSources = [];
let activeTier = 'all';
let searchQuery = '';

function render() {
  const filtered = allSources.filter((s) => {
    if (activeTier !== 'all' && s.tier !== activeTier) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const text = `${s.title} ${s.author || ''} ${s.collection || ''} ${s.kind || ''}`.toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  });

  const cards = filtered.map((s) => {
    const statusClass = s.status === 'verified' ? 'ok' : 'muted-badge';
    return h('div', { class: 'card source-card', 'data-tier': s.tier },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, s.title[0]),
      h('div', { class: 'source-card-body' },
        h('h3', {}, h('a', { href: `/sources/${s.slug}` }, s.title)),
        h('p', { class: 'meta' }, [
          s.author || 'Anonymous',
          TIER_LABELS[s.tier] || s.tier,
          s.kind ? label(s.kind) : null
        ].filter(Boolean).join(' · ')),
        s.edition_used ? h('p', { class: 'blurb' }, s.edition_used) : null,
        h('div', { class: 'source-stats' },
          h('span', { class: `badge ${statusClass}` }, s.status),
          h('span', { class: 'chip sm' }, plural(s.passages || s.links, 'recorded citation')),
          s.verified_links ? h('span', { class: 'chip sm accent' }, `${s.verified_links} verified links`) : null
        )
      )
    );
  });

  const counts = {
    all: allSources.length,
    primary: allSources.filter((s) => s.tier === 'primary').length,
    supplementary: allSources.filter((s) => s.tier === 'supplementary').length,
    scholarly: allSources.filter((s) => s.tier === 'scholarly').length
  };

  root.replaceChildren(
    h('p', { class: 'crumbs' }, h('a', { href: '/' }, 'Home'), h('span', { class: 'crumb-sep' }, '›'), 'Ancient Sources'),
    h('div', { class: 'page-head' },
      h('h1', {}, 'Ancient Sources & Evidence'),
      h('p', { class: 'intro' },
        'Every factual claim in Mythos is grounded in an ancient textual witness or qualified scholarly study. Explore the catalogued texts, their editions, and the specific passages that support our records.'
      )
    ),
    h('div', { class: 'sources-toolbar' },
      h('div', { class: 'filter-tabs' },
        ['all', 'primary', 'supplementary', 'scholarly'].map((t) => h('button', {
          class: `tab-btn ${activeTier === t ? 'active' : ''}`,
          type: 'button',
          onclick: () => { activeTier = t; render(); }
        }, `${t === 'all' ? 'All Sources' : TIER_LABELS[t]} (${counts[t]})`))
      ),
      h('input', {
        class: 'input-search',
        type: 'search',
        placeholder: 'Search source titles, authors, editions…',
        value: searchQuery,
        oninput: (e) => { searchQuery = e.target.value.trim(); render(); }
      })
    ),
    h('div', { class: 'cards source-grid' }, cards.length ? cards : h('p', { class: 'empty' }, 'No sources match the selected criteria.'))
  );
}

try {
  const data = await api('/sources');
  allSources = data.items;
  render();
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, `Could not load sources: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
