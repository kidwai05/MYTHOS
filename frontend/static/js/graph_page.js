import { api, h, label } from './common.js';
import { MythosGraph } from './graph.js';

const root = document.getElementById('graph-page-root');
const initialRoot = root.dataset.root || 'zeus';

root.replaceChildren(
  h('div', { class: 'graph-page-header' },
    h('div', {},
      h('h1', {}, 'Interactive Relationship Graph'),
      h('p', { class: 'intro' },
        'Explore genealogical networks, social ties, narrative conflicts, and primary-source attestations outward from any mythological figure.'
      )
    ),
    h('div', { class: 'graph-root-selector' },
      h('label', { for: 'root-select' }, 'Center graph on: '),
      h('select', {
        id: 'root-select',
        class: 'input-select',
        onchange: (e) => {
          const val = e.target.value;
          history.pushState(null, '', `/graph?root=${val}`);
          graph.loadGraph(val, 1);
        }
      },
        h('optgroup', { label: 'Greek' },
          h('option', { value: 'zeus', selected: initialRoot === 'zeus' }, 'Zeus (King of Olympians)'),
          h('option', { value: 'cronus', selected: initialRoot === 'cronus' }, 'Cronus (Titan King)'),
          h('option', { value: 'gaia', selected: initialRoot === 'gaia' }, 'Gaia (Earth Mother)'),
          h('option', { value: 'heracles', selected: initialRoot === 'heracles' }, 'Heracles (Hero)'),
          h('option', { value: 'aphrodite', selected: initialRoot === 'aphrodite' }, 'Aphrodite (Love & Beauty)'),
          h('option', { value: 'poseidon', selected: initialRoot === 'poseidon' }, 'Poseidon (Sea & Storms)')
        ),
        h('optgroup', { label: 'Norse' },
          h('option', { value: 'odin', selected: initialRoot === 'odin' }, 'Odin (Allfather)'),
          h('option', { value: 'thor', selected: initialRoot === 'thor' }, 'Thor (Thunder)'),
          h('option', { value: 'loki', selected: initialRoot === 'loki' }, 'Loki (Trickster)')
        ),
        h('optgroup', { label: 'Egyptian' },
          h('option', { value: 'osiris', selected: initialRoot === 'osiris' }, 'Osiris (Lord of the Duat)'),
          h('option', { value: 'isis', selected: initialRoot === 'isis' }, 'Isis (Goddess of Magic)'),
          h('option', { value: 'horus', selected: initialRoot === 'horus' }, 'Horus (Falcon-headed Lord)')
        )
      )
    )
  ),
  h('div', { id: 'main-graph-container', class: 'full-graph-wrapper' })
);

const graphWrapper = document.getElementById('main-graph-container');
const graph = new MythosGraph(graphWrapper, { rootSlug: initialRoot });

root.setAttribute('aria-busy', 'false');
