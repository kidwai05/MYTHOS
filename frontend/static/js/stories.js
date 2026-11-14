import { api, h, label, plural } from './common.js';

const root = document.getElementById('stories-root');
let allStories = [];
let activeMyth = 'all';
let searchQuery = '';

function render() {
  const filtered = allStories.filter((s) => {
    if (activeMyth !== 'all' && s.mythology.slug !== activeMyth) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const text = `${s.title} ${s.mythology.name} ${s.summary || ''}`.toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  });

  const cards = filtered.map((s) => {
    return h('div', { class: 'card story-card', 'data-myth': s.mythology.slug },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, s.title[0]),
      h('div', { class: 'story-card-body' },
        h('h3', {}, h('a', { href: `/stories/${s.slug}` }, s.title)),
        h('p', { class: 'meta' }, [
          s.mythology.name,
          plural(s.participants, 'recorded participant')
        ].join(' · ')),
        s.summary ? h('p', { class: 'blurb' }, s.summary) : null,
        h('div', { class: 'story-actions' },
          h('a', { class: 'btn sm ghost', href: `/stories/${s.slug}` }, 'Read Story & Sources →')
        )
      )
    );
  });

  const counts = {
    all: allStories.length,
    greek: allStories.filter((s) => s.mythology.slug === 'greek').length,
    norse: allStories.filter((s) => s.mythology.slug === 'norse').length,
    egyptian: allStories.filter((s) => s.mythology.slug === 'egyptian').length
  };

  root.replaceChildren(
    h('p', { class: 'crumbs' }, h('a', { href: '/' }, 'Home'), h('span', { class: 'crumb-sep' }, '›'), 'Stories & Myths'),
    h('div', { class: 'page-head' },
      h('h1', {}, 'Stories & Mythological Narratives'),
      h('p', { class: 'intro' },
        'Epic conflicts, cosmological creation accounts, and legendary episodes grounded in ancient textual attestations.'
      )
    ),
    h('div', { class: 'sources-toolbar' },
      h('div', { class: 'filter-tabs' },
        ['all', 'greek', 'norse', 'egyptian'].map((m) => h('button', {
          class: `tab-btn ${activeMyth === m ? 'active' : ''}`,
          type: 'button',
          onclick: () => { activeMyth = m; render(); }
        }, `${m === 'all' ? 'All Traditions' : label(m)} (${counts[m] || 0})`))
      ),
      h('input', {
        class: 'input-search',
        type: 'search',
        placeholder: 'Search story titles or participants…',
        value: searchQuery,
        oninput: (e) => { searchQuery = e.target.value.trim(); render(); }
      })
    ),
    h('div', { class: 'cards' }, cards.length ? cards : h('p', { class: 'empty' }, 'No stories match the selected criteria.'))
  );
}

try {
  const data = await api('/stories');
  allStories = data.items;
  render();
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, `Could not load stories: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
