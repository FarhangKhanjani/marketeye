// Shared helpers and charts for index.html and history.html.
const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fmtPct = v => (v > 0 ? "+" : "") + v.toFixed(2) + "%";
const fmtVol = v => Math.round(v).toLocaleString("en-US");
const show = code => code.replace(/^_+/, "") || code;   // LCW prefixes duplicate tickers with underscores
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));


// Beeswarm of coins by 24h % vs BTC. d = {long, short, outliers}; settings = ranges for the shaded zones.
function drawTape(svg, d, settings) {
  const longS = new Set(d.long.map(c => c.code)), shortS = new Set(d.short.map(c => c.code));
  const coins = [...new Map([...d.long, ...d.short, ...d.outliers].map(c => [c.code, c])).values()].map(c => ({
    ...c, b: longS.has(c.code) && shortS.has(c.code) ? "both" : longS.has(c.code) ? "long" : shortS.has(c.code) ? "short" : "outlier" }));
  const W = 900, H = 300, m = { l: 20, r: 20, t: 28, b: 34 };
  const L = settings.long_range, Sr = settings.short_range;
  const pcts = coins.map(c => c.pct).concat([L.min_pct, L.max_pct, Sr.min_pct, Sr.max_pct]);
  const lo = Math.min(-15, Math.floor(Math.min(...pcts) / 5) * 5), hi = Math.max(15, Math.ceil(Math.max(...pcts) / 5) * 5);
  const step = (hi - lo) > 80 ? 20 : (hi - lo) > 40 ? 10 : 5;
  const x = v => m.l + (v - lo) / (hi - lo) * (W - m.l - m.r), cy = m.t + (H - m.t - m.b) / 2;
  svg.innerHTML = ""; svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.style.cssText = "width:100%;min-width:640px;display:block";
  el("rect", { x: x(L.min_pct), y: m.t, width: x(L.max_pct) - x(L.min_pct), height: H - m.t - m.b, fill: "var(--long-tint)" }, svg);
  el("rect", { x: x(Sr.min_pct), y: m.t, width: x(Sr.max_pct) - x(Sr.min_pct), height: H - m.t - m.b, fill: "var(--short-tint)" }, svg);
  el("text", { x: x(L.max_pct) - 6, y: m.t - 10, "text-anchor": "end", style: "fill:var(--long)" }, svg).textContent = "LONG ZONE →";
  el("text", { x: x(Sr.min_pct) + 6, y: m.t - 10, style: "fill:var(--short)" }, svg).textContent = "← SHORT ZONE";
  for (let t = Math.ceil(lo / step) * step; t <= hi; t += step) {
    el("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, stroke: "var(--line)", "stroke-width": t === 0 ? 1.5 : 1 }, svg);
    el("text", { x: x(t), y: H - m.b + 18, "text-anchor": "middle" }, svg).textContent = (t > 0 ? "+" : "") + t + "%";
  }
  const r = v => 3.5 + 3.2 * Math.log10(Math.max(v, 500) / 500);
  const placed = [];
  [...coins].sort((a, b) => b.vol - a.vol).forEach(c => {
    const px = x(c.pct), rad = r(c.vol); let py = cy;
    for (let i = 0; i < 400; i++) { py = cy + Math.ceil(i / 2) * 2 * (i % 2 ? -1 : 1); if (!placed.some(p => Math.hypot(p.x - px, p.y - py) < p.r + rad + 1)) break; }
    placed.push({ x: px, y: py, r: rad, c });
  });
  const col = { long: "var(--long)", short: "var(--short)", both: "var(--both)", outlier: "var(--outlier)" };
  placed.forEach(p => {
    const dot = el("circle", { cx: p.x, cy: p.y, r: p.r, fill: col[p.c.b], "fill-opacity": .78, stroke: "var(--surface)", "stroke-width": 1 }, svg);
    el("title", {}, dot).textContent = `${show(p.c.code)} · ${p.c.name}\n${fmtPct(p.c.pct)} vs BTC · ${fmtVol(p.c.vol)} BTC volume`;
  });
  const toLabel = new Set([...d.outliers.map(c => c.code), ...[...coins].sort((a, b) => b.vol - a.vol).slice(0, 3).map(c => c.code)]);
  const boxes = [];
  placed.filter(p => toLabel.has(p.c.code)).forEach(p => {
    const t = show(p.c.code), w = t.length * 7 + 6;
    const tries = [p.y - p.r - 4, p.y + p.r + 12, p.y - p.r - 18, p.y + p.r + 26, p.y - p.r - 32];
    const ly = tries.find(ty => !boxes.some(b => Math.abs(b.x - p.x) < (b.w + w) / 2 && Math.abs(b.y - ty) < 13)) ?? tries[0];
    boxes.push({ x: p.x, y: ly, w });
    el("text", { x: p.x, y: ly, "text-anchor": "middle", class: "lbl" }, svg).textContent = t;
  });
}

// Line chart of [timestamp_ms, dominance_pct] points.
function drawDom(svg, pts) {
  if (!pts || pts.length < 2) return;
  const W = 900, H = 240, m = { l: 48, r: 64, t: 16, b: 30 };
  const vals = pts.map(p => p[1]);
  const lo = Math.floor(Math.min(...vals) * 2) / 2 - .5, hi = Math.ceil(Math.max(...vals) * 2) / 2;
  const t0 = pts[0][0], t1 = pts[pts.length - 1][0];
  const x = t => m.l + (t - t0) / (t1 - t0) * (W - m.l - m.r), y = v => m.t + (hi - v) / (hi - lo) * (H - m.t - m.b);
  svg.innerHTML = ""; svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.style.cssText = "width:100%;min-width:560px;display:block";
  for (let v = lo; v <= hi + 1e-9; v += .5) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: "var(--line)" }, svg);
    el("text", { x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }, svg).textContent = v.toFixed(1) + "%";
  }
  for (let t = t0; t <= t1; t += 7 * 864e5)
    el("text", { x: x(t), y: H - 8, "text-anchor": "middle" }, svg).textContent = new Date(t).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const line = pts.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join("");
  el("path", { d: line + `L${x(t1)},${y(lo)}L${x(t0)},${y(lo)}Z`, fill: "var(--btc)", "fill-opacity": .10 }, svg);
  el("path", { d: line, fill: "none", stroke: "var(--btc)", "stroke-width": 2, "stroke-linejoin": "round" }, svg);
  const last = pts[pts.length - 1];
  el("circle", { cx: x(last[0]), cy: y(last[1]), r: 4.5, fill: "var(--btc)", stroke: "var(--surface)", "stroke-width": 2 }, svg);
  el("text", { x: x(last[0]) + 9, y: y(last[1]) + 4, class: "lbl" }, svg).textContent = last[1].toFixed(2) + "%";
}

