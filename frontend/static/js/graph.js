// MYTHOS Interactive Knowledge Graph Engine
// Canvas-based force simulation with progressive expansion, path-finding, filtering, and minimap.
import { api, h, label, plural, icon } from './common.js';

const PALETTE = {
  deity: { fill: '#2a1f11', stroke: '#d9a441', text: '#f3e6c8', glyph: '✦' },
  primordial: { fill: '#1f1629', stroke: '#9b8ec4', text: '#e7defa', glyph: '✹' },
  hero: { fill: '#261b14', stroke: '#c07a3f', text: '#f7dfce', glyph: '▲' },
  creature: { fill: '#291414', stroke: '#a8321f', text: '#fcdcd7', glyph: '▼' },
  story: { fill: '#14261f', stroke: '#4e8770', text: '#d7f0e5', glyph: '◆' },
  source: { fill: '#1f2619', stroke: '#8a9a5b', text: '#e6f0d7', glyph: '■' },
  passage: { fill: '#1a2228', stroke: '#738a9c', text: '#dbe5ec', glyph: '●' },
  character: { fill: '#222026', stroke: '#b0a495', text: '#eae5dc', glyph: '●' },
};

const EDGE_COLORS = {
  genealogical: '#d9a441',
  family: '#d9a441',
  social: '#e06c75',
  narrative: '#4e8770',
  divine_symbolic: '#9b8ec4',
  cross_cultural: '#61afef',
  evidence: '#8a9a5b',
  other: '#7e758a'
};

export class MythosGraph {
  constructor(container, options = {}) {
    this.container = container;
    this.rootSlug = options.rootSlug || 'zeus';
    this.onNodeClick = options.onNodeClick || null;
    this.onNavigate = options.onNavigate || null;

    this.nodes = new Map();
    this.edges = new Map();
    this.selectedNode = null;
    this.secondSelectedNode = null;
    this.highlightedPath = null;
    this.hoveredNode = null;

    this.filters = {
      categories: new Set(['genealogical', 'family', 'social', 'narrative', 'divine_symbolic', 'cross_cultural', 'evidence', 'other']),
      includeStories: true,
      includeSources: false,
      includePassages: false
    };

    // Camera transform
    this.transform = { x: 0, y: 0, k: 1 };
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.draggedNode = null;

    this.initDOM();
    this.setupEvents();
    this.loadGraph(this.rootSlug, 1);
  }

  initDOM() {
    this.container.innerHTML = '';
    this.container.classList.add('graph-container');

    // Controls Toolbar
    this.toolbar = h('div', { class: 'graph-toolbar' },
      h('div', { class: 'graph-btn-group' },
        h('button', { class: 'btn sm ghost', title: 'Reset View & Center', onclick: () => this.resetView() }, 'Center'),
        h('button', { class: 'btn sm ghost', title: 'Zoom In', onclick: () => this.zoom(1.25) }, '+'),
        h('button', { class: 'btn sm ghost', title: 'Zoom Out', onclick: () => this.zoom(0.8) }, '−'),
        h('button', { class: 'btn sm ghost', title: 'Fit to Screen', onclick: () => this.fitView() }, 'Fit'),
        h('button', { class: 'btn sm ghost', title: 'Toggle Accessible View', onclick: () => this.toggleTableView() }, 'List View')
      ),
      h('div', { class: 'graph-filter-pills' },
        this.makePill('Genealogy', 'genealogical', true),
        this.makePill('Social', 'social', true),
        this.makePill('Narrative', 'narrative', true),
        this.makePill('Divine', 'divine_symbolic', true),
        this.makeToggle('Stories', 'includeStories', this.filters.includeStories),
        this.makeToggle('Sources', 'includeSources', this.filters.includeSources),
        this.makeToggle('Passages', 'includePassages', this.filters.includePassages)
      )
    );

    // Canvas wrapper
    this.stage = h('div', { class: 'graph-stage' });
    this.canvas = h('canvas', { class: 'graph-canvas' });
    this.minimap = h('canvas', { class: 'graph-minimap', width: '140', height: '100', title: 'Minimap' });

    // Node detail inspector
    this.inspector = h('div', { class: 'graph-inspector', hidden: true });

    // Table view container (accessible fallback)
    this.tableView = h('div', { class: 'graph-table-view', hidden: true });

    this.stage.append(this.canvas, this.minimap, this.inspector, this.tableView);
    this.container.append(this.toolbar, this.stage);

    this.ctx = this.canvas.getContext('2d');
    this.mctx = this.minimap.getContext('2d');
    this.resizeCanvas();
  }

  makePill(title, categoryKey, checked) {
    const btn = h('button', {
      class: `pill-btn ${checked ? 'active' : ''}`,
      type: 'button',
      onclick: () => {
        if (this.filters.categories.has(categoryKey)) {
          this.filters.categories.delete(categoryKey);
          btn.classList.remove('active');
        } else {
          this.filters.categories.add(categoryKey);
          btn.classList.add('active');
        }
        this.render();
        this.updateTableView();
      }
    }, title);
    return btn;
  }

  makeToggle(title, filterKey, checked) {
    const btn = h('button', {
      class: `pill-btn toggle ${checked ? 'active' : ''}`,
      type: 'button',
      onclick: async () => {
        this.filters[filterKey] = !this.filters[filterKey];
        btn.classList.toggle('active', this.filters[filterKey]);
        await this.reloadCurrent();
      }
    }, title);
    return btn;
  }

  resizeCanvas() {
    const rect = this.stage.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.width = rect.width || 800;
    this.height = rect.height || 550;
    this.canvas.width = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  async loadGraph(slug, depth = 1) {
    this.currentSlug = slug;
    try {
      this.inspector.hidden = true;
      const data = await api(`/characters/${slug}/graph`, {
        depth: depth,
        include_stories: this.filters.includeStories,
        include_sources: this.filters.includeSources,
        include_passages: this.filters.includePassages
      });
      this.populateData(data);
      this.resetView();
      this.startSimulation();
    } catch (e) {
      this.container.append(h('p', { class: 'error' }, `Graph could not load: ${e.message}`));
    }
  }

  async reloadCurrent() {
    await this.loadGraph(this.currentSlug, 1);
  }

  populateData(data) {
    const existingPos = new Map();
    for (const [id, n] of this.nodes.entries()) {
      existingPos.set(id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy });
    }

    this.nodes.clear();
    this.edges.clear();
    this.rootNodeId = data.root;

    data.nodes.forEach((n, idx) => {
      const prev = existingPos.get(n.id);
      const angle = (idx / Math.max(1, data.nodes.length)) * Math.PI * 2;
      const radius = n.is_root ? 0 : (n.degree === 1 ? 160 : 280);
      const x = prev ? prev.x : Math.cos(angle) * radius + (Math.random() - 0.5) * 20;
      const y = prev ? prev.y : Math.sin(angle) * radius + (Math.random() - 0.5) * 20;
      this.nodes.set(n.id, {
        ...n,
        x, y,
        vx: prev ? prev.vx : 0,
        vy: prev ? prev.vy : 0,
        radius: n.is_root ? 26 : (n.entity_type === 'character' ? 18 : (n.entity_type === 'story' ? 16 : 14))
      });
    });

    data.edges.forEach((e) => {
      if (this.nodes.has(e.source) && this.nodes.has(e.target)) {
        this.edges.set(e.id, { ...e });
      }
    });

    this.updateTableView();
  }

  startSimulation() {
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
    let iterations = 140;
    const step = () => {
      if (iterations > 0) {
        this.tickPhysics();
        iterations--;
      }
      this.render();
      this.animFrame = requestAnimationFrame(step);
    };
    this.animFrame = requestAnimationFrame(step);
  }

  tickPhysics() {
    const nodeList = Array.from(this.nodes.values());
    const kRepel = 2200;
    const kSpring = 0.045;
    const desiredDist = 130;

    // Node-node repulsion
    for (let i = 0; i < nodeList.length; i++) {
      const a = nodeList[i];
      for (let j = i + 1; j < nodeList.length; j++) {
        const b = nodeList[j];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distSq = dx * dx + dy * dy || 1;
        let dist = Math.sqrt(distSq);
        if (dist < 400) {
          let force = kRepel / (distSq + 20);
          let fx = (dx / dist) * force;
          let fy = (dy / dist) * force;
          if (!a.is_root && a !== this.draggedNode) { a.vx -= fx; a.vy -= fy; }
          if (!b.is_root && b !== this.draggedNode) { b.vx += fx; b.vy += fy; }
        }
      }
    }

    // Edge spring forces
    for (const e of this.edges.values()) {
      if (!this.isEdgeVisible(e)) continue;
      const a = this.nodes.get(e.source);
      const b = this.nodes.get(e.target);
      if (!a || !b) continue;
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      let dist = Math.sqrt(dx * dx + dy * dy) || 1;
      let diff = dist - desiredDist;
      let fx = (dx / dist) * diff * kSpring;
      let fy = (dy / dist) * diff * kSpring;
      if (!a.is_root && a !== this.draggedNode) { a.vx += fx; a.vy += fy; }
      if (!b.is_root && b !== this.draggedNode) { b.vx -= fx; b.vy -= fy; }
    }

    // Centering & velocity damping
    for (const n of nodeList) {
      if (n.is_root) {
        n.vx = 0; n.vy = 0; n.x = 0; n.y = 0;
        continue;
      }
      if (n === this.draggedNode) continue;
      n.vx += -n.x * 0.002;
      n.vy += -n.y * 0.002;
      n.vx *= 0.85;
      n.vy *= 0.85;
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  isEdgeVisible(e) {
    if (e.category && !this.filters.categories.has(e.category)) return false;
    return true;
  }

  render() {
    const ctx = this.ctx;
    ctx.save();
    ctx.clearRect(0, 0, this.width, this.height);

    // Camera transform
    ctx.translate(this.width / 2 + this.transform.x, this.height / 2 + this.transform.y);
    ctx.scale(this.transform.k, this.transform.k);

    // Draw edges
    for (const e of this.edges.values()) {
      if (!this.isEdgeVisible(e)) continue;
      const s = this.nodes.get(e.source);
      const t = this.nodes.get(e.target);
      if (!s || !t) continue;

      const isPath = this.highlightedPath && this.highlightedPath.edges.has(e.id);
      const isConnected = this.selectedNode && (e.source === this.selectedNode.id || e.target === this.selectedNode.id);
      const baseColor = EDGE_COLORS[e.category] || EDGE_COLORS.other;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);

      if (isPath) {
        ctx.strokeStyle = '#ffd700';
        ctx.lineWidth = 3.5;
        ctx.shadowColor = '#d9a441';
        ctx.shadowBlur = 10;
      } else if (isConnected) {
        ctx.strokeStyle = baseColor;
        ctx.lineWidth = 2.4;
      } else {
        ctx.strokeStyle = this.selectedNode ? 'rgba(120, 110, 130, 0.2)' : baseColor;
        ctx.globalAlpha = this.selectedNode ? 0.2 : 0.6;
        ctx.lineWidth = 1.2;
      }
      ctx.stroke();

      // Directed Arrowhead
      if (e.directed && dist(s, t) > 40) {
        const angle = Math.atan2(t.y - s.y, t.x - s.x);
        const arrowDist = t.radius + 6;
        const ax = t.x - Math.cos(angle) * arrowDist;
        const ay = t.y - Math.sin(angle) * arrowDist;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - 9 * Math.cos(angle - Math.PI / 6), ay - 9 * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(ax - 9 * Math.cos(angle + Math.PI / 6), ay - 9 * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();
      }

      // Edge label (drawn when hovered, selected, or high zoom)
      if (isConnected || isPath || this.transform.k > 1.3) {
        const mx = (s.x + t.x) / 2;
        const my = (s.y + t.y) / 2;
        ctx.font = '10px "Cinzel", serif';
        ctx.fillStyle = isPath ? '#ffd700' : 'rgba(230, 220, 200, 0.9)';
        ctx.textAlign = 'center';
        ctx.fillText(e.label, mx, my - 4);
      }
      ctx.restore();
    }

    // Draw nodes
    for (const n of this.nodes.values()) {
      const isSelected = this.selectedNode && this.selectedNode.id === n.id;
      const isSecond = this.secondSelectedNode && this.secondSelectedNode.id === n.id;
      const isHovered = this.hoveredNode && this.hoveredNode.id === n.id;
      const isPath = this.highlightedPath && this.highlightedPath.nodes.has(n.id);
      const style = PALETTE[n.node_type] || PALETTE.character;

      ctx.save();
      // Outer glow for selected or path
      if (isSelected || isSecond || isPath) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 6, 0, Math.PI * 2);
        ctx.fillStyle = isPath ? 'rgba(217, 164, 65, 0.4)' : 'rgba(217, 164, 65, 0.3)';
        ctx.fill();
      }

      // Node body
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = style.fill;
      ctx.fill();

      // Node border
      ctx.lineWidth = isSelected || isSecond ? 2.8 : (n.is_root ? 2.4 : 1.5);
      ctx.strokeStyle = isSelected || isSecond ? '#ffd700' : style.stroke;
      ctx.stroke();

      // Node Glyph / Symbol
      ctx.font = `${Math.round(n.radius * 0.9)}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = style.stroke;
      ctx.fillText(style.glyph, n.x, n.y + 1);

      // Label below node
      ctx.font = `${n.is_root ? '600 13px' : '500 11px'} "Cinzel", serif`;
      ctx.fillStyle = isSelected ? '#ffd700' : (isHovered ? '#fff' : style.text);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(n.label, n.x, n.y + n.radius + 4);

      ctx.restore();
    }

    ctx.restore();
    this.renderMinimap();
  }

  renderMinimap() {
    const ctx = this.mctx;
    const w = 140, h = 100;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = 'rgba(15, 12, 22, 0.85)';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(217, 164, 65, 0.3)';
    ctx.strokeRect(0, 0, w, h);

    if (!this.nodes.size) return;

    let minX = 0, maxX = 0, minY = 0, maxY = 0;
    for (const n of this.nodes.values()) {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    }
    const spanX = Math.max(300, maxX - minX + 80);
    const spanY = Math.max(200, maxY - minY + 80);
    const scale = Math.min((w - 20) / spanX, (h - 20) / spanY);

    const mapX = (x) => w / 2 + (x - (minX + maxX) / 2) * scale;
    const mapY = (y) => h / 2 + (y - (minY + maxY) / 2) * scale;

    // Minimap nodes
    for (const n of this.nodes.values()) {
      ctx.beginPath();
      ctx.arc(mapX(n.x), mapY(n.y), n.is_root ? 3 : 1.8, 0, Math.PI * 2);
      ctx.fillStyle = n.is_root ? '#ffd700' : (PALETTE[n.node_type] || PALETTE.character).stroke;
      ctx.fill();
    }

    // Viewport rectangle
    const vpW = (this.width / this.transform.k) * scale;
    const vpH = (this.height / this.transform.k) * scale;
    const vpX = mapX(-this.transform.x / this.transform.k) - vpW / 2;
    const vpY = mapY(-this.transform.y / this.transform.k) - vpH / 2;
    ctx.strokeStyle = 'rgba(217, 164, 65, 0.7)';
    ctx.lineWidth = 1;
    ctx.strokeRect(vpX, vpY, vpW, vpH);
  }

  setupEvents() {
    window.addEventListener('resize', () => {
      this.resizeCanvas();
      this.render();
    });

    this.canvas.setAttribute('tabindex', '0');
    this.canvas.setAttribute('role', 'region');
    this.canvas.setAttribute('aria-label', 'Interactive Relationship Graph. Use arrow keys to pan, + and - to zoom, 0 to reset, Enter to expand selected node.');

    this.canvas.addEventListener('keydown', (e) => {
      let handled = true;
      if (e.key === 'ArrowLeft') { this.transform.x += 40; }
      else if (e.key === 'ArrowRight') { this.transform.x -= 40; }
      else if (e.key === 'ArrowUp') { this.transform.y += 40; }
      else if (e.key === 'ArrowDown') { this.transform.y -= 40; }
      else if (e.key === '+' || e.key === '=') { this.zoom(1.2); }
      else if (e.key === '-' || e.key === '_') { this.zoom(0.8); }
      else if (e.key === '0') { this.resetView(); }
      else if ((e.key === 'Enter' || e.key === ' ') && this.selectedNode) {
        this.expandNode(this.selectedNode);
      } else {
        handled = false;
      }
      if (handled) {
        e.preventDefault();
        this.render();
      }
    });

    const getPos = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return {
        screenX: clientX - rect.left,
        screenY: clientY - rect.top,
        x: (clientX - rect.left - this.width / 2 - this.transform.x) / this.transform.k,
        y: (clientY - rect.top - this.height / 2 - this.transform.y) / this.transform.k
      };
    };

    const findNodeAt = (pos) => {
      for (const n of this.nodes.values()) {
        const d = Math.sqrt((n.x - pos.x) ** 2 + (n.y - pos.y) ** 2);
        if (d <= n.radius + 4) return n;
      }
      return null;
    };

    this.canvas.addEventListener('mousedown', (e) => {
      const pos = getPos(e);
      const hit = findNodeAt(pos);
      if (hit) {
        this.draggedNode = hit;
      } else {
        this.isDragging = true;
        this.dragStart = { x: e.clientX - this.transform.x, y: e.clientY - this.transform.y };
      }
    });

    this.canvas.addEventListener('mousemove', (e) => {
      const pos = getPos(e);
      if (this.draggedNode) {
        this.draggedNode.x = pos.x;
        this.draggedNode.y = pos.y;
        this.render();
      } else if (this.isDragging) {
        this.transform.x = e.clientX - this.dragStart.x;
        this.transform.y = e.clientY - this.dragStart.y;
        this.render();
      } else {
        const hit = findNodeAt(pos);
        if (hit !== this.hoveredNode) {
          this.hoveredNode = hit;
          this.canvas.style.cursor = hit ? 'pointer' : 'grab';
          this.render();
        }
      }
    });

    const onUp = (e) => {
      if (this.draggedNode && !this.isDragging) {
        const hit = this.draggedNode;
        this.draggedNode = null;
        if (e.shiftKey) {
          // Multi-selection for path highlighting
          this.handleMultiSelect(hit);
        } else {
          this.handleNodeClick(hit);
        }
      } else {
        this.draggedNode = null;
        this.isDragging = false;
      }
    };

    this.canvas.addEventListener('mouseup', onUp);
    this.canvas.addEventListener('mouseleave', () => {
      this.isDragging = false;
      this.draggedNode = null;
      this.hoveredNode = null;
    });

    // Mouse wheel zoom
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      this.zoom(zoomFactor, e.clientX, e.clientY);
    });

    // Touch support
    this.canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        const pos = getPos(e);
        const hit = findNodeAt(pos);
        if (hit) {
          this.draggedNode = hit;
        } else {
          this.isDragging = true;
          this.dragStart = { x: e.touches[0].clientX - this.transform.x, y: e.touches[0].clientY - this.transform.y };
        }
      }
    });

    this.canvas.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1) {
        const pos = getPos(e);
        if (this.draggedNode) {
          this.draggedNode.x = pos.x;
          this.draggedNode.y = pos.y;
          this.render();
        } else if (this.isDragging) {
          this.transform.x = e.touches[0].clientX - this.dragStart.x;
          this.transform.y = e.touches[0].clientY - this.dragStart.y;
          this.render();
        }
      }
    });

    this.canvas.addEventListener('touchend', (e) => {
      if (this.draggedNode) {
        const hit = this.draggedNode;
        this.draggedNode = null;
        this.handleNodeClick(hit);
      }
      this.isDragging = false;
    });
  }

  handleNodeClick(n) {
    this.selectedNode = n;
    this.secondSelectedNode = null;
    this.highlightedPath = null;
    this.showInspector(n);
    this.render();
    if (this.onNodeClick) this.onNodeClick(n);
  }

  handleMultiSelect(n) {
    if (!this.selectedNode) {
      this.handleNodeClick(n);
      return;
    }
    this.secondSelectedNode = n;
    this.highlightedPath = this.findShortestPath(this.selectedNode.id, n.id);
    this.showPathInspector(this.selectedNode, n, this.highlightedPath);
    this.render();
  }

  findShortestPath(startId, endId) {
    if (startId === endId) return { nodes: new Set([startId]), edges: new Set() };
    const queue = [[startId]];
    const visited = new Set([startId]);
    const edgeMap = new Map(); // target -> edgeId used to reach it

    // Build adjacency
    const adj = new Map();
    for (const e of this.edges.values()) {
      if (!this.isEdgeVisible(e)) continue;
      if (!adj.has(e.source)) adj.set(e.source, []);
      if (!adj.has(e.target)) adj.set(e.target, []);
      adj.get(e.source).push({ next: e.target, edgeId: e.id });
      adj.get(e.target).push({ next: e.source, edgeId: e.id });
    }

    while (queue.length > 0) {
      const path = queue.shift();
      const cur = path[path.length - 1];
      if (cur === endId) {
        const edgeSet = new Set();
        for (let i = 0; i < path.length - 1; i++) {
          const u = path[i], v = path[i + 1];
          const found = (adj.get(u) || []).find((x) => x.next === v);
          if (found) edgeSet.add(found.edgeId);
        }
        return { nodes: new Set(path), edges: edgeSet, pathList: path };
      }
      for (const neighbor of adj.get(cur) || []) {
        if (!visited.has(neighbor.next)) {
          visited.add(neighbor.next);
          queue.push([...path, neighbor.next]);
        }
      }
    }
    return null; // No path found
  }

  showInspector(n) {
    this.inspector.hidden = false;
    let url = '#';
    if (n.entity_type === 'character') url = `/characters/${n.slug}`;
    else if (n.entity_type === 'story') url = `/stories/${n.slug}`;
    else if (n.entity_type === 'source') url = `/sources/${n.slug}`;

    const connectedEdges = Array.from(this.edges.values()).filter(
      (e) => (e.source === n.id || e.target === n.id) && this.isEdgeVisible(e)
    );

    const relList = connectedEdges.map((e) => {
      const otherId = e.source === n.id ? e.target : e.source;
      const otherNode = this.nodes.get(otherId);
      const isSrc = e.source === n.id;
      const relLabel = isSrc ? e.label : (e.inverse_label || `Related to (${e.label})`);
      const otherName = otherNode ? otherNode.label : otherId;
      return h('li', { class: 'inspector-rel-item' },
        h('span', { class: 'rel-tag' }, relLabel),
        h('span', { class: 'rel-target' }, ' ', otherName),
        e.evidence && e.evidence.length ? h('span', { class: 'chip sm' }, `${e.evidence.length} citations`) : null
      );
    });

    this.inspector.replaceChildren(
      h('div', { class: 'inspector-head' },
        h('div', {},
          h('h3', {}, n.label),
          h('span', { class: 'meta' }, [
            n.node_type ? label(n.node_type) : null,
            n.tradition_name || null,
            n.mythology_name || null
          ].filter(Boolean).join(' · '))
        ),
        h('button', { class: 'btn-close', type: 'button', 'aria-label': 'Close panel', onclick: () => { this.inspector.hidden = true; } }, '×')
      ),
      n.summary ? h('p', { class: 'blurb' }, n.summary) : null,
      h('div', { class: 'inspector-actions' },
        n.entity_type === 'character' ? h('button', {
          class: 'btn sm primary',
          type: 'button',
          onclick: () => this.expandNode(n)
        }, 'Expand Connections') : null,
        url !== '#' ? h('a', { class: 'btn sm ghost', href: url }, 'View Full Profile →') : null
      ),
      connectedEdges.length ? h('div', { class: 'inspector-rels' },
        h('h4', {}, `Connections (${connectedEdges.length})`),
        h('ul', {}, relList)
      ) : null,
      h('p', { class: 'help-text' }, 'Tip: Hold Shift and click a second node to trace paths between them.')
    );
  }

  showPathInspector(startNode, endNode, pathObj) {
    this.inspector.hidden = false;
    if (!pathObj) {
      this.inspector.replaceChildren(
        h('div', { class: 'inspector-head' },
          h('h3', {}, 'No Connection Found'),
          h('button', { class: 'btn-close', type: 'button', onclick: () => { this.inspector.hidden = true; } }, '×')
        ),
        h('p', { class: 'blurb' }, `No direct or indirect connections found between ${startNode.label} and ${endNode.label} under current filters.`)
      );
      return;
    }

    const steps = pathObj.pathList.map((id) => this.nodes.get(id)?.label || id).join(' → ');
    this.inspector.replaceChildren(
      h('div', { class: 'inspector-head' },
        h('h3', {}, 'Path Traced'),
        h('button', { class: 'btn-close', type: 'button', onclick: () => { this.inspector.hidden = true; } }, '×')
      ),
      h('p', { class: 'blurb' }, h('strong', {}, 'Shortest Connection: '), steps),
      h('p', { class: 'help-text' }, `${pathObj.edges.size} steps between ${startNode.label} and ${endNode.label}. Highlighted on graph.`)
    );
  }

  async expandNode(n) {
    if (n.entity_type !== 'character') return;
    try {
      const data = await api(`/characters/${n.slug}/graph`, {
        depth: 1,
        include_stories: this.filters.includeStories,
        include_sources: this.filters.includeSources,
        include_passages: this.filters.includePassages
      });

      // Merge newly discovered nodes and edges
      data.nodes.forEach((newNode) => {
        if (!this.nodes.has(newNode.id)) {
          const angle = Math.random() * Math.PI * 2;
          this.nodes.set(newNode.id, {
            ...newNode,
            x: n.x + Math.cos(angle) * 140,
            y: n.y + Math.sin(angle) * 140,
            vx: 0, vy: 0,
            radius: newNode.entity_type === 'character' ? 18 : 14
          });
        }
      });

      data.edges.forEach((newEdge) => {
        if (this.nodes.has(newEdge.source) && this.nodes.has(newEdge.target)) {
          this.edges.set(newEdge.id, newEdge);
        }
      });

      this.startSimulation();
      this.showInspector(n);
      this.updateTableView();
    } catch (e) {
      console.error('Failed to expand node:', e);
    }
  }

  updateTableView() {
    if (!this.tableView) return;
    const rows = [];
    for (const n of this.nodes.values()) {
      const connectedEdges = Array.from(this.edges.values()).filter(
        (e) => (e.source === n.id || e.target === n.id) && this.isEdgeVisible(e)
      );
      rows.push(h('tr', {},
        h('td', {}, h('strong', {}, n.label)),
        h('td', {}, label(n.node_type || n.entity_type)),
        h('td', {}, n.mythology_name || n.mythology || '—'),
        h('td', {}, n.tradition_name || '—'),
        h('td', {}, `${connectedEdges.length} connections`),
        h('td', {},
          n.entity_type === 'character' ? h('a', { href: `/characters/${n.slug}` }, 'Profile') :
          (n.entity_type === 'story' ? h('a', { href: `/stories/${n.slug}` }, 'Story') :
          (n.entity_type === 'source' ? h('a', { href: `/sources/${n.slug}` }, 'Source') : '—'))
        )
      ));
    }

    this.tableView.replaceChildren(
      h('h3', {}, 'Accessible Node & Relationship Catalog'),
      h('table', { class: 'data-table' },
        h('thead', {},
          h('tr', {},
            h('th', {}, 'Entity'),
            h('th', {}, 'Type'),
            h('th', {}, 'Mythology'),
            h('th', {}, 'Tradition'),
            h('th', {}, 'Connections'),
            h('th', {}, 'Link')
          )
        ),
        h('tbody', {}, rows)
      )
    );
  }

  toggleTableView() {
    const isHidden = this.tableView.hidden;
    this.tableView.hidden = !isHidden;
    this.canvas.style.display = isHidden ? 'none' : 'block';
    this.minimap.style.display = isHidden ? 'none' : 'block';
  }

  zoom(factor) {
    this.transform.k = Math.max(0.3, Math.min(3.5, this.transform.k * factor));
    this.render();
  }

  resetView() {
    this.transform = { x: 0, y: 0, k: 1 };
    this.render();
  }

  fitView() {
    if (!this.nodes.size) return;
    let minX = 0, maxX = 0, minY = 0, maxY = 0;
    for (const n of this.nodes.values()) {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    }
    const spanX = Math.max(200, maxX - minX + 120);
    const spanY = Math.max(200, maxY - minY + 120);
    const k = Math.min((this.width - 60) / spanX, (this.height - 60) / spanY, 1.8);
    this.transform = {
      x: -((minX + maxX) / 2) * k,
      y: -((minY + maxY) / 2) * k,
      k: Math.max(0.4, k)
    };
    this.render();
  }
}

function dist(a, b) {
  return Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2);
}
