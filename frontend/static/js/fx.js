// Atmosphere and interaction layer: starfield, pointer light, reveals, theme, sigils.
// Everything here is decoration or progressive enhancement; the site works without it.
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
const root = document.documentElement;
const html = (s) => { const t = document.createElement('template'); t.innerHTML = s.trim(); return t.content.firstElementChild; };

/* ---------- Sigils: one emblem per tradition ---------- */
const SIGILS = {
  greek: `<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linejoin="round" aria-hidden="true">
    <circle cx="50" cy="50" r="46"/><circle cx="50" cy="50" r="41" stroke-dasharray="1.4 3.2"/>
    <path d="M50 11l7.6 31.4L89 50l-31.4 7.6L50 89l-7.6-31.4L11 50l31.4-7.6z"/>
    <path d="M23 23l54 54M77 23L23 77" opacity=".45"/><circle cx="50" cy="50" r="15"/><circle cx="50" cy="50" r="4.5" fill="currentColor" stroke="none"/></svg>`,
  norse: `<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" aria-hidden="true">
    <circle cx="50" cy="50" r="46"/><circle cx="50" cy="50" r="41" stroke-dasharray="1.4 3.2"/>
    <g id="vk"><path d="M50 52L33 21H67Z"/><path d="M50 52L38 28H62Z" opacity=".55"/></g>
    <use href="#vk" transform="rotate(120 50 50)"/><use href="#vk" transform="rotate(240 50 50)"/>
    <circle cx="50" cy="50" r="3.4" fill="currentColor" stroke="none"/></svg>`,
  egyptian: `<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <circle cx="50" cy="50" r="46"/><circle cx="50" cy="50" r="41" stroke-dasharray="1.4 3.2"/>
    <ellipse cx="50" cy="35" rx="11.5" ry="15"/><ellipse cx="50" cy="35" rx="5.5" ry="9" opacity=".5"/><path d="M50 50V82M33 60H67"/>
    <path d="M20 74Q50 62 80 74" opacity=".55"/><path d="M26 82Q50 72 74 82" opacity=".35"/></svg>`,
  default: `<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true"><circle cx="50" cy="50" r="46"/><path d="M50 12l7 31 31 7-31 7-7 31-7-31-31-7 31-7z"/></svg>`
};
export function sigil(slug, cls = '') { const el = html(SIGILS[slug] || SIGILS.default); el.setAttribute('class', `sigil ${cls}`.trim()); return el; }

export function icon(name) {
  const paths = {
    check: '<path d="M4.5 12.5l5 5L19.5 7" />',
    quill: '<path d="M20 4c-7 0-12 4-13 11l-2 5 5-2c7-1 11-6 10-14z"/><path d="M8 16l7-7"/>',
    book: '<path d="M4 5.5C7 4.5 10 4.5 12 6c2-1.5 5-1.5 8-.5V19c-3-1-6-1-8 .5C10 18 7 18 4 19z"/><path d="M12 6v13.5"/>'
  };
  return html(`<svg class="ico" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${paths[name] || ''}</svg>`);
}

/* ---------- Theme ---------- */
function initTheme() {
  const btn = document.getElementById('theme'); if (!btn) return;
  const sync = () => { const light = root.dataset.theme === 'light'; btn.setAttribute('aria-pressed', String(light)); btn.setAttribute('aria-label', light ? 'Switch to night theme' : 'Switch to parchment theme'); };
  btn.addEventListener('click', () => {
    const next = root.dataset.theme === 'light' ? 'dark' : 'light';
    root.classList.add('theme-fade'); root.dataset.theme = next; sync();
    try { localStorage.setItem('mythos-theme', next); } catch { /* private mode */ }
    setTimeout(() => root.classList.remove('theme-fade'), 600);
  });
  sync();
}

/* ---------- Ambient starfield ---------- */
function initAmbient() {
  const c = document.createElement('canvas'); c.id = 'ambient'; c.setAttribute('aria-hidden', 'true'); document.body.prepend(c);
  const ctx = c.getContext('2d'); if (!ctx) return;
  let w = 0, h = 0, stars = [], motes = [], comets = [], t = 0, px = 0, py = 0, tx = 0, ty = 0, last = 0, nextComet = 6;
  const rnd = (a, b) => a + Math.random() * (b - a);
  const TINTS = ['236,232,255', '255,232,184', '184,206,255', '255,255,255'];
  const mote = (initial) => ({ x: rnd(0, w), y: initial ? rnd(0, h) : h + 10, vy: rnd(8, 22), sway: rnd(8, 26), ph: rnd(0, 6.28), r: rnd(.8, 2.2), a: rnd(.25, .7) });
  function size() {
    const dpr = Math.min(devicePixelRatio || 1, 2); w = innerWidth; h = innerHeight;
    c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.max(70, Math.min(230, Math.round(w * h / 8500)));
    stars = Array.from({ length: n }, () => ({ x: rnd(0, w), y: rnd(0, h), z: Math.random(), r: rnd(.25, 1.25) * (Math.random() < .08 ? 1.7 : 1), ph: rnd(0, 6.28), sp: rnd(.5, 1.7), tint: TINTS[(Math.random() * TINTS.length) | 0] }));
    motes = Array.from({ length: Math.round(Math.min(46, w / 30)) }, () => mote(true));
    draw(0);
  }
  function draw(dt) {
    ctx.clearRect(0, 0, w, h);
    if (root.dataset.theme === 'light') return;
    px += (tx - px) * .04; py += (ty - py) * .04;
    for (const s of stars) {
      const tw = reduce.matches ? .75 : .45 + .55 * (.5 + .5 * Math.sin(t * s.sp + s.ph));
      const x = s.x + px * s.z * 16, y = s.y + py * s.z * 16;
      ctx.fillStyle = `rgba(${s.tint},${(tw * (.35 + s.z * .6)).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(x, y, s.r, 0, 6.283); ctx.fill();
      if (s.r > 1.45) { ctx.strokeStyle = `rgba(${s.tint},${(tw * .35).toFixed(3)})`; ctx.lineWidth = .6; ctx.beginPath(); ctx.moveTo(x - s.r * 4, y); ctx.lineTo(x + s.r * 4, y); ctx.moveTo(x, y - s.r * 4); ctx.lineTo(x, y + s.r * 4); ctx.stroke(); }
    }
    ctx.globalCompositeOperation = 'lighter';
    for (const m of motes) {
      if (!reduce.matches) { m.y -= m.vy * dt; m.x += Math.sin(t * .6 + m.ph) * m.sway * dt; if (m.y < -10) Object.assign(m, mote(false)); }
      const fade = Math.min(1, Math.max(0, m.y / (h * .25)), (h - m.y) / 60 + .2), a = m.a * Math.min(1, fade);
      const g = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.r * 6);
      g.addColorStop(0, `rgba(255,214,140,${a})`); g.addColorStop(.25, `rgba(240,180,96,${a * .35})`); g.addColorStop(1, 'rgba(240,180,96,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(m.x, m.y, m.r * 6, 0, 6.283); ctx.fill();
    }
    for (let i = comets.length - 1; i >= 0; i--) {
      const k = comets[i]; k.x += k.vx * dt; k.y += k.vy * dt; k.life -= dt;
      if (k.life <= 0) { comets.splice(i, 1); continue; }
      const g = ctx.createLinearGradient(k.x, k.y, k.x - k.vx * .22, k.y - k.vy * .22);
      g.addColorStop(0, `rgba(255,244,214,${Math.min(1, k.life) * .9})`); g.addColorStop(1, 'rgba(255,244,214,0)');
      ctx.strokeStyle = g; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(k.x, k.y); ctx.lineTo(k.x - k.vx * .22, k.y - k.vy * .22); ctx.stroke();
    }
    ctx.globalCompositeOperation = 'source-over';
  }
  function frame(ts) {
    const dt = Math.min(.05, (ts - last) / 1000 || 0); last = ts; t += dt;
    if (!reduce.matches && !document.hidden) {
      nextComet -= dt; if (nextComet <= 0 && root.dataset.theme !== 'light') { nextComet = rnd(9, 20); const a = rnd(.35, .6); comets.push({ x: rnd(w * .2, w), y: rnd(0, h * .35), vx: -Math.cos(a) * rnd(520, 760), vy: Math.sin(a) * rnd(520, 760), life: 1.1 }); }
      draw(dt);
    }
    requestAnimationFrame(frame);
  }
  addEventListener('resize', size);
  addEventListener('pointermove', (e) => { tx = (e.clientX / w - .5) * 2; ty = (e.clientY / h - .5) * 2; }, { passive: true });
  reduce.addEventListener?.('change', () => draw(0));
  size(); requestAnimationFrame(frame);
}

/* ---------- Pointer light: page glow + per-card spotlight + hero parallax ---------- */
function initPointer() {
  if (!finePointer.matches) return;
  const glow = document.createElement('div'); glow.className = 'cursor-glow'; glow.setAttribute('aria-hidden', 'true'); document.body.append(glow);
  let gx = innerWidth / 2, gy = innerHeight / 2, tx = gx, ty = gy, shown = false;
  const lerp = () => { gx += (tx - gx) * .14; gy += (ty - gy) * .14; glow.style.transform = `translate3d(${gx}px,${gy}px,0)`; requestAnimationFrame(lerp); };
  requestAnimationFrame(lerp);
  addEventListener('pointermove', (e) => {
    tx = e.clientX; ty = e.clientY; if (!shown) { shown = true; glow.classList.add('on'); }
    root.style.setProperty('--px', ((e.clientX / innerWidth - .5) * 2).toFixed(3));
    root.style.setProperty('--py', ((e.clientY / innerHeight - .5) * 2).toFixed(3));
    const el = e.target.closest?.('.card,.myth-card,.panel,.cols3>div');
    if (el) { const r = el.getBoundingClientRect(); el.style.setProperty('--mx', `${e.clientX - r.left}px`); el.style.setProperty('--my', `${e.clientY - r.top}px`); }
  }, { passive: true });
  document.addEventListener('pointerleave', () => glow.classList.remove('on'));
}

/* ---------- Scroll: reveals, progress bar, header state ---------- */
const REVEAL = '.card,.myth-card,.panel,.cols3>div,.sec-title,.page-head,.profile-head,.summary-wrap,.summary,.crumbs,.chips,.results-bar,.filters,.big-search,.pager,.src-group,.rel-group,.stats';
export function reveal(scope = document) {
  if (reduce.matches || !('IntersectionObserver' in window)) return;
  const fresh = [...scope.querySelectorAll(REVEAL)].filter((el) => !el.dataset.rv);
  for (const el of fresh) { el.dataset.rv = '0'; }
  for (const el of fresh) io.observe(el);
}
const io = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
  let i = 0;
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    e.target.style.setProperty('--d', `${Math.min(i++, 10) * 55}ms`);
    e.target.dataset.rv = '1'; io.unobserve(e.target);
  }
}, { threshold: .08, rootMargin: '0px 0px -4% 0px' }) : null;

function initScroll() {
  const bar = document.querySelector('.progress'), head = document.querySelector('.site-header');
  const on = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = `scaleX(${max > 0 ? Math.min(1, scrollY / max) : 0})`;
    head?.classList.toggle('scrolled', scrollY > 12);
  };
  addEventListener('scroll', on, { passive: true }); on();
}

/* ---------- Numbers that count up ---------- */
export function countUp(el, to) {
  if (reduce.matches || !to) { el.textContent = to; return; }
  const t0 = performance.now(), dur = 1100 + Math.min(900, to * 4);
  const step = (now) => { const p = Math.min(1, (now - t0) / dur); el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); };
  el.textContent = 0; requestAnimationFrame(step);
}

/* ---------- Boot ---------- */
initTheme(); initScroll(); initAmbient(); initPointer();
// Pick up anything inserted by page scripts after the first paint.
let pending = 0;
new MutationObserver(() => { cancelAnimationFrame(pending); pending = requestAnimationFrame(() => reveal(document.getElementById('main') || document)); })
  .observe(document.getElementById('main') || document.body, { childList: true, subtree: true });
reveal();
