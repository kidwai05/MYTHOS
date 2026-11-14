import { api, h, label, plural, icon } from './common.js';

const root = document.getElementById('source-detail-root');
const slug = root.dataset.slug;
const TIER = { primary: 'Primary source', supplementary: 'Supplementary source', scholarly: 'Scholarly reference' };

const checkedBadge = () => h('span', { class: 'badge ok', title: 'The passage was read in the named edition' }, icon('check'), 'checked');
const uncheckedBadge = () => h('span', { class: 'badge no', title: 'Passage not yet verified in edition' }, 'unchecked');

try {
  const s = await api(`/sources/${slug}`);
  document.title = `${s.title} | Sources | Mythos`;

  // Status lifecycle pills
  const LIFECYCLE = ['catalogued', 'edition-chosen', 'reading', 'extracted', 'verified'];
  const curIdx = LIFECYCLE.indexOf(s.status);
  const statusMeter = h('div', { class: 'status-lifecycle' },
    h('span', { class: 'lifecycle-label' }, 'Research status:'),
    h('div', { class: 'lifecycle-steps' },
      LIFECYCLE.map((step, idx) => h('span', {
        class: `step ${idx <= curIdx ? 'done' : ''} ${idx === curIdx ? 'current' : ''}`,
        title: `Research stage: ${label(step)}`
      }, label(step)))
    )
  );

  // Passages Section
  const passagesTable = s.passages.length ? h('table', { class: 'data-table' },
    h('thead', {},
      h('tr', {},
        h('th', {}, 'Locator'),
        h('th', {}, 'Verification'),
        h('th', {}, 'Entities Supported'),
        h('th', {}, 'Notes')
      )
    ),
    h('tbody', {}, s.passages.map((p) => {
      const charLinks = (s.characters_mentioned || []).filter((c) => c.locator === p.locator);
      const relLinks = (s.relationships_supported || []).filter((r) => r.locator === p.locator);
      const storyLinks = (s.stories_associated || []).filter((st) => st.locator === p.locator);
      return h('tr', {},
        h('td', { class: 'loc' }, h('strong', {}, p.locator)),
        h('td', {}, p.verified ? checkedBadge() : uncheckedBadge()),
        h('td', {},
          charLinks.length ? h('div', { class: 'passage-entity-list' },
            h('span', { class: 'meta' }, 'Characters: '),
            charLinks.map((c) => h('a', { class: 'chip sm', href: `/characters/${c.slug}` }, c.name))
          ) : null,
          relLinks.length ? h('div', { class: 'passage-entity-list' },
            h('span', { class: 'meta' }, 'Relationships: '),
            relLinks.map((r) => h('span', { class: 'chip sm' }, `${r.source.name} ↔ ${r.target.name}`))
          ) : null,
          storyLinks.length ? h('div', { class: 'passage-entity-list' },
            h('span', { class: 'meta' }, 'Stories: '),
            storyLinks.map((st) => h('a', { class: 'chip sm accent', href: `/stories/${st.slug}` }, st.title))
          ) : null
        ),
        h('td', { class: 'notes-cell' }, p.notes || '—')
      );
    }))
  ) : h('p', { class: 'empty' }, 'No individual passages logged yet for this text.');

  // Characters mentioned
  const charsGrid = s.characters_mentioned.length ? h('div', { class: 'cards' },
    s.characters_mentioned.map((c) => h('a', { class: 'card', href: `/characters/${c.slug}` },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, c.name[0]),
      h('span', {},
        h('h3', {}, c.name),
        h('span', { class: 'meta' }, [c.mythology.name, c.relation ? `Relation: ${c.relation}` : null].filter(Boolean).join(' · ')),
        c.claim ? h('span', { class: 'blurb' }, c.claim) : null,
        h('span', { class: 'meta' }, c.locator ? `Locator: ${c.locator}` : null)
      )
    ))
  ) : h('p', { class: 'empty' }, 'No characters directly linked to this text yet.');

  // Relationships supported
  const relsTable = s.relationships_supported.length ? h('table', { class: 'data-table' },
    h('thead', {},
      h('tr', {},
        h('th', {}, 'Source Entity'),
        h('th', {}, 'Relationship'),
        h('th', {}, 'Target Entity'),
        h('th', {}, 'Locator & Claim')
      )
    ),
    h('tbody', {}, s.relationships_supported.map((r) => h('tr', {},
      h('td', {}, h('a', { href: `/characters/${r.source.slug}` }, r.source.name)),
      h('td', {}, h('span', { class: 'chip' }, r.label)),
      h('td', {}, h('a', { href: `/characters/${r.target.slug}` }, r.target.name)),
      h('td', {}, h('span', { class: 'loc' }, r.locator), ' ', r.claim || '')
    )))
  ) : h('p', { class: 'empty' }, 'No relationships supported by this text yet.');

  // Stories associated
  const storiesList = s.stories_associated.length ? h('ul', { class: 'stories-list' },
    s.stories_associated.map((st) => h('li', { class: 'story-item' },
      h('a', { href: `/stories/${st.slug}`, class: 'story-link' }, st.title),
      st.locator ? h('span', { class: 'loc' }, st.locator) : null,
      st.claim ? h('span', { class: 'claim-text' }, st.claim) : null
    ))
  ) : h('p', { class: 'empty' }, 'No stories associated with this source yet.');

  root.replaceChildren(
    h('p', { class: 'crumbs' },
      h('a', { href: '/' }, 'Home'),
      h('span', { class: 'crumb-sep' }, '›'),
      h('a', { href: '/sources' }, 'Sources'),
      h('span', { class: 'crumb-sep' }, '›'),
      s.title
    ),
    h('div', { class: 'profile-head' },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, s.title[0]),
      h('div', {},
        h('h1', {}, s.title),
        h('p', { class: 'aka' }, [
          s.author ? `By ${s.author}` : 'Author: Anonymous / Traditional',
          s.period_or_origin ? `Period: ${s.period_or_origin}` : null,
          s.collection ? `Collection: ${s.collection}` : null
        ].filter(Boolean).join(' · '))
      )
    ),
    h('div', { class: 'chips' },
      h('span', { class: 'chip accent' }, TIER[s.tier] || s.tier),
      s.kind ? h('span', { class: 'chip' }, label(s.kind)) : null,
      s.license ? h('span', { class: 'chip' }, s.license) : null
    ),
    statusMeter,
    h('div', { class: 'panel source-meta-box' },
      h('h2', {}, 'Edition & Text Provenance'),
      s.edition_used ? h('p', { class: 'edition-info' }, h('strong', {}, 'Edition used: '), s.edition_used) :
        h('p', { class: 'muted' }, 'A canonical public-domain edition has not yet been selected for this seed source.'),
      s.url ? h('p', {}, h('a', { class: 'btn sm primary', href: s.url, target: '_blank', rel: 'noopener' }, 'Open Public-Domain Translation ↗')) : null,
      h('div', { class: 'meta-stats-row' },
        h('div', { class: 'stat-pill' }, h('span', { class: 'stat-num' }, String(s.counts.passages)), ' passages recorded'),
        h('div', { class: 'stat-pill' }, h('span', { class: 'stat-num' }, String(s.counts.characters)), ' characters mentioned'),
        h('div', { class: 'stat-pill' }, h('span', { class: 'stat-num' }, String(s.counts.relationships)), ' relationships attested'),
        h('div', { class: 'stat-pill' }, h('span', { class: 'stat-num' }, String(s.counts.stories)), ' stories witnessed')
      )
    ),
    h('section', { class: 'panel' },
      h('h2', {}, `Recorded Passages (${s.counts.passages})`),
      h('p', { class: 'muted' }, 'Every passage listed below is an identifiable text locator in our chosen edition with its direct evidential citations.'),
      passagesTable
    ),
    h('section', { class: 'panel' },
      h('h2', {}, `Characters Attested in this Text (${s.counts.characters})`),
      charsGrid
    ),
    h('section', { class: 'panel' },
      h('h2', {}, `Relationships Grounded in this Source (${s.counts.relationships})`),
      relsTable
    ),
    h('section', { class: 'panel' },
      h('h2', {}, `Stories Documented (${s.counts.stories})`),
      storiesList
    )
  );
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, e.status === 404 ? 'Source not found.' : `Could not load: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
