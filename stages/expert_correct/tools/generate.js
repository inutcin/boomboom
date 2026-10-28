'use strict';
/*
 * Генератор листов этапа «Корректировки и замечания после инженерной экспертизы».
 * Запуск: node stages/expert_correct/tools/generate.js
 * Результат: stages/expert_correct/fig/*.svg (A3, viewBox 420x297, 200 dpi)
 *
 * Только примитивы SVG, без внешних изображений и шрифтов.
 * Геометрия — в мм модели; каждый вид масштабируется в свой квадрант.
 */
const fs = require('fs');
const nodePath = require('path');

const ROOT = nodePath.join(__dirname, '..');
const OUT = nodePath.join(ROOT, 'fig');
fs.mkdirSync(OUT, { recursive: true });

const W = 420;
const H = 297;
const DPI = 200;
const PX = 3307;
const PY = 2339;

const INK = '#171717';
const MID = '#666666';
const LIGHT = '#ededed';
const FILL = '#d8d8d8';
const FILL2 = '#c4c4c4';
const PC = '#dceaf5';
const BLUE = '#1d4f8f';
const RED = '#a11d1d';
const AMBER = '#b06a00';
const WHITE = '#ffffff';
const DATE = '28.10.2026';

// ---------------------------------------------------------------------------
// Базовые примитивы
// ---------------------------------------------------------------------------
const f = (v) => {
  const r = Math.round(v * 100) / 100;
  return Math.abs(r) < 0.005 ? '0' : String(r);
};
const esc = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function attrs(o = {}) {
  const a = [];
  if (o.fill !== undefined) a.push(`fill="${o.fill}"`);
  if (o.stroke !== undefined) a.push(`stroke="${o.stroke}"`);
  if (o.sw !== undefined) a.push(`stroke-width="${o.sw}"`);
  if (o.dash) a.push(`stroke-dasharray="${o.dash}"`);
  if (o.opacity !== undefined) a.push(`opacity="${o.opacity}"`);
  if (o.fillOpacity !== undefined) a.push(`fill-opacity="${o.fillOpacity}"`);
  if (o.strokeOpacity !== undefined) a.push(`stroke-opacity="${o.strokeOpacity}"`);
  if (o.linecap) a.push(`stroke-linecap="${o.linecap}"`);
  if (o.linejoin) a.push(`stroke-linejoin="${o.linejoin}"`);
  if (o.fillRule) a.push(`fill-rule="${o.fillRule}"`);
  return a.join(' ');
}

function line(x1, y1, x2, y2, o = {}) {
  return `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" ${attrs({
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
  })}/>`;
}

function rect(x, y, w, h, o = {}) {
  return `<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? 'none',
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
    strokeOpacity: o.strokeOpacity,
  })}${o.rx ? ` rx="${f(o.rx)}"` : ''}/>`;
}

function circle(x, y, r, o = {}) {
  return `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? 'none',
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
    strokeOpacity: o.strokeOpacity,
  })}/>`;
}

function ellipse(x, y, rx, ry, o = {}) {
  return `<ellipse cx="${f(x)}" cy="${f(y)}" rx="${f(rx)}" ry="${f(ry)}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? 'none',
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
    strokeOpacity: o.strokeOpacity,
  })}${o.rot ? ` transform="rotate(${o.rot} ${f(x)} ${f(y)})"` : ''}/>`;
}

function path(d, o = {}) {
  return `<path d="${d}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
    fillRule: o.fillRule,
    linejoin: o.linejoin ?? 'round',
    linecap: o.linecap ?? 'round',
  })}/>`;
}

function poly(points, o = {}) {
  const p = points.map(([x, y]) => `${f(x)},${f(y)}`).join(' ');
  return `<polygon points="${p}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
    linejoin: o.linejoin ?? 'round',
  })}/>`;
}

function polyline(points, o = {}) {
  const p = points.map(([x, y]) => `${f(x)},${f(y)}`).join(' ');
  return `<polyline points="${p}" ${attrs({
    fill: 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    linejoin: o.linejoin ?? 'round',
    linecap: o.linecap ?? 'round',
  })}/>`;
}

// ---- оценка ширины строки (DejaVu Sans) -----------------------------------
function cw(ch) {
  if (ch === ' ') return 0.32;
  if (".,:;!|'’`".includes(ch)) return 0.29;
  if ('—–'.includes(ch)) return 0.85;
  if ('·±×'.includes(ch)) return 0.55;
  if ('≥≤≈≠√²°Ø'.includes(ch)) return 0.72;
  if ('mwMWШЩЮМЖФЫ'.includes(ch)) return 0.87;
  if (/[A-ZА-ЯЁ]/.test(ch)) return 0.68;
  if (/[0-9]/.test(ch)) return 0.62;
  if ('()[]'.includes(ch)) return 0.35;
  return 0.56;
}
function tw(s, size) {
  let w = 0;
  for (const ch of String(s)) w += cw(ch);
  return w * size * 1.1;
}
function wrap(s, size, maxW) {
  const words = String(s).split(' ');
  const out = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (tw(t, size) > maxW && cur) {
      out.push(cur);
      cur = w;
    } else cur = t;
  }
  if (cur) out.push(cur);
  return out;
}

const BOXES = [];
function text(x, y, s, o = {}) {
  const size = o.size ?? 2.4;
  const anchor = o.anchor ?? 'start';
  const weight = o.weight ?? 'normal';
  const fill = o.fill ?? INK;
  let out = '';
  if (o.bg) {
    const w = tw(s, size) + 1.0;
    const h = size * 1.2 + 0.5;
    const bx = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
    out += rect(bx - 0.5, y - h / 2, w, h, { fill: o.bg, stroke: 'none' });
  }
  BOXES.push({ x, y, w: tw(s, size), anchor, size, s, rot: o.rot || 0 });
  out += `<text x="${f(x)}" y="${f(y)}" font-size="${f(size)}" text-anchor="${anchor}" font-weight="${weight}" fill="${fill}" dominant-baseline="middle"${o.rot ? ` transform="rotate(${o.rot} ${f(x)} ${f(y)})"` : ''}>${esc(s)}</text>`;
  return out;
}

function textBlock(x, y, lines, o = {}) {
  const size = o.size ?? 2.3;
  const lh = o.lh ?? size * 1.45;
  let out = '';
  lines.forEach((ln, i) => {
    out += text(x, y + i * lh, ln, { ...o, size });
  });
  return out;
}

function arrow(x1, y1, x2, y2, o = {}) {
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const L = o.head ?? 1.8;
  const Wd = o.hw ?? 0.65;
  const c = Math.cos(ang);
  const sn = Math.sin(ang);
  const p1 = [x2 - L * c + Wd * sn, y2 - L * sn - Wd * c];
  const p2 = [x2 - L * c - Wd * sn, y2 - L * sn + Wd * c];
  const col = o.stroke ?? INK;
  return (
    line(x1, y1, x2, y2, { sw: o.sw ?? 0.4, stroke: col, dash: o.dash }) +
    poly([[x2, y2], p1, p2], { fill: col, stroke: col, sw: 0.08 })
  );
}

// ---------------------------------------------------------------------------
// 2D-вид: горизонталь H, вертикаль V (мм модели)
// ---------------------------------------------------------------------------
let V = { s: 1, ox: 0, oy: 0 };
const X = (h) => V.ox + V.s * h;
const Y = (v) => V.oy - V.s * v;

function set2D(box, hMin, hMax, vMin, vMax, pad = 0.9) {
  const s = Math.min(box.w / (hMax - hMin), box.h / (vMax - vMin)) * pad;
  V = {
    s,
    ox: box.x + box.w / 2 - (s * (hMin + hMax)) / 2,
    oy: box.y + box.h / 2 + (s * (vMin + vMax)) / 2,
  };
  return V;
}
function vLine(h1, v1, h2, v2, o = {}) {
  return line(X(h1), Y(v1), X(h2), Y(v2), o);
}
function vRect(h1, v1, h2, v2, o = {}) {
  return rect(X(h1), Y(Math.max(v1, v2)), Math.abs(X(h2) - X(h1)), Math.abs(Y(v1) - Y(v2)), o);
}
function vCircle(h, v, r, o = {}) {
  return circle(X(h), Y(v), r * V.s, o);
}
function vEllipse(h, v, rh, rv, o = {}) {
  return ellipse(X(h), Y(v), rh * V.s, rv * V.s, o);
}
function vPoly(points, o = {}) {
  return poly(points.map(([h, v]) => [X(h), Y(v)]), o);
}
function vPolyline(points, o = {}) {
  return polyline(points.map(([h, v]) => [X(h), Y(v)]), o);
}
function vText(h, v, s, o = {}) {
  return text(X(h), Y(v), s, o);
}
function vDot(h, v, r = 0.55, o = {}) {
  return circle(X(h), Y(v), r, { fill: o.fill ?? INK, stroke: 'none' });
}

function vDimH(h1, h2, v, txt, o = {}) {
  const x1 = X(h1), x2 = X(h2), yy = Y(v);
  let out = '';
  if (o.from !== undefined) {
    const vv = Y(o.from);
    out += line(x1, vv, x1, yy + (vv > yy ? 1.2 : -1.2), { sw: 0.18, stroke: o.stroke ?? INK });
    out += line(x2, vv, x2, yy + (vv > yy ? 1.2 : -1.2), { sw: 0.18, stroke: o.stroke ?? INK });
  }
  out += arrow(x1, yy, x2, yy, { sw: 0.22, head: 1.5, hw: 0.55, stroke: o.stroke });
  out += arrow(x2, yy, x1, yy, { sw: 0.22, head: 1.5, hw: 0.55, stroke: o.stroke });
  if (txt)
    out += text((x1 + x2) / 2, yy + (o.side === 'below' ? 2.2 : -2.0), txt, {
      size: o.size ?? 2.15,
      anchor: 'middle',
      bg: o.bg ?? WHITE,
      fill: o.stroke ?? INK,
    });
  return out;
}

function vDimV(v1, v2, h, txt, o = {}) {
  const xx = X(h), y1 = Y(v1), y2 = Y(v2);
  let out = '';
  if (o.from !== undefined) {
    const hh = X(o.from);
    out += line(hh, y1, xx + (hh > xx ? 1.2 : -1.2), y1, { sw: 0.18, stroke: o.stroke ?? INK });
    out += line(hh, y2, xx + (hh > xx ? 1.2 : -1.2), y2, { sw: 0.18, stroke: o.stroke ?? INK });
  }
  out += arrow(xx, y1, xx, y2, { sw: 0.22, head: 1.5, hw: 0.55, stroke: o.stroke });
  out += arrow(xx, y2, xx, y1, { sw: 0.22, head: 1.5, hw: 0.55, stroke: o.stroke });
  if (txt)
    out += text(xx + (o.side === 'right' ? 2.0 : -2.0), (y1 + y2) / 2, txt, {
      size: o.size ?? 2.15,
      anchor: 'middle',
      rot: -90,
      bg: o.bg ?? WHITE,
      fill: o.stroke ?? INK,
    });
  return out;
}

function vLeader(h, v, tx, ty, s, o = {}) {
  return (
    line(X(h), Y(v), tx, ty, { sw: 0.22 }) +
    text(tx, ty, s, { size: o.size ?? 2.2, anchor: o.anchor ?? 'start', bg: WHITE }) +
    circle(X(h), Y(v), 0.55, { fill: INK, stroke: 'none' })
  );
}

function vSpring(h, v1, v2, halfW, coils = 7) {
  const x = X(h), y1 = Y(v1), y2 = Y(v2);
  const w = halfW * V.s;
  const n = coils * 2;
  const dy = (y2 - y1) / n;
  const pts = [[x, y1]];
  for (let i = 0; i < n; i++) {
    pts.push([x + (i % 2 ? w : -w), y1 + dy * (i + 0.5)]);
  }
  pts.push([x, y2]);
  let out = polyline(pts, { sw: 0.42, stroke: INK });
  out += line(x - w, y1, x + w, y1, { sw: 0.45 });
  out += line(x - w, y2, x + w, y2, { sw: 0.45 });
  return out;
}

// ---------------------------------------------------------------------------
// Изометрия
// ---------------------------------------------------------------------------
function vsub(a, b) { return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }; }
function vdot(a, b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
function vcross(a, b) {
  return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
}
function vnorm(a) {
  const l = Math.hypot(a.x, a.y, a.z) || 1;
  return { x: a.x / l, y: a.y / l, z: a.z / l };
}
let viewF = vnorm({ x: -0.5, y: -0.6, z: -1 });
let viewR = vnorm(vcross(viewF, { x: 0, y: 1, z: 0 }));
let viewU = vcross(viewR, viewF);
function setIsoCamera(elev, xdir = -0.5) {
  viewF = vnorm({ x: xdir, y: -elev, z: -1 });
  viewR = vnorm(vcross(viewF, { x: 0, y: 1, z: 0 }));
  viewU = vcross(viewR, viewF);
}
const ISO_TARGET = { x: 0, y: 480, z: 0 };
function isoRaw(p) {
  const q = vsub(p, ISO_TARGET);
  return { x: vdot(q, viewR), y: -vdot(q, viewU) };
}
let ISO_FIT = { s: 0.2, tx: 200, ty: 200 };
function fitIso(points, opts = {}) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of points) {
    const q = isoRaw(p);
    minX = Math.min(minX, q.x); maxX = Math.max(maxX, q.x);
    minY = Math.min(minY, q.y); maxY = Math.max(maxY, q.y);
  }
  const availW = opts.w ?? 100;
  const availH = opts.h ?? 90;
  const cx = opts.cx ?? 218;
  const cy = opts.cy ?? 200;
  const s = Math.min(availW / (maxX - minX || 1), availH / (maxY - minY || 1));
  ISO_FIT = {
    s,
    tx: cx - ((minX + maxX) / 2) * s,
    ty: cy - ((minY + maxY) / 2) * s,
  };
}
function iso(p) {
  const q = isoRaw(p);
  return [ISO_FIT.tx + q.x * ISO_FIT.s, ISO_FIT.ty + q.y * ISO_FIT.s];
}
function asPoint(p) { return Array.isArray(p) ? { x: p[0], y: p[1], z: p[2] } : p; }
function isoLine(a, b, o = {}) {
  const p = iso(asPoint(a)), q = iso(asPoint(b));
  return line(p[0], p[1], q[0], q[1], o);
}
function isoPoly(points, o = {}) {
  return poly(points.map((p) => iso(asPoint(p))), o);
}
function isoPath(points, o = {}) {
  const p = points.map((q) => iso(asPoint(q)));
  return path('M ' + p.map(([x, y]) => `${f(x)} ${f(y)}`).join(' L '), o);
}
function isoCirclePts(cx, cy, cz, r, n = 48) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const a = (2 * Math.PI * i) / n;
    pts.push({ x: cx, y: cy + r * Math.cos(a), z: cz + r * Math.sin(a) });
  }
  return pts;
}
function isoBox(x0, x1, y0, y1, z0, z1, o = {}) {
  const top = [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]];
  const sideX = [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]];
  const sideZ = [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  let out = '';
  out += isoPoly(sideX, { fill: o.side ?? FILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.32, fillOpacity: o.fillOpacity, opacity: o.opacity });
  out += isoPoly(sideZ, { fill: o.side2 ?? FILL2, stroke: o.stroke ?? INK, sw: o.sw ?? 0.32, fillOpacity: o.fillOpacity, opacity: o.opacity });
  out += isoPoly(top, { fill: o.top ?? WHITE, stroke: o.stroke ?? INK, sw: o.sw ?? 0.32, fillOpacity: o.fillOpacity, opacity: o.opacity });
  return out;
}
function isoGhostBox(x0, x1, y0, y1, z0, z1, o = {}) {
  const top = [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]];
  const sideX = [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]];
  const sideZ = [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  const st = o.stroke ?? '#5f7390';
  return (
    isoPoly(sideX, { fill: 'none', stroke: st, sw: o.sw ?? 0.32, dash: o.dash ?? '1.6 1' }) +
    isoPoly(sideZ, { fill: 'none', stroke: st, sw: o.sw ?? 0.32, dash: o.dash ?? '1.6 1' }) +
    isoPoly(top, { fill: 'none', stroke: st, sw: o.sw ?? 0.32, dash: o.dash ?? '1.6 1' })
  );
}
function isoCylinderX(x0, x1, cy, cz, r, o = {}) {
  const a = isoCirclePts(x0, cy, cz, r);
  const b = isoCirclePts(x1, cy, cz, r);
  let out = '';
  const band = [];
  for (let i = 0; i < a.length; i++) band.push(a[i]);
  for (let i = b.length - 1; i >= 0; i--) band.push(b[i]);
  out += isoPoly(band, { fill: o.side ?? FILL, stroke: 'none', opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(a, { fill: o.front ?? '#fafafa', stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(b, { fill: o.back ?? 'none', stroke: o.stroke ?? INK, sw: 0.25, dash: '1.3 1', opacity: 0.6 });
  return out;
}
function isoCylinderY(cx, cz, y0, y1, r, o = {}) {
  const a = isoCirclePts(cx, y0, cz, r);
  const b = isoCirclePts(cx, y1, cz, r);
  let out = '';
  const band = [];
  for (let i = 0; i < a.length; i++) band.push(a[i]);
  for (let i = b.length - 1; i >= 0; i--) band.push(b[i]);
  out += isoPoly(band, { fill: o.side ?? FILL, stroke: 'none', opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(b, { fill: o.bottom ?? '#e0e0e0', stroke: o.stroke ?? INK, sw: o.sw ?? 0.3, opacity: o.opacity });
  out += isoPoly(a, { fill: o.top ?? WHITE, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, opacity: o.opacity, fillOpacity: o.fillOpacity });
  return out;
}
function isoHexY(cx, cz, yNear, yFar, r, o = {}) {
  const h = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 6 + (Math.PI * i) / 3;
    h.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]);
  }
  const near = h.map(([x, z]) => ({ x, y: yNear, z }));
  const far = h.map(([x, z]) => ({ x, y: yFar, z }));
  const band = [];
  for (const p of near) band.push(p);
  for (let i = far.length - 1; i >= 0; i--) band.push(far[i]);
  let out = '';
  out += isoPoly(band, { fill: o.side ?? FILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.3 });
  out += isoPoly(near, { fill: o.face ?? '#d8d8d8', stroke: o.stroke ?? INK, sw: o.sw ?? 0.35 });
  if (o.holeR) {
    out += isoPoly(isoCirclePts(cx, yNear + 0.15, cz, o.holeR), {
      fill: '#7d7d7d', stroke: o.stroke ?? INK, sw: 0.25,
    });
  }
  out += isoPoly(far, { fill: 'none', stroke: o.stroke ?? INK, sw: 0.2, dash: '1.2 0.9' });
  return out;
}

function isoSpring(x, z, y0, y1, r, coils = 7) {  const pts = [];
  const steps = coils * 16;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const a = t * coils * 2 * Math.PI;
    pts.push({ x: x + r * Math.cos(a), y: y0 + (y1 - y0) * t, z: z + r * Math.sin(a) });
  }
  return isoPath(pts, { sw: 0.4, stroke: INK });
}
function isoBall(cx, cy, cz, r) {
  const p = iso({ x: cx, y: cy, z: cz });
  const rr = r * ISO_FIT.s;
  return (
    circle(p[0], p[1], rr, { fill: '#c9c9c9', stroke: INK, sw: 0.3 }) +
    circle(p[0] - rr * 0.28, p[1] - rr * 0.28, rr * 0.28, { fill: '#eeeeee', stroke: 'none', opacity: 0.8 })
  );
}

// ---------------------------------------------------------------------------
// Параметры конструкции (единый источник истины)
// ---------------------------------------------------------------------------
const G = {
  frame: { x0: -300, x1: 300, z0: -250, z1: 250, y0: 20, y1: 860, tube: 30, wall: 1.5, foot: 20 },
  table: { x: 500, z: 400, t: 15, yTop: 560, yBot: 545, dish: 6, skinTop: 0.5, skinBot: 0.4 },
  sub: { x: 500, z: 400, t: 18, yTop: 450, yBot: 432, slotW: 40, slotL: 250, slotX: -50 },
  cam: { x: -50, t: 20, R: 110, e: [1.38, 2.76, 4.6], A: [3, 6, 10], cy: 395 },
  roller: { y: 515, z: 50, d: 35, w: 11, n: 2, contactW: 22, axle: 12 },
  bracket: { baseX: 100, baseZ: 60, baseT: 8, cheekX: 60, cheekY: 65, cheekT: 4, gap: 24 },
  drill: {
    cy: 395, bodyD: 70, bodyX0: 70, bodyX1: 300,
    chuckD: 50, chuckX0: 0, chuckX1: 70,
    ubX: [130, 260], ubZ: 45, ubR: 40, pad: 2.5,
  },
  bearings: { x: [-75, -25], od: 35, id: 15, w: 11 },
  shaft: { x0: -100, x1: 50, d: 12 },
  beams: { y0: 670, y1: 710, z: [-180, 180], w: 60, x0: -270, x1: 270 },
  cross: { x: [-270, 270], y0: 670, y1: 710, z: [-250, 250], w: 40 },
  springs: { x: [-150, 150], z: [-180, 180], y0: 560, y1: 670, od: 30, d: 2, n: 16, L0: 233, Linst: 110, F: 45, fn: 3.5, k: 0.366 },
  guides: { x: [-225, 225], z: [-180, 180], d: 20, y0: 535, y1: 700, brg: 'LM20UU', brgL: 32, brgW: 45 },
  catchers: { x: [-100, 100], z: [-100, 100], y0: 450, y1: 540, d: 40 },
  dome: { d: 420, y0: 570, y1: 1000, top: 1060 },
  doors: { x: 300, y0: 450, y1: 260, return: 60 },
  control: { x: -300, y0: 660, y1: 780, z0: 80, z1: 180 },
};

const CAM_RMAX = (e) => G.cam.R + e;
const CAM_RMIN = (e) => G.cam.R - e;
const AMP = (e) =>
  Math.sqrt(Math.pow(G.cam.R + e + G.roller.d / 2, 2) - Math.pow(G.roller.z, 2)) -
  Math.sqrt(Math.pow(G.cam.R - e + G.roller.d / 2, 2) - Math.pow(G.roller.z, 2));

// ---------------------------------------------------------------------------
// Каркас листа, спецификация, титульный блок
// ---------------------------------------------------------------------------
function sheetSVG(title, body) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${PX}" height="${PY}" viewBox="0 0 ${W} ${H}">
<title>${esc(title)}</title>
<defs>
  <pattern id="hatch" patternUnits="userSpaceOnUse" width="2.2" height="2.2" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="2.2" stroke="#555555" stroke-width="0.26"/>
  </pattern>
  <pattern id="hatchLight" patternUnits="userSpaceOnUse" width="3.2" height="3.2" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="3.2" stroke="#888888" stroke-width="0.2"/>
  </pattern>
  <pattern id="grid" patternUnits="userSpaceOnUse" width="10" height="10">
    <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#e8e8e8" stroke-width="0.2"/>
  </pattern>
</defs>
<style>
  text { font-family: 'DejaVu Sans', Arial, sans-serif; fill: ${INK}; }
</style>
<rect x="0" y="0" width="${W}" height="${H}" fill="${WHITE}"/>
${body}
</svg>
`;
}

function specPanel(rows, notes, tb, topGraphic) {
  const x = 300, y = 30, w = 110, h = 252;
  const extra = topGraphic ? 38 : 0;
  let s = rect(x, y, w, h, { fill: WHITE, stroke: INK, sw: 0.7 });
  s += text(x + 5, y + 7, 'СПЕЦИФИКАЦИЯ', { size: 3.3, weight: 'bold' });
  s += line(x, y + 12, x + w, y + 12, { sw: 0.35 });

  if (topGraphic) s += topGraphic;

  // шапка таблицы
  const cx = { num: x + 5, name: x + 12, qty: x + 80, note: x + 88 };
  s += text(cx.num, y + 16.5 + extra, '№', { size: 2.2, anchor: 'middle', fill: MID });
  s += text(cx.name, y + 16.5 + extra, 'Наименование', { size: 2.2, fill: MID });
  s += text(cx.qty, y + 16.5 + extra, 'Кол.', { size: 2.2, anchor: 'middle', fill: MID });
  s += text(cx.note, y + 16.5 + extra, 'Примечание', { size: 2.2, fill: MID });
  s += line(x + 9, y + 19.5 + extra, x + w, y + 19.5 + extra, { sw: 0.28 });

  let yy = y + 24 + extra;
  const rowH = [];
  for (const r of rows) {
    const nameLines = wrap(r[1], 2.2, 66);
    const noteLines = r[3] ? wrap(r[3], 2.0, 21) : [];
    const lines = Math.max(nameLines.length, noteLines.length, 1);
    const rh = Math.max(7.2, lines * 3.4 + 3.6);
    rowH.push(rh);
    s += text(cx.num, yy + 3.2, String(r[0]), { size: 2.25, anchor: 'middle', weight: 'bold' });
    nameLines.forEach((ln, i) => {
      s += text(cx.name, yy + 3.2 + i * 3.4, ln, { size: 2.2 });
    });
    s += text(cx.qty, yy + 3.2, String(r[2]), { size: 2.2, anchor: 'middle' });
    noteLines.forEach((ln, i) => {
      s += text(cx.note, yy + 3.2 + i * 3.4, ln, { size: 1.95, fill: MID });
    });
    yy += rh;
    s += line(x + 9, yy, x + w, yy, { sw: 0.16, stroke: '#cfcfcf' });
  }
  const tableBottom = yy;
  s += line(x, tableBottom + 1.5, x + w, tableBottom + 1.5, { sw: 0.3 });

  // примечания
  let ny = tableBottom + 7;
  if (notes && notes.length) {
    for (const n of notes) {
      if (n.type === 'warn') {
        s += rect(x + 3, ny - 2.2, 1.4, 4.0, { fill: RED, stroke: 'none' });
        const lines = wrap(n.text, 2.05, 99);
        lines.forEach((ln, i) => {
          s += text(x + 7, ny + i * 3.2, ln, { size: 2.05, fill: RED });
        });
        ny += lines.length * 3.2 + 2.2;
      } else if (n.type === 'head') {
        s += text(x + 4, ny, n.text, { size: 2.2, weight: 'bold', fill: MID });
        ny += 3.8;
      } else {
        const lines = wrap(n.text, 2.0, 100);
        lines.forEach((ln, i) => {
          s += text(x + 4, ny + i * 3.1, ln, { size: 2.0, fill: n.fill ?? INK });
        });
        ny += lines.length * 3.1 + 1.4;
      }
    }
  }

  // титульный блок
  const ty = 226;
  s += line(x, ty, x + w, ty, { sw: 0.5 });
  s += text(x + 5, ty + 6.5, 'ВИБРОСТОЛ', { size: 4.0, weight: 'bold' });
  s += text(x + 5, ty + 12, 'Этап: корректировки после экспертизы', { size: 2.0, fill: MID });
  s += text(x + 5, ty + 18, tb.title, { size: 2.55, weight: 'bold' });
  s += text(x + 5, ty + 23.5, tb.scale, { size: 2.0, fill: MID });
  s += text(x + 5, ty + 29, `Лист ${tb.no} из 5`, { size: 2.3, weight: 'bold' });
  s += text(x + 5, ty + 34, `${DATE}  ·  DeepSeek / OpenCode`, { size: 1.9, fill: MID });
  s += text(x + w - 5, ty + 34, 'A3 · 1:10', { size: 1.9, anchor: 'end', fill: MID });
  return s;
}

function sheetFrame(title, subtitle, no, body, specRows, notes, tb, topGraphic) {
  let out = '';
  out += rect(5, 5, 410, 287, { fill: WHITE, stroke: INK, sw: 0.8 });
  out += rect(10, 10, 400, 277, { fill: 'none', stroke: INK, sw: 0.4 });
  out += text(150, 18, title, { size: 4.2, anchor: 'middle', weight: 'bold' });
  out += text(150, 24, subtitle, { size: 2.55, anchor: 'middle', fill: MID });
  out += body;
  out += specPanel(specRows, notes, tb, topGraphic);
  out += text(150, 290, `Корректировки после инженерной экспертизы · ${DATE} · лист ${no} из 5`, {
    size: 2.1,
    anchor: 'middle',
    fill: MID,
  });
  return out;
}

// ---------------------------------------------------------------------------
// Выноски: номера в двух колонках вокруг вида; линии не пересекаются
// ---------------------------------------------------------------------------
const GROUPS = new Map();
const LEADERS = [];
let CUR_GROUP = null;

function group(id, cfg) {
  GROUPS.set(id, { id, items: [], ...cfg });
  CUR_GROUP = id;
}
function feature(num, px, py) {
  if (!CUR_GROUP) return;
  const g = GROUPS.get(CUR_GROUP);
  g.items.push({ num, x: px, y: py });
}
function renderLeaders() {
  let out = '';
  for (const g of GROUPS.values()) {
    if (!g.items.length) continue;
    const left = [], right = [];
    const cx = (g.x0 + g.x1) / 2;
    if (g.items.length === 1) {
      (g.items[0].x < cx ? left : right).push(g.items[0]);
    } else {
      const byX = g.items.slice().sort((a, b) => a.x - b.x || a.y - b.y);
      const half = Math.ceil(byX.length / 2);
      byX.slice(0, half).forEach((it) => left.push(it));
      byX.slice(half).forEach((it) => right.push(it));
    }
    const place = (arr, side) => {
      if (!arr.length) return;
      const bx = side === 'L' ? g.x0 : g.x1;
      const top = g.y0 + 4;
      const bot = g.y1 - 4;
      const n = arr.length;
      const ys = arr.map((_, i) => (n === 1 ? (top + bot) / 2 : top + ((bot - top) * i) / (n - 1)));
      const count = (order) => {
        let c = 0;
        for (let i = 0; i < order.length; i++) {
          for (let j = i + 1; j < order.length; j++) {
            if (segIntersect(
              { x1: bx, y1: ys[i], x2: order[i].x, y2: order[i].y },
              { x1: bx, y1: ys[j], x2: order[j].x, y2: order[j].y }
            )) c++;
          }
        }
        return c;
      };
      let best = arr.slice();
      let bestC = count(best);
      if (bestC > 0) {
        const perm = (a, k = 0) => {
          if (bestC === 0 || k === a.length) {
            if (k === a.length) {
              const c = count(a);
              if (c < bestC) { bestC = c; best = a.slice(); }
            }
            return;
          }
          for (let i = k; i < a.length; i++) {
            [a[k], a[i]] = [a[i], a[k]];
            perm(a, k + 1);
            [a[k], a[i]] = [a[i], a[k]];
          }
        };
        if (n <= 7) perm(arr.slice());
      }
      best.forEach((it, i) => {
        const by = ys[i];
        out += line(bx, by, it.x, it.y, { sw: 0.22 });
        LEADERS.push({ x1: bx, y1: by, x2: it.x, y2: it.y, group: g.id, num: it.num });
        out += circle(bx, by, 2.25, { fill: WHITE, stroke: INK, sw: 0.32 });
        out += text(bx, by + 0.05, String(it.num), {
          size: 2.25,
          anchor: 'middle',
          weight: 'bold',
        });
        out += circle(it.x, it.y, 0.55, { fill: INK, stroke: 'none' });
      });
    };
    place(left, 'L');
    place(right, 'R');
  }
  return out;
}

function segIntersect(a, b) {
  const d = (p, q, r, s) =>
    (q.x - p.x) * (s.y - r.y) - (q.y - p.y) * (s.x - r.x);
  const den = d(
    { x: a.x1, y: a.y1 },
    { x: a.x2, y: a.y2 },
    { x: b.x1, y: b.y1 },
    { x: b.x2, y: b.y2 }
  );
  if (Math.abs(den) < 1e-6) return false;
  const t = ((b.x1 - a.x1) * (b.y2 - b.y1) - (b.y1 - a.y1) * (b.x2 - b.x1)) / den;
  const u = ((b.x1 - a.x1) * (a.y2 - a.y1) - (b.y1 - a.y1) * (a.x2 - a.x1)) / den;
  return t > 0.02 && t < 0.98 && u > 0.02 && u < 0.98;
}

function checkLeaders() {
  let bad = 0;
  for (let i = 0; i < LEADERS.length; i++) {
    for (let j = i + 1; j < LEADERS.length; j++) {
      const a = LEADERS[i], b = LEADERS[j];
      if (a.group !== b.group) continue;
      if (segIntersect(a, b)) {
        console.error(`[выноски:${a.group}] пересечение ${a.num}(${a.x1.toFixed(1)},${a.y1.toFixed(1)}->${a.x2.toFixed(1)},${a.y2.toFixed(1)}) / ${b.num}(${b.x1.toFixed(1)},${b.y1.toFixed(1)}->${b.x2.toFixed(1)},${b.y2.toFixed(1)})`);
        bad++;
      }
    }
  }
  return bad;
}

function verify(name) {
  let bad = 0;
  for (const b of BOXES) {
    let x0 = b.x;
    const w = b.rot ? b.size : b.w;
    if (b.anchor === 'middle') x0 = b.x - w / 2;
    if (b.anchor === 'end') x0 = b.x - w;
    const x1 = x0 + w;
    const y0 = b.y - b.size / 2;
    const y1 = b.y + b.size / 2;
    if (x0 < 11 || x1 > 409 || y0 < 11 || y1 > 291.5) {
      console.error(
        `[${name}] вне листа: "${b.s}" x ${x0.toFixed(1)}..${x1.toFixed(1)} y ${y0.toFixed(1)}..${y1.toFixed(1)}`
      );
      bad++;
    }
  }
  return bad;
}

module.exports = {};

// ---------------------------------------------------------------------------
// Общие элементы
// ---------------------------------------------------------------------------
function viewBox(box, label, scale) {
  let s = rect(box.x, box.y, box.w, box.h, { fill: 'none', stroke: '#dcdcdc', sw: 0.25, dash: '1.4 1.2' });
  s += text(box.x, box.y - 3.2, label, { size: 2.35, weight: 'bold' });
  s += text(box.x + box.w, box.y - 3.2, scale, { size: 2.0, anchor: 'end', fill: MID });
  return s;
}

let CLIP_ID = 0;
function clipBegin(box) {
  const id = `cl${++CLIP_ID}`;
  return `<clipPath id="${id}"><rect x="${f(box.x)}" y="${f(box.y)}" width="${f(box.w)}" height="${f(box.h)}"/></clipPath><g clip-path="url(#${id})">`;
}
function clipEnd() {
  return '</g>';
}

function dishCurve(h0, h1, yTop, dish, n = 40) {
  const pts = [];
  const hm = (h0 + h1) / 2;
  const half = (h1 - h0) / 2;
  for (let i = 0; i <= n; i++) {
    const h = h0 + ((h1 - h0) * i) / n;
    const u = (h - hm) / half;
    pts.push([h, yTop - dish * Math.max(0, 1 - u * u)]);
  }
  return pts;
}

function tableSection2D(h0, h1, yTop, yBot, dish, o = {}) {
  const top = dishCurve(h0, h1, yTop, dish, 30);
  let s = vPoly([...top, [h1, yBot], [h0, yBot]], {
    fill: o.fill ?? LIGHT,
    stroke: INK,
    sw: o.sw ?? 0.5,
  });
  s += vPolyline(top, { sw: o.sw ?? 0.55 });
  s += vLine(h0, yTop, h1, yTop, { sw: 0.2, dash: '1 0.8', stroke: MID });
  s += vLine(h0, yBot, h1, yBot, { sw: 0.5 });
  return s;
}

function camProfilePts(cx, cy, e, n = 180) {
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = (2 * Math.PI * i) / n;
    const r = G.cam.R + e * Math.cos(2 * t);
    pts.push([cx + r * Math.sin(t), cy + r * Math.cos(t)]);
  }
  return pts;
}

function drawCam2D(cx, cy, e, o = {}) {
  const pts = camProfilePts(cx, cy, e);
  let s = vPoly(pts, {
    fill: o.fill ?? LIGHT,
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.55,
    dash: o.dash,
  });
  s += vCircle(cx, cy, G.cam.R, { sw: 0.22, dash: '2 1.2', stroke: MID });
  s += vCircle(cx, cy, 6.2, { fill: WHITE, stroke: INK, sw: 0.4 });
  s += vLine(cx - 8, cy, cx + 8, cy, { sw: 0.2, dash: '2 1 0.7 1' });
  s += vLine(cx, cy - 8, cx, cy + 8, { sw: 0.2, dash: '2 1 0.7 1' });
  return s;
}

function drawRoller2D(h, v, o = {}) {
  let s = vCircle(h, v, G.roller.d / 2, { fill: o.fill ?? WHITE, stroke: INK, sw: 0.45 });
  s += vCircle(h, v, G.roller.d / 2 - 5, { fill: WHITE, stroke: INK, sw: 0.3 });
  s += vCircle(h, v, 2.2, { fill: WHITE, stroke: INK, sw: 0.3 });
  s += vCircle(h, v, 0.6, { fill: INK, stroke: 'none' });
  return s;
}

function drawBearing2D(h, v, r, o = {}) {
  let s = vCircle(h, v, r, { fill: o.fill ?? '#f2f2f2', stroke: INK, sw: 0.45 });
  s += vCircle(h, v, r * 0.62, { fill: 'none', stroke: INK, sw: 0.3 });
  s += vCircle(h, v, r * 0.36, { fill: WHITE, stroke: INK, sw: 0.3 });
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * 2 * Math.PI;
    s += vCircle(h + r * 0.49 * Math.cos(a), v + r * 0.49 * Math.sin(a), r * 0.09, {
      fill: INK,
      stroke: 'none',
    });
  }
  return s;
}

function drawSpringTable() {
  // компактная таблица данных пружины для правой панели
  let s = '';
  const x = 305, y = 196;
  s += text(x, y, 'ПРУЖИНА (предв.)', { size: 2.3, weight: 'bold', fill: AMBER });
  const rows = [
    ['d / D', '2,0 / 30 мм'],
    ['n / L0', '16 / 233 мм'],
    ['L уст.', '110 мм'],
    ['F / k', '45 Н / 0,366 Н/мм'],
    ['f соб.', '3,5 Гц'],
  ];
  rows.forEach((r, i) => {
    s += text(x, y + 5 + i * 4.2, r[0], { size: 2.0, fill: MID });
    s += text(x + 25, y + 5 + i * 4.2, r[1], { size: 2.0 });
  });
  return s;
}

// ---------------------------------------------------------------------------
// ЛИСТ 1. Общий вид
// ---------------------------------------------------------------------------
function sheetGeneral() {
  const TL = { x: 24, y: 38, w: 112, h: 92 };
  const TR = { x: 162, y: 38, w: 112, h: 92 };
  const BL = { x: 24, y: 154, w: 112, h: 96 };
  const BR = { x: 162, y: 154, w: 112, h: 106 };
  let s = '';
  s += viewBox(TL, 'ВИД СВЕРХУ', '1:6');
  s += viewBox(TR, 'ВИД СЛЕВА', '1:13');
  s += viewBox(BL, 'ВИД СБОКУ', '1:13');
  s += viewBox(BR, 'ИЗОМЕТРИЯ', '1:12');

  // ===================== ВИД СВЕРХУ =====================
  set2D(TL, -320, 320, -270, 270, 0.94);
  group('tl', { x0: 15, x1: 145, y0: TL.y, y1: TL.y + TL.h });
  s += clipBegin(TL);
  // рама
  s += vRect(-300, -250, 300, 250, { fill: 'none', stroke: INK, sw: 0.5 });
  s += vRect(-300, -250, 300, -220, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vRect(-300, 220, 300, 250, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vRect(-300, -220, -270, 220, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vRect(270, -220, 300, 220, { fill: LIGHT, stroke: INK, sw: 0.35 });
  for (const x of [-300, 270]) for (const z of [-250, 220]) {
    s += vRect(x, z, x + 30, z + 30, { fill: FILL, stroke: INK, sw: 0.35 });
  }
  // панели ПК
  s += vRect(-297, -247, 297, 247, { fill: PC, stroke: BLUE, sw: 0.3, fillOpacity: 0.18 });
  // крышка и купол
  s += vRect(-300, -250, 300, 250, { fill: 'none', stroke: INK, sw: 0.45, dash: '2 1' });
  s += vCircle(0, 0, G.dome.d / 2, { fill: PC, stroke: BLUE, sw: 0.5, fillOpacity: 0.22 });
  s += vCircle(0, 0, G.dome.d / 2 + 5, { fill: 'none', stroke: BLUE, sw: 0.25, dash: '1.5 1' });
  s += vLine(-230, 0, 230, 0, { sw: 0.2, dash: '3 1 0.8 1' });
  s += vLine(0, -230, 0, 230, { sw: 0.2, dash: '3 1 0.8 1' });
  // петли и защёлка крышки
  s += vRect(-160, -255, 160, -245, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vRect(-60, 250, 60, 258, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vText(0, 263, 'защёлка', { size: 1.9, anchor: 'middle', fill: MID });
  s += vText(0, -262, 'петли', { size: 1.9, anchor: 'middle', fill: MID });
  // стол и щель
  s += vRect(-250, -200, 250, 200, { fill: 'none', stroke: MID, sw: 0.3, dash: '2 1.2' });
  s += vRect(-70, -125, -30, 125, { fill: '#f7e6e6', stroke: RED, sw: 0.35, dash: '1.8 1' });
  s += vText(-50, 135, 'щель 250×40', { size: 1.8, anchor: 'middle', fill: RED });
  // шарик
  s += vCircle(0, 0, 16.5, { fill: FILL, stroke: INK, sw: 0.4 });
  s += vCircle(0, 0, 8, { fill: WHITE, stroke: INK, sw: 0.3 });
  // дверцы (внизу, показаны штриховой)
  s += vRect(280, -245, 300, -10, { fill: 'none', stroke: MID, sw: 0.3, dash: '1.8 1.2' });
  s += vRect(280, 10, 300, 245, { fill: 'none', stroke: MID, sw: 0.3, dash: '1.8 1.2' });
  s += vRect(240, -245, 280, -225, { fill: 'none', stroke: MID, sw: 0.3, dash: '1.8 1.2' });
  s += vRect(240, 225, 280, 245, { fill: 'none', stroke: MID, sw: 0.3, dash: '1.8 1.2' });
  s += vText(288, -200, 'Г-дверцы', { size: 1.55, anchor: 'end', fill: MID });
  // панель управления
  s += vRect(-296, 80, -276, 180, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vCircle(-286, 158, 5, { fill: RED, stroke: RED, sw: 0.2 });
  s += vCircle(-286, 140, 3.5, { fill: WHITE, stroke: INK, sw: 0.3 });
  s += vCircle(-286, 120, 3.5, { fill: WHITE, stroke: INK, sw: 0.3 });
  // размеры
  s += vDimH(-300, 300, 282, '600', { size: 2.1 });
  s += vDimV(-250, 250, -322, '500', { size: 2.1 });
  // выноски
  feature(1, X(-285), Y(-235));
  feature(2, X(297), Y(120));
  feature(3, X(290), Y(-160));
  feature(12, X(-285), Y(235));
  s += clipEnd();

  // ===================== ВИД СЛЕВА =====================
  set2D(TR, -260, 260, 0, 1100, 0.9);
  group('tr', { x0: 155, x1: 291, y0: TR.y, y1: TR.y + TR.h });
  s += clipBegin(TR);
  // стойки и обвязка
  for (const z of [-250, 220]) {
    s += vRect(z, 20, z + 30, 860, { fill: LIGHT, stroke: INK, sw: 0.4 });
    s += vRect(z - 5, 0, z + 35, 20, { fill: '#8a8a8a', stroke: INK, sw: 0.3 });
  }
  s += vRect(-250, 830, 250, 860, { fill: LIGHT, stroke: INK, sw: 0.4 });
  s += vRect(-250, 20, 250, 50, { fill: LIGHT, stroke: INK, sw: 0.4 });
  s += vRect(-250, 670, 250, 700, { fill: LIGHT, stroke: INK, sw: 0.4 });
  // диагональные раскосы (дальняя сторона — штрих)
  s += vLine(-250, 50, 250, 300, { sw: 1.2, stroke: FILL });
  s += vLine(-250, 50, 250, 300, { sw: 0.3, stroke: INK });
  s += vLine(250, 50, -250, 300, { sw: 0.25, stroke: MID, dash: '3 1.5' });
  // панели ПК (прозрачные)
  s += vRect(-247, 450, 247, 860, { fill: PC, stroke: BLUE, sw: 0.3, fillOpacity: 0.18 });
  s += vRect(-247, 50, 247, 450, { fill: PC, stroke: BLUE, sw: 0.3, fillOpacity: 0.14 });
  // купол
  const dTop = G.dome.y1;
  s += path(
    `M ${f(X(-210))} ${f(Y(G.dome.y0))} L ${f(X(-210))} ${f(Y(dTop))} Q ${f(X(0))} ${f(Y(G.dome.top + 60))} ${f(X(210))} ${f(Y(dTop))} L ${f(X(210))} ${f(Y(G.dome.y0))}`,
    { fill: PC, stroke: BLUE, sw: 0.45, fillOpacity: 0.18 }
  );
  s += vLine(0, G.dome.y0, 0, G.dome.top, { sw: 0.18, dash: '3 1 0.8 1', stroke: BLUE });
  s += vText(0, G.dome.top + 22, 'Ø420', { size: 1.9, anchor: 'middle', fill: BLUE });
  // крышка
  s += vRect(-250, 860, -215, 868, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(215, 860, 250, 868, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(-160, 868, -80, 872, { fill: INK, stroke: INK, sw: 0.2 });
  s += vRect(80, 868, 160, 872, { fill: INK, stroke: INK, sw: 0.2 });
  // стол
  s += tableSection2D(-200, 200, 560, 545, 6, { fill: LIGHT });
  s += vCircle(0, 570, 16.5, { fill: FILL, stroke: INK, sw: 0.35 });
  // подстолье со щелью
  s += vRect(-200, 432, -125, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(125, 432, 200, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vText(0, 441, 'щель', { size: 1.7, anchor: 'middle', fill: MID });
  // балки
  s += vRect(-210, 670, -150, 710, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(150, 670, 210, 710, { fill: FILL2, stroke: INK, sw: 0.35 });
  // пружины и направляющие
  for (const z of [-180, 180]) {
    s += vSpring(z, 560, 670, 15, 7);
    s += vLine(z, 535, z, 700, { sw: 0.35, dash: '2 1', stroke: MID });
    s += vRect(z - 22, 545, z + 22, 577, { fill: FILL, stroke: INK, sw: 0.3 });
  }
  // ловители
  for (const z of [-100, 100]) {
    s += vRect(z - 10, 450, z + 10, 530, { fill: LIGHT, stroke: INK, sw: 0.3 });
    s += vRect(z - 20, 530, z + 20, 540, { fill: '#8a8a8a', stroke: INK, sw: 0.3 });
  }
  // размеры
  s += vDimV(0, 860, -285, '860', { size: 2.0 });
  s += vDimV(0, 1060, -315, '1060', { size: 2.0 });
  s += vDimV(450, 560, 285, '110', { size: 1.9 });
  s += vDimV(560, 670, 265, '110', { size: 1.9 });
  s += vDimH(-250, 250, -25, '500', { size: 1.9 });
  // выноски
  feature(4, X(0), Y(1000));
  feature(5, X(195), Y(556));
  feature(6, X(-195), Y(441));
  feature(7, X(180), Y(670));
  s += clipEnd();

  // ===================== ВИД СБОКУ =====================
  set2D(BL, -330, 330, -50, 1100, 0.9);
  group('bl', { x0: 15, x1: 145, y0: BL.y, y1: BL.y + BL.h });
  s += clipBegin(BL);
  // стойки
  for (const x of [-300, 270]) {
    s += vRect(x, 20, x + 30, 860, { fill: LIGHT, stroke: INK, sw: 0.4 });
    s += vRect(x - 5, 0, x + 35, 20, { fill: '#8a8a8a', stroke: INK, sw: 0.3 });
  }
  s += vRect(-300, 830, 300, 860, { fill: LIGHT, stroke: INK, sw: 0.4 });
  s += vRect(-300, 20, 300, 50, { fill: LIGHT, stroke: INK, sw: 0.4 });
  s += vRect(-300, 670, 300, 700, { fill: LIGHT, stroke: INK, sw: 0.4 });
  // раскосы
  s += vLine(-270, 50, 270, 320, { sw: 1.2, stroke: FILL });
  s += vLine(-270, 50, 270, 320, { sw: 0.3, stroke: INK });
  s += vLine(270, 50, -270, 320, { sw: 0.25, stroke: MID, dash: '3 1.5' });
  // панели
  s += vLine(-300, 450, -300, 860, { sw: 1.4, stroke: PC });
  s += vLine(-300, 50, -300, 450, { sw: 1.4, stroke: PC });
  // купол
  s += path(
    `M ${f(X(-210))} ${f(Y(G.dome.y0))} L ${f(X(-210))} ${f(Y(G.dome.y1))} Q ${f(X(0))} ${f(Y(G.dome.top + 60))} ${f(X(210))} ${f(Y(G.dome.y1))} L ${f(X(210))} ${f(Y(G.dome.y0))}`,
    { fill: PC, stroke: BLUE, sw: 0.45, fillOpacity: 0.18 }
  );
  // крышка
  s += vRect(-300, 860, -215, 868, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(215, 860, 300, 868, { fill: FILL, stroke: INK, sw: 0.35 });
  // стол, шарик
  s += tableSection2D(-250, 250, 560, 545, 6, { fill: LIGHT });
  s += vCircle(0, 570, 16.5, { fill: FILL, stroke: INK, sw: 0.35 });
  // подстолье со щелью
  s += vRect(-250, 432, -70, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(-30, 432, 250, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  // балки и поперечины
  s += vRect(-270, 670, 270, 710, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(-270, 670, -230, 710, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vRect(230, 670, 270, 710, { fill: FILL, stroke: INK, sw: 0.3 });
  // пружины, направляющие, ловители
  for (const x of [-150, 150]) s += vSpring(x, 560, 670, 15, 7);
  for (const x of [-225, 225]) {
    s += vLine(x, 535, x, 700, { sw: 0.4 });
    s += vRect(x - 22, 545, x + 22, 577, { fill: FILL, stroke: INK, sw: 0.3 });
  }
  for (const x of [-100, 100]) {
    s += vRect(x - 10, 450, x + 10, 530, { fill: LIGHT, stroke: INK, sw: 0.3 });
    s += vRect(x - 20, 530, x + 20, 540, { fill: '#8a8a8a', stroke: INK, sw: 0.3 });
  }
  // привод: дрель, патрон, кулачок
  s += vRect(70, 360, 295, 430, { fill: '#f7f7f7', stroke: INK, sw: 0.45, rx: 2 });
  s += vRect(295, 360, 300, 430, { fill: 'none', stroke: MID, sw: 0.25, dash: '1.5 1' });
  s += vCircle(295, 395, 35, { fill: '#f7f7f7', stroke: INK, sw: 0.45 });
  s += vRect(0, 370, 70, 420, { fill: LIGHT, stroke: INK, sw: 0.4 });
  s += vRect(-60, 280.4, -40, 509.6, { fill: LIGHT, stroke: INK, sw: 0.5 });
  s += vLine(-50, 280, -50, 510, { sw: 0.2, dash: '3 1 0.8 1' });
  s += vLine(-60, 395, -40, 395, { sw: 0.2, dash: '2 1' });
  // ролики и кронштейны
  s += vRect(-100, 537, 0, 545, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(-62, 472, -58, 537, { fill: FILL2, stroke: INK, sw: 0.3 });
  s += vRect(-42, 472, -38, 537, { fill: FILL2, stroke: INK, sw: 0.3 });
  s += drawRoller2D(-50, 515);
  // вал, подвесы, гайки
  s += vRect(-100, 389, 50, 401, { fill: LIGHT, stroke: INK, sw: 0.35 });
  for (const x of [-75, -25]) {
    s += vRect(x - 3, 395, x + 3, 432, { fill: FILL2, stroke: INK, sw: 0.3 });
    s += vRect(x - 17.5, 377.5, x + 17.5, 412.5, { fill: 'none', stroke: INK, sw: 0.3 });
  }
  // ручка и выносной рычаг
  s += vRect(230, 300, 300, 360, { fill: LIGHT, stroke: INK, sw: 0.4, rx: 2 });
  s += vRect(285, 320, 300, 340, { fill: LIGHT, stroke: INK, sw: 0.4, rx: 1 });
  s += vRect(292, 315, 300, 345, { fill: FILL, stroke: INK, sw: 0.3 });
  // дверца с вырезом
  s += vLine(300, 260, 300, 315, { sw: 1.6, stroke: PC });
  s += vLine(300, 345, 300, 450, { sw: 1.6, stroke: PC });
  s += vText(302, 330, 'вырез', { size: 1.7, fill: MID });
  s += vRect(294, 262, 301, 272, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vText(303, 267, 'шпингалет', { size: 1.45, fill: MID });
  s += vCircle(300, 450, 1.2, { fill: INK, stroke: 'none' });
  // панель управления
  s += vRect(-296, 680, -276, 760, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vCircle(-286, 740, 5, { fill: RED, stroke: RED, sw: 0.2 });
  s += vCircle(-286, 715, 3.5, { fill: WHITE, stroke: INK, sw: 0.3 });
  // размеры
  s += vDimH(-300, 300, -35, '600', { size: 2.0 });
  s += vDimV(0, 860, -320, '860', { size: 2.0 });
  s += vDimV(0, 1060, -342, '1060', { size: 2.0 });
  s += vDimV(0, 450, 315, '450', { size: 1.9 });
  s += vDimV(0, 560, 330, '560', { size: 1.9 });
  s += vDimH(0, 70, 450, '70', { size: 1.8 });
  s += vDimH(-60, -40, 520, '20', { size: 1.8 });
  // выноски
  feature(8, X(250), Y(395));
  feature(9, X(-50), Y(470));
  feature(10, X(-75), Y(420));
  feature(11, X(-286), Y(740));
  s += clipEnd();

  // ===================== ИЗОМЕТРИЯ =====================
  setIsoCamera(0.62, -0.52);
  const pts = [];
  for (const x of [-300, 300]) for (const z of [-250, 250]) for (const y of [0, 1060]) pts.push({ x, y, z });
  for (const x of [-210, 210]) for (const z of [-210, 210]) for (const y of [570, 1060]) pts.push({ x, y, z });
  fitIso(pts, { w: 100, h: 96, cx: BR.x + BR.w / 2, cy: BR.y + BR.h / 2 + 2 });
  s += clipBegin(BR);

  // рамка
  const leg = (x, z) => isoBox(x, x + 30, 20, 860, z, z + 30, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2', sw: 0.25 });
  s += leg(-300, -250) + leg(270, -250) + leg(-300, 220) + leg(270, 220);
  s += isoBox(-300, 300, 830, 860, -250, -220, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2' });
  s += isoBox(-300, 300, 830, 860, 220, 250, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2' });
  s += isoBox(-300, -270, 830, 860, -220, 220, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2' });
  s += isoBox(270, 300, 830, 860, -220, 220, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2' });
  s += isoBox(-300, 300, 20, 50, -250, -220, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2' });
  s += isoBox(-300, 300, 20, 50, 220, 250, { top: '#f4f4f4', side: '#e4e4e4', side2: '#d2d2d2' });
  // диагональные раскосы (по одному на боковину + два сзади)
  for (const z of [-240, 240]) {
    s += isoLine([-270, 60, z], [270, 320, z], { sw: 0.7, stroke: '#9a9a9a' });
    s += isoLine([270, 60, z], [-270, 320, z], { sw: 0.35, stroke: '#bdbdbd', dash: '2 1.2' });
  }
  s += isoLine([-270, 60, -250], [-270, 320, 250], { sw: 0.5, stroke: '#b0b0b0' });
  s += isoLine([270, 60, -250], [270, 320, 250], { sw: 0.5, stroke: '#b0b0b0' });
  // подстолье и стол
  s += isoBox(-250, 250, 432, 450, -200, 200, { top: '#ececec', side: '#d8d8d8', side2: '#c4c4c4', sw: 0.3 });
  s += isoBox(-250, 250, 545, 560, -200, 200, { top: '#eaf1f8', side: '#c9d6e4', side2: '#b6c7d9', sw: 0.35 });
  // балки и пружины
  s += isoBox(-270, 270, 670, 710, 150, 210, { top: '#e8e8e8', side: '#d4d4d4', side2: '#c0c0c0' });
  s += isoBox(-270, 270, 670, 710, -210, -150, { top: '#e8e8e8', side: '#d4d4d4', side2: '#c0c0c0' });
  for (const x of [-150, 150]) for (const z of [-180, 180]) {
    s += isoSpring(x, z, 560, 670, 15, 7);
  }
  for (const x of [-225, 225]) for (const z of [-180, 180]) {
    s += isoCylinderY(x, z, 535, 700, 10, { front: '#f0f0f0', side: '#d8d8d8', sw: 0.3 });
  }
  // купол
  s += isoCylinderY(0, 0, 570, 1000, 210, {
    front: '#eaf3fb', side: PC, top: '#eaf3fb', stroke: BLUE, sw: 0.35, fillOpacity: 0.10,
  });
  for (const [yy, rr] of [[1015, 196], [1030, 160], [1045, 105], [1057, 45]]) {
    s += isoPoly(isoCirclePts(0, yy, 0, rr), { fill: 'none', stroke: BLUE, sw: 0.25, dash: '1.4 1' });
  }
  s += isoLine([-210, 1000, 0], [-45, 1060, 0], { sw: 0.3, stroke: BLUE });
  s += isoLine([210, 1000, 0], [45, 1060, 0], { sw: 0.3, stroke: BLUE });
  // дрель, патрон, кулачок
  s += isoCylinderX(70, 300, 395, 0, 35, { front: '#fafafa', side: '#dcdcdc', sw: 0.4 });
  s += isoCylinderX(0, 70, 395, 0, 25, { front: '#f0f0f0', side: '#cccccc', sw: 0.35 });
  s += isoCylinderX(-60, -40, 395, 0, 114.6, { front: '#ececec', side: '#c8c8c8', sw: 0.4 });
  s += isoCylinderX(-61, -39, 515, 50, 17.5, { front: '#f4f4f4', side: '#d0d0d0', sw: 0.35 });
  s += isoCylinderX(-61, -39, 515, -50, 17.5, { front: '#f4f4f4', side: '#d0d0d0', sw: 0.35 });
  // шарик
  s += isoBall(0, 570, 0, 16.5);
  // выноски
  feature(1, iso({ x: -285, y: 500, z: -235 })[0], iso({ x: -285, y: 500, z: -235 })[1]);
  feature(5, iso({ x: 240, y: 560, z: 160 })[0], iso({ x: 240, y: 560, z: 160 })[1]);
  s += clipEnd();

  s += renderLeaders();

  const rows = [
    [1, 'Рама 30×30×1,5', 1, 'сталь, раскосы'],
    [2, 'Панели ПК 4–5 мм', 'к-т', '3 стороны + верх'],
    [3, 'Дверцы нижние Г-обр.', 2, 'петли, защёлка, концевик'],
    [4, 'Крышка + купол', 1, 'Ø420, верх 1060'],
    [5, 'Стол 500×400×15', 1, 'печать + сталь'],
    [6, 'Подстолье 500×400×18', 1, 'щель 250×40'],
    [7, 'Подвеска стола', 'к-т', '4 пружины, 4 направ.'],
    [8, 'Дрель', 1, 'покупная'],
    [9, 'Кулачок 20 мм', '1 из 3', 'PETG / PA-CF'],
    [10, 'Крепление дрели', 'к-т', '2 U-болта M8'],
    [11, 'E-stop / УЗО', 'к-т', 'E-stop, УЗО, знаки'],
    [12, 'Опоры / косынки', 'к-т', 'резина, сталь'],
  ];
  const notes = [
    { type: 'warn', text: 'Масса ≈38–45 кг. Лимит 20 кг НЕ выполнен — принятое отклонение.' },
    { type: 'text', text: 'Рама 30×30×1,5: жёсткость ≈4,4× ниже 40×40×3; раскосы обязательны.' },
    { type: 'text', text: 'Габарит с куполом 600×500×1060; рама 860, стол 560, подстолье 450.' },
    { type: 'text', text: 'Купол закреплён на крышке и поднимается вместе с ней.' },
  ];
  return sheetFrame(
    'Общий вид установки',
    'Рама 600×500×860, кожух ПК 4–5 мм, купол-уловитель, привод с кулачком',
    1,
    s,
    rows,
    notes,
    { title: 'Общий вид', scale: 'М 1:6…1:13 · размеры, мм', no: 1 }
  );
}

// ---------------------------------------------------------------------------
// ЛИСТ 2. Подвеска стола
// ---------------------------------------------------------------------------
function sheetSuspension() {
  const TL = { x: 24, y: 38, w: 112, h: 92 };
  const TR = { x: 162, y: 38, w: 112, h: 92 };
  const BL = { x: 24, y: 154, w: 112, h: 96 };
  const BR = { x: 162, y: 154, w: 112, h: 106 };
  let s = '';
  s += viewBox(TL, 'ВИД СВЕРХУ', '1:5');
  s += viewBox(TR, 'ВИД СЛЕВА', '1:4,5');
  s += viewBox(BL, 'ВИД СБОКУ', '1:5');
  s += viewBox(BR, 'ИЗОМЕТРИЯ', '1:6');

  // ===================== ВИД СВЕРХУ =====================
  set2D(TL, -280, 280, -230, 230, 0.94);
  group('s2tl', { x0: 15, x1: 145, y0: TL.y, y1: TL.y + TL.h });
  s += clipBegin(TL);
  // подстолье
  s += vRect(-250, -200, 250, 200, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1.2' });
  s += vText(0, -210, 'подстолье 500×400 (внизу)', { size: 1.8, anchor: 'middle', fill: MID });
  // стол
  s += vRect(-250, -200, 250, 200, { fill: '#f7f7f7', stroke: INK, sw: 0.5, rx: 1 });
  s += vEllipse(0, 0, 200, 150, { fill: 'none', stroke: '#b9b9b9', sw: 0.25 });
  s += vEllipse(0, 0, 150, 110, { fill: 'none', stroke: '#cfcfcf', sw: 0.25 });
  s += vEllipse(0, 0, 80, 55, { fill: 'none', stroke: '#e0e0e0', sw: 0.25 });
  s += vText(0, -155, 'вогнутость 6 мм', { size: 1.8, anchor: 'middle', fill: MID });
  // сегменты печати
  for (const x of [-125, 125]) {
    s += vLine(x, -198, x, 198, { sw: 0.25, dash: '3 1.5', stroke: MID });
  }
  s += vLine(-248, 0, 248, 0, { sw: 0.25, dash: '3 1.5', stroke: MID });
  s += vText(230, 12, 'сегменты', { size: 1.6, anchor: 'end', fill: MID });
  // балки
  s += vRect(-270, 150, 270, 210, { fill: '#e8e8e8', stroke: INK, sw: 0.4 });
  s += vRect(-270, -210, 270, -150, { fill: '#e8e8e8', stroke: INK, sw: 0.4 });
  // поперечины
  s += vRect(-270, -250, -230, 250, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(230, -250, 270, 250, { fill: FILL, stroke: INK, sw: 0.35 });
  // пружины
  for (const x of [-150, 150]) for (const z of [-180, 180]) {
    s += vCircle(x, z, 15, { fill: '#f6f6f6', stroke: INK, sw: 0.4 });
    s += vCircle(x, z, 10, { fill: 'none', stroke: MID, sw: 0.25 });
    s += vCircle(x, z, 5, { fill: 'none', stroke: MID, sw: 0.25 });
  }
  // направляющие и корпуса подшипников
  for (const x of [-225, 225]) for (const z of [-180, 180]) {
    s += vRect(x - 22.5, z - 22.5, x + 22.5, z + 22.5, { fill: '#5f5f5f', stroke: INK, sw: 0.35 });
    s += vCircle(x, z, 10, { fill: WHITE, stroke: INK, sw: 0.3 });
  }
  // ловители
  for (const x of [-100, 100]) for (const z of [-100, 100]) {
    s += vCircle(x, z, 20, { fill: 'none', stroke: '#8a8a8a', sw: 0.4, dash: '2 1' });
    s += vCircle(x, z, 14, { fill: '#d0d0d0', stroke: INK, sw: 0.3 });
  }
  // кулачок и ролики (под столом)
  s += vRect(-70, -125, -30, 125, { fill: '#f7e6e6', stroke: RED, sw: 0.35, dash: '1.8 1' });
  s += vRect(-61, 32.5, -39, 67.5, { fill: LIGHT, stroke: INK, sw: 0.35, dash: '1.6 1' });
  s += vRect(-61, -67.5, -39, -32.5, { fill: LIGHT, stroke: INK, sw: 0.35, dash: '1.6 1' });
  s += vText(-50, 140, 'кулачок z=±50', { size: 1.7, anchor: 'middle', fill: RED });
  // шарик
  s += vCircle(0, 0, 16.5, { fill: FILL, stroke: INK, sw: 0.35 });
  // размеры
  s += vDimH(-250, 250, 222, '500', { size: 1.9 });
  s += vDimV(-200, 200, -262, '400', { size: 1.9 });
  s += vDimH(-225, 225, -215, '450', { size: 1.8 });
  s += vDimV(-180, 180, 265, '360', { size: 1.8 });
  // выноски
  feature(1, X(-230), Y(-180));
  feature(4, X(220), Y(180));
  feature(5, X(150), Y(180));
  feature(6, X(225), Y(-180));
  feature(8, X(100), Y(100));
  s += clipEnd();

  // ===================== ВИД СЛЕВА =====================
  set2D(TR, -230, 230, 400, 760, 0.93);
  group('s2tr', { x0: 155, x1: 291, y0: TR.y, y1: TR.y + TR.h });
  s += clipBegin(TR);
  // подстолье со щелью 250
  s += vRect(-200, 432, -125, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(125, 432, 200, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vText(0, 441, 'щель 250', { size: 1.7, anchor: 'middle', fill: MID });
  // стол
  s += tableSection2D(-200, 200, 560, 545, 6, { fill: LIGHT });
  s += vCircle(0, 570, 16.5, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vText(0, 620, 'пакет: сталь 0,5 + печать 14 + сталь 0,4', { size: 1.45, anchor: 'middle', fill: MID });
  s += vText(0, 588, 'шарик Ø20–33', { size: 1.7, anchor: 'middle', fill: MID });
  // балки
  s += vRect(-210, 670, -150, 710, { fill: FILL2, stroke: INK, sw: 0.4 });
  s += vRect(150, 670, 210, 710, { fill: FILL2, stroke: INK, sw: 0.4 });
  // пружины
  for (const z of [-180, 180]) {
    s += vSpring(z, 560, 670, 15, 7);
    s += vRect(z - 22, 545, z + 22, 577, { fill: FILL, stroke: INK, sw: 0.3 });
    s += vLine(z, 535, z, 700, { sw: 0.3, dash: '2 1', stroke: MID });
  }
  // ловители
  for (const z of [-100, 100]) {
    s += vRect(z - 10, 450, z + 10, 530, { fill: LIGHT, stroke: INK, sw: 0.3 });
    s += vRect(z - 20, 530, z + 20, 540, { fill: '#8a8a8a', stroke: INK, sw: 0.3 });
  }
  // мини-схема контакта (не в масштабе вида)
  s += circle(218, 121, 5.2, { fill: '#f2f2f2', stroke: INK, sw: 0.35 });
  s += circle(218, 121, 1.2, { fill: WHITE, stroke: INK, sw: 0.25 });
  s += circle(214, 116, 2.2, { fill: WHITE, stroke: INK, sw: 0.35 });
  s += circle(222, 116, 2.2, { fill: WHITE, stroke: INK, sw: 0.35 });
  s += line(218, 121, 214, 116, { sw: 0.2, stroke: RED });
  s += line(218, 121, 222, 116, { sw: 0.2, stroke: RED });
  s += circle(214, 116, 0.5, { fill: RED, stroke: 'none' });
  s += circle(222, 116, 0.5, { fill: RED, stroke: 'none' });
  s += text(218, 128.5, 'контакт (лист 3)', { size: 1.55, anchor: 'middle', fill: MID });
  // размеры
  s += vDimV(450, 560, 245, '110', { size: 1.9 });
  s += vDimV(560, 670, 245, '110', { size: 1.9 });
  s += vDimV(450, 670, 275, '220', { size: 1.9 });
  s += vDimH(-200, 200, 420, '400', { size: 1.9 });
  s += vDimV(670, 710, -245, '40', { size: 1.8 });
  // выноски
  feature(1, X(-200), Y(552));
  feature(2, X(0), Y(560));
  feature(3, X(0), Y(545));
  feature(5, X(180), Y(610));
  feature(6, X(180), Y(690));
  feature(8, X(-100), Y(500));
  feature(10, X(50), Y(515));
  s += clipEnd();

  // ===================== ВИД СБОКУ =====================
  s += clipBegin(BL);
  set2D(BL, -280, 280, 400, 760, 0.94);
  group('s2bl', { x0: 15, x1: 145, y0: BL.y, y1: BL.y + BL.h });
  // подстолье со щелью
  s += vRect(-250, 432, -70, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  s += vRect(-30, 432, 250, 450, { fill: FILL, stroke: INK, sw: 0.35 });
  // стол
  s += tableSection2D(-250, 250, 560, 545, 6, { fill: LIGHT });
  s += vCircle(0, 570, 16.5, { fill: FILL, stroke: INK, sw: 0.35 });
  // балки и поперечины
  s += vRect(-270, 670, 270, 710, { fill: FILL2, stroke: INK, sw: 0.4 });
  s += vRect(-270, 670, -230, 710, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vRect(230, 670, 270, 710, { fill: FILL, stroke: INK, sw: 0.3 });
  // пружины и направляющие
  for (const x of [-150, 150]) s += vSpring(x, 560, 670, 15, 7);
  for (const x of [-225, 225]) {
    s += vLine(x, 535, x, 700, { sw: 0.35 });
    s += vRect(x - 22, 545, x + 22, 577, { fill: FILL, stroke: INK, sw: 0.3 });
  }
  // ловители
  for (const x of [-100, 100]) {
    s += vRect(x - 10, 450, x + 10, 530, { fill: LIGHT, stroke: INK, sw: 0.3 });
    s += vRect(x - 20, 530, x + 20, 540, { fill: '#8a8a8a', stroke: INK, sw: 0.3 });
  }
  // ролик и кронштейн; кулачок показан схематично
  s += vLine(-82, 492, -18, 492, { sw: 0.3, dash: '2 1', stroke: RED });
  s += vText(-50, 484, 'кулачок (лист 3)', { size: 1.55, anchor: 'middle', fill: RED });
  s += drawRoller2D(-50, 515);
  s += vRect(-100, 537, 0, 545, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(-62, 472, -58, 537, { fill: FILL2, stroke: INK, sw: 0.3 });
  s += vRect(-42, 472, -38, 537, { fill: FILL2, stroke: INK, sw: 0.3 });
  // размеры
  s += vDimH(-250, 250, 735, '500', { size: 1.9 });
  s += vDimH(-150, 150, 725, '300', { size: 1.8 });
  s += vDimH(-225, 225, 745, '450', { size: 1.8 });
  s += vDimV(450, 560, 270, '110', { size: 1.9 });
  s += vDimV(560, 670, 270, '110', { size: 1.9 });
  s += vText(0, 420, 'нижние пружины удалены', { size: 1.7, anchor: 'middle', fill: AMBER });
  s += clipEnd();
  // выноски (вне клипа)
  feature(1, X(-200), Y(552));
  feature(4, X(200), Y(690));
  feature(5, X(150), Y(610));
  feature(6, X(225), Y(660));
  feature(7, X(225), Y(560));
  feature(9, X(0), Y(700));

  // ===================== ИЗОМЕТРИЯ =====================
  setIsoCamera(0.68, -0.55);
  const pts = [];
  for (const x of [-250, 250]) for (const z of [-200, 200]) for (const y of [432, 560, 710]) pts.push({ x, y, z });
  for (const x of [-270, 270]) for (const z of [-210, 210]) for (const y of [670, 710]) pts.push({ x, y, z });
  for (const x of [-225, 225]) for (const z of [-180, 180]) for (const y of [535, 700]) pts.push({ x, y, z });
  fitIso(pts, { w: 104, h: 96, cx: BR.x + BR.w / 2, cy: BR.y + BR.h / 2 + 1 });
  s += clipBegin(BR);
  // подстолье
  s += isoBox(-250, 250, 432, 450, -200, 200, { top: '#ececec', side: '#d8d8d8', side2: '#c4c4c4', sw: 0.3 });
  // балки и поперечины
  s += isoBox(-270, 270, 670, 710, 150, 210, { top: '#e8e8e8', side: '#d4d4d4', side2: '#c0c0c0' });
  s += isoBox(-270, 270, 670, 710, -210, -150, { top: '#e8e8e8', side: '#d4d4d4', side2: '#c0c0c0' });
  s += isoBox(-270, -230, 670, 710, -250, 250, { top: '#e2e2e2', side: '#cecece', side2: '#bababa' });
  s += isoBox(230, 270, 670, 710, -250, 250, { top: '#e2e2e2', side: '#cecece', side2: '#bababa' });
  // пружины
  for (const x of [-150, 150]) for (const z of [-180, 180]) s += isoSpring(x, z, 560, 670, 15, 7);
  // направляющие
  for (const x of [-225, 225]) for (const z of [-180, 180]) {
    s += isoCylinderY(x, z, 535, 700, 10, { front: '#f2f2f2', side: '#d8d8d8', sw: 0.3 });
    s += isoBox(x - 22, x + 22, 545, 577, z - 22, z + 22, { top: '#7a7a7a', side: '#6a6a6a', side2: '#5a5a5a', sw: 0.25 });
  }
  // ловители
  for (const x of [-100, 100]) for (const z of [-100, 100]) {
    s += isoCylinderY(x, z, 450, 530, 10, { front: '#e8e8e8', side: '#d0d0d0', sw: 0.25 });
    s += isoCylinderY(x, z, 530, 540, 20, { front: '#8a8a8a', side: '#707070', sw: 0.25 });
  }
  // стол
  s += isoBox(-250, 250, 545, 560, -200, 200, { top: '#eaf1f8', side: '#c9d6e4', side2: '#b6c7d9', sw: 0.35 });
  s += isoBall(0, 570, 0, 16.5);
  // ролики (кулачок не показан)
  s += isoCylinderX(-61, -39, 515, 50, 17.5, { front: '#f4f4f4', side: '#d0d0d0', sw: 0.3 });
  s += isoCylinderX(-61, -39, 515, -50, 17.5, { front: '#f4f4f4', side: '#d0d0d0', sw: 0.3 });
  // выноски
  feature(1, iso({ x: 240, y: 552, z: 180 })[0], iso({ x: 240, y: 552, z: 180 })[1]);
  feature(4, iso({ x: 260, y: 690, z: -180 })[0], iso({ x: 260, y: 690, z: -180 })[1]);
  s += clipEnd();

  s += renderLeaders();

  const rows = [
    [1, 'Стол печатный 500×400×15', 1, 'PETG/PA-CF; ≈3 кг'],
    [2, 'Накладка сталь 0,5', 1, 'сверху'],
    [3, 'Накладка сталь 0,4', 1, 'снизу'],
    [4, 'Балка 60×40', 2, 'сталь, y=670'],
    [5, 'Пружина d2,0 D30', 4, 'предв.'],
    [6, 'Направляющая Ø20', 4, 'сталь'],
    [7, 'Подшипник LM20UU', 4, 'линейный'],
    [8, 'Ловитель резиновый', 4, 'Ø40, зазор 5'],
    [9, 'Крепёж M8', 'к-т', 'шайбы, гайки'],
    [10, 'Кулачок / ролик', 'схем.', 'см. лист 3'],
  ];
  const notes = [
    { type: 'head', text: 'ПРУЖИНА (предварительно)' },
    { type: 'text', text: 'd=2,0; D=30; n=16; L0=233; L уст.=110 мм.' },
    { type: 'text', text: 'k=0,366 Н/мм; F=45 Н/пружину; ΣF=180 Н.' },
    { type: 'text', text: 'f соб.=3,5 Гц; требуется проверка на макете.' },
    { type: 'warn', text: 'Нижние пружины удалены; поджим только верхними.' },
    { type: 'text', text: 'Бортики и саморезы по краям; сегменты печати.' },
    { type: 'text', text: 'Боковой люфт ≤0,1 мм; наклон ≤0,1°.' },
  ];
  return sheetFrame(
    'Подвеска стола',
    'Стол на 4 пружинах и 4 направляющих; балки на 670; нижние пружины убраны',
    2,
    s,
    rows,
    notes,
    { title: 'Подвеска стола', scale: 'М 1:5…1:6 · размеры, мм', no: 2 }
  );
}
function sheetCamRoller() {
  const TL = { x: 24, y: 38, w: 112, h: 92 };
  const TR = { x: 162, y: 38, w: 112, h: 92 };
  const BL = { x: 24, y: 154, w: 112, h: 96 };
  const BR = { x: 162, y: 154, w: 112, h: 106 };
  let s = '';
  s += viewBox(TL, 'ВИД СВЕРХУ', '1:3');
  s += viewBox(TR, 'ВИД СЛЕВА', '1:3,5');
  s += viewBox(BL, 'ВИД СБОКУ', '1:3,5');
  s += viewBox(BR, 'ИЗОМЕТРИЯ', '1:3');

  // ===================== ВИД СВЕРХУ =====================
  set2D(TL, -150, 150, -120, 120, 0.94);
  group('s3tl', { x0: 15, x1: 145, y0: TL.y, y1: TL.y + TL.h });
  s += clipBegin(TL);
  s += vRect(-150, -110, 150, 110, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1.2' });
  s += vText(0, 118, 'стол 500×400 (фрагмент)', { size: 1.8, anchor: 'middle', fill: MID });
  for (const zc of [-50, 50]) {
    s += vRect(-100, zc - 30, 0, zc + 30, { fill: '#ececec', stroke: INK, sw: 0.45 });
    s += vRect(-62, zc - 30, -58, zc + 30, { fill: FILL2, stroke: INK, sw: 0.3 });
    s += vRect(-42, zc - 30, -38, zc + 30, { fill: FILL2, stroke: INK, sw: 0.3 });
    for (const x of [-80, -20]) for (const z of [zc - 18, zc + 18]) {
      s += vCircle(x, z, 4, { fill: WHITE, stroke: INK, sw: 0.3 });
      s += vCircle(x, z, 2.2, { fill: 'none', stroke: MID, sw: 0.25 });
    }
    s += vRect(-78, zc - 6, -22, zc + 6, { fill: LIGHT, stroke: INK, sw: 0.35 });
    s += vCircle(-78, zc, 6, { fill: FILL, stroke: INK, sw: 0.3 });
    s += vRect(-61, zc - 17.5, -39, zc + 17.5, { fill: '#f4f4f4', stroke: INK, sw: 0.4 });
    s += vLine(-50, zc - 17.5, -50, zc + 17.5, { sw: 0.25, dash: '1.5 1' });
    s += vText(-50, zc + 23, '2×6202', { size: 1.6, anchor: 'middle', fill: MID });
  }
  s += vRect(-60, -115, -40, 115, { fill: '#f7e6e6', stroke: RED, sw: 0.4, dash: '2 1.2' });
  s += vCircle(-50, 0, 6, { fill: WHITE, stroke: RED, sw: 0.3 });
  s += vText(-50, -118, 'кулачок 20', { size: 1.7, anchor: 'middle', fill: RED });
  s += vDimH(-100, 0, -78, '100', { size: 1.8 });
  s += vDimV(-80, 80, -112, '160', { size: 1.8 });
  s += vDimH(-50, 50, 86, '100', { size: 1.8 });
  s += vDimH(-62, -38, 72, '24', { size: 1.6 });
  s += vDimV(32.5, 67.5, 30, '35', { size: 1.6 });
  feature(1, X(-50), Y(-100));
  feature(2, X(-50), Y(50));
  feature(3, X(-5), Y(75));
  feature(4, X(-75), Y(-50));
  feature(5, X(-80), Y(68));
  s += clipEnd();

  // ===================== ВИД СЛЕВА =====================
  set2D(TR, -145, 145, 270, 570, 0.93);
  group('s3tr', { x0: 155, x1: 291, y0: TR.y, y1: TR.y + TR.h });
  s += clipBegin(TR);
  s += vLine(-145, 450, -125, 450, { sw: 0.3, dash: '2 1', stroke: MID });
  s += vLine(125, 450, 145, 450, { sw: 0.3, dash: '2 1', stroke: MID });
  s += vText(0, 455, 'подстолье, щель 250', { size: 1.6, anchor: 'middle', fill: MID });
  s += vRect(-145, 545, 145, 560, { fill: LIGHT, stroke: INK, sw: 0.4 });
  s += drawCam2D(0, 395, 2.76, { fill: '#f2f2f2' });
  for (const zc of [-50, 50]) {
    s += vRect(-30, 472, 30, 537, { fill: 'none', stroke: MID, sw: 0.3, dash: '1.8 1' });
  }
  s += drawRoller2D(-50, 515);
  s += drawRoller2D(50, 515);
  s += vLine(0, 395, -50, 515, { sw: 0.25, dash: '2 1', stroke: RED });
  s += vLine(0, 395, 50, 515, { sw: 0.25, dash: '2 1', stroke: RED });
  const ar = 45;
  s += path(`M ${f(X(0))} ${f(Y(395 + ar))} A ${f(ar * V.s)} ${f(ar * V.s)} 0 0 0 ${f(X(0 - ar * Math.sin(0.394)))} ${f(Y(395 + ar * Math.cos(0.394)))}`, { sw: 0.25, stroke: RED });
  s += vText(-15, 438, '22,5°', { size: 2.0, anchor: 'end', fill: RED });
  s += vCircle(-49.2, 497.5, 1.2, { fill: RED, stroke: RED, sw: 0.2 });
  s += vCircle(49.2, 497.5, 1.2, { fill: RED, stroke: RED, sw: 0.2 });
  s += vDimV(395, 515, -130, '120', { size: 1.8 });
  s += vDimH(-50, 50, 535, '100', { size: 1.8 });
  s += vLine(-50, 515, 50, 515, { sw: 0.2, dash: '2 1', stroke: MID });
  s += vText(0, 524, 'd=130', { size: 1.7, anchor: 'middle', fill: MID });
  feature(1, X(0), Y(480));
  feature(2, X(50), Y(515));
  feature(3, X(-30), Y(490));
  feature(8, X(0), Y(420));
  s += clipEnd();

  // ===================== ВИД СБОКУ =====================
  set2D(BL, -110, 40, 270, 570, 0.93);
  group('s3bl', { x0: 15, x1: 145, y0: BL.y, y1: BL.y + BL.h });
  s += clipBegin(BL);
  s += vRect(-120, 545, 25, 560, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += vRect(-100, 537, 0, 545, { fill: FILL2, stroke: INK, sw: 0.4 });
  s += vRect(-62, 472, -58, 537, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(-42, 472, -38, 537, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(-60, 330, -40, 510, { fill: '#f2f2f2', stroke: INK, sw: 0.45 });
  s += vLine(-50, 330, -50, 510, { sw: 0.2, dash: '3 1 0.8 1' });
  s += vLine(-60, 395, -40, 395, { sw: 0.2, dash: '2 1' });
  s += vText(-50, 340, 'кулачок', { size: 1.6, anchor: 'middle', fill: MID });
  s += vText(-75, 370, '15/12', { size: 1.35, anchor: 'middle', fill: MID });
  s += vRect(-61, 497.5, -50, 532.5, { fill: '#f4f4f4', stroke: INK, sw: 0.4 });
  s += vRect(-50, 497.5, -39, 532.5, { fill: '#f4f4f4', stroke: INK, sw: 0.4 });
  s += vLine(-50, 497.5, -50, 532.5, { sw: 0.25, dash: '1.5 1' });
  s += vRect(-76, 509, -24, 521, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vRect(-72, 504, -66, 526, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vRect(-34, 504, -28, 526, { fill: FILL, stroke: INK, sw: 0.3 });
  s += vCircle(-50, 497.5, 1.2, { fill: RED, stroke: RED, sw: 0.2 });
  s += vDimH(-60, -40, 500, '20', { size: 1.7 });
  s += vDimH(-61, -39, 480, '22', { size: 1.7 });
  s += vDimH(-62, -38, 465, '24', { size: 1.7 });
  s += vDimV(472, 537, -108, '65', { size: 1.7 });
  s += vDimV(497.5, 532.5, -84, 'Ø35', { size: 1.7 });
  s += vDimH(-100, 0, 565, '100', { size: 1.7 });
  feature(1, X(-50), Y(440));
  feature(2, X(-55), Y(515));
  feature(3, X(-90), Y(540));
  feature(4, X(-70), Y(515));
  feature(6, X(0), Y(552));
  s += clipEnd();

  // ===================== ИЗОМЕТРИЯ =====================
  setIsoCamera(0.72, -0.55);
  const pts = [];
  for (const x of [-100, 0]) for (const y of [472, 560]) for (const z of [-80, 80]) pts.push({ x, y, z });
  for (const x of [-60, -40]) for (const y of [280, 510]) for (const z of [-115, 115]) pts.push({ x, y, z });
  for (const y of [497.5, 532.5]) for (const z of [-67.5, 67.5]) pts.push({ x: -61, y, z });
  fitIso(pts, { w: 100, h: 96, cx: BR.x + BR.w / 2, cy: BR.y + BR.h / 2 + 1 });
  s += clipBegin(BR);
  s += isoBox(-120, 0, 545, 560, -70, 70, { top: '#eaf1f8', side: '#c9d6e4', side2: '#b6c7d9', sw: 0.35 });
  for (const zc of [-50, 50]) {
    s += isoBox(-100, 0, 537, 545, zc - 30, zc + 30, { top: '#ececec', side: '#d6d6d6', side2: '#c2c2c2', sw: 0.3 });
    s += isoBox(-62, -58, 472, 537, zc - 30, zc + 30, { top: '#e8e8e8', side: '#d2d2d2', side2: '#bebebe', sw: 0.3 });
    s += isoBox(-42, -38, 472, 537, zc - 30, zc + 30, { top: '#e8e8e8', side: '#d2d2d2', side2: '#bebebe', sw: 0.3 });
    s += isoCylinderX(-80, -20, 515, zc, 6, { front: '#f2f2f2', side: '#d0d0d0', sw: 0.3 });
    s += isoCylinderX(-61, -39, 515, zc, 17.5, { front: '#f4f4f4', side: '#d0d0d0', sw: 0.35 });
    s += isoCylinderX(-50.5, -49.5, 515, zc, 17.5, { front: 'none', side: 'none', stroke: INK, sw: 0.2 });
  }
  const camFront = [];
  const camBack = [];
  for (let i = 0; i <= 120; i++) {
    const t = (2 * Math.PI * i) / 120;
    const r = G.cam.R + 2.76 * Math.cos(2 * t);
    camFront.push({ x: -60, y: 395 + r * Math.cos(t), z: r * Math.sin(t) });
    camBack.push({ x: -40, y: 395 + r * Math.cos(t), z: r * Math.sin(t) });
  }
  const band = [];
  for (const p of camFront) band.push(p);
  for (let i = camBack.length - 1; i >= 0; i--) band.push(camBack[i]);
  s += isoPoly(band, { fill: '#bdbdbd', stroke: 'none' });
  s += isoPoly(camFront, { fill: '#ededed', stroke: INK, sw: 0.4 });
  feature(1, iso({ x: -50, y: 460, z: 80 })[0], iso({ x: -50, y: 460, z: 80 })[1]);
  feature(2, iso({ x: -50, y: 515, z: 50 })[0], iso({ x: -50, y: 515, z: 50 })[1]);
  s += clipEnd();

  s += renderLeaders();

  const rows = [
    [1, 'Кулачок 20 мм', 3, 'PETG/PA-CF'],
    [2, 'Ролик 6202-2RS', 4, '2 на ролик'],
    [3, 'Кронштейн', 2, 'щёки 60×65'],
    [4, 'Ось M12', 2, 'сталь 8.8'],
    [5, 'Винт M8', 8, 'крепление к столу'],
    [6, 'Стол (фрагмент)', 1, 'см. лист 2'],
    [7, 'Пятно контакта', '22 мм', '2×11'],
    [8, 'Угол контакта', '22,5°', 'z=±50'],
  ];
  const notes = [
    { type: 'head', text: 'АМПЛИТУДА (два ролика, z=±50)' },
    { type: 'text', text: 'A=√((R+e+r)²−z²) − √((R−e+r)²−z²).' },
    { type: 'text', text: 'e=1,38 / 2,76 / 4,60 → A=3 / 6 / 10 мм.' },
    { type: 'text', text: 'R=110; r=17,5; z=50; ширина контакта 22.' },
    { type: 'warn', text: 'Кулачок без стальной вставки; ресурс проверить.' },
    { type: 'text', text: 'Зазор щёк 24 мм; 2×6202 = 22 мм.' },
  ];
  let pg = text(305, 44, 'ПРОФИЛИ (e×6)', { size: 1.85, weight: 'bold', fill: MID });
  const pe = [1.38, 2.76, 4.6];
  pe.forEach((e, i) => {
    const cx = 318 + i * 24;
    const cy = 57;
    const rr = 7;
    const pts = [];
    for (let k = 0; k <= 90; k++) {
      const t = (2 * Math.PI * k) / 90;
      const r = rr + e * 0.55 * Math.cos(2 * t);
      pts.push([cx + r * Math.sin(t), cy + r * Math.cos(t)]);
    }
    pg += poly(pts, { fill: 'none', stroke: i === 1 ? INK : MID, sw: i === 1 ? 0.45 : 0.3, dash: i === 2 ? '1.4 0.9' : undefined });
    pg += text(cx, 68, `e=${String(e).replace('.', ',')}`, { size: 1.6, anchor: 'middle', fill: MID });
    pg += text(cx, 72, i === 0 ? 'A=3' : i === 1 ? 'A=6' : 'A=10', { size: 1.6, anchor: 'middle', weight: 'bold' });
  });
  pg += line(303, 77, 407, 77, { sw: 0.25, stroke: '#cfcfcf' });
  return sheetFrame(
    'Контакт кулачка и роликов',
    'Три профиля e=1,38/2,76/4,60; два ролика, по два 6202-2RS; кронштейны 100×60',
    3,
    s,
    rows,
    notes,
    { title: 'Кулачок–ролики', scale: 'М 1:3 · размеры, мм', no: 3 },
    pg
  );
}
function sheetCamMount() {
  const TL = { x: 24, y: 38, w: 112, h: 92 };
  const TR = { x: 162, y: 38, w: 112, h: 92 };
  const BL = { x: 24, y: 154, w: 112, h: 96 };
  const BR = { x: 162, y: 154, w: 112, h: 106 };
  let s = '';
  s += viewBox(TL, 'ВИД СВЕРХУ', '1:5');
  s += viewBox(TR, 'ВИД СЛЕВА', '1:4,5');
  s += viewBox(BL, 'ВИД СБОКУ', '1:4,5');
  s += viewBox(BR, 'ИЗОМЕТРИЯ', '1:5');

  // ===================== ВИД СВЕРХУ =====================
  set2D(TL, -280, 280, -230, 230, 0.94);
  group('s4tl', { x0: 15, x1: 145, y0: TL.y, y1: TL.y + TL.h });
  s += clipBegin(TL);
  s += vRect(-250, -200, 250, 200, { fill: '#f7f7f7', stroke: INK, sw: 0.45 });
  s += vRect(-70, -125, -30, 125, { fill: '#5f5f5f', stroke: INK, sw: 0.35 });
  s += vText(-50, 135, 'щель 250×40', { size: 1.7, anchor: 'middle', fill: RED });
  // кулачок под подстольем
  s += vRect(-60, -115, -40, 115, { fill: '#f7e6e6', stroke: RED, sw: 0.35, dash: '2 1.2' });
  // подвесы
  for (const x of [-75, -25]) {
    s += vRect(x - 4, -60, x + 4, 60, { fill: FILL2, stroke: INK, sw: 0.35 });
    s += vCircle(x, 0, 17.5, { fill: 'none', stroke: INK, sw: 0.3 });
  }
  // вал
  s += vRect(-100, -6, 50, 6, { fill: LIGHT, stroke: INK, sw: 0.3 });
  // дрель (скрыта)
  s += vRect(0, -25, 70, 25, { fill: 'none', stroke: MID, sw: 0.3, dash: '2 1.2' });
  s += vRect(70, -35, 295, 35, { fill: 'none', stroke: MID, sw: 0.3, dash: '2 1.2' });
  s += vRect(280, -35, 300, 35, { fill: 'none', stroke: MID, sw: 0.25, dash: '1.4 1' });
  // оси
  s += vLine(0, -200, 0, 200, { sw: 0.2, dash: '3 1 0.8 1', stroke: RED });
  s += vLine(-50, -200, -50, 200, { sw: 0.2, dash: '3 1 0.8 1', stroke: RED });
  s += vLine(-75, -60, -75, 60, { sw: 0.15, dash: '2 1', stroke: MID });
  s += vLine(-25, -60, -25, 60, { sw: 0.15, dash: '2 1', stroke: MID });
  // размеры
  s += vDimH(-250, 250, 222, '500', { size: 1.9 });
  s += vDimV(-200, 200, -262, '400', { size: 1.9 });
  s += vDimH(-70, -30, 150, '40', { size: 1.7 });
  s += vDimV(-125, 125, 282, '250', { size: 1.8 });
  s += vDimH(-75, -25, 190, '50', { size: 1.7 });
  s += vDimH(-50, 0, 210, '50', { size: 1.7, stroke: RED });
  // выноски
  feature(1, X(200), Y(-180));
  feature(2, X(-50), Y(100));
  feature(3, X(-75), Y(-50));
  feature(4, X(-25), Y(40));
  feature(5, X(20), Y(0));
  feature(6, X(-60), Y(-20));
  s += clipEnd();

  // ===================== ВИД СЛЕВА =====================
  set2D(TR, -230, 230, 350, 480, 0.93);
  group('s4tr', { x0: 155, x1: 291, y0: TR.y, y1: TR.y + TR.h });
  s += clipBegin(TR);
  // подстолье со щелью
  s += vRect(-200, 432, -125, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  s += vRect(125, 432, 200, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  s += vText(0, 441, 'щель 250', { size: 1.7, anchor: 'middle', fill: MID });
  // кулачок (за подстольем)
  s += drawCam2D(0, 395, 2.76, { fill: '#f7f7f7', dash: '2 1.2' });
  // подвесы и подшипники
  s += vRect(-60, 395, 60, 432, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1' });
  s += drawBearing2D(0, 395, 17.5, { fill: '#f2f2f2' });
  // дрель за кулачком
  s += vCircle(0, 395, 35, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1.2' });
  s += vCircle(0, 395, 25, { fill: 'none', stroke: MID, sw: 0.3, dash: '2 1.2' });
  s += vCircle(0, 395, 6, { fill: WHITE, stroke: INK, sw: 0.35 });
  // размеры
  s += vDimV(377.5, 412.5, 215, 'Ø35', { size: 1.7 });
  s += vDimV(360, 430, 235, 'Ø70', { size: 1.7 });
  s += vDimV(370, 420, 250, 'Ø50', { size: 1.7 });
  s += vDimV(432, 450, -215, '18', { size: 1.7 });
  // выноски
  feature(1, X(-200), Y(441));
  feature(4, X(0), Y(395));
  feature(8, X(0), Y(370));
  feature(10, X(0), Y(360));
  s += clipEnd();

  // ===================== ВИД СБОКУ =====================
  set2D(BL, -130, 330, 350, 600, 0.93);
  group('s4bl', { x0: 15, x1: 145, y0: BL.y, y1: BL.y + BL.h });
  s += clipBegin(BL);
  // стол и шарик
  s += vRect(-130, 545, 250, 560, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += vCircle(0, 570, 16.5, { fill: FILL, stroke: INK, sw: 0.35 });
  // подстолье со щелью
  s += vRect(-130, 432, -70, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  s += vRect(-30, 432, 330, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  // кулачок
  s += vRect(-60, 280, -40, 510, { fill: '#f2f2f2', stroke: INK, sw: 0.45 });
  s += vLine(-50, 280, -50, 510, { sw: 0.2, dash: '3 1 0.8 1' });
  s += vLine(-60, 395, -40, 395, { sw: 0.2, dash: '2 1' });
  // подвесы
  for (const x of [-75, -25]) {
    s += vRect(x - 3, 395, x + 3, 432, { fill: FILL2, stroke: INK, sw: 0.3 });
    s += vRect(x - 4, 430, x + 4, 432, { fill: '#d8d8d8', stroke: INK, sw: 0.2 });
    s += drawBearing2D(x, 395, 17.5, { fill: '#f2f2f2' });
  }
  // вал
  s += vRect(-100, 389, 50, 401, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vRect(0, 389, 50, 401, { fill: '#e8e8e8', stroke: INK, sw: 0.3 });
  // конические гайки и контрагайки
  for (const sgn of [-1, 1]) {
    const x0 = sgn < 0 ? -68 : 32;
    const x1 = sgn < 0 ? -58 : 42;
    s += vRect(x0, 386, x1, 404, { fill: FILL, stroke: INK, sw: 0.3 });
    s += vRect(sgn < 0 ? -62 : 38, 389, sgn < 0 ? -58 : 42, 401, { fill: '#bdbdbd', stroke: INK, sw: 0.25 });
  }
  // стопорная пластина и штифт
  s += vRect(-40, 470, -32, 500, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(-34, 485, -30, 495, { fill: INK, stroke: INK, sw: 0.2 });
  s += vLine(-40, 490, -50, 490, { sw: 1.4, stroke: RED });
  // патрон и дрель
  s += vRect(0, 370, 70, 420, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += vRect(70, 360, 295, 430, { fill: '#f7f7f7', stroke: INK, sw: 0.45, rx: 2 });
  s += vRect(280, 360, 300, 430, { fill: 'none', stroke: MID, sw: 0.25, dash: '1.5 1' });
  // размеры
  s += vDimH(-50, 0, 575, '50', { size: 1.8, stroke: RED });
  s += vDimH(-60, -40, 515, '20', { size: 1.7 });
  s += vDimH(-70, -30, 445, '40', { size: 1.7 });
  s += vDimH(0, 70, 350, '70', { size: 1.7 });
  s += vDimH(70, 295, 340, '225', { size: 1.7 });
  s += vLine(0, 580, 0, 350, { sw: 0.2, dash: '3 1 0.8 1', stroke: RED });
  s += vLine(-50, 580, -50, 350, { sw: 0.2, dash: '3 1 0.8 1', stroke: RED });
  s += vText(0, 590, 'центр стола x=0', { size: 1.6, anchor: 'middle', fill: RED });
  // стрелка вращения против часовой
  s += path(`M ${f(X(-90))} ${f(Y(460))} A ${f(40 * V.s)} ${f(40 * V.s)} 0 0 1 ${f(X(-72))} ${f(Y(425))}`, { sw: 0.8, stroke: RED });
  s += arrow(X(-72), Y(425), X(-80), Y(418), { sw: 0.8, head: 2.6, hw: 1.1, stroke: RED });
  s += vText(-110, 462, 'CCW', { size: 2.2, weight: 'bold', fill: RED });
  // выноски
  feature(2, X(-50), Y(470));
  feature(3, X(-75), Y(415));
  feature(4, X(-25), Y(395));
  feature(5, X(20), Y(401));
  feature(6, X(-63), Y(395));
  feature(7, X(-36), Y(485));
  feature(8, X(35), Y(395));
  feature(9, X(-75), Y(431));
  s += clipEnd();

  // ===================== ИЗОМЕТРИЯ =====================
  setIsoCamera(0.58, -0.55);
  const pts = [];
  for (const x of [-120, 320]) for (const y of [350, 580]) for (const z of [-130, 130]) pts.push({ x, y, z });
  for (const x of [-75, -25]) for (const y of [395, 432]) for (const z of [-60, 60]) pts.push({ x, y, z });
  fitIso(pts, { w: 102, h: 96, cx: BR.x + BR.w / 2, cy: BR.y + BR.h / 2 + 1 });
  s += clipBegin(BR);
  // подстолье
  s += isoBox(-250, 250, 432, 450, -200, 200, { top: '#ececec', side: '#d8d8d8', side2: '#c4c4c4', sw: 0.3, fillOpacity: 0.35 });
  s += isoBox(-70, -30, 432, 451, -125, 125, { top: '#5f5f5f', side: '#4f4f4f', side2: '#424242', sw: 0.25, fillOpacity: 0.5 });
  // подвесы
  for (const x of [-75, -25]) {
    s += isoBox(x - 3, x + 3, 395, 432, -60, 60, { top: '#e0e0e0', side: '#cccccc', side2: '#b8b8b8', sw: 0.3 });
    s += isoCylinderX(x - 17.5, x + 17.5, 395, 0, 17.5, { front: '#f2f2f2', side: '#d0d0d0', sw: 0.3 });
  }
  // вал
  s += isoCylinderX(-100, 50, 395, 0, 6, { front: '#f2f2f2', side: '#d0d0d0', sw: 0.3 });
  // кулачок
  const camFront = [];
  const camBack = [];
  for (let i = 0; i <= 100; i++) {
    const t = (2 * Math.PI * i) / 100;
    const r = G.cam.R + 2.76 * Math.cos(2 * t);
    camFront.push({ x: -60, y: 395 + r * Math.cos(t), z: r * Math.sin(t) });
    camBack.push({ x: -40, y: 395 + r * Math.cos(t), z: r * Math.sin(t) });
  }
  const band = [];
  for (const p of camFront) band.push(p);
  for (let i = camBack.length - 1; i >= 0; i--) band.push(camBack[i]);
  s += isoPoly(band, { fill: '#bdbdbd', stroke: 'none' });
  s += isoPoly(camFront, { fill: '#ededed', stroke: INK, sw: 0.4 });
  // гайки и патрон
  s += isoCylinderX(-68, -58, 395, 0, 20, { front: '#d8d8d8', side: '#bdbdbd', sw: 0.3 });
  s += isoCylinderX(32, 42, 395, 0, 20, { front: '#d8d8d8', side: '#bdbdbd', sw: 0.3 });
  s += isoCylinderX(0, 70, 395, 0, 25, { front: '#f0f0f0', side: '#cccccc', sw: 0.35 });
  s += isoCylinderX(70, 295, 395, 0, 35, { front: '#fafafa', side: '#dcdcdc', sw: 0.4 });
  feature(1, iso({ x: 240, y: 450, z: 180 })[0], iso({ x: 240, y: 450, z: 180 })[1]);
  feature(2, iso({ x: -50, y: 470, z: 100 })[0], iso({ x: -50, y: 470, z: 100 })[1]);
  feature(4, iso({ x: -25, y: 395, z: 20 })[0], iso({ x: -25, y: 395, z: 20 })[1]);
  feature(8, iso({ x: 40, y: 395, z: 25 })[0], iso({ x: 40, y: 395, z: 25 })[1]);
  s += clipEnd();

  s += renderLeaders();

  const rows = [
    [1, 'Подстолье 500×400×18', 1, 'щель 250×40'],
    [2, 'Кулачок 20 мм', 1, 'x=−50'],
    [3, 'Подвес подшипника', 2, 'x=−75/−25'],
    [4, 'Подшипник 6202-2RS', 2, '35×15×11; втулка 15/12'],
    [5, 'Вал-шпилька M12', 1, 'Ø12 в патрон'],
    [6, 'Гайка конич. + контр.', '2+2', 'M12'],
    [7, 'Стопорная пластина', 1, 'штифт/винт'],
    [8, 'Патрон дрели', 1, 'покупной'],
    [9, 'Шайбы-подкладки', 'к-т', '0,5/1/2 мм'],
    [10, 'Резьбовой фиксатор', 1, 'средний'],
  ];
  const notes = [
    { type: 'warn', text: 'Ось кулачка смещена на 50 мм от центра стола; подшипники −75/−25.' },
    { type: 'warn', text: 'Вращение принудительно против часовой; резьба правая — патрон не должен самоотвинчиваться.' },
    { type: 'text', text: 'Затяжка: большой момент + конические гайки + контрагайки + фиксатор + штифт.' },
    { type: 'text', text: 'Щель 250×40 усилить накладками; биение кромки ≤0,05 мм.' },
    { type: 'text', text: 'Корпус дрели 70…300; на виде 70…295 + резерв.' },
  ];
  return sheetFrame(
    'Крепление кулачка на оси',
    'Кулачок на шпильке M12, два подшипника 6202; смещение 50 мм; хвостовик в патроне',
    4,
    s,
    rows,
    notes,
    { title: 'Крепление кулачка', scale: 'М 1:4,5…1:5 · размеры, мм', no: 4 }
  );
}
function sheetDrillMount() {
  const TL = { x: 24, y: 38, w: 112, h: 92 };
  const TR = { x: 162, y: 38, w: 112, h: 92 };
  const BL = { x: 24, y: 154, w: 112, h: 96 };
  const BR = { x: 162, y: 154, w: 112, h: 106 };
  let s = '';
  s += viewBox(TL, 'ВИД СВЕРХУ', '1:6');
  s += viewBox(TR, 'ВИД СЛЕВА', '1:4,5');
  s += viewBox(BL, 'ВИД СБОКУ', '1:4,5');
  s += viewBox(BR, 'ИЗОМЕТРИЯ', '1:5');

  // ===================== ВИД СВЕРХУ =====================
  set2D(TL, -280, 350, -230, 230, 0.94);
  group('s5tl', { x0: 15, x1: 145, y0: TL.y, y1: TL.y + TL.h });
  s += clipBegin(TL);
  s += vRect(-250, -200, 250, 200, { fill: '#f7f7f7', stroke: INK, sw: 0.45 });
  s += vRect(-70, -125, -30, 125, { fill: '#5f5f5f', stroke: INK, sw: 0.3 });
  // дрель
  s += vRect(0, -25, 70, 25, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1.2' });
  s += vRect(70, -35, 295, 35, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1.2' });
  s += vRect(280, -35, 300, 35, { fill: 'none', stroke: MID, sw: 0.25, dash: '1.4 1' });
  // резиновая подкладка
  s += vRect(70, -38, 295, 38, { fill: '#bdbdbd', stroke: '#8a8a8a', sw: 0.2, fillOpacity: 0.35 });
  // U-болты
  for (const x of [130, 260]) {
    s += vLine(x - 4, -45, x - 4, 45, { sw: 0.6, stroke: INK });
    s += vLine(x + 4, -45, x + 4, 45, { sw: 0.6, stroke: INK });
    for (const z of [-45, 45]) {
      s += vCircle(x, z, 8, { fill: FILL, stroke: INK, sw: 0.35 });
      s += vCircle(x, z, 4.5, { fill: WHITE, stroke: INK, sw: 0.3 });
    }
  }
  // упор от проворота
  s += vRect(195, 50, 225, 75, { fill: FILL2, stroke: INK, sw: 0.4 });
  s += vLine(210, 50, 210, 35, { sw: 1.4, stroke: RED });
  s += vText(210, 82, 'упор', { size: 1.7, anchor: 'middle', fill: RED });
  // рычаг курка и вырез
  s += vRect(230, -20, 300, 20, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += vRect(290, -30, 300, 30, { fill: 'none', stroke: RED, sw: 0.4, dash: '1.8 1' });
  s += vText(295, 38, 'вырез', { size: 1.6, anchor: 'middle', fill: RED });
  // оси
  s += vLine(-50, -200, -50, 200, { sw: 0.2, dash: '3 1 0.8 1', stroke: RED });
  s += vLine(0, -200, 0, 200, { sw: 0.2, dash: '2 1', stroke: MID });
  // размеры
  s += vDimH(-250, 250, 222, '500', { size: 1.9 });
  s += vDimV(-200, 200, -262, '400', { size: 1.9 });
  s += vDimH(130, 260, -100, '130', { size: 1.8 });
  s += vDimV(-45, 45, 285, '90', { size: 1.8 });
  s += vDimH(-50, 0, 160, '50', { size: 1.7, stroke: RED });
  s += vDimH(70, 295, 190, '225', { size: 1.7 });
  // выноски
  feature(1, X(250), Y(30));
  feature(2, X(260), Y(45));
  feature(3, X(100), Y(-38));
  feature(5, X(210), Y(65));
  feature(7, X(270), Y(0));
  s += clipEnd();

  // ===================== ВИД СЛЕВА =====================
  set2D(TR, -230, 230, 340, 470, 0.93);
  group('s5tr', { x0: 155, x1: 291, y0: TR.y, y1: TR.y + TR.h });
  s += clipBegin(TR);
  // подстолье
  s += vRect(-200, 432, 200, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  // дрель
  s += vCircle(0, 395, 35, { fill: '#f7f7f7', stroke: INK, sw: 0.45 });
  s += vCircle(0, 395, 25, { fill: LIGHT, stroke: INK, sw: 0.35 });
  // резиновая подкладка
  s += path(
    `M ${f(X(-40))} ${f(Y(395))} A ${f(40 * V.s)} ${f(40 * V.s)} 0 0 1 ${f(X(40))} ${f(Y(395))}`,
    { fill: 'none', stroke: '#8a8a8a', sw: 2.2, opacity: 0.8 }
  );
  // U-болт
  const ub = [];
  ub.push([45, 450]);
  ub.push([45, 395]);
  for (let i = 0; i <= 30; i++) {
    const a = (Math.PI * i) / 30;
    ub.push([40 * Math.cos(a), 395 - 40 * Math.sin(a)]);
  }
  ub.push([-45, 395]);
  ub.push([-45, 450]);
  s += vPolyline(ub, { sw: 1.6, stroke: INK });
  // гайки и шайбы
  for (const z of [-45, 45]) {
    s += vRect(z - 8, 450, z + 8, 458, { fill: '#d8d8d8', stroke: INK, sw: 0.3 });
    s += vRect(z - 5, 458, z + 5, 470, { fill: FILL, stroke: INK, sw: 0.3 });
  }
  // упор от проворота
  s += vRect(55, 432, 65, 450, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(58, 395, 62, 432, { fill: FILL2, stroke: INK, sw: 0.3 });
  // размеры
  s += vDimV(360, 430, 215, 'Ø70', { size: 1.8 });
  s += vDimV(355, 435, 235, 'Ø80', { size: 1.8 });
  s += vDimH(-45, 45, 475, '90', { size: 1.8 });
  s += vDimV(432, 450, -215, '18', { size: 1.7 });
  // выноски
  feature(1, X(0), Y(380));
  feature(2, X(-40), Y(370));
  feature(3, X(38), Y(395));
  feature(4, X(45), Y(458));
  feature(5, X(60), Y(440));
  s += clipEnd();

  // ===================== ВИД СБОКУ =====================
  set2D(BL, -130, 330, 280, 580, 0.93);
  group('s5bl', { x0: 15, x1: 145, y0: BL.y, y1: BL.y + BL.h });
  s += clipBegin(BL);
  // стол, подстолье
  s += vRect(-130, 545, 250, 560, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += vRect(-130, 432, -70, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  s += vRect(-30, 432, 330, 450, { fill: FILL, stroke: INK, sw: 0.4 });
  // дрель
  s += vRect(0, 370, 70, 420, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += vRect(70, 360, 295, 430, { fill: '#f7f7f7', stroke: INK, sw: 0.45, rx: 2 });
  s += vRect(280, 360, 300, 430, { fill: 'none', stroke: MID, sw: 0.25, dash: '1.5 1' });
  // кулачок — контур
  s += vRect(-60, 280, -40, 510, { fill: 'none', stroke: MID, sw: 0.35, dash: '2 1' });
  s += vLine(-50, 280, -50, 510, { sw: 0.2, dash: '3 1 0.8 1' });
  // U-болты (в проекции — хомуты)
  for (const x of [130, 260]) {
    s += vRect(x - 4, 360, x + 4, 432, { fill: '#3a3a3a', stroke: INK, sw: 0.3 });
    s += vRect(x - 10, 430, x + 10, 440, { fill: FILL, stroke: INK, sw: 0.3 });
  }
  // резиновая подкладка
  s += vRect(70, 428, 295, 432, { fill: '#8a8a8a', stroke: INK, sw: 0.25 });
  // рычаг курка
  s += vRect(230, 300, 295, 340, { fill: LIGHT, stroke: INK, sw: 0.4, rx: 2 });
  s += vRect(295, 315, 300, 335, { fill: FILL, stroke: INK, sw: 0.3 });
  // дверца с вырезом
  s += vLine(300, 260, 300, 315, { sw: 1.8, stroke: PC });
  s += vLine(300, 335, 300, 450, { sw: 1.8, stroke: PC });
  s += vRect(295, 305, 305, 345, { fill: 'none', stroke: RED, sw: 0.4, dash: '1.8 1' });
  s += vText(307, 325, 'вырез', { size: 1.7, fill: RED });
  // упор от проворота
  s += vRect(195, 432, 225, 450, { fill: FILL2, stroke: INK, sw: 0.35 });
  s += vRect(207, 400, 213, 432, { fill: FILL2, stroke: INK, sw: 0.3 });
  // размеры
  s += vDimH(70, 295, 350, '225', { size: 1.8 });
  s += vDimH(130, 260, 275, '130', { size: 1.7 });
  s += vDimV(432, 450, 315, '18', { size: 1.7 });
  // выноски
  feature(1, X(250), Y(395));
  feature(2, X(130), Y(400));
  feature(3, X(200), Y(430));
  feature(5, X(210), Y(440));
  feature(7, X(270), Y(320));
  s += clipEnd();

  // ===================== ИЗОМЕТРИЯ =====================
  setIsoCamera(0.6, -0.55);
  const pts = [];
  for (const x of [-130, 330]) for (const y of [280, 580]) for (const z of [-130, 130]) pts.push({ x, y, z });
  fitIso(pts, { w: 102, h: 96, cx: BR.x + BR.w / 2, cy: BR.y + BR.h / 2 + 1 });
  s += clipBegin(BR);
  // подстолье
  s += isoBox(-250, 250, 432, 450, -200, 200, { top: '#ececec', side: '#d8d8d8', side2: '#c4c4c4', sw: 0.3, fillOpacity: 0.35 });
  s += isoBox(-70, -30, 432, 451, -125, 125, { top: '#5f5f5f', side: '#4f4f4f', side2: '#424242', sw: 0.25, fillOpacity: 0.5 });
  // дрель
  s += isoCylinderX(0, 70, 395, 0, 25, { front: '#f0f0f0', side: '#cccccc', sw: 0.35 });
  s += isoCylinderX(70, 295, 395, 0, 35, { front: '#fafafa', side: '#dcdcdc', sw: 0.4 });
  // ось кулачка — не показан
  s += isoLine([-50, 395, -60], [-50, 395, 60], { sw: 0.3, dash: '2 1', stroke: MID });
  // U-болты
  for (const x of [130, 260]) {
    const ub3 = [];
    ub3.push({ x, y: 450, z: 45 });
    ub3.push({ x, y: 400, z: 42 });
    for (let i = 0; i <= 20; i++) {
      const a = (Math.PI * i) / 20;
      ub3.push({ x, y: 395 - 40 * Math.sin(a), z: 42 * Math.cos(a) });
    }
    ub3.push({ x, y: 400, z: -42 });
    ub3.push({ x, y: 450, z: -45 });
    s += isoPath(ub3, { sw: 1.6, stroke: '#2a2a2a' });
    s += isoHexY(x, 45, 458, 450, 7.5, { face: '#d8d8d8', side: '#bdbdbd', holeR: 4 });
    s += isoHexY(x, -45, 458, 450, 7.5, { face: '#d8d8d8', side: '#bdbdbd', holeR: 4 });
  }
  // упор
  s += isoBox(195, 225, 432, 450, 50, 75, { top: '#d0d0d0', side: '#bdbdbd', side2: '#a8a8a8', sw: 0.3 });
  // рычаг
  s += isoBox(230, 300, 300, 340, -20, 20, { top: '#f0f0f0', side: '#dcdcdc', side2: '#c8c8c8', sw: 0.3 });
  feature(1, iso({ x: 250, y: 395, z: 35 })[0], iso({ x: 250, y: 395, z: 35 })[1]);
  feature(2, iso({ x: 260, y: 395, z: 42 })[0], iso({ x: 260, y: 395, z: 42 })[1]);
  feature(5, iso({ x: 210, y: 440, z: 60 })[0], iso({ x: 210, y: 440, z: 60 })[1]);
  feature(7, iso({ x: 280, y: 320, z: 20 })[0], iso({ x: 280, y: 320, z: 20 })[1]);
  s += clipEnd();

  s += renderLeaders();

  const rows = [
    [1, 'Дрель бытовая', 1, 'покупная'],
    [2, 'U-болт M8 под Ø80', 2, 'x=130/260'],
    [3, 'Подкладка резиновая 2–3', 2, 'под скобу'],
    [4, 'Шайба / гайка M8', '4+4', 'сталь'],
    [5, 'Упор от проворота', 1, 'положительный'],
    [6, 'Шайбы-подкладки', 'к-т', '0,5/1/2 мм'],
    [7, 'Рычаг курка', 1, 'через вырез'],
    [8, 'Ось кулачка', 1, 'x=−50'],
    [9, 'Подстолье', 1, 'см. лист 4'],
  ];
  const notes = [
    { type: 'warn', text: 'U-болты не должны перекрывать вентиляционные окна дрели.' },
    { type: 'warn', text: 'Проверить отсутствие проворота при 2-кратном моменте.' },
    { type: 'text', text: 'Резина 2–3 мм; шайбы/подкладки для регулировки высоты.' },
    { type: 'text', text: 'Рычаг курка выведен наружу через вырез в дверце.' },
    { type: 'text', text: 'Ось кулачка x=−50; патрон 0…70; корпус 70…295 (резерв 300).' },
  ];
  return sheetFrame(
    'Крепление дрели к подстолью',
    'Два U-болта M8 под Ø80, резина 2–3 мм, упор от проворота, рычаг курка',
    5,
    s,
    rows,
    notes,
    { title: 'Крепление дрели', scale: 'М 1:4,5…1:6 · размеры, мм', no: 5 }
  );
}

function sheetCover() {
  let s = '';
  s += rect(5, 5, 410, 287, { fill: WHITE, stroke: INK, sw: 0.8 });
  s += rect(10, 10, 400, 277, { fill: 'none', stroke: INK, sw: 0.4 });
  s += text(30, 40, 'ВИБРОСТОЛ', { size: 10, weight: 'bold' });
  s += text(30, 56, 'Корректировки и замечания после инженерной экспертизы', {
    size: 5.2,
    fill: MID,
  });
  s += line(30, 66, 390, 66, { sw: 0.7 });
  s += text(30, 82, 'Альбом листов этапа expert_correct', { size: 4.0, weight: 'bold' });
  const items = [
    ['01', 'Общий вид установки', 'рама, кожух, купол, привод'],
    ['02', 'Подвеска стола', 'балки, пружины, направляющие, демпферы'],
    ['03', 'Контакт кулачка и роликов', 'профили, кронштейны, 2×6202 на ролик'],
    ['04', 'Крепление кулачка на оси', 'смещение 50 мм, два подшипника, гайки'],
    ['05', 'Крепление дрели', 'U-болты M8, резина, упор от проворота'],
  ];
  items.forEach((it, i) => {
    const y = 100 + i * 15;
    s += text(32, y, it[0], { size: 4.0, weight: 'bold', fill: BLUE });
    s += text(46, y, it[1], { size: 3.4, weight: 'bold' });
    s += text(46, y + 5.2, it[2], { size: 2.6, fill: MID });
  });
  s += line(30, 182, 260, 182, { sw: 0.4 });
  s += text(30, 194, 'Габарит: 600 × 500 × 1060 мм', { size: 3.0 });
  s += text(30, 203, 'Рама: 600 × 500 × 860, труба 30×30×1,5, раскосы', { size: 2.8 });
  s += text(30, 212, 'Кожух: поликарбонат 4–5 мм, дверцы, купол Ø420', { size: 2.8 });
  s += text(30, 221, 'Привод: дрель → патрон → шпилька M12 → 2 подшипника → кулачок', { size: 2.8 });
  s += rect(30, 232, 230, 18, { fill: '#f7e6e6', stroke: RED, sw: 0.5 });
  s += text(34, 241, 'Масса ≈38–45 кг. Лимит 20 кг не выполнен — принятое отклонение.', {
    size: 2.8,
    weight: 'bold',
    fill: RED,
  });
  s += text(30, 262, '28.10.2026 · DeepSeek / OpenCode · A3 · 6 страниц', { size: 2.4, fill: MID });

  // схема сбоку на обложке (не в масштабе)
  const cs = 0.125, cx = 340, cy = 240;
  const SX = (x) => cx + x * cs;
  const SY = (y) => cy - y * cs;
  const SR = (x, y, w, h, o = {}) => rect(SX(x), SY(y + h), w * cs, h * cs, o);
  const SL = (x1, y1, x2, y2, o = {}) => line(SX(x1), SY(y1), SX(x2), SY(y2), o);
  const SC = (x, y, r, o = {}) => circle(SX(x), SY(y), r * cs, o);
  const ST = (x, y, str, o = {}) => text(SX(x), SY(y), str, o);

  // станина
  for (const x of [-300, 270]) s += SR(x, 20, 30, 840, { fill: '#f4f4f4', stroke: INK, sw: 0.3 });
  s += SR(-300, 830, 600, 30, { fill: '#f4f4f4', stroke: INK, sw: 0.3 });
  s += SR(-300, 20, 600, 30, { fill: '#f4f4f4', stroke: INK, sw: 0.3 });
  s += SR(-300, 670, 600, 30, { fill: '#f4f4f4', stroke: INK, sw: 0.3 });
  s += SL(-270, 60, 270, 320, { sw: 0.55, stroke: '#9a9a9a' });
  s += SL(270, 60, -270, 320, { sw: 0.35, stroke: '#bdbdbd', dash: '2 1.2' });
  // панели
  s += SL(-300, 450, -300, 860, { sw: 1.4, stroke: PC });
  s += SL(-300, 50, -300, 450, { sw: 1.4, stroke: PC });
  // купол
  s += path(
    `M ${f(SX(-210))} ${f(SY(570))} L ${f(SX(-210))} ${f(SY(1000))} Q ${f(SX(0))} ${f(SY(1120))} ${f(SX(210))} ${f(SY(1000))} L ${f(SX(210))} ${f(SY(570))}`,
    { fill: PC, stroke: BLUE, sw: 0.35, fillOpacity: 0.15 }
  );
  s += SL(0, 570, 0, 1060, { sw: 0.2, stroke: BLUE, dash: '2 1' });
  // крышка
  s += SR(-300, 860, 85, 8, { fill: FILL, stroke: INK, sw: 0.25 });
  s += SR(215, 860, 85, 8, { fill: FILL, stroke: INK, sw: 0.25 });
  // стол, подстолье
  s += SR(-250, 545, 500, 15, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += SR(-250, 432, 500, 18, { fill: FILL, stroke: INK, sw: 0.3 });
  s += SC(0, 570, 16.5, { fill: FILL, stroke: INK, sw: 0.3 });
  // балки, пружины, направляющие
  s += SR(-270, 670, 540, 40, { fill: FILL2, stroke: INK, sw: 0.3 });
  for (const x of [-150, 150]) {
    const pts = [[x, 560]];
    for (let i = 0; i < 12; i++) pts.push([x + (i % 2 ? 12 : -12), 560 + (110 * (i + 0.5)) / 12]);
    pts.push([x, 670]);
    s += polyline(pts.map(([xx, yy]) => [SX(xx), SY(yy)]), { sw: 0.35 });
  }
  for (const x of [-225, 225]) s += SL(x, 535, x, 700, { sw: 0.3 });
  // дрель, патрон, кулачок, ролики
  s += SR(70, 360, 225, 70, { fill: '#f7f7f7', stroke: INK, sw: 0.35 });
  s += SR(0, 370, 70, 50, { fill: LIGHT, stroke: INK, sw: 0.3 });
  s += SR(-60, 280, 20, 230, { fill: LIGHT, stroke: INK, sw: 0.35 });
  s += SC(-50, 515, 17.5, { fill: WHITE, stroke: INK, sw: 0.35 });
  // дверцы и вырез
  s += SL(300, 260, 300, 315, { sw: 1.4, stroke: PC });
  s += SL(300, 345, 300, 450, { sw: 1.4, stroke: PC });
  // размеры
  s += SL(-330, 0, -330, 1060, { sw: 0.2 });
  s += text(295, 170, '1060', { size: 1.9, anchor: 'middle', rot: -90, bg: WHITE });
  s += SL(-300, -20, 300, -20, { sw: 0.2 });
  s += text(340, 253, '600', { size: 1.9, anchor: 'middle', bg: WHITE });
  // подписи
  const leader = (x1, y1, x2, y2, str, anchor = 'start') =>
    line(SX(x1), SY(y1), SX(x2), SY(y2), { sw: 0.18 }) + text(SX(x2), SY(y2), str, { size: 2.0, anchor, bg: WHITE });
  s += leader(120, 1010, 150, 1035, 'купол', 'start');
  s += leader(260, 395, 300, 340, 'дрель', 'start');
  s += leader(-50, 420, -90, 360, 'кулачок', 'end');
  s += text(340, 260, 'Схематично, без масштаба', { size: 1.8, anchor: 'middle', fill: MID });

  return sheetSVG('Обложка альбома expert_correct', s);
}

// ---------------------------------------------------------------------------
const files = [
  ['00_cover.svg', 'Обложка', sheetCover],
  ['01_general.svg', 'Общий вид', sheetGeneral],
  ['02_suspension.svg', 'Подвеска стола', sheetSuspension],
  ['03_cam_roller.svg', 'Контакт кулачка и роликов', sheetCamRoller],
  ['04_cam_mount.svg', 'Крепление кулачка', sheetCamMount],
  ['05_drill_mount.svg', 'Крепление дрели', sheetDrillMount],
];

let totalBad = 0;
for (const [file, name, fn] of files) {
  BOXES.length = 0;
  LEADERS.length = 0;
  GROUPS.clear();
  CUR_GROUP = null;
  const body = fn();
  const svg = file === '00_cover.svg' ? body : sheetSVG(name, body);
  totalBad += verify(name);
  totalBad += checkLeaders();
  fs.writeFileSync(nodePath.join(OUT, file), svg, 'utf8');
  console.log(`${file}: ${(svg.length / 1024).toFixed(1)} КБ`);
}
if (totalBad) console.error(`Предупреждений: ${totalBad}`);
