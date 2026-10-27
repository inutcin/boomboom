'use strict';
/*
 * Генератор листов этапа «Замечания и корректировки по модели. Часть 1».
 * Запуск: node stages/correct/1/tools/generate.js
 * Результат: stages/correct/1/figs/*.svg
 *
 * Листы A3, 200 dpi. Размеры модели — в мм.
 */
const fs = require('fs');
const nodePath = require('path');

const OUT = nodePath.join(__dirname, '..', 'figs');
fs.mkdirSync(OUT, { recursive: true });

const W = 420;
const H = 297;
const DPI = 200;
const PX = Math.round((W / 25.4) * DPI);
const PY = Math.round((H / 25.4) * DPI);

const INK = '#171717';
const MID = '#666666';
const LIGHT = '#f4f4f4';
const MIDFILL = '#d6d6d6';
const DARKFILL = '#bcbcbc';
const STEEL = '#c8c8c8';
const RUBBER = '#8a8a8a';
const RED = '#8f1d1d';

const f = (v) => (Math.abs(v) < 1e-6 ? '0' : Number(v).toFixed(2));
const esc = (s) =>
  String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

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
    sw: o.sw ?? 0.5,
    dash: o.dash,
    opacity: o.opacity,
  })}/>`;
}

function rect(x, y, w, h, o = {}) {
  return `<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.5,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
    fillRule: o.fillRule,
  })}${o.rx ? ` rx="${f(o.rx)}"` : ''}/>`;
}

function circle(x, y, r, o = {}) {
  return `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.5,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
  })}/>`;
}

function ellipse(x, y, rx, ry, o = {}) {
  return `<ellipse cx="${f(x)}" cy="${f(y)}" rx="${f(rx)}" ry="${f(ry)}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.5,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
  })}${o.rot ? ` transform="rotate(${o.rot} ${f(x)} ${f(y)})"` : ''}/>`;
}

function path(d, o = {}) {
  return `<path d="${d}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.5,
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
    sw: o.sw ?? 0.5,
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
    sw: o.sw ?? 0.5,
    dash: o.dash,
    opacity: o.opacity,
    linejoin: o.linejoin ?? 'round',
    linecap: o.linecap ?? 'round',
  })}/>`;
}

function text(x, y, s, o = {}) {
  const size = o.size ?? 3;
  const anchor = o.anchor ?? 'start';
  const weight = o.weight ?? 'normal';
  const fill = o.fill ?? INK;
  const rot = o.rot ? ` transform="rotate(${o.rot} ${f(x)} ${f(y)})"` : '';
  return `<text x="${f(x)}" y="${f(y)}" font-size="${f(size)}" text-anchor="${anchor}" font-weight="${weight}" fill="${fill}" dominant-baseline="middle"${rot}>${esc(s)}</text>`;
}

function label(x, y, s, o = {}) {
  const size = o.size ?? 3;
  const anchor = o.anchor ?? 'middle';
  const rot = o.rot ?? 0;
  const w = s.length * size * 0.58 + 1.8;
  const h = size + 1.7;
  const bx = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
  const by = y - h / 2;
  const inner =
    rect(bx, by, w, h, { fill: '#ffffff', stroke: 'none' }) +
    text(x, y, s, { size, anchor, weight: o.weight, fill: o.fill });
  if (!rot) return inner;
  return `<g transform="rotate(${rot} ${f(x)} ${f(y)})">${inner}</g>`;
}

// ---------------------------------------------------------------------------
// 2D-вид: горизонталь — x (или z), вертикаль — y
// ---------------------------------------------------------------------------
let V = { ox: 150, oy: 240, s: 0.2 };

function setView(ox, oy, s = 0.2) {
  V = { ox, oy, s };
}
function mx(h) { return V.ox + V.s * h; }
function my(y) { return V.oy - V.s * y; }

function rectM(h1, y1, h2, y2, o = {}) {
  return rect(mx(h1), my(y2), (h2 - h1) * V.s, (y2 - y1) * V.s, o);
}
function lineM(h1, y1, h2, y2, o = {}) {
  return line(mx(h1), my(y1), mx(h2), my(y2), o);
}
function circleM(h, y, r, o = {}) {
  return circle(mx(h), my(y), r * V.s, o);
}
function polyM(points, o = {}) {
  return poly(points.map(([h, y]) => [mx(h), my(y)]), o);
}
function polylineM(points, o = {}) {
  return polyline(points.map(([h, y]) => [mx(h), my(y)]), o);
}
function textM(h, y, s, o = {}) {
  return text(mx(h), my(y), s, o);
}

function arrowH(x, y, dir) {
  const L = 1.6, Wd = 0.6;
  const pts = dir < 0
    ? [[x, y], [x + L, y - Wd], [x + L, y + Wd]]
    : [[x, y], [x - L, y - Wd], [x - L, y + Wd]];
  return poly(pts, { fill: INK, stroke: INK, sw: 0.1 });
}
function arrowV(x, y, dir) {
  const L = 1.6, Wd = 0.6;
  const pts = dir < 0
    ? [[x, y], [x - Wd, y + L], [x + Wd, y + L]]
    : [[x, y], [x - Wd, y - L], [x + Wd, y - L]];
  return poly(pts, { fill: INK, stroke: INK, sw: 0.1 });
}

function dimH(h1, h2, y, s, fromY) {
  const x1 = mx(h1), x2 = mx(h2), yy = my(y);
  let out = '';
  if (fromY !== undefined) {
    out += line(x1, my(fromY), x1, yy + (yy > my(fromY) ? 1.4 : -1.4), { sw: 0.22 });
    out += line(x2, my(fromY), x2, yy + (yy > my(fromY) ? 1.4 : -1.4), { sw: 0.22 });
  }
  out += line(x1, yy, x2, yy, { sw: 0.22 });
  out += arrowH(x1, yy, -1) + arrowH(x2, yy, 1);
  out += label((x1 + x2) / 2, yy - 1.8, s, { size: 2.9 });
  return out;
}

function dimV(h, y1, y2, s, fromH) {
  const xx = mx(h), y1p = my(y1), y2p = my(y2);
  let out = '';
  if (fromH !== undefined) {
    out += line(mx(fromH), y1p, xx + (xx > mx(fromH) ? 1.4 : -1.4), y1p, { sw: 0.22 });
    out += line(mx(fromH), y2p, xx + (xx > mx(fromH) ? 1.4 : -1.4), y2p, { sw: 0.22 });
  }
  out += line(xx, y1p, xx, y2p, { sw: 0.22 });
  out += arrowV(xx, y1p, -1) + arrowV(xx, y2p, 1);
  out += label(xx - 1.8, (y1p + y2p) / 2, s, { size: 2.9, rot: -90 });
  return out;
}

function leader(h, y, lx, ly, num) {
  const x = mx(h), yy = my(y);
  return (
    line(x, yy, lx, ly, { sw: 0.22 }) +
    circle(lx, ly, 2.2, { fill: '#ffffff', stroke: INK, sw: 0.32 }) +
    text(lx, ly + 0.1, String(num), { size: 2.5, anchor: 'middle', weight: 'bold' }) +
    circle(x, yy, 0.6, { fill: INK, stroke: 'none' })
  );
}

function dimLeader(h, y, lx, ly, s) {
  const x = mx(h), yy = my(y);
  return (
    line(x, yy, lx, ly, { sw: 0.22 }) +
    text(lx, ly, s, { size: 2.8, anchor: 'start' }) +
    circle(x, yy, 0.6, { fill: INK, stroke: 'none' })
  );
}

function leaderAt(x, y, lx, ly, s) {
  return (
    line(x, y, lx, ly, { sw: 0.22 }) +
    text(lx, ly, s, { size: 2.8, anchor: 'start' }) +
    circle(x, y, 0.6, { fill: INK, stroke: 'none' })
  );
}

function cross(h, y, size = 5) {
  const x = mx(h), yy = my(y);
  return (
    line(x - size, yy, x + size, yy, { sw: 0.22, dash: '2.2 1.2' }) +
    line(x, yy - size, x, yy + size, { sw: 0.22, dash: '2.2 1.2' })
  );
}

function centerlineH(h1, h2, y) {
  return lineM(h1, y, h2, y, { sw: 0.2, dash: '3 1 0.8 1' });
}
function centerlineV(h, y1, y2) {
  return lineM(h, y1, h, y2, { sw: 0.2, dash: '3 1 0.8 1' });
}

function hexPlan(cx, cz, r) {
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 6 + (Math.PI * i) / 3;
    pts.push([mx(cx + r * Math.cos(a)), my(cz + r * Math.sin(a))]);
  }
  return poly(pts, { fill: '#d8d8d8', stroke: INK, sw: 0.4 });
}

function hexAt(h, y, r) {
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 6 + (Math.PI * i) / 3;
    pts.push([mx(h + r * Math.cos(a)), my(y + r * Math.sin(a))]);
  }
  return poly(pts, { fill: '#d8d8d8', stroke: INK, sw: 0.4 });
}

function hexSheet(cx, cy, r) {
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 6 + (Math.PI * i) / 3;
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return poly(pts, { fill: '#707070', stroke: INK, sw: 0.35 });
}

function roundedRectM(x0, z0, x1, z1, r, o = {}) {
  return rect(mx(x0), my(z1), (x1 - x0) * V.s, (z1 - z0) * V.s, {
    ...o,
    rx: r * V.s,
  });
}

function roundedRectPts(u0, u1, v0, v1, r, n = 4) {
  const pts = [];
  const arc = (cu, cv, a0, a1) => {
    for (let i = 0; i <= n; i++) {
      const a = a0 + ((a1 - a0) * i) / n;
      pts.push([cu + r * Math.cos(a), cv + r * Math.sin(a)]);
    }
  };
  arc(u1 - r, v0 + r, -Math.PI / 2, 0);
  arc(u1 - r, v1 - r, 0, Math.PI / 2);
  arc(u0 + r, v1 - r, Math.PI / 2, Math.PI);
  arc(u0 + r, v0 + r, Math.PI, 1.5 * Math.PI);
  return pts;
}

function isoRoundedPlateXZ(x0, x1, y0, y1, z0, z1, r, o = {}) {
  const pts = roundedRectPts(x0, x1, z0, z1, r);
  const near = pts.map(([x, z]) => ({ x, y: y0, z }));
  const far = pts.map(([x, z]) => ({ x, y: y1, z }));
  const band = [];
  for (const p of near) band.push(p);
  for (let i = far.length - 1; i >= 0; i--) band.push(far[i]);
  let out = '';
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35 });
  out += isoPoly(near, { fill: o.bottom ?? '#eeeeee', stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, fillOpacity: o.fillOpacity });
  out += isoPoly(far, { fill: 'none', stroke: o.stroke ?? INK, sw: 0.25, dash: '1.4 1' });
  return out;
}

function isoRoundedPlateYZ(xNear, xFar, y0, y1, z0, z1, r, o = {}) {
  const pts = roundedRectPts(y0, y1, z0, z1, r);
  const near = pts.map(([y, z]) => ({ x: xNear, y, z }));
  const far = pts.map(([y, z]) => ({ x: xFar, y, z }));
  const band = [];
  for (const p of near) band.push(p);
  for (let i = far.length - 1; i >= 0; i--) band.push(far[i]);
  let out = '';
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35 });
  out += isoPoly(near, { fill: o.face ?? '#eeeeee', stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, fillOpacity: o.fillOpacity });
  if (o.hole) {
    out += isoPoly(isoCirclePts(xNear + 0.25, o.hole.y, o.hole.z, o.hole.r), {
      fill: 'none', stroke: o.stroke ?? INK, sw: 0.35,
    });
  }
  out += isoPoly(far, { fill: 'none', stroke: o.stroke ?? INK, sw: 0.25, dash: '1.4 1' });
  return out;
}

function hexYZ(cy, cz, r) {
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 6 + (Math.PI * i) / 3;
    pts.push([cy + r * Math.cos(a), cz + r * Math.sin(a)]);
  }
  return pts;
}

function isoHexX(xNear, xFar, cy, cz, r, o = {}) {
  const h = hexYZ(cy, cz, r);
  const near = h.map(([y, z]) => ({ x: xNear, y, z }));
  const far = h.map(([y, z]) => ({ x: xFar, y, z }));
  const band = [];
  for (const p of near) band.push(p);
  for (let i = far.length - 1; i >= 0; i--) band.push(far[i]);
  let out = '';
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35 });
  out += isoPoly(near, { fill: o.face ?? '#d8d8d8', stroke: o.stroke ?? INK, sw: o.sw ?? 0.4 });
  if (o.holeR) {
    out += isoPoly(isoCirclePts(xNear + 0.15, cy, cz, o.holeR), {
      fill: '#7d7d7d', stroke: o.stroke ?? INK, sw: 0.3,
    });
  }
  out += isoPoly(far, { fill: 'none', stroke: o.stroke ?? INK, sw: 0.25, dash: '1.3 1' });
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
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35 });
  out += isoPoly(near, { fill: o.face ?? '#d8d8d8', stroke: o.stroke ?? INK, sw: o.sw ?? 0.4 });
  if (o.holeR) {
    out += isoPoly(isoCirclePts(cx, yNear + 0.15, cz, o.holeR), {
      fill: '#7d7d7d', stroke: o.stroke ?? INK, sw: 0.3,
    });
  }
  out += isoPoly(far, { fill: 'none', stroke: o.stroke ?? INK, sw: 0.25, dash: '1.3 1' });
  return out;
}

function hatchPath(points, o = {}) {
  if (!points.length) return '';
  let d = `M ${f(points[0][0])} ${f(points[0][1])}`;
  for (let i = 1; i < points.length; i++) d += ` L ${f(points[i][0])} ${f(points[i][1])}`;
  d += ' Z';
  return path(d, { fill: 'url(#hatch)', stroke: INK, sw: o.sw ?? 0.5, linejoin: 'round' });
}

// ---------------------------------------------------------------------------
// Изометрия
// ---------------------------------------------------------------------------
const ISO = {
  target: { x: 0, y: 430, z: 0 },
};

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

function isoRaw(p) {
  const q = vsub(p, ISO.target);
  return { x: vdot(q, viewR), y: -vdot(q, viewU) };
}

let ISO_FIT = { s: 0.2, tx: 135, ty: 100 };

function fitIso(points, opts = {}) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of points) {
    const q = isoRaw(p);
    minX = Math.min(minX, q.x); maxX = Math.max(maxX, q.x);
    minY = Math.min(minY, q.y); maxY = Math.max(maxY, q.y);
  }
  const availW = opts.w ?? 220;
  const availH = opts.h ?? 150;
  const cx = opts.cx ?? 135;
  const cy = opts.cy ?? 110;
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

function asPoint(p) {
  return Array.isArray(p) ? { x: p[0], y: p[1], z: p[2] } : p;
}
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
function isoClosedPath(points, o = {}) {
  const p = points.map((q) => iso(asPoint(q)));
  return path('M ' + p.map(([x, y]) => `${f(x)} ${f(y)}`).join(' L ') + ' Z', o);
}

function isoBox(x0, x1, y0, y1, z0, z1, o = {}) {
  const top = [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]];
  const sideX = [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]];
  const sideZ = [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  let out = '';
  out += isoPoly(sideX, { fill: o.side ?? MIDFILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, fillOpacity: o.fillOpacity, opacity: o.opacity });
  out += isoPoly(sideZ, { fill: o.side2 ?? DARKFILL, stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, fillOpacity: o.fillOpacity, opacity: o.opacity });
  out += isoPoly(top, { fill: o.top ?? '#ffffff', stroke: o.stroke ?? INK, sw: o.sw ?? 0.35, fillOpacity: o.fillOpacity, opacity: o.opacity });
  return out;
}

function isoGhostBox(x0, x1, y0, y1, z0, z1, o = {}) {
  const top = [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]];
  const sideX = [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]];
  const sideZ = [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  const st = o.stroke ?? '#5f7390';
  return (
    isoPoly(sideX, { fill: 'none', stroke: st, sw: o.sw ?? 0.38, dash: o.dash ?? '2 1.2' }) +
    isoPoly(sideZ, { fill: 'none', stroke: st, sw: o.sw ?? 0.38, dash: o.dash ?? '2 1.2' }) +
    isoPoly(top, { fill: 'none', stroke: st, sw: o.sw ?? 0.38, dash: o.dash ?? '2 1.2' })
  );
}

function isoCirclePts(cx, cy, cz, r, n = 72) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const a = (2 * Math.PI * i) / n;
    pts.push({ x: cx, y: cy + r * Math.cos(a), z: cz + r * Math.sin(a) });
  }
  return pts;
}

function isoCylinderX(x0, x1, cy, cz, r, o = {}) {
  const a = isoCirclePts(x0, cy, cz, r);
  const b = isoCirclePts(x1, cy, cz, r);
  let out = '';
  const band = [];
  for (let i = 0; i < a.length; i++) band.push(a[i]);
  for (let i = b.length - 1; i >= 0; i--) band.push(b[i]);
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: 'none', opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(a, { fill: o.front ?? '#fafafa', stroke: o.stroke ?? INK, sw: o.sw ?? 0.4, opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(b, { fill: o.back ?? 'none', stroke: o.stroke ?? INK, sw: 0.28, dash: '1.3 1', opacity: 0.65 });
  return out;
}

function isoCylinderY(cx, cz, y0, y1, r, o = {}) {
  const a = isoCirclePts(cx, y0, cz, r);
  const b = isoCirclePts(cx, y1, cz, r);
  let out = '';
  const band = [];
  for (let i = 0; i < a.length; i++) band.push(a[i]);
  for (let i = b.length - 1; i >= 0; i--) band.push(b[i]);
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: 'none', opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(b, { fill: o.bottom ?? '#e0e0e0', stroke: o.stroke ?? INK, sw: o.sw ?? 0.3, opacity: o.opacity });
  out += isoPoly(a, { fill: o.top ?? '#ffffff', stroke: o.stroke ?? INK, sw: o.sw ?? 0.4, opacity: o.opacity, fillOpacity: o.fillOpacity });
  return out;
}

function isoSpring(x, z, y0, y1, r, coils = 7) {
  const pts = [];
  const steps = coils * 20;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const a = t * coils * 2 * Math.PI;
    pts.push({ x: x + r * Math.cos(a), y: y0 + (y1 - y0) * t, z: z + r * Math.sin(a) });
  }
  return isoPath(pts, { sw: 0.5, stroke: INK });
}

function isoBall(cx, cy, cz, r) {
  const p = iso({ x: cx, y: cy, z: cz });
  const rr = r * ISO_FIT.s;
  return (
    circle(p[0], p[1], rr, { fill: '#c9c9c9', stroke: INK, sw: 0.35 }) +
    circle(p[0] - rr * 0.28, p[1] - rr * 0.28, rr * 0.28, { fill: '#eeeeee', stroke: 'none', opacity: 0.8 })
  );
}

// ---------------------------------------------------------------------------
// Параметры
// ---------------------------------------------------------------------------
const P = {
  table: {
    x: 250, z: 200, t: 12,
    yTop: 560, yBot: 548,
    dishR: 180, dishH: 3,
    rimW: 10, rimH: 10,
    studX: 220, studZ: 170, studD: 14,
    boltX: 32, boltZ: 50, boltD: 8.5,
    screwD: 8, screwLen: 20, screwHeadD: 16, screwHeadH: 4.4, plugD: 16,
    ballD: 20,
  },
  sub: {
    x: 250, z: 200,
    yTop: 450, yBot: 432,
    winR: 125,
    studX: 220, studZ: 170, studD: 14,
    ubX: [130, 260], ubZ: 45, ubD: 9,
  },
  roller: {
    y: 515, z: 50,
    d: 35, w: 11,
    axleD: 12, bushOD: 15,
    axleLen: 45, headD: 20, headH: 7, washerD: 24, washerT: 2.5,
    nutD: 19, nutH: 10,
    baseY0: 544, baseY1: 548,
    baseX: 42, baseZ: 25,
    earX: 7.5, earT: 4, earY0: 492.5,
    baseHoleX: 32,
  },
  drill: {
    cy: 394.5,
    bodyX0: 73, bodyX1: 303, bodyD: 70,
    chuckX0: 3, chuckX1: 73, chuckD: 50,
    ubX: [130, 260], ubZ: 45, ubR: 45,
    ubTop: 450, ubBottom: 349.5,
    padT: 2, linerT: 10,
  },
  cam: {
    cy: 394.5, R: 110, e: 3, t: 6,
    boreR: 20,
    x0: -3, x1: 3,
    shankD: 10, shankX0: 3, shankX1: 43,
    flangeD: 40, flangeX0: -3, flangeX1: 3,
    washerD: 60, washerX0: -7, washerX1: -3,
    screwD: 8, screwX0: -16, screwX1: -7,
  },
};

const camRmax = P.cam.R + P.cam.e;
const camRmin = P.cam.R - P.cam.e;

function dishY(x, z) {
  const r2 = x * x + z * z;
  const R = P.table.dishR;
  if (r2 >= R * R) return P.table.yTop;
  return P.table.yTop - P.table.dishH * (1 - r2 / (R * R));
}

function camProfilePoints(steps = 200) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const ph = (2 * Math.PI * i) / steps;
    const r = P.cam.R + P.cam.e * Math.cos(2 * ph);
    pts.push([r * Math.sin(ph), P.cam.cy + r * Math.cos(ph)]);
  }
  return pts;
}

// ---------------------------------------------------------------------------
// Рамка, спецификация, титульный блок
// ---------------------------------------------------------------------------
function partsPanel(parts) {
  const x = 270, y = 12, w = 140, h = 188;
  let s =
    rect(x, y, w, h, { fill: '#ffffff', stroke: INK, sw: 0.6 }) +
    text(x + 5, y + 8, 'СПЕЦИФИКАЦИЯ', { size: 3.7, weight: 'bold' }) +
    line(x, y + 13, x + w, y + 13, { sw: 0.4 });
  s += text(x + 3, y + 17.5, 'Поз.', { size: 2.5, fill: MID });
  s += text(x + 13, y + 17.5, 'Наименование', { size: 2.5, fill: MID });
  s += text(x + 101, y + 17.5, 'Кол.', { size: 2.5, fill: MID });
  s += text(x + 113, y + 17.5, 'Примечание', { size: 2.5, fill: MID });
  s += line(x, y + 21, x + w, y + 21, { sw: 0.35 });
  parts.forEach((p, i) => {
    const yy = y + 27 + i * 10.8;
    s += text(x + 5, yy, String(i + 1), { size: 2.6, anchor: 'middle', weight: 'bold' });
    s += text(x + 13, yy, p[0], { size: 2.55 });
    s += text(x + 105, yy, String(p[1]), { size: 2.55, anchor: 'middle' });
    s += text(x + 113, yy, p[2] || '', { size: 2.4 });
  });
  return s;
}

function titleBlock(sheetNo, sheetName, scale, source) {
  const tb = { x: 270, y: 205, w: 140, h: 82 };
  const tx = tb.x, ty = tb.y;
  let s =
    rect(tx, ty, tb.w, tb.h, { fill: '#ffffff', stroke: INK, sw: 0.7 }) +
    line(tx, ty + 18, tx + tb.w, ty + 18, { sw: 0.4 }) +
    line(tx, ty + 33, tx + tb.w, ty + 33, { sw: 0.4 }) +
    line(tx, ty + 50, tx + tb.w, ty + 50, { sw: 0.4 }) +
    line(tx, ty + 65, tx + tb.w, ty + 65, { sw: 0.4 }) +
    line(tx + 88, ty + 33, tx + 88, ty + tb.h, { sw: 0.4 }) +
    text(tx + 6, ty + 10, 'ВИБРОСТОЛ', { size: 6.0, weight: 'bold' }) +
    text(tx + 6, ty + 26, 'Модель устройства', { size: 3.2 }) +
    text(tx + 6, ty + 41, 'Этап: замечания и корректировки, часть 1', { size: 2.25 }) +
    text(tx + 6, ty + 57, sheetName, { size: 2.8, weight: 'bold' }) +
    text(tx + 6, ty + 72, source || 'Источник: stages/model/figs/', { size: 2.2 }) +
    text(tx + 92, ty + 39, 'Масштаб', { size: 2.4, fill: MID }) +
    text(tx + 92, ty + 46, scale, { size: 3.4, weight: 'bold' }) +
    text(tx + 92, ty + 57, 'Размеры, мм', { size: 2.2, fill: MID }) +
    text(tx + 92, ty + 73, `Лист ${sheetNo}`, { size: 3.0, weight: 'bold' }) +
    text(tx + 6, ty + 79, '27.10.2026   DeepSeek / OpenCode', { size: 2.2, fill: MID });
  return s;
}

function frame(title, subtitle, sheetNo, sheetName, scale, parts, body, opts = {}) {
  let out = '';
  out += rect(5, 5, 410, 287, { fill: '#ffffff', stroke: INK, sw: 0.8 });
  out += rect(10, 10, 400, 277, { fill: 'none', stroke: INK, sw: 0.4 });
  out += text(135, opts.titleY ?? 21, title, { size: 4.3, anchor: 'middle', weight: 'bold' });
  if (subtitle) out += text(135, 28, subtitle, { size: 2.8, anchor: 'middle', fill: MID });
  out += body;
  out += partsPanel(parts);
  out += titleBlock(sheetNo, sheetName, scale, opts.source);
  if (opts.note) out += opts.note;
  return out;
}

function sheetSVG(title, body) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${PX}" height="${PY}" viewBox="0 0 ${W} ${H}">
<title>${esc(title)}</title>
<defs>
  <pattern id="hatch" patternUnits="userSpaceOnUse" width="2.2" height="2.2" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="2.2" stroke="#555555" stroke-width="0.28"/>
  </pattern>
  <pattern id="hatchLight" patternUnits="userSpaceOnUse" width="3.2" height="3.2" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="3.2" stroke="#888888" stroke-width="0.22"/>
  </pattern>
</defs>
<style>
  text { font-family: 'DejaVu Sans', Arial, sans-serif; fill: ${INK}; }
</style>
<rect x="0" y="0" width="${W}" height="${H}" fill="#ffffff"/>
${body}
</svg>`;
}

function isoCallout(x, y, z, lx, ly, num) {
  const p = iso({ x, y, z });
  return (
    line(p[0], p[1], lx, ly, { sw: 0.22 }) +
    circle(lx, ly, 2.2, { fill: '#ffffff', stroke: INK, sw: 0.32 }) +
    text(lx, ly + 0.1, String(num), { size: 2.5, anchor: 'middle', weight: 'bold' }) +
    circle(p[0], p[1], 0.6, { fill: INK, stroke: 'none' })
  );
}

// ---------------------------------------------------------------------------
// Лист 1. Столешница
// ---------------------------------------------------------------------------
function drawTable() {
  const T = P.table;
  const g = [];

  // --- изометрия ---
  setIsoCamera(0.68, -0.45);
  const fitPts = [];
  for (const x of [-250, 250]) for (const z of [-200, 200]) for (const y of [T.yBot, T.yTop, T.yTop + T.rimH]) fitPts.push({ x, y, z });
  fitPts.push({ x: 0, y: T.yTop + T.ballD / 2, z: 0 });
  fitIso(fitPts, { w: 135, h: 95, cx: 78, cy: 86 });

  g.push(isoBox(-250, 250, T.yBot, T.yTop, -200, 200, {
    top: '#ededed', side: '#dedede', side2: '#c9c9c9', sw: 0.5,
  }));

  // сферическая лунка: концентрические кольца
  for (let i = 0; i <= 10; i++) {
    const r = T.dishR * (1 - i / 10);
    const y = dishY(r, 0);
    const shade = 246 - i * 4;
    g.push(isoPoly(isoCirclePts(0, y, 0, r, 72), {
      fill: `rgb(${shade},${shade},${shade})`, stroke: 'none',
    }));
  }
  g.push(isoPath(isoCirclePts(0, T.yTop, 0, T.dishR, 72), { stroke: INK, sw: 0.42, dash: '2.4 1.2' }));

  // бортик 10 x 10
  const rim = { top: '#f3f3f3', side: '#e2e2e2', side2: '#d0d0d0', sw: 0.38 };
  g.push(isoBox(-250, 250, T.yTop, T.yTop + T.rimH, -200, -190, rim));
  g.push(isoBox(-250, 250, T.yTop, T.yTop + T.rimH, 190, 200, rim));
  g.push(isoBox(-250, -240, T.yTop, T.yTop + T.rimH, -190, 190, rim));
  g.push(isoBox(240, 250, T.yTop, T.yTop + T.rimH, -190, 190, rim));

  // отверстия шпилек
  for (const x of [-T.studX, T.studX]) {
    for (const z of [-T.studZ, T.studZ]) {
      g.push(isoCylinderY(x, z, T.yBot, T.yTop, T.studD / 2, {
        side: '#bdbdbd', bottom: '#e6e6e6', top: 'none', stroke: INK, sw: 0.3,
      }));
    }
  }
  // пробки над крепежом роликов
  for (const x of [-T.boltX, T.boltX]) {
    for (const z of [-T.boltZ, T.boltZ]) {
      const yy = dishY(x, z);
      g.push(isoPoly(isoCirclePts(x, yy, z, 8, 28), { fill: '#e9e9e9', stroke: INK, sw: 0.3 }));
      g.push(isoLine([x - 3, yy, z], [x + 3, yy, z], { sw: 0.25 }));
      g.push(isoLine([x, yy, z - 3], [x, yy, z + 3], { sw: 0.25 }));
    }
  }

  // шарик
  g.push(isoBall(0, T.yTop - T.dishH + T.ballD / 2, 0, T.ballD / 2));

  // след секущей плоскости А–А
  g.push(isoLine([-250, T.yTop + 1, 0], [250, T.yTop + 1, 0], { sw: 0.35, dash: '4 1.4' }));
  g.push(text(iso({ x: -250, y: T.yTop + 6, z: 0 })[0] - 2, iso({ x: -250, y: T.yTop + 6, z: 0 })[1], 'А', { size: 3.0, anchor: 'middle', weight: 'bold' }));
  g.push(text(iso({ x: 250, y: T.yTop + 6, z: 0 })[0] + 2, iso({ x: 250, y: T.yTop + 6, z: 0 })[1], 'А', { size: 3.0, anchor: 'middle', weight: 'bold' }));

  // выноски
  const call = [
    [1, 250, T.yTop - 2, -200, 200, 48],
    [2, 0, T.yTop - T.dishH, 0, 18, 68],
    [3, 240, T.yTop + T.rimH, 190, 200, 88],
    [4, 0, T.yTop - T.dishH + T.ballD / 2, 0, 18, 108],
    [5, T.studX, T.yTop, T.studZ, 200, 128],
    [6, T.boltX, dishY(T.boltX, T.boltZ), T.boltZ, 18, 148],
  ];
  for (const [n, x, y, z, lx, ly] of call) g.push(isoCallout(x, y, z, lx, ly, n));

  g.push(text(16, 36, 'Столешница: фанера 12 мм; лунка Ø360 × 3, R ≈ 5400; бортик 10 × 10', { size: 2.5, fill: MID }));
  g.push(text(16, 41, 'Шарик Ø20 — сталь. Масса стола ≈ 1,9 кг; подвижной сборки ≈ 2,6 кг', { size: 2.4, fill: MID }));

  // --- разрез А–А (1:2,5) ---
  setView(135, 469, 0.4);
  const top = [];
  for (let i = 0; i <= 48; i++) {
    const x = -T.dishR + (2 * T.dishR * i) / 48;
    top.push([mx(x), my(dishY(x, 0))]);
  }
  const pts = [];
  pts.push([mx(-250), my(T.yBot)]);
  pts.push([mx(250), my(T.yBot)]);
  pts.push([mx(250), my(T.yTop + T.rimH)]);
  pts.push([mx(240), my(T.yTop + T.rimH)]);
  pts.push([mx(240), my(T.yTop)]);
  pts.push([mx(T.dishR), my(T.yTop)]);
  for (const p of top) pts.push(p);
  pts.push([mx(-T.dishR), my(T.yTop)]);
  pts.push([mx(-240), my(T.yTop)]);
  pts.push([mx(-240), my(T.yTop + T.rimH)]);
  pts.push([mx(-250), my(T.yTop + T.rimH)]);
  g.push(hatchPath(pts, { sw: 0.6 }));
  g.push(lineM(-250, T.yBot, 250, T.yBot, { sw: 0.6 }));
  g.push(lineM(-240, T.yTop, -T.dishR, T.yTop, { sw: 0.55 }));
  g.push(lineM(T.dishR, T.yTop, 240, T.yTop, { sw: 0.55 }));
  g.push(polylineM([[-T.dishR, T.yTop], ...Array.from({ length: 49 }, (_, i) => {
    const x = -T.dishR + (2 * T.dishR * i) / 48;
    return [x, dishY(x, 0)];
  }), [T.dishR, T.yTop]], { sw: 0.6 }));
  g.push(lineM(-250, T.yTop + T.rimH, -240, T.yTop + T.rimH, { sw: 0.5 }));
  g.push(lineM(240, T.yTop + T.rimH, 250, T.yTop + T.rimH, { sw: 0.5 }));

  // шарик в разрезе
  g.push(circleM(0, T.yTop - T.dishH + T.ballD / 2, T.ballD / 2, { fill: '#dcdcdc', stroke: INK, sw: 0.4 }));
  g.push(circleM(-1.7, T.yTop - T.dishH + T.ballD / 2 + 1.7, 2.0, { fill: '#f4f4f4', stroke: 'none' }));
  g.push(centerlineV(0, T.yBot - 8, T.yTop + T.ballD + 8));

  g.push(dimH(-250, 250, T.yBot - 12, '500', T.yBot));
  g.push(dimV(-265, T.yBot, T.yTop, '12', -250));
  g.push(dimV(-287, T.yTop, T.yTop + T.rimH, '10', -250));
  g.push(dimH(-T.dishR, T.dishR, T.yTop + T.rimH + 8, '360', T.yTop));
  g.push(dimLeader(0, dishY(0, 0), 52, 262, 'лунка: Ø360; h=3; R≈5400'));
  g.push(dimLeader(-250, T.yTop + 5, 16, 268, 'бортик 10×10'));
  g.push(leader(0, T.yTop - T.dishH + T.ballD / 2, 214, 252, 4));
  g.push(text(135, 275, 'А–А  (1:2,5)', { size: 3.0, anchor: 'middle', weight: 'bold' }));

  // --- деталь А: центр лунки (1:1) ---
  setView(200, 768, 1.0);
  const dPts = [];
  for (let i = 0; i <= 24; i++) {
    const x = -60 + (120 * i) / 24;
    dPts.push([mx(x), my(dishY(x, 0))]);
  }
  const dSection = [
    [mx(-60), my(T.yBot)],
    [mx(60), my(T.yBot)],
    [mx(60), my(dishY(60, 0))],
    ...dPts.slice().reverse(),
  ];
  g.push(hatchPath(dSection, { sw: 0.55 }));
  g.push(polylineM(Array.from({ length: 25 }, (_, i) => {
    const x = -60 + (120 * i) / 24;
    return [x, dishY(x, 0)];
  }), { sw: 0.6 }));
  g.push(circleM(0, T.yTop - T.dishH + T.ballD / 2, T.ballD / 2, { fill: '#dcdcdc', stroke: INK, sw: 0.45 }));
  g.push(circleM(-2.8, T.yTop - T.dishH + T.ballD / 2 + 2.8, 3.2, { fill: '#f0f0f0', stroke: 'none' }));
  g.push(centerlineV(0, T.yBot - 6, T.yTop + T.ballD + 6));
  g.push(dimV(-70, T.yTop - T.dishH, T.yTop, '3', -60));
  g.push(dimV(-90, T.yBot, T.yTop, '12', -60));
  g.push(dimH(-T.ballD / 2, T.ballD / 2, T.yTop + T.ballD + 8, 'Ø20', T.yTop - T.dishH + T.ballD / 2));
  g.push(text(200, 226, 'Деталь А (1:1)', { size: 2.8, anchor: 'middle', weight: 'bold' }));

  const parts = [
    ['Столешница 500×400×12', 1, 'фанера 12 мм'],
    ['Бортик 10×10', 4, 'рейка, клей'],
    ['Шарик Ø20', 1, 'сталь'],
    ['Винт M8×20 (вн. шестигр.)', 4, 'сталь'],
    ['Пробка Ø16', 4, 'заподлицо'],
    ['Шайба Ø30 / гайка M12', 4, 'сталь'],
  ];

  return frame(
    'Столешница. Облегчение и вогнутость',
    'Изометрия, разрез А–А и деталь А; шарик Ø20 удерживается лункой и бортиком',
    1,
    'Столешница',
    '1:5 / 1:2,5 / 1:1',
    parts,
    g.join(''),
    { source: 'Источник: stages/model/figs/isometric.svg', note: '' }
  );
}

// ---------------------------------------------------------------------------
// Лист 2. Подстолье
// ---------------------------------------------------------------------------
function drawSubtable() {
  const S = P.sub;
  const g = [];

  setIsoCamera(0.62, -0.5);
  const fitPts = [];
  for (const x of [-S.x, S.x]) for (const z of [-S.z, S.z]) for (const y of [S.yBot, S.yTop]) fitPts.push({ x, y, z });
  fitIso(fitPts, { w: 185, h: 95, cx: 135, cy: 95 });

  g.push(isoBox(-S.x, S.x, S.yBot, S.yTop, -S.z, S.z, {
    top: '#ececec', side: '#dedede', side2: '#c8c8c8', sw: 0.5,
  }));
  g.push(isoCylinderY(0, 0, S.yBot, S.yTop, S.winR, {
    side: '#9a9a9a', bottom: '#f2f2f2', top: 'none', stroke: INK, sw: 0.45,
  }));
  for (const x of [-S.studX, S.studX]) {
    for (const z of [-S.studZ, S.studZ]) {
      g.push(isoCylinderY(x, z, S.yBot, S.yTop, S.studD / 2, {
        side: '#9a9a9a', bottom: '#ffffff', top: 'none', stroke: INK, sw: 0.3,
      }));
    }
  }
  for (const x of S.ubX) {
    for (const z of [-S.ubZ, S.ubZ]) {
      g.push(isoCylinderY(x, z, S.yBot, S.yTop, S.ubD / 2, {
        side: '#8f8f8f', bottom: '#ffffff', top: 'none', stroke: INK, sw: 0.3,
      }));
    }
  }

  const call = [
    [1, 250, S.yTop, -200, 22, 55],
    [2, 0, S.yTop, S.winR, 220, 68],
    [3, S.studX, S.yTop, S.studZ, 220, 88],
    [4, S.ubX[0], S.yTop, S.ubZ, 22, 108],
  ];
  for (const [n, x, y, z, lx, ly] of call) g.push(isoCallout(x, y, z, lx, ly, n));
  g.push(text(16, 36, 'Подстолье: фанера 18 мм; окно Ø250; отверстия шпилек Ø14 и U-болтов Ø9', { size: 2.5, fill: MID }));

  // --- план (1:8) ---
  setView(135, 215, 0.125);
  g.push(rectM(-250, -200, 250, 200, { fill: '#f7f7f7', stroke: INK, sw: 0.65 }));
  g.push(circleM(0, 0, S.winR, { fill: '#ffffff', stroke: INK, sw: 0.55 }));
  g.push(centerlineH(-270, 270, 0));
  g.push(centerlineV(0, -220, 220));
  for (const x of [-S.studX, S.studX]) {
    for (const z of [-S.studZ, S.studZ]) {
      g.push(circleM(x, z, S.studD / 2, { fill: '#ffffff', stroke: INK, sw: 0.4 }));
      g.push(cross(x, z, 4));
    }
  }
  for (const x of S.ubX) {
    for (const z of [-S.ubZ, S.ubZ]) {
      g.push(circleM(x, z, S.ubD / 2, { fill: '#ffffff', stroke: INK, sw: 0.4 }));
    }
  }
  g.push(dimH(-250, 250, -230, '500', -200));
  g.push(dimV(-280, -200, 200, '400', -250));
  g.push(dimH(-S.studX, S.studX, 220, '440', 200));
  g.push(dimV(280, -S.studZ, S.studZ, '340', 250));
  g.push(dimLeader(0, S.winR, 24, 182, 'Ø250'));
  g.push(dimLeader(-S.studX, S.studZ, 24, 204, 'Ø14 (4)'));
  g.push(dimLeader(S.ubX[0], -S.ubZ, 24, 228, 'Ø9 (4)'));
  g.push(text(135, 258, 'U-болты M8: (130; ±45), (260; ±45)', { size: 2.5, anchor: 'middle', fill: MID }));
  g.push(text(135, 268, 'План (вид сверху)', { size: 3.0, anchor: 'middle', weight: 'bold' }));

  const parts = [
    ['Подстолье 500×400×18', 1, 'фанера 18 мм'],
    ['Окно Ø250', 1, 'вырез'],
    ['Отверстие Ø14', 4, 'шпильки M12'],
    ['Отверстие Ø9', 4, 'U-болты M8'],
  ];

  return frame(
    'Подстолье. Окно и посадочные отверстия',
    'Изометрия и план; окно Ø250, шпильки M12, U-болты M8',
    2,
    'Подстолье',
    '1:5 / 1:8',
    parts,
    g.join(''),
    { source: 'Источник: stages/model/figs/left_view.svg' }
  );
}

// ---------------------------------------------------------------------------
// Лист 3. Крепление ролика к столешнице
// ---------------------------------------------------------------------------
function drawRollerAssembly() {
  const R = P.roller;
  const T = P.table;
  const g = [];

  // --- изометрия снизу: что и как прижато к столу ---
  setIsoCamera(-0.55, -0.5);
  const fitPts = [];
  for (const x of [-60, 60]) for (const z of [20, 80]) for (const y of [T.yBot, T.yTop]) fitPts.push({ x, y, z });
  for (const x of [-R.baseX, R.baseX]) for (const z of [R.z - R.baseZ, R.z + R.baseZ]) for (const y of [544, 548]) fitPts.push({ x, y, z });
  for (const x of [-9.5, 9.5]) for (const z of [R.z - R.baseZ, R.z + R.baseZ]) for (const y of [R.earY0, 544]) fitPts.push({ x, y, z });
  for (const x of [-22, 19]) for (const y of [R.y - 17.5, R.y + 17.5]) fitPts.push({ x, y, z: R.z });
  for (const x of [-T.boltX, T.boltX]) for (const y of [535.9, 544]) fitPts.push({ x, y, z: R.z });
  fitIso(fitPts, { w: 180, h: 95, cx: 125, cy: 92 });

  g.push(isoGhostBox(-60, 60, T.yBot, T.yTop, 20, 80, { sw: 0.4 }));
  // основание кронштейна — скруглённая пластина, видна снизу
  g.push(isoRoundedPlateXZ(-R.baseX, R.baseX, R.baseY0, 548, R.z - R.baseZ, R.z + R.baseZ, 5, {
    side: '#d6d6d6', bottom: '#eeeeee', sw: 0.5,
  }));
  // дальняя щека (скруглённая), ось/гайка с дальней стороны
  g.push(isoCylinderX(-9.5, -22, R.y, R.z, R.axleD / 2, { front: '#e8e8e8', side: '#cfcfcf', sw: 0.3 }));
  g.push(isoCylinderX(-9.5, -12, R.y, R.z, R.washerD / 2, { front: '#eeeeee', side: '#d0d0d0', sw: 0.3 }));
  g.push(isoHexX(-12, -22, R.y, R.z, R.nutD / 2 + 1.0, { face: '#d4d4d4', side: '#bdbdbd', holeR: 6 }));
  g.push(isoRoundedPlateYZ(-5.5, -9.5, R.earY0, 544, R.z - R.baseZ, R.z + R.baseZ, 5, {
    face: '#eeeeee', side: '#d0d0d0', sw: 0.45, hole: { y: R.y, z: R.z, r: 6.5 },
  }));
  // подшипник
  g.push(isoCylinderX(R.w / 2, -R.w / 2, R.y, R.z, R.d / 2, {
    front: '#ececec', side: '#c9c9c9', sw: 0.45,
  }));
  g.push(isoCylinderX(R.w / 2, -R.w / 2, R.y, R.z, R.bushOD / 2, {
    front: '#ffffff', side: '#dddddd', sw: 0.35,
  }));
  g.push(isoCylinderX(R.w / 2, -R.w / 2, R.y, R.z, R.axleD / 2, {
    front: '#e8e8e8', side: '#cfcfcf', sw: 0.25,
  }));
  // ближняя щека — полупрозрачная, чтобы видеть подшипник
  g.push(isoRoundedPlateYZ(9.5, 5.5, R.earY0, 544, R.z - R.baseZ, R.z + R.baseZ, 5, {
    face: '#eeeeee', side: '#d0d0d0', sw: 0.45, fillOpacity: 0.55, hole: { y: R.y, z: R.z, r: 6.5 },
  }));
  // ближняя сторона оси: шайба, шестигранная головка болта
  g.push(isoCylinderX(9.5, 12, R.y, R.z, R.washerD / 2, { front: '#eeeeee', side: '#d0d0d0', sw: 0.3 }));
  g.push(isoHexX(19, 12, R.y, R.z, R.headD / 2 + 0.4, { face: '#d8d8d8', side: '#bdbdbd' }));
  // гайки M8 снизу основания — шестигранные
  for (const x of [-T.boltX, T.boltX]) {
    g.push(isoCylinderY(x, R.z, 542.4, 544, 8.1, { side: '#cfcfcf', bottom: '#eeeeee', top: '#e0e0e0', stroke: INK, sw: 0.3 }));
    g.push(isoHexY(x, R.z, 535.9, 542.4, 7.5, { face: '#d8d8d8', side: '#bdbdbd', holeR: 4 }));
  }

  g.push(text(16, 33, 'Вид снизу: кронштейн прижат к столешнице двумя винтами M8; гайки M8 — снизу', { size: 2.4, fill: MID }));
  g.push(text(16, 38, 'Ближняя щека показана полупрозрачной; подшипник — между щеками', { size: 2.4, fill: MID }));
  g.push(text(16, 43, 'Позиции: 1 — кронштейн; 2 — подшипник; 3 — втулка; 4 — болт; 7 — винт M8', { size: 2.35, fill: MID }));

  // --- вид снизу (1:1) ---
  setView(78, 232, 1.0);
  g.push(rectM(-60, 10, 60, 90, { fill: 'none', stroke: '#5f7390', sw: 0.4, dash: '2 1.2' }));
  g.push(roundedRectM(-R.baseX, R.z - R.baseZ, R.baseX, R.z + R.baseZ, 5, { fill: '#f2f2f2', stroke: INK, sw: 0.6 }));
  g.push(roundedRectM(-9.5, R.z - R.baseZ, -5.5, R.z + R.baseZ, 1.5, { fill: '#e4e4e4', stroke: INK, sw: 0.45 }));
  g.push(roundedRectM(5.5, R.z - R.baseZ, 9.5, R.z + R.baseZ, 1.5, { fill: '#e4e4e4', stroke: INK, sw: 0.45 }));
  // ролик/подшипник в проекции снизу: прямоугольник 11 x 35
  g.push(rectM(-R.w / 2, R.y - R.d / 2, R.w / 2, R.y + R.d / 2, { fill: '#ededed', stroke: INK, sw: 0.55 }));
  g.push(rectM(-R.w / 2, R.y - R.bushOD / 2, R.w / 2, R.y + R.bushOD / 2, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
  // шайбы, головка болта, гайка
  g.push(rectM(9.5, R.y - R.washerD / 2, 12, R.y + R.washerD / 2, { fill: '#eeeeee', stroke: INK, sw: 0.3 }));
  g.push(rectM(12, R.y - R.headD / 2, 19, R.y + R.headD / 2, { fill: '#d8d8d8', stroke: INK, sw: 0.4 }));
  g.push(rectM(-12, R.y - R.washerD / 2, -9.5, R.y + R.washerD / 2, { fill: '#eeeeee', stroke: INK, sw: 0.3 }));
  g.push(rectM(-22, R.y - R.nutD / 2, -12, R.y + R.nutD / 2, { fill: '#d4d4d4', stroke: INK, sw: 0.4 }));
  // гайки M8 с шайбами
  for (const x of [-T.boltX, T.boltX]) {
    g.push(circleM(x, R.z, 8.1, { fill: '#eeeeee', stroke: INK, sw: 0.35 }));
    g.push(hexPlan(x, R.z, 7.2));
  }
  g.push(centerlineH(-52, 52, R.z));
  g.push(centerlineV(0, 15, 85));
  g.push(dimH(-R.baseX, R.baseX, 22, '84', R.z - R.baseZ));
  g.push(dimV(-55, R.z - R.baseZ, R.z + R.baseZ, '50', -R.baseX));
  g.push(dimH(-T.boltX, T.boltX, 82, '64', R.z + R.baseZ));
  g.push(dimLeader(-R.w / 2, R.z, 145, 150, 'ролик Ø35'));
  g.push(dimLeader(19, R.z, 145, 165, 'болт M12×45'));
  g.push(dimLeader(T.boltX, R.z, 145, 180, 'M8'));
  g.push(text(78, 240, 'Вид снизу (1:1)', { size: 3.0, anchor: 'middle', weight: 'bold' }));
  g.push(text(78, 246, 'Основание 84×50, R5; щеки 19 наруж., 11 внутр.', { size: 2.3, anchor: 'middle', fill: MID }));

  // --- местный разрез Д–Д через винт M8 (2:1) ---
  setView(105, 1304, 2.0);
  // стол в зоне лунки
  const topPts = [];
  for (let i = 0; i <= 20; i++) {
    const x = 24 + (20 * i) / 20;
    topPts.push([mx(x), my(dishY(x, R.z))]);
  }
  const tableSection = [
    [mx(24), my(548)],
    [mx(44), my(548)],
    ...topPts.slice().reverse(),
  ];
  g.push(hatchPath(tableSection, { sw: 0.55 }));
  g.push(polylineM(Array.from({ length: 21 }, (_, i) => {
    const x = 24 + (20 * i) / 20;
    return [x, dishY(x, R.z)];
  }), { sw: 0.55 }));
  // кронштейн
  g.push(rectM(24, R.baseY0, 44, R.baseY1, { fill: 'url(#hatch)', sw: 0.5 }));
  // пробка и потайной винт с внутренним шестигранником
  g.push(rectM(24, 552.9, 40, 557.3, { fill: '#e4d8bc', stroke: INK, sw: 0.45 }));
  g.push(poly([[mx(24), my(552.9)], [mx(40), my(552.9)], [mx(34), my(548.3)], [mx(30), my(548.3)]], {
    fill: '#bdbdbd', stroke: INK, sw: 0.4,
  }));
  g.push(rectM(29, 550.5, 35, 552.9, { fill: '#707070', stroke: INK, sw: 0.3 }));
  g.push(rectM(30, 532.9, 34, 548.3, { fill: '#d8d8d8', stroke: INK, sw: 0.4 }));
  g.push(rectM(24, 542.4, 40, 544, { fill: '#eeeeee', stroke: INK, sw: 0.35 }));
  g.push(rectM(28, 535.9, 36, 542.4, { fill: '#c8c8c8', stroke: INK, sw: 0.4 }));
  g.push(centerlineV(32, 530, 560));
  g.push(lineM(24, 534, 24, 558, { sw: 0.35, dash: '2 1' }));
  g.push(lineM(44, 534, 44, 558, { sw: 0.35, dash: '2 1' }));
  g.push(dimLeader(32, 557.3, 208, 185, 'пробка Ø16, заподлицо'));
  g.push(dimLeader(32, 548.3, 208, 220, 'винт M8×20, потайной, 90°'));
  g.push(dimLeader(44, 552, 208, 205, 'фанера 12 (местная 9,3)'));
  g.push(dimLeader(44, 546, 208, 232, 'кронштейн 4, R5'));
  g.push(dimLeader(32, 540, 208, 245, 'шайба Ø16 + гайка M8'));
  g.push(text(170, 252, 'Д–Д  (2:1)', { size: 3.0, anchor: 'middle', weight: 'bold' }));

  // вид на головку винта M8 (пробка снята): внутренний шестигранник
  setView(168, 355, 2.0);
  g.push(circleM(32, R.z, 8, { fill: '#d8d8d8', stroke: INK, sw: 0.5 }));
  g.push(hexPlan(32, R.z, 3));
  g.push(centerlineH(20, 44, R.z));
  g.push(centerlineV(32, 38, 62));
  g.push(text(232, 236, 'пробка снята', { size: 2.3, anchor: 'middle', fill: MID }));
  g.push(text(232, 278, 'внутр. шестигранник 6', { size: 2.3, anchor: 'middle', fill: MID }));

  const parts = [
    ['Кронштейн 84×50, R5', 1, 'сварной, 4 мм'],
    ['Подшипник 6202-2RS', 1, '35×15×11'],
    ['Втулка 15/12×11', 1, 'сталь'],
    ['Болт M12×45 (шестигр.)', 1, '8.8'],
    ['Шайба M12', 2, 'сталь'],
    ['Гайка M12 (шестигр.)', 1, 'самоконтрящаяся'],
    ['Винт M8×20 (вн. шестигр.)', 2, 'потайной'],
    ['Пробка Ø16', 2, 'заподлицо'],
    ['Шайба Ø16 / гайка M8', '2+2', 'гайка шестигр.'],
    ['Столешница (фрагмент)', 1, 'фанера 12'],
  ];

  return frame(
    'Крепление ролика к столешнице',
    'Вид снизу, изометрия снизу и местный разрез Д–Д; основание 84×50, R5; M8×20',
    3,
    'Крепление ролика',
    '1:1 / 2:1',
    parts,
    g.join(''),
    { source: 'Источник: stages/model/figs/left_view.svg' }
  );
}

// ---------------------------------------------------------------------------
// Лист 4. Ось ролика и подшипник
// ---------------------------------------------------------------------------
function drawRollerAxle() {
  const R = P.roller;
  const T = P.table;
  const g = [];

  // --- разрез А–А по оси ролика и винтам M8 (1:1) ---
  setView(80, 610, 1.0);
  // стол (фрагмент) с лункой
  const top = [];
  for (let i = 0; i <= 40; i++) {
    const x = -50 + (100 * i) / 40;
    top.push([mx(x), my(dishY(x, R.z))]);
  }
  const tablePts = [
    [mx(-50), my(T.yBot)],
    [mx(50), my(T.yBot)],
    ...top.slice().reverse(),
  ];
  g.push(hatchPath(tablePts, { sw: 0.55 }));
  g.push(polylineM(Array.from({ length: 41 }, (_, i) => {
    const x = -50 + (100 * i) / 40;
    return [x, dishY(x, R.z)];
  }), { sw: 0.55 }));
  // кронштейн: основание и щеки
  g.push(rectM(-R.baseX, R.baseY0, R.baseX, R.baseY1, { fill: 'url(#hatch)', sw: 0.5 }));
  g.push(rectM(-9.5, R.earY0, -5.5, 508.5, { fill: 'url(#hatch)', sw: 0.5 }));
  g.push(rectM(-9.5, 521.5, -5.5, R.baseY0, { fill: 'url(#hatch)', sw: 0.5 }));
  g.push(rectM(5.5, R.earY0, 9.5, 508.5, { fill: 'url(#hatch)', sw: 0.5 }));
  g.push(rectM(5.5, 521.5, 9.5, R.baseY0, { fill: 'url(#hatch)', sw: 0.5 }));
  // подшипник: наружное и внутреннее кольца, шарики, уплотнения
  g.push(rectM(-R.w / 2, R.y - R.d / 2, R.w / 2, R.y - 15, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(-R.w / 2, R.y + 15, R.w / 2, R.y + R.d / 2, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(-R.w / 2, R.y - R.bushOD / 2, R.w / 2, R.y - 5, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(-R.w / 2, R.y + 5, R.w / 2, R.y + R.bushOD / 2, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(circleM(0, R.y - 12.5, 2.75, { fill: '#f4f4f4', stroke: INK, sw: 0.35 }));
  g.push(circleM(0, R.y + 12.5, 2.75, { fill: '#f4f4f4', stroke: INK, sw: 0.35 }));
  g.push(rectM(-R.w / 2, R.y - 15, -R.w / 2 + 0.5, R.y + 15, { fill: '#777777', stroke: 'none' }));
  g.push(rectM(R.w / 2 - 0.5, R.y - 15, R.w / 2, R.y + 15, { fill: '#777777', stroke: 'none' }));
  // втулка и ось
  g.push(rectM(-R.w / 2, R.y - R.bushOD / 2, R.w / 2, R.y - R.axleD / 2, { fill: '#d0d0d0', stroke: INK, sw: 0.3 }));
  g.push(rectM(-R.w / 2, R.y + R.axleD / 2, R.w / 2, R.y + R.bushOD / 2, { fill: '#d0d0d0', stroke: INK, sw: 0.3 }));
  g.push(rectM(-22, R.y - R.axleD / 2, 19, R.y + R.axleD / 2, { fill: '#e8e8e8', stroke: INK, sw: 0.35 }));
  g.push(rectM(12, R.y - R.headD / 2, 19, R.y + R.headD / 2, { fill: '#cfcfcf', stroke: INK, sw: 0.4 }));
  g.push(rectM(-22, R.y - R.nutD / 2, -12, R.y + R.nutD / 2, { fill: '#cfcfcf', stroke: INK, sw: 0.4 }));
  g.push(rectM(9.5, R.y - R.washerD / 2, 12, R.y + R.washerD / 2, { fill: '#eeeeee', stroke: INK, sw: 0.3 }));
  g.push(rectM(-12, R.y - R.washerD / 2, -9.5, R.y + R.washerD / 2, { fill: '#eeeeee', stroke: INK, sw: 0.3 }));
  // винты M8 и пробки в столешнице
  for (const sgn of [-1, 1]) {
    const x = sgn * T.boltX;
    const yTop = dishY(x, R.z);
    g.push(rectM(x - 8, yTop - T.screwHeadH, x + 8, yTop, { fill: '#e4d8bc', stroke: INK, sw: 0.4 }));
    g.push(poly([[mx(x - 8), my(yTop - 4.4)], [mx(x + 8), my(yTop - 4.4)], [mx(x + 4), my(548.3)], [mx(x - 4), my(548.3)]], {
      fill: '#bdbdbd', stroke: INK, sw: 0.35,
    }));
    g.push(rectM(x - 4, 532.9, x + 4, 548.3, { fill: '#d8d8d8', stroke: INK, sw: 0.35 }));
    g.push(rectM(x - 3, 550.5, x + 3, 552.9, { fill: '#707070', stroke: INK, sw: 0.3 }));
    g.push(rectM(x - 8, 542.4, x + 8, 544, { fill: '#eeeeee', stroke: INK, sw: 0.3 }));
    g.push(rectM(x - 6.5, 535.9, x + 6.5, 542.4, { fill: '#c8c8c8', stroke: INK, sw: 0.35 }));
  }
  g.push(centerlineH(-50, 50, R.y));
  g.push(centerlineV(0, 490, 565));
  g.push(dimH(-R.baseX, R.baseX, 490, '84', R.baseY0));
  g.push(dimV(50, R.y - R.d / 2, R.y + R.d / 2, 'Ø35', R.baseX));
  g.push(leader(0, 555, 80, 40, 1));
  g.push(leader(-R.baseX, 546, 15, 60, 2));
  g.push(leader(-7.5, 530, 15, 72, 3));
  g.push(leader(-5.5, 530, 15, 84, 4));
  g.push(leader(0, 527.5, 15, 96, 5));
  g.push(leader(5.5, 525, 15, 108, 6));
  g.push(leader(0, 521.5, 15, 120, 7));
  g.push(leader(19, 515, 132, 80, 8));
  g.push(leader(12, 515, 132, 90, 9));
  g.push(leader(-22, 515, 15, 132, 10));
  g.push(leader(T.boltX, 540, 132, 60, 11));
  g.push(leader(T.boltX, dishY(T.boltX, R.z) - 2, 132, 45, 12));
  g.push(text(80, 145, 'А–А  (1:1)', { size: 3.0, anchor: 'middle', weight: 'bold' }));

  // --- виды по оси: шестигранные головка и гайка (1:1) ---
  setView(-5, 705, 1.0);
  g.push(circleM(50, 515, 17.5, { fill: '#ededed', stroke: INK, sw: 0.55 }));
  g.push(circleM(50, 515, 12, { fill: '#eeeeee', stroke: INK, sw: 0.35 }));
  g.push(hexAt(50, 515, 11));
  g.push(circleM(50, 515, 6, { fill: '#7d7d7d', stroke: INK, sw: 0.3 }));
  g.push(centerlineH(30, 70, 515));
  g.push(centerlineV(50, 495, 535));
  g.push(text(45, 218, 'гайка M12', { size: 2.6, anchor: 'middle', weight: 'bold' }));
  g.push(text(45, 224, 'шестигранник', { size: 2.3, anchor: 'middle', fill: MID }));
  setView(55, 705, 1.0);
  g.push(circleM(50, 515, 17.5, { fill: '#ededed', stroke: INK, sw: 0.55 }));
  g.push(circleM(50, 515, 12, { fill: '#eeeeee', stroke: INK, sw: 0.35 }));
  g.push(hexAt(50, 515, 10.4));
  g.push(circleM(50, 515, 2, { fill: INK, stroke: 'none' }));
  g.push(centerlineH(30, 70, 515));
  g.push(centerlineV(50, 495, 535));
  g.push(text(105, 218, 'головка болта M12', { size: 2.6, anchor: 'middle', weight: 'bold' }));
  g.push(text(105, 224, 'шестигранник', { size: 2.3, anchor: 'middle', fill: MID }));
  g.push(text(80, 235, 'кронштейн не показан', { size: 2.3, anchor: 'middle', fill: MID }));

  // --- разнесённая изометрия ---
  setIsoCamera(0.7, -0.5);
  const fitPts = [];
  for (const x of [-45, 130]) for (const y of [R.earY0, T.yTop]) for (const z of [R.z - R.baseZ, R.z + R.baseZ]) fitPts.push({ x, y, z });
  fitIso(fitPts, { w: 95, h: 82, cx: 205, cy: 82 });

  // кронштейн — скруглённые пластины
  g.push(isoRoundedPlateXZ(-R.baseX, R.baseX, 548, R.baseY0, R.z - R.baseZ, R.z + R.baseZ, 5, {
    side: '#d6d6d6', bottom: '#eeeeee', sw: 0.45,
  }));
  g.push(isoRoundedPlateYZ(-5.5, -9.5, R.earY0, 544, R.z - R.baseZ, R.z + R.baseZ, 5, {
    face: '#eeeeee', side: '#d0d0d0', sw: 0.45, hole: { y: R.y, z: R.z, r: 6.5 },
  }));
  g.push(isoRoundedPlateYZ(9.5, 5.5, R.earY0, 544, R.z - R.baseZ, R.z + R.baseZ, 5, {
    face: '#eeeeee', side: '#d0d0d0', sw: 0.45, fillOpacity: 0.6, hole: { y: R.y, z: R.z, r: 6.5 },
  }));
  // подшипник, втулка, болт — разнесены вдоль оси
  g.push(isoCylinderX(61, 50, R.y, R.z, R.d / 2, { front: '#ececec', side: '#c9c9c9', sw: 0.45 }));
  g.push(isoCylinderX(61, 50, R.y, R.z, R.bushOD / 2, { front: '#ffffff', side: '#dddddd', sw: 0.35 }));
  g.push(isoCylinderX(78, 67, R.y, R.z, R.bushOD / 2, { front: '#d0d0d0', side: '#bdbdbd', sw: 0.35 }));
  g.push(isoCylinderX(78, 67, R.y, R.z, R.axleD / 2, { front: '#ffffff', side: '#e8e8e8', sw: 0.3 }));
  g.push(isoCylinderX(118, 83, R.y, R.z, R.axleD / 2, { front: '#e8e8e8', side: '#cfcfcf', sw: 0.35 }));
  g.push(isoHexX(125, 118, R.y, R.z, R.headD / 2 + 0.4, { face: '#d8d8d8', side: '#bdbdbd' }));
  g.push(isoCylinderX(83, 78, R.y, R.z, R.washerD / 2, { front: '#eeeeee', side: '#d0d0d0', sw: 0.3 }));
  g.push(isoCylinderX(-48, -60, R.y, R.z, R.washerD / 2, { front: '#eeeeee', side: '#d0d0d0', sw: 0.3 }));
  g.push(isoHexX(-60, -70, R.y, R.z, R.nutD / 2 + 1.0, { face: '#d4d4d4', side: '#bdbdbd', holeR: 6 }));
  g.push(isoLine([-70, R.y, R.z], [128, R.y, R.z], { sw: 0.2, dash: '3 1 0.8 1' }));
  g.push(text(205, 132, 'Порядок сборки: кронштейн → подшипник с втулкой → шайбы → болт/гайка', { size: 2.3, anchor: 'middle', fill: MID }));

  // --- деталь Е: подшипник и втулка (3:1) ---
  setView(200, 1745, 3.0);
  g.push(rectM(-R.w / 2, R.y - R.d / 2, R.w / 2, R.y - 15, { fill: 'url(#hatch)', sw: 0.45 }));
  g.push(rectM(-R.w / 2, R.y + 15, R.w / 2, R.y + R.d / 2, { fill: 'url(#hatch)', sw: 0.45 }));
  g.push(rectM(-R.w / 2, R.y - R.bushOD / 2, R.w / 2, R.y - 5, { fill: 'url(#hatch)', sw: 0.45 }));
  g.push(rectM(-R.w / 2, R.y + 5, R.w / 2, R.y + R.bushOD / 2, { fill: 'url(#hatch)', sw: 0.45 }));
  g.push(circleM(0, R.y - 12.5, 2.75, { fill: '#f4f4f4', stroke: INK, sw: 0.4 }));
  g.push(circleM(0, R.y + 12.5, 2.75, { fill: '#f4f4f4', stroke: INK, sw: 0.4 }));
  g.push(rectM(-R.w / 2, R.y - 15, -R.w / 2 + 0.5, R.y + 15, { fill: '#777777', stroke: 'none' }));
  g.push(rectM(R.w / 2 - 0.5, R.y - 15, R.w / 2, R.y + 15, { fill: '#777777', stroke: 'none' }));
  g.push(rectM(-R.w / 2, R.y - R.bushOD / 2, R.w / 2, R.y - R.axleD / 2, { fill: '#d0d0d0', stroke: INK, sw: 0.3 }));
  g.push(rectM(-R.w / 2, R.y + R.axleD / 2, R.w / 2, R.y + R.bushOD / 2, { fill: '#d0d0d0', stroke: INK, sw: 0.3 }));
  g.push(rectM(-12, R.y - R.axleD / 2, 12, R.y + R.axleD / 2, { fill: '#e8e8e8', stroke: INK, sw: 0.35 }));
  g.push(rectM(-9.5, R.y - R.d / 2, -R.w / 2, R.y - 5, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(-9.5, R.y + 5, -R.w / 2, R.y + R.d / 2, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(R.w / 2, R.y - R.d / 2, 9.5, R.y - 5, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(R.w / 2, R.y + 5, 9.5, R.y + R.d / 2, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(centerlineH(-14, 14, R.y));
  g.push(dimV(15, R.y - R.d / 2, R.y + R.d / 2, 'Ø35', R.w / 2));
  g.push(dimV(-15, R.y - R.bushOD / 2, R.y + R.bushOD / 2, 'Ø15', -R.w / 2));
  g.push(dimV(-22, R.y - R.axleD / 2, R.y + R.axleD / 2, 'Ø12', -12));
  g.push(leader(-5.5, R.y + 15, 252, 150, 4));
  g.push(leader(0, R.y + 12.5, 252, 165, 5));
  g.push(leader(5.5, R.y + 10, 252, 180, 6));
  g.push(leader(0, R.y + 7.5, 252, 195, 7));
  g.push(leader(12, R.y, 252, 210, 8));
  g.push(text(200, 268, 'Е  (3:1)', { size: 2.8, anchor: 'middle', weight: 'bold' }));

  const parts = [
    ['Столешница (фрагмент)', 1, 'фанера 12'],
    ['Кронштейн 84×50, R5', 1, 'сварной, 4 мм'],
    ['Щека 50×55, R5', 2, '4 мм'],
    ['Наружное кольцо 6202', 1, '35×11'],
    ['Шарик', 8, '6202'],
    ['Внутреннее кольцо', 1, '15×11'],
    ['Втулка 15/12×11', 1, 'сталь'],
    ['Болт M12×45 (шестигр.)', 1, '8.8'],
    ['Шайба M12', 2, 'сталь'],
    ['Гайка M12 (шестигр.)', 1, 'самоконтрящаяся'],
    ['Винт M8×20 (вн. шестигр.)', 2, 'потайной'],
    ['Пробка Ø16', 2, 'заподлицо'],
  ];

  return frame(
    'Ось ролика и подшипник',
    'Разрез А–А, разнесённая изометрия и деталь Е; 6202-2RS, втулка 15/12×11, болт M12×45',
    4,
    'Ось ролика',
    '1:1 / 3:1',
    parts,
    g.join(''),
    { source: 'Источник: stages/model/figs/left_view.svg' }
  );
}

function T_TABLE_TOP() { return P.table.yTop; }

// ---------------------------------------------------------------------------
// Лист 4. Крепление дрели к подстолью
// ---------------------------------------------------------------------------
function drawDrillMount() {
  const D = P.drill;
  const g = [];

  setIsoCamera(0.55, -0.5);
  const fitPts = [];
  for (const x of [90, 300]) for (const z of [-100, 100]) for (const y of [P.sub.yBot, P.sub.yTop]) fitPts.push({ x, y, z });
  for (const x of [90, 300]) for (const z of [-35, 0, 35]) for (const y of [D.cy - 35, D.cy + 35]) fitPts.push({ x, y, z });
  for (const x of D.ubX) for (const z of [-D.ubR, 0, D.ubR]) for (const y of [D.ubBottom, D.ubTop]) fitPts.push({ x, y, z });
  fitIso(fitPts, { w: 150, h: 100, cx: 115, cy: 95 });

  g.push(isoGhostBox(90, 300, P.sub.yBot, P.sub.yTop, -100, 100, { sw: 0.4 }));
  const aMax = Math.acos(90 / P.sub.winR);
  const winArc = [];
  for (let i = 0; i <= 18; i++) {
    const a = -aMax + (2 * aMax * i) / 18;
    winArc.push({ x: P.sub.winR * Math.cos(a), y: P.sub.yTop, z: P.sub.winR * Math.sin(a) });
  }
  g.push(isoPath(winArc, { sw: 0.4, dash: '2.4 1.2', stroke: MID }));
  g.push(text(24, 36, 'Окно подстолья Ø250 — слева; показан фрагмент', { size: 2.4, fill: MID }));
  g.push(text(24, 41, 'Крепление дрели: два U-болта M8 под трубу Ø80, резиновые подкладки', { size: 2.4, fill: MID }));

  g.push(isoCylinderX(90, 300, D.cy, 0, D.bodyD / 2, {
    front: '#f7f7f7', side: '#d8d8d8', sw: 0.45,
  }));
  g.push(isoBox(120, 290, D.cy + 35, P.sub.yBot, -30, 30, {
    top: '#b0b0b0', side: '#969696', side2: '#828282', sw: 0.3,
  }));

  for (const x of D.ubX) {
    // подкладка-седло под U-болтом
    const liner = [];
    for (let i = 0; i <= 24; i++) {
      const a = (Math.PI * i) / 24;
      liner.push({ x, y: D.cy - D.ubR * Math.sin(a), z: D.ubR * Math.cos(a) });
    }
    for (let i = 24; i >= 0; i--) {
      const a = (Math.PI * i) / 24;
      liner.push({ x, y: D.cy - 35 * Math.sin(a), z: 35 * Math.cos(a) });
    }
    g.push(isoPoly(liner, { fill: '#9a9a9a', stroke: 'none', opacity: 0.9 }));

    const pts = [];
    for (let i = 0; i <= 12; i++) {
      const t = i / 12;
      pts.push({ x, y: D.ubTop - (D.ubTop - D.cy) * t, z: D.ubR });
    }
    for (let i = 0; i <= 24; i++) {
      const a = (Math.PI * i) / 24;
      pts.push({ x, y: D.cy - D.ubR * Math.sin(a), z: D.ubR * Math.cos(a) });
    }
    for (let i = 0; i <= 12; i++) {
      const t = i / 12;
      pts.push({ x, y: D.cy + (D.ubTop - D.cy) * t, z: -D.ubR });
    }
    g.push(isoPath(pts, { stroke: '#333333', sw: 1.7, linecap: 'round' }));
    for (const z of [-D.ubZ, D.ubZ]) {
      g.push(isoHexY(x, z, P.sub.yTop + 8, P.sub.yTop, 7.5, {
        face: '#d8d8d8', side: '#bdbdbd', holeR: 4,
      }));
    }
  }

  const call = [
    [1, 290, P.sub.yTop, 80, 210, 48],
    [2, 290, D.cy, 0, 24, 70],
    [3, D.ubX[1], D.cy - D.ubR, 0, 210, 120],
    [4, D.ubX[1], D.cy - 40, 0, 24, 140],
    [5, D.ubX[1], D.cy + 34, 0, 210, 80],
    [6, D.ubX[1], P.sub.yTop + 4, D.ubZ, 150, 38],
  ];
  for (const [n, x, y, z, lx, ly] of call) g.push(isoCallout(x, y, z, lx, ly, n));

  // --- разрез В–В (1:2) ---
  setView(150, 410, 0.5);
  g.push(rectM(-100, P.sub.yBot, 100, P.sub.yTop, { fill: 'url(#hatch)', sw: 0.5 }));
  for (const z of [-D.ubZ, D.ubZ]) {
    g.push(rectM(z - D.ubD / 2, P.sub.yBot, z + D.ubD / 2, P.sub.yTop, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
  }
  g.push(circleM(0, D.cy, D.bodyD / 2, { fill: 'url(#hatchLight)', stroke: INK, sw: 0.55 }));

  // резиновая подкладка (под U-болтом)
  const lin2 = [];
  for (let i = 0; i <= 24; i++) {
    const a = (Math.PI * i) / 24;
    lin2.push([D.ubR * Math.cos(a), D.cy - D.ubR * Math.sin(a)]);
  }
  for (let i = 24; i >= 0; i--) {
    const a = (Math.PI * i) / 24;
    lin2.push([35 * Math.cos(a), D.cy - 35 * Math.sin(a)]);
  }
  g.push(polyM(lin2, { fill: '#9a9a9a', stroke: 'none', opacity: 0.85 }));

  // U-болт
  const ub = [];
  ub.push([D.ubZ, D.ubTop]);
  ub.push([D.ubZ, D.cy]);
  for (let i = 0; i <= 24; i++) {
    const a = (Math.PI * i) / 24;
    ub.push([D.ubR * Math.cos(a), D.cy - D.ubR * Math.sin(a)]);
  }
  ub.push([-D.ubZ, D.cy]);
  ub.push([-D.ubZ, D.ubTop]);
  g.push(polylineM(ub, { sw: 1.5, linecap: 'round' }));

  g.push(rectM(-30, D.cy + 35, 30, P.sub.yBot, { fill: '#9a9a9a', stroke: INK, sw: 0.3 }));
  for (const z of [-D.ubZ, D.ubZ]) {
    g.push(rectM(z - 8, P.sub.yTop, z + 8, P.sub.yTop + 8, { fill: '#d0d0d0', stroke: INK, sw: 0.35 }));
  }
  g.push(centerlineV(0, D.cy - 60, P.sub.yTop + 12));
  g.push(dimV(112, D.cy - 35, D.cy + 35, 'Ø70', 100));
  g.push(dimV(128, D.cy - D.ubR, D.cy + D.ubR, 'Ø90', 100));
  g.push(dimV(-112, P.sub.yBot, P.sub.yTop, '18', -100));
  g.push(dimH(-D.ubZ, D.ubZ, D.cy - 58, '90', D.cy - D.ubR));
  g.push(dimLeader(0, D.cy - D.ubR, 30, 174, 'U-болт M8; подкладка 10 мм'));
  g.push(text(150, 258, 'В–В  (1:2)', { size: 3.0, anchor: 'middle', weight: 'bold' }));
  g.push(text(16, 272, 'Разрез по U-болту. Дрель прижата к подстолью через подкладку 2 мм', { size: 2.4, fill: MID }));

  const parts = [
    ['Дрель (корпус Ø70)', 1, 'покупная'],
    ['U-болт M8 под Ø80', 2, 'покупной'],
    ['Подкладка-седло 10 мм', 2, 'резина'],
    ['Подкладка 2 мм', 2, 'резина'],
    ['Шайба Ø16 / гайка M8', 4, 'гайка шестигр.'],
    ['Подстолье', 1, 'см. лист 2'],
  ];

  return frame(
    'Крепление дрели к подстолью',
    'Изометрия и разрез В–В; два U-болта M8, окно Ø250',
    5,
    'Крепление дрели',
    '1:2',
    parts,
    g.join(''),
    { source: 'Источник: stages/model/figs/side_view.svg' }
  );
}

// ---------------------------------------------------------------------------
// Лист 5. Крепление кулачкового диска
// ---------------------------------------------------------------------------
function drawCamMount() {
  const C = P.cam;
  const g = [];
  const prof = camProfilePoints(200);

  // --- вид на диск (1:2) ---
  const face = { cx: 85, cy: 118, s: 0.5 };
  const fx = (z) => face.cx + face.s * z;
  const fy = (y) => face.cy - face.s * (y - C.cy);
  g.push(poly(prof.map(([z, y]) => [fx(z), fy(y)]), { fill: '#ededed', stroke: INK, sw: 0.6 }));
  g.push(circle(fx(0), fy(C.cy), C.R * face.s, { fill: 'none', stroke: MID, sw: 0.35, dash: '2.2 1.2' }));
  g.push(circle(fx(0), fy(C.cy), C.boreR * face.s, { fill: '#ffffff', stroke: INK, sw: 0.5 }));
  g.push(line(fx(-125), fy(C.cy), fx(125), fy(C.cy), { sw: 0.22, dash: '3 1 0.8 1' }));
  g.push(line(fx(0), fy(C.cy - 125), fx(0), fy(C.cy + 125), { sw: 0.22, dash: '3 1 0.8 1' }));
  g.push(circle(fx(0), fy(C.cy), 1.0, { fill: INK, stroke: 'none' }));
  g.push(leaderAt(fx(0), fy(C.cy + camRmax), 145, 55, 'Rmax=113'));
  g.push(leaderAt(fx(camRmin), fy(C.cy), 145, 170, 'Rmin=107'));
  const dx = fx(-130);
  g.push(line(dx, fy(C.cy + camRmax), dx, fy(C.cy - camRmax), { sw: 0.22 }));
  g.push(line(dx - 1.4, fy(C.cy + camRmax), fx(-camRmin) + 1, fy(C.cy + camRmax), { sw: 0.22 }));
  g.push(line(dx - 1.4, fy(C.cy - camRmax), fx(-camRmin) + 1, fy(C.cy - camRmax), { sw: 0.22 }));
  g.push(arrowV(dx, fy(C.cy + camRmax), -1));
  g.push(arrowV(dx, fy(C.cy - camRmax), 1));
  g.push(label(dx - 2, (fy(C.cy + camRmax) + fy(C.cy - camRmax)) / 2, 'Ø226', { size: 2.8, rot: -90 }));
  g.push(leaderAt(fx(C.boreR * 0.7), fy(C.cy + C.boreR * 0.7), 150, 70, 'Ø40'));
  g.push(text(85, 182, 'Вид на диск (1:2)', { size: 3.0, anchor: 'middle', weight: 'bold' }));
  g.push(text(85, 193, 'R=110; e=3; два лепестка через 180°', { size: 2.5, anchor: 'middle', fill: MID }));
  g.push(text(85, 199, 'Центр масс на оси; диск уравновешен', { size: 2.5, anchor: 'middle', fill: MID }));

  // --- изометрия, разнесённая ---
  setIsoCamera(0.7, -0.5);
  const fitPts = [];
  for (const x of [-24, 100]) for (const y of [C.cy - camRmax, C.cy + camRmax]) for (const z of [-camRmax, camRmax]) fitPts.push({ x, y, z });
  fitIso(fitPts, { w: 80, h: 93, cx: 205, cy: 98 });

  g.push(isoCylinderX(98, 70, C.cy, 0, 25, { front: '#f2f2f2', side: '#d4d4d4', sw: 0.4 }));
  g.push(text(205, 38, 'к патрону', { size: 2.4, anchor: 'middle', fill: MID }));
  g.push(isoCylinderX(70, 34, C.cy, 0, C.shankD / 2, { front: '#e8e8e8', side: '#c8c8c8', sw: 0.35 }));
  g.push(isoCylinderX(34, 26, C.cy, 0, C.flangeD / 2, { front: '#d8d8d8', side: '#bcbcbc', sw: 0.4 }));
  const discFront = 8, discBack = 2;
  const front = prof.map(([z, y]) => ({ x: discFront, y, z }));
  const back = prof.map(([z, y]) => ({ x: discBack, y, z }));
  const rim = [];
  for (const p of front) rim.push(p);
  for (let i = back.length - 1; i >= 0; i--) rim.push(back[i]);
  g.push(isoPoly(rim, { fill: '#b8b8b8', stroke: 'none' }));
  g.push(isoPoly(front, { fill: '#ececec', stroke: INK, sw: 0.5 }));
  g.push(isoPoly(isoCirclePts(discFront + 0.4, C.cy, 0, C.boreR, 36), { fill: '#ffffff', stroke: INK, sw: 0.4 }));
  g.push(isoCylinderX(-2, -6, C.cy, 0, C.washerD / 2, { front: '#e0e0e0', side: '#c8c8c8', sw: 0.35 }));
  g.push(isoCylinderX(-8, -16, C.cy, 0, 7, { front: '#c8c8c8', side: '#a8a8a8', sw: 0.35 }));
  g.push(isoBox(-20, -16, C.cy - 7, C.cy + 7, -7, 7, { top: '#b0b0b0', side: '#989898', side2: '#858585', sw: 0.3 }));
  g.push(isoLine([-26, C.cy, 0], [102, C.cy, 0], { sw: 0.22, dash: '3 1 0.8 1' }));
  g.push(text(205, 158, 'Разнесённая изометрия', { size: 2.8, anchor: 'middle', weight: 'bold' }));
  g.push(text(205, 164, 'патрон — оправка — диск — шайба — винт', { size: 2.3, anchor: 'middle', fill: MID }));

  // --- деталь Б: оправка (1:1) ---
  setView(200, 609.5, 1.0);
  g.push(rectM(C.chuckX0, C.cy - 25, 50, C.cy + 25, { fill: 'url(#hatchLight)', sw: 0.45 }));
  g.push(rectM(C.shankX0, C.cy - C.shankD / 2, C.shankX1, C.cy + C.shankD / 2, { fill: '#e8e8e8', stroke: INK, sw: 0.4 }));
  g.push(rectM(C.flangeX0, C.cy - C.flangeD / 2, C.flangeX1, C.cy + C.flangeD / 2, { fill: '#d8d8d8', stroke: INK, sw: 0.45 }));
  g.push(rectM(C.x0, C.cy + C.boreR, C.x1, C.cy + 45, { fill: 'url(#hatch)', sw: 0.5 }));
  g.push(rectM(C.x0, C.cy - 45, C.x1, C.cy - C.boreR, { fill: 'url(#hatch)', sw: 0.5 }));
  g.push(rectM(C.washerX0, C.cy - C.washerD / 2, C.washerX1, C.cy + C.washerD / 2, { fill: '#dcdcdc', stroke: INK, sw: 0.45 }));
  g.push(rectM(C.screwX1, C.cy - C.screwD / 2, C.screwX0, C.cy + C.screwD / 2, { fill: '#bdbdbd', stroke: INK, sw: 0.4 }));
  g.push(rectM(C.screwX0 - 3, C.cy - 7, C.screwX0, C.cy + 7, { fill: '#b0b0b0', stroke: INK, sw: 0.4 }));
  g.push(rectM(C.screwX0 - 3, C.cy - 3, C.screwX0 + 1, C.cy + 3, { fill: '#707070', stroke: INK, sw: 0.3 }));
  g.push(centerlineH(-24, 58, C.cy));
  g.push(centerlineV(0, C.cy - 48, C.cy + 48));
  g.push(lineM(-3, C.cy + 45, 3, C.cy + 45, { sw: 0.35, dash: '2 1' }));
  g.push(lineM(-3, C.cy - 45, 3, C.cy - 45, { sw: 0.35, dash: '2 1' }));
  g.push(textM(20, C.cy + 49, 'диск Ø226 (фрагмент)', { size: 2.2, fill: MID }));
  g.push(dimV(-20, C.cy - C.boreR, C.cy + C.boreR, 'Ø40', C.x0));
  g.push(dimLeader(C.shankX1, C.cy + C.shankD / 2, 140, 250, 'хвостовик Ø10×40 в патрон'));
  g.push(dimLeader(C.washerX0, C.cy + C.washerD / 2, 140, 218, 'шайба Ø60×4'));
  g.push(dimLeader(C.screwX0 - 3, C.cy + 7, 140, 234, 'винт M8×25 (вн. шестигр.)'));
  g.push(text(205, 268, 'Деталь Б (1:1)', { size: 2.8, anchor: 'middle', weight: 'bold' }));
  g.push(circle(245, 245, 7, { fill: '#d8d8d8', stroke: INK, sw: 0.45 }));
  g.push(hexSheet(245, 245, 3));
  g.push(text(245, 258, 'M8: внутр. шестигранник 6', { size: 2.2, anchor: 'middle', fill: MID }));

  g.push(text(16, 36, 'Крепление диска: оправка Ø10/Ø40, диск с отв. Ø40, прижим M8 + шайба Ø60', { size: 2.4, fill: MID }));

  const parts = [
    ['Диск кулачковый Ø226×6', 1, 'сталь, отв. Ø40'],
    ['Оправка Ø10/Ø40', 1, 'точение'],
    ['Шайба Ø60×4', 1, 'сталь'],
    ['Винт M8×25 (вн. шестигр.)', 1, 'сталь'],
    ['Патрон дрели', 1, 'покупной'],
  ];

  return frame(
    'Крепление кулачкового диска к дрели',
    'Вид на диск, разнесённая изометрия и деталь Б; оправка Ø10/Ø40, винт M8',
    6,
    'Крепление диска',
    '1:2 / 1:1',
    parts,
    g.join(''),
    { source: 'Источник: stages/model/figs/isometric.svg' }
  );
}

// ---------------------------------------------------------------------------
// Запись
// ---------------------------------------------------------------------------
const sheets = [
  ['table.svg', 'Вибростол — столешница', drawTable()],
  ['subtable.svg', 'Вибростол — подстолье', drawSubtable()],
  ['roller_unit.svg', 'Вибростол — крепление ролика', drawRollerAssembly()],
  ['roller_axle.svg', 'Вибростол — ось ролика', drawRollerAxle()],
  ['drill_mount.svg', 'Вибростол — крепление дрели', drawDrillMount()],
  ['cam_mount.svg', 'Вибростол — крепление диска', drawCamMount()],
];

for (const [name, title, body] of sheets) {
  fs.writeFileSync(nodePath.join(OUT, name), sheetSVG(title, body), 'utf8');
  console.log('written:', nodePath.join(OUT, name));
}
