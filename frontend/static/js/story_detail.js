import { api, h, label, plural, icon } from './common.js';

const root = document.getElementById('story-detail-root');
const slug = root.dataset.slug;

try {
  const s = await api(`/stories/${slug}`);
  document.body.dataset.myth = s.mythology.slug;
  document.title = `${s.title} | Stories | Mythos`;

  const participantsList = s.participants.length ? h('div', { class: 'cards' },
    s.participants.map((p) => h('a', { class: 'card', href: `/characters/${p.slug}` },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, p.name[0]),
      h('span', {},
        h('h3', {}, p.name),
        h('span', { class: 'meta' }, p.role ? `Role: ${label(p.role)}` : 'Participant'),
        p.notes ? h('span', { class: 'blurb' }, p.notes) : null
      )
    ))
  ) : h('p', { class: 'empty' }, 'No participants catalogued for this story.');

  const sourcesList = s.sources.length ? h('div', { class: 'sources-block' },
    s.sources.map((l) => h('div', { class: 'src-group' },
      h('h3', {}, h('a', { href: `/sources/${l.source.slug}` }, l.source.title)),
      h('p', { class: 'src-meta' }, [
        l.source.author,
        l.source.tier ? `${label(l.source.tier)} source` : null,
        l.source.edition_used ? `Edition: ${l.source.edition_used}` : null
      ].filter(Boolean).join(' · ')),
      h('ul', { class: 'passages' },
        h('li', {},
          h('span', { class: 'loc' }, l.locator || 'Unspecified section'),
          h('span', {}, l.claim || h('em', { class: 'muted' }, 'Passage awaiting detailed extraction')),
          l.verified ? h('span', { class: 'badge ok' }, icon('check'), 'checked') :
            h('span', { class: 'badge no' }, 'unchecked')
        )
      )
    ))
  ) : h('p', { class: 'empty' }, 'No supporting textual citations recorded yet.');

  root.replaceChildren(
    h('p', { class: 'crumbs' },
      h('a', { href: '/' }, 'Home'),
      h('span', { class: 'crumb-sep' }, '›'),
      h('a', { href: '/stories' }, 'Stories'),
      h('span', { class: 'crumb-sep' }, '›'),
      s.title
    ),
    h('div', { class: 'profile-head' },
      h('span', { class: 'mono', 'aria-hidden': 'true' }, s.title[0]),
      h('div', {},
        h('h1', {}, s.title),
        h('p', { class: 'aka' }, [
          `${s.mythology.name} tradition`,
          s.tradition ? `${s.tradition.name} tradition` : null,
          plural(s.participants.length, 'participant')
        ].filter(Boolean).join(' · '))
      )
    ),
    h('div', { class: 'chips' },
      h('a', { class: 'chip accent', href: `/characters?mythology=${s.mythology.slug}` }, s.mythology.name),
      s.tradition ? h('a', { class: 'chip highlight', href: `/characters?tradition=${s.tradition.slug}` }, s.tradition.name) : null,
      h('span', { class: 'chip' }, plural(s.participants.length, 'participant'))
    ),
    s.summary ? h('div', { class: 'summary-wrap' },
      h('p', { class: 'summary' }, s.summary)
    ) : h('p', { class: 'muted summary' }, 'Narrative summary has not yet been drafted from verified textual witnesses.'),
    h('section', { class: 'panel' },
      h('h2', {}, `Story Participants (${s.participants.length})`),
      h('p', { class: 'muted' }, 'Catalogued figures in this episode and their scholarly-identified narrative roles.'),
      participantsList
    ),
    h('section', { class: 'panel' },
      h('h2', {}, `Ancient Textual Sources & Attestations (${s.sources.length})`),
      h('p', { class: 'muted' }, 'Texts attesting or recounting this episode.'),
      sourcesList
    )
  );
} catch (e) {
  root.replaceChildren(h('p', { class: 'error' }, e.status === 404 ? 'Story not found.' : `Could not load: ${e.message}`));
}
root.setAttribute('aria-busy', 'false');
