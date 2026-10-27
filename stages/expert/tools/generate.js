'use strict';
/*
 * Генератор листов этапа «Инженерная экспертиза».
 * Запуск: node stages/expert/tools/generate.js
 * Результат: stages/expert/figs/{kinematics,dynamics,safety}.svg
 *
 * A3 landscape, 200 dpi, viewBox 0 0 420 297 (мм листа).
 * Только примитивы SVG, без внешних изображений и шрифтов.
 */

const fs = require('fs');
const nodePath = require('path');

const OUT = nodePath.join(__dirname, '..', 'figs');
fs.mkdirSync(OUT, { recursive: true });

const W = 420;
const H = 297;
const DPI = 200;
const PX = Math.round((W / 25.4) * DPI); // 3307
const PY = Math.round((H / 25.4) * DPI); // 2339

const INK = '#171717';
const MID = '#666666';
const LIGHT = '#ededed';
const RED = '#a11d1d';
const AMBER = '#b06a00';
const BLUE = '#1d4f8f';
const WHITE = '#ffffff';

const DATE = '28.10.2026';

// ---------------------------------------------------------------------------
// Базовые помощники
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

function path(d, o = {}) {
  return `<path d="${d}" ${attrs({
    fill: o.fill ?? 'none',
    stroke: o.stroke ?? INK,
    sw: o.sw ?? 0.45,
    dash: o.dash,
    opacity: o.opacity,
    fillOpacity: o.fillOpacity,
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
  if ('≥≤≈≠√²'.includes(ch)) return 0.68;
  if ('mwMWШЩЮМЖФЫ'.includes(ch)) return 0.87;
  if (/[A-ZА-ЯЁ]/.test(ch)) return 0.68;
  if (/[0-9]/.test(ch)) return 0.62;
  if ('()[]'.includes(ch)) return 0.35;
  return 0.56;
}
function tw(s, size) {
  let w = 0;
  for (const ch of String(s)) w += cw(ch);
  return w * size;
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
  const size = o.size ?? 2.6;
  const anchor = o.anchor ?? 'start';
  const weight = o.weight ?? 'normal';
  const fill = o.fill ?? INK;
  const rot = o.rot ? ` transform="rotate(${o.rot} ${f(x)} ${f(y)})"` : '';
  let out = '';
  if (o.bg) {
    const w = tw(s, size) + 1.2;
    const h = size * 1.25 + 0.7;
    const bx = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
    out += rect(bx - 0.6, y - h / 2, w, h, { fill: o.bg, stroke: 'none' });
  }
  BOXES.push({ x, y, w: tw(s, size), anchor, size, s, rot: o.rot || 0 });
  out += `<text x="${f(x)}" y="${f(y)}" font-size="${f(size)}" text-anchor="${anchor}" font-weight="${weight}" fill="${fill}" dominant-baseline="middle"${rot}>${esc(s)}</text>`;
  return out;
}

function textBlock(x, y, lines, o = {}) {
  const size = o.size ?? 2.4;
  const lh = o.lh ?? size * 1.35;
  let out = '';
  lines.forEach((ln, i) => {
    out += text(x, y + i * lh, ln, { ...o, size });
  });
  return out;
}

function arrow(x1, y1, x2, y2, o = {}) {
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const L = o.head ?? 2.0;
  const Wd = o.hw ?? 0.72;
  const c = Math.cos(ang);
  const sn = Math.sin(ang);
  const p1 = [x2 - L * c + Wd * sn, y2 - L * sn - Wd * c];
  const p2 = [x2 - L * c - Wd * sn, y2 - L * sn + Wd * c];
  const col = o.stroke ?? INK;
  return (
    line(x1, y1, x2, y2, { sw: o.sw ?? 0.4, stroke: col, dash: o.dash }) +
    poly([[x2, y2], p1, p2], { fill: col, stroke: col, sw: 0.1 })
  );
}

function dimH(x1, x2, y, txt, o = {}) {
  let out = '';
  if (o.from !== undefined) {
    const over = o.from < y ? -1.6 : 1.6;
    out += line(x1, o.from, x1, y + over, { sw: 0.2 });
    out += line(x2, o.from, x2, y + over, { sw: 0.2 });
  }
  out += arrow(x1, y, x2, y, { sw: 0.22, head: 1.7, hw: 0.6 });
  out += arrow(x2, y, x1, y, { sw: 0.22, head: 1.7, hw: 0.6 });
  if (txt)
    out += text((x1 + x2) / 2, y + (o.side === 'below' ? 2.4 : -2.2), txt, {
      size: o.size ?? 2.5,
      anchor: 'middle',
      bg: o.bg ?? WHITE,
    });
  return out;
}

function dimV(x, y1, y2, txt, o = {}) {
  let out = '';
  if (o.from !== undefined) {
    const over = o.from < x ? -1.5 : 1.5;
    out += line(o.from, y1, x + over, y1, { sw: 0.2 });
    out += line(o.from, y2, x + over, y2, { sw: 0.2 });
  }
  out += arrow(x, y1, x, y2, { sw: 0.22, head: 1.7, hw: 0.6 });
  out += arrow(x, y2, x, y1, { sw: 0.22, head: 1.7, hw: 0.6 });
  if (txt)
    out += text(x + (o.side === 'right' ? 2.2 : -2.2), (y1 + y2) / 2, txt, {
      size: o.size ?? 2.5,
      anchor: 'middle',
      rot: -90,
      bg: o.bg ?? WHITE,
    });
  return out;
}

function panel(x, y, w, h, title, o = {}) {
  let out = rect(x, y, w, h, { fill: o.fill ?? WHITE, stroke: INK, sw: 0.7 });
  if (title) {
    out += text(x + 5, y + 8, title, {
      size: o.size ?? 3.6,
      weight: 'bold',
      fill: o.color ?? INK,
    });
    out += line(x, y + 13.5, x + w, y + 13.5, { sw: 0.4 });
  }
  return out;
}

function table(x, y, w, cols, rows, o = {}) {
  const hh = o.hh ?? 8;
  const rh = o.rh ?? 8;
  const size = o.size ?? 2.2;
  let out = '';
  for (const c of cols)
    out += text(c.x, y + hh / 2, c.t, {
      size: c.size ?? size,
      anchor: c.align ?? 'start',
      fill: MID,
    });
  out += line(x, y + hh, x + w, y + hh, { sw: 0.35 });
  rows.forEach((r, i) => {
    const yy = y + hh + rh * (i + 0.5);
    r.forEach((v, j) => {
      out += text(cols[j].x, yy, v, {
        size: o.rowSize ?? size + 0.2,
        anchor: cols[j].align ?? 'start',
        weight: j === 0 ? 'bold' : 'normal',
      });
    });
    if (o.hlines)
      out += line(x, y + hh + rh * (i + 1), x + w, y + hh + rh * (i + 1), { sw: 0.2, stroke: '#d8d8d8' });
  });
  if (o.frame !== false)
    out += line(x, y + hh + rh * rows.length, x + w, y + hh + rh * rows.length, { sw: 0.35 });
  return out;
}

function springV(x, y1, y2, coils = 6, halfW = 3.4) {
  const n = coils * 2;
  const dy = (y2 - y1) / n;
  const pts = [];
  for (let i = 0; i <= n / 2; i++) {
    pts.push([x - halfW, y1 + dy * (2 * i + 0.5)]);
    pts.push([x + halfW, y1 + dy * (2 * i + 1.5)]);
  }
  const strip = [pts[0], ...pts.slice(0, -1), [x, y2]];
  return polyline([[x, y1], ...strip, [x, y2]], { sw: 0.42 });
}

// ---------------------------------------------------------------------------
// Каркас листа
// ---------------------------------------------------------------------------
function sheet(title, subtitle, sheetNo, body) {
  const head =
    rect(5, 5, 410, 287, { fill: WHITE, stroke: INK, sw: 0.8 }) +
    rect(10, 10, 400, 277, { fill: 'none', stroke: INK, sw: 0.4 }) +
    text(210, 20, title, { size: 5.5, anchor: 'middle', weight: 'bold' }) +
    text(210, 27.4, subtitle, { size: 3.0, anchor: 'middle', fill: MID });
  const foot = text(
    210,
    290,
    `Инженерная экспертиза · ${DATE} · DeepSeek / OpenCode · Лист ${sheetNo}`,
    { size: 2.35, anchor: 'middle', fill: MID }
  );
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${PX}" height="${PY}" viewBox="0 0 ${W} ${H}">
<title>${esc(title)}</title>
<defs>
  <pattern id="hatch" patternUnits="userSpaceOnUse" width="2.4" height="2.4" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="2.4" stroke="#666666" stroke-width="0.3"/>
  </pattern>
  <clipPath id="clipDyn"><rect x="42" y="178" width="206" height="84"/></clipPath>
</defs>
<style>
  text { font-family: 'DejaVu Sans', Arial, sans-serif; fill: ${INK}; }
</style>
<rect x="0" y="0" width="${W}" height="${H}" fill="${WHITE}"/>
${head}
${body}
${foot}
</svg>
`;
}

// ===========================================================================
// ЛИСТ 1. Кинематика кулачок–ролики
// ===========================================================================
const CAM_R = 110;
const ROLL_R = 17.5;
const CAM_Z = 50;
const CAM_E = 3;
const SC = 0.32; // мм листа на 1 мм модели

const Aof = (e) =>
  Math.sqrt(Math.pow(CAM_R + e + ROLL_R, 2) - CAM_Z * CAM_Z) -
  Math.sqrt(Math.pow(CAM_R - e + ROLL_R, 2) - CAM_Z * CAM_Z);

function sheetKinematics() {
  const C = { x: 130, y: 105 };
  let s = '';

  // --- стол ---------------------------------------------------------------
  s += rect(20, 52, 230, 4, { fill: LIGHT, stroke: INK, sw: 0.5 });
  s += text(22, 60.2, 'стол, низ 548', { size: 2.4 });
  s += text(18, 38, 'Схема Y–Z, не в масштабе; 0,32 мм листа на 1 мм модели', {
    size: 2.1,
    fill: MID,
  });
  s += text(18, 44.6, 'A=6,52 мм (e=3)', { size: 2.6, weight: 'bold' });

  // --- кронштейны роликов -------------------------------------------------
  for (const x of [114, 146]) {
    s += poly(
      [
        [x - 7, 56],
        [x - 7, 66.4],
        [x + 7, 66.4],
        [x + 7, 56],
      ],
      { fill: '#f4f4f4', sw: 0.4 }
    );
  }

  // --- профиль кулачка ----------------------------------------------------
  const pts = [];
  for (let i = 0; i < 240; i++) {
    const t = (i / 240) * Math.PI * 2;
    const r = 110 + 3 * Math.cos(2 * t);
    pts.push([C.x + r * Math.sin(t) * SC, C.y - r * Math.cos(t) * SC]);
  }
  s += poly(pts, { fill: LIGHT, sw: 0.55 });
  s += circle(C.x, C.y, 110 * SC, { dash: '1.5 1.1', sw: 0.25, stroke: MID });
  s += line(C.x - 2.4, C.y, C.x + 2.4, C.y, { sw: 0.2, dash: '1.6 0.8' });
  s += line(C.x, C.y - 2.4, C.x, C.y + 2.4, { sw: 0.2, dash: '1.6 0.8' });

  // --- ролики -------------------------------------------------------------
  for (const x of [114, 146]) {
    s += circle(x, 66.4, 5.6, { fill: WHITE, stroke: INK, sw: 0.5 });
    s += circle(x, 66.4, 2.4, { fill: WHITE, stroke: INK, sw: 0.4 });
    s += circle(x, 66.4, 0.45, { fill: INK, stroke: 'none' });
  }
  s += text(105, 61, 'z=−50', { size: 2.3, anchor: 'end' });
  s += text(155, 61, 'z=+50', { size: 2.3 });
  s += line(105, 61, 110.6, 64.4, { sw: 0.2 });
  s += line(155, 61, 149.4, 64.4, { sw: 0.2 });

  // --- линия центров ------------------------------------------------------
  const ang = Math.atan2(146 - C.x, C.y - 66.4); // от вертикали
  const ux = Math.sin(ang);
  const uy = -Math.cos(ang);
  s += line(C.x, C.y, C.x + ux * 42.3, C.y + uy * 42.3, { sw: 0.25, dash: '2 1.2' });
  s += line(C.x, C.y, C.x, 62, { sw: 0.2, dash: '3 1 0.8 1' });
  // дуга угла
  const ar = 16;
  const ax = C.x + ar * ux;
  const ay = C.y + ar * uy;
  s += path(`M ${f(C.x)} ${f(C.y - ar)} A ${ar} ${ar} 0 0 1 ${f(ax)} ${f(ay)}`, {
    sw: 0.25,
  });
  s += text(138.6, 91.4, '22,5°', { size: 2.3, bg: LIGHT });

  // точка контакта
  const kx = C.x + 36.15 * ux;
  const ky = C.y + 36.15 * uy;
  s += circle(kx, ky, 1.15, { fill: RED, stroke: RED, sw: 0.2 });

  // --- радиусы ------------------------------------------------------------
  const ray = (aDeg, rr, label, lx, ly) => {
    const a = (aDeg * Math.PI) / 180;
    const px = C.x + rr * Math.sin(a) * SC;
    const py = C.y - rr * Math.cos(a) * SC;
    let out = line(C.x, C.y, px, py, { sw: 0.22, dash: '1.4 1' });
    out += text(lx, ly, label, { size: 2.3, anchor: 'end', bg: LIGHT });
    return out;
  };
  s += ray(225, 110, 'R=110', 104, 131.6);
  s += ray(250, 113, 'Rmax=113', 94.5, 119.4);
  s += ray(290, 107, 'Rmin=107', 96.5, 92.4);
  s += text(70, 147, 'кулачок Ø226×6', { size: 2.3 });
  s += line(72, 146, 110, 136.4, { sw: 0.2 });
  s += circle(110, 136.4, 0.5, { fill: INK, stroke: 'none' });

  // --- размер A -----------------------------------------------------------
  for (const y of [65.35, 67.44]) {
    s += line(152, y, 171.5, y, { sw: 0.2, dash: '2.6 0.9 0.7 0.9' });
  }
  s += arrow(170, 63.2, 170, 65.35, { sw: 0.22, head: 1.5, hw: 0.55 });
  s += arrow(170, 69.6, 170, 67.44, { sw: 0.22, head: 1.5, hw: 0.55 });
  s += line(170, 63.2, 170, 69.6, { sw: 0.2 });
  s += text(173.5, 61.2, 'A=6,52', { size: 2.3 });
  s += line(173.2, 62.4, 170.4, 64.8, { sw: 0.18 });

  // --- подписи справа -----------------------------------------------------
  s += line(150.8, 69.9, 176.4, 74.6, { sw: 0.2 });
  s += circle(150.8, 69.9, 0.5, { fill: INK, stroke: 'none' });
  s += text(178, 75, 'ролик 6202-2RS Ø35', { size: 2.2 });

  s += line(kx + 1.2, ky + 1.2, 155, 79.6, { sw: 0.25, stroke: RED });
  s += text(157, 81, 'r_к=112,96 — контакт не на вершине', { size: 2.2, fill: RED });

  s += line(152, 77.6, 171, 87.4, { sw: 0.2 });
  s += circle(152, 77.6, 0.5, { fill: INK, stroke: 'none' });
  s += text(173, 88.4, 'd=130,46', { size: 2.3 });

  // --- силы у правого ролика ---------------------------------------------
  const O = { x: 196, y: 138 };
  const F = 18;
  const Ex = O.x + F * ux;
  const Ey = O.y + F * uy;
  s += arrow(O.x, O.y, Ex, Ey, { sw: 0.5, head: 2.3, hw: 0.8 });
  s += arrow(O.x, O.y, O.x, Ey, { sw: 0.5, head: 2.3, hw: 0.8 });
  s += arrow(O.x, O.y, Ex, O.y, { sw: 0.5, head: 2.3, hw: 0.8 });
  s += line(Ex, Ey, Ex, O.y, { sw: 0.2, dash: '1.6 1.1' });
  s += text(Ex + 2.2, 126.5, 'F', { size: 3.0, weight: 'bold' });
  s += text(194, 116.6, 'F_v=0,924F', { size: 2.3, anchor: 'end' });
  s += text(Ex + 2.2, 140, 'F_h=0,383F', { size: 2.3 });
  s += text(196, 146.2, 'силы на правом ролике, z=+50', {
    size: 2.05,
    anchor: 'middle',
    fill: MID,
  });

  s += text(18, 146.2, 'ΣF_h=0 только при симметрии', { size: 2.15 });

  // --- график A(e) --------------------------------------------------------
  const px0 = 42;
  const px1 = 246;
  const py0 = 260;
  const py1 = 176;
  const X = (e) => px0 + (e / 5.5) * (px1 - px0);
  const Y = (a) => py0 - (a / 12) * (py0 - py1);

  s += text(20, 167, 'Зависимость амплитуды от эксцентриситета', {
    size: 2.6,
    weight: 'bold',
  });

  // сетка
  for (let e = 0; e <= 5; e++) {
    s += line(X(e), py1, X(e), py0, { sw: 0.22, stroke: LIGHT });
    s += text(X(e), 265, String(e).replace('.', ','), { size: 2.2, anchor: 'middle' });
  }
  for (let a = 0; a <= 12; a += 2) {
    s += line(px0, Y(a), px1, Y(a), { sw: 0.22, stroke: LIGHT });
    s += text(38.5, Y(a), String(a), { size: 2.2, anchor: 'end' });
  }
  s += line(px0, py0, px1, py0, { sw: 0.45 });
  s += line(px0, py1, px0, py0, { sw: 0.45 });
  s += text(144, 272, 'e, мм', { size: 2.5, anchor: 'middle' });
  s += text(29.5, 218, 'A, мм', { size: 2.5, anchor: 'middle', rot: -90 });

  // 2e
  s += line(X(0), Y(0), X(5.5), Y(11), { sw: 0.4, stroke: MID, dash: '2.4 1.3' });
  // требование 10 мм
  s += line(px0, Y(10), px1, Y(10), { sw: 0.5, stroke: RED, dash: '4 1.6' });
  s += text(44, 186.6, 'требование 10 мм', { size: 2.2, fill: RED });

  // фактическая кривая
  const curve = [];
  for (let i = 0; i <= 60; i++) {
    const e = (i / 60) * 5.5;
    curve.push([X(e), Y(Aof(e))]);
  }
  s += polyline(curve, { sw: 0.8, stroke: BLUE });

  // точки
  const marks = [
    { e: 1.5, a: 3.26, t: '3,26', dx: 2.2, dy: 4.0, col: INK },
    { e: 3.0, a: 6.52, t: '6,52', dx: 2.2, dy: 4.0, col: INK },
    { e: 5.0, a: 10.87, t: '10,87', dx: -1.6, dy: -3.6, col: RED },
  ];
  for (const m of marks) {
    const mx = X(m.e);
    const my = Y(m.a);
    s += circle(mx, my, 1.15, { fill: WHITE, stroke: m.col, sw: 0.4 });
    s += circle(mx, my, 0.5, { fill: m.col, stroke: 'none' });
    s += text(mx + m.dx, my + m.dy, m.t, {
      size: 2.4,
      weight: 'bold',
      fill: m.col,
      anchor: m.dx < 0 ? 'end' : 'start',
    });
  }

  // легенда
  const lg = [
    { y: 236, txt: 'A факт', col: BLUE, dash: null },
    { y: 242, txt: '2e', col: MID, dash: '2.4 1.3' },
    { y: 248, txt: 'граница 10 мм', col: RED, dash: '3 1.4' },
  ];
  for (const it of lg) {
    s += line(164, it.y, 171, it.y, { sw: 0.7, stroke: it.col, dash: it.dash });
    s += text(173, it.y, it.txt, { size: 2.2 });
  }

  // --- правая панель ------------------------------------------------------
  s += panel(268, 32, 142, 253, 'РАСЧЁТ');
  s += table(
    272,
    49,
    134,
    [
      { t: 'e, мм', x: 274, align: 'start' },
      { t: 'A факт, мм', x: 334, align: 'end' },
      { t: '2e, мм', x: 368, align: 'end' },
      { t: 'A−2e, мм', x: 404, align: 'end' },
    ],
    [
      ['1,5', '3,26', '3,00', '+0,26'],
      ['3,0', '6,52', '6,00', '+0,52'],
      ['5,0', '10,87', '10,00', '+0,87'],
    ],
    { hh: 8, rh: 7.6, size: 2.15, rowSize: 2.4 }
  );

  s += text(274, 88.5, 'A = sqrt((R+e+r)²−z²) − sqrt((R−e+r)²−z²)', {
    size: 2.15,
  });
  s += text(274, 95.5, 'R=110; r=17,5; z=50', { size: 2.3 });
  s += line(272, 100, 406, 100, { sw: 0.25 });
  s += text(274, 106.5, 'ТЕЗИСЫ', { size: 2.5, weight: 'bold', fill: MID });

  const theses = [
    'Контакт происходит не на вершине кулачка, а под углом ≈22,5°.',
    'На каждый ролик действует горизонтальная сила 0,383F.',
    'Два ролика компенсируют её только при идеальной симметрии.',
    'A ≠ 2e; требование 6 README о линейности не выполняется.',
    'Для точных 3/6/10 мм при двух роликах нужно e ≈ 1,38 / 2,76 / 4,60 мм.',
    'Рекомендация: один центральный ролик + направляющая либо плоский толкатель; пересчитать диски.',
  ];
  let ty = 116;
  for (const t of theses) {
    const lines = wrap(t, 2.35, 126);
    s += rect(273.2, ty - 0.7, 1.3, 1.3, { fill: INK });
    lines.forEach((ln, i) => {
      s += text(277.5, ty + i * 3.5, ln, { size: 2.35 });
    });
    ty += lines.length * 3.5 + 5.2;
  }

  // вывод
  s += rect(272, 200, 134, 40, { fill: LIGHT, stroke: 'none' });
  s += rect(272, 200, 1.6, 40, { fill: RED, stroke: 'none' });
  s += text(277, 209, 'ВЫВОД', { size: 2.7, weight: 'bold', fill: RED });
  const concl = [
    'Фактическая амплитуда 10,87 мм > 10 мм.',
    'A ≠ 2e: требование линейности не выполняется.',
    'Нужны e ≈ 1,38 / 2,76 / 4,60 мм либо новая схема привода.',
  ];
  concl.forEach((c, i) => {
    s += text(277, 218 + i * 6.4, c, { size: 2.3 });
  });
  s += text(274, 252, 'Проверено численно по 60 точкам; см. график слева.', {
    size: 2.15,
    fill: MID,
  });

  return s;
}

// ===========================================================================
// ЛИСТ 2. Динамика подвески и контакт
// ===========================================================================
function sheetDynamics() {
  let s = '';

  // --- схема --------------------------------------------------------------
  s += text(15, 37, 'Расчётная схема', { size: 2.4, weight: 'bold', fill: MID });

  // верхняя опора
  s += rect(92, 40, 86, 8, { fill: 'url(#hatch)', stroke: INK, sw: 0.45 });
  s += line(92, 48, 178, 48, { sw: 0.55 });

  // пружины
  s += springV(110, 48, 78, 6, 3.4);
  s += springV(160, 48, 78, 6, 3.4);
  s += text(115, 56, 'k_в', { size: 2.5 });
  s += line(115, 56.6, 110, 58, { sw: 0.18 });

  // стол
  s += rect(95, 78, 80, 10, { fill: LIGHT, stroke: INK, sw: 0.55 });
  s += text(135, 83, 'm = 2,6 кг', { size: 2.6, anchor: 'middle', weight: 'bold' });

  // нижние пружины и подстолье
  s += springV(110, 88, 118, 6, 3.4);
  s += springV(160, 88, 118, 6, 3.4);
  s += text(115, 100, 'k_н', { size: 2.5 });
  s += line(115, 100.6, 110, 102, { sw: 0.18 });
  s += rect(92, 118, 34, 4, { fill: 'url(#hatch)', stroke: INK, sw: 0.45 });
  s += rect(144, 118, 34, 4, { fill: 'url(#hatch)', stroke: INK, sw: 0.45 });
  s += line(92, 118, 126, 118, { sw: 0.55 });
  s += line(144, 118, 178, 118, { sw: 0.55 });
  s += text(94, 127, 'подстолье', { size: 2.15, fill: MID });

  // кронштейн ролика
  s += line(128, 88, 128, 124, { sw: 0.45 });
  s += line(142, 88, 142, 124, { sw: 0.45 });
  s += line(128, 124, 142, 124, { sw: 0.45 });

  // ролик и кулачок
  s += circle(135, 124, 5, { fill: WHITE, stroke: INK, sw: 0.5 });
  s += circle(135, 124, 1.4, { fill: WHITE, stroke: INK, sw: 0.35 });
  s += circle(135, 142, 18, { fill: LIGHT, stroke: INK, sw: 0.55 });
  s += circle(135, 142, 3, { fill: WHITE, stroke: INK, sw: 0.4 });
  s += line(135, 142, 148, 142, { sw: 0.25, dash: '3 1 0.8 1' });

  // силы и координата
  s += arrow(124, 88, 124, 104, { sw: 0.45, head: 2.0, hw: 0.7 });
  s += text(122, 102.5, 'mg', { size: 2.4, anchor: 'end' });

  s += arrow(135, 68, 135, 77, { sw: 0.45, head: 2.0, hw: 0.7 });
  s += text(133, 71.8, 'F_в', { size: 2.4, anchor: 'end' });

  s += arrow(147, 112, 147, 94, { sw: 0.45, head: 2.0, hw: 0.7 });
  s += text(148, 91.6, 'F_н', { size: 2.4 });

  s += arrow(135, 121.8, 135, 98, { sw: 0.45, head: 2.0, hw: 0.7 });
  s += text(136.5, 96, 'F_ц(t) ≥ 0', { size: 2.2 });

  s += arrow(88, 112, 88, 95, { sw: 0.35, head: 1.8, hw: 0.6, stroke: MID });
  s += text(88, 92.2, 'x', { size: 2.5, anchor: 'middle', fill: MID });

  // --- формулы ------------------------------------------------------------
  s += text(182, 36, 'Уравнение движения', { size: 2.4, weight: 'bold', fill: MID });
  s += text(182, 44, 'm·ẍ + (k_в + k_н)·x = F_ц(t) − F_0', { size: 2.3 });
  s += text(182, 53, 'контакт: F_ц ≥ 0', { size: 2.3 });
  s += text(182, 62, 'вверху: F_пружин↓ ≥ m·a_max', { size: 2.3 });
  s += text(182, 72, 'a_max = 44,4 м/с² (4,5g)', { size: 2.2, fill: MID });
  s += text(182, 85, 'нижние пружины толкают вверх', { size: 2.2 });
  s += text(182, 91, 'и уменьшают поджим', { size: 2.2 });

  // --- график -------------------------------------------------------------
  const px0 = 42;
  const px1 = 248;
  const py0 = 262;
  const py1 = 178;
  const X = (fr) => px0 + (fr / 20) * (px1 - px0);
  const Y = (Fv) => py0 - (Fv / 140) * (py0 - py1);

  s += text(20, 172, 'Сила инерции и запас пружин', { size: 2.6, weight: 'bold' });

  for (let fr = 0; fr <= 20; fr += 2) {
    s += line(X(fr), py1, X(fr), py0, { sw: 0.2, stroke: LIGHT });
  }
  for (let i = 0; i <= 20; i += 5) {
    s += text(X(i), 267, String(i), { size: 2.2, anchor: 'middle' });
  }
  for (let Fv = 0; Fv <= 140; Fv += 20) {
    s += line(px0, Y(Fv), px1, Y(Fv), { sw: 0.2, stroke: LIGHT });
    s += text(38.5, Y(Fv), String(Fv), { size: 2.2, anchor: 'end' });
  }
  s += line(px0, py0, px1, py0, { sw: 0.45 });
  s += line(px0, py1, px0, py0, { sw: 0.45 });
  s += text(145, 272, 'частота f, Гц', { size: 2.5, anchor: 'middle' });
  s += text(29.5, 220, 'F, Н', { size: 2.5, anchor: 'middle', rot: -90 });

  // кривая
  const curve = [];
  for (let i = 0; i <= 80; i++) {
    const fr = (i / 80) * 20;
    const Fv = 2.6 * Math.pow(2 * Math.PI * fr, 2) * 0.005;
    curve.push([X(fr), Y(Math.min(Fv, 160))]);
  }
  s += `<g clip-path="url(#clipDyn)">${polyline(curve, { sw: 0.85, stroke: BLUE })}</g>`;

  // запас пружин
  s += line(px0, Y(6.3), px1, Y(6.3), { sw: 0.45, stroke: MID, dash: '2.4 1.3' });
  s += text(44, 255, '6,3 Н — запас пружин без поджима', { size: 2.15, fill: MID });

  // точка 15 Гц
  const fx = X(15);
  const fy = Y(115.5);
  s += line(fx, py0, fx, fy, { sw: 0.22, stroke: MID, dash: '1.6 1.1' });
  s += circle(fx, fy, 1.25, { fill: WHITE, stroke: BLUE, sw: 0.45 });
  s += circle(fx, fy, 0.55, { fill: BLUE, stroke: 'none' });
  s += text(fx - 3.5, fy - 6.2, '115,5 Н при 15 Гц', { size: 2.25, anchor: 'end' });

  // стрелка предподжима
  s += arrow(fx + 6, Y(6.3), fx + 6, fy + 0.6, { sw: 0.35, head: 1.8, hw: 0.6 });
  s += arrow(fx + 6, fy + 0.6, fx + 6, Y(6.3), { sw: 0.35, head: 1.8, hw: 0.6 });
  s += text(fx + 9, 226, 'нужен предподжим ≥109 Н', { size: 2.2 });

  // легенда
  s += line(52, 186, 59, 186, { sw: 0.8, stroke: BLUE });
  s += text(61, 186, 'F ин = m·(2πf)²·A/2', { size: 2.2 });
  s += line(52, 192, 59, 192, { sw: 0.45, stroke: MID, dash: '2.4 1.3' });
  s += text(61, 192, 'запас пружин 6,3 Н', { size: 2.2 });

  // --- правая панель ------------------------------------------------------
  s += panel(268, 32, 142, 253, 'ПРУЖИНЫ');
  s += table(
    272,
    49,
    134,
    [
      { t: 'f_соб, Гц', x: 274, align: 'start', size: 2.0 },
      { t: 'k, Н/м', x: 322, align: 'end', size: 2.0 },
      { t: 'стат. прогиб, мм', x: 366, align: 'end', size: 2.0 },
      { t: 'F0 при 15 Гц/10 мм, Н', x: 404, align: 'end', size: 1.95 },
    ],
    [
      ['3,5', '1257', '20,3', '109'],
      ['5', '2566', '9,9', '103'],
      ['10', '10264', '2,5', '64'],
      ['20', '41058', '0,6', '0'],
    ],
    { hh: 9, rh: 8, size: 2.05, rowSize: 2.35 }
  );

  s += text(274, 90, 'F0 = max(0, m·a − k·A/2)', { size: 2.3 });
  s += text(274, 97, 'm=2,6 кг; a=44,4 м/с²; A/2=5 мм', { size: 2.15, fill: MID });
  s += line(272, 101.5, 406, 101.5, { sw: 0.25 });
  s += text(274, 107.5, 'ТЕЗИСЫ', { size: 2.5, weight: 'bold', fill: MID });

  const theses = [
    'Пружины не заданы: нет d, L0, k, материала, поджима.',
    'При f_соб=3,5 Гц сила пружин на ±5 мм — 6,3 Н; этого мало.',
    'Нижние пружины уменьшают результирующий поджим; их влияние не рассчитано.',
    'Для 5 кг: m=7,6 кг, F=337,6 Н, F0 ≥ 320 Н; все силы ×2,9.',
    'Резонанс 3–4 Гц; рабочий диапазон 5–15 Гц; пуск проходит через резонанс.',
    'Рекомендация: 4 верхние пружины, F0 ≥ 170 Н (2,6 кг) / 480 Н (5 кг), демпфер, ловители; проверить напряжение, усталость, surge.',
  ];
  let ty = 117;
  for (const t of theses) {
    const lines = wrap(t, 2.3, 126);
    s += rect(273.2, ty - 0.7, 1.3, 1.3, { fill: INK });
    lines.forEach((ln, i) => s += text(277.5, ty + i * 3.4, ln, { size: 2.3 }));
    ty += lines.length * 3.4 + 5.4;
  }

  s += rect(272, 200, 134, 34, { fill: LIGHT, stroke: 'none' });
  s += rect(272, 200, 1.6, 34, { fill: AMBER, stroke: 'none' });
  s += text(277, 208, 'ПРОВЕРКА ПРИ 5 КГ', { size: 2.6, weight: 'bold', fill: AMBER });
  s += text(277, 216, 'F = 337,6 Н — вне шкалы графика 0…140 Н.', { size: 2.2 });
  s += text(277, 222.5, 'F0 ≥ 320 Н; все силы ×2,9 к варианту 2,6 кг.', { size: 2.2 });
  s += text(277, 229, 'Верхние пружины должны держать стол на поджиме.', { size: 2.2 });

  s += text(274, 252, 'Источник: Report.md, разделы «Динамика» и «Пружины».', {
    size: 2.1,
    fill: MID,
  });

  return s;
}

// ===========================================================================
// ЛИСТ 3. Карта рисков и защита
// ===========================================================================
const CRIT = [
  'открытый привод без кожуха/E-stop',
  'диск в патроне дрели',
  'осевое крепление диска',
  'нет направляющих стола',
  'пружины не рассчитаны',
  'фанера в несущей цепи',
  'крепление дрели на трении',
];
const IMPORTANT = [
  'A ≠ 2e, 10,87 > 10',
  'гармоничность не обеспечена',
  'нестабильная частота дрели',
  'резонанс 3–4 Гц',
  'зазор кронштейна 11/11',
  'винт M8×20 короток',
  'шарик/лунка 3 мм',
  'чертежи model/correct/1 расходятся',
];
const WISH = [
  'мотор-редуктор + ЧРП',
  'тахометр/акселерометр',
  'твёрдая чаша',
  'спецификация/поставщики',
  'CAD/STEP',
  'регламент обслуживания',
];

function badge(x, y, n, color) {
  return (
    circle(x, y, 5.2, { fill: color, stroke: color, sw: 0.3, fillOpacity: 0.1, strokeOpacity: 0.35, dash: '1.4 1' }) +
    circle(x, y, 2.35, { fill: WHITE, stroke: color, sw: 0.5 }) +
    text(x, y + 0.05, String(n), { size: 2.4, anchor: 'middle', weight: 'bold', fill: color })
  );
}

function sheetSafety() {
  let s = '';

  // --- вид сбоку ----------------------------------------------------------
  s += text(15, 37, 'Вид сбоку, схематично', { size: 2.4, weight: 'bold', fill: MID });

  // рама
  s += rect(20, 178, 120, 5, { fill: 'url(#hatch)', stroke: INK, sw: 0.5 });
  s += rect(26, 49, 5, 129, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += rect(127, 49, 5, 129, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += rect(28, 44, 104, 5, { fill: 'url(#hatch)', stroke: INK, sw: 0.5 });

  // пружины и стол
  s += springV(55, 49, 72, 5, 3.2);
  s += springV(105, 49, 72, 5, 3.2);
  s += rect(44, 72, 78, 6, { fill: LIGHT, stroke: INK, sw: 0.5 });
  s += springV(55, 78, 108, 5, 3.2);
  s += springV(105, 78, 108, 5, 3.2);

  // подстолье
  s += rect(31, 108, 33, 5, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += rect(106, 108, 21, 5, { fill: LIGHT, stroke: INK, sw: 0.45 });

  // кулачок и ролики
  s += circle(85, 95, 12.5, { fill: LIGHT, stroke: INK, sw: 0.5 });
  s += circle(85, 95, 3, { fill: WHITE, stroke: INK, sw: 0.35 });
  s += circle(79, 81, 4.4, { fill: WHITE, stroke: INK, sw: 0.45 });
  s += circle(91, 81, 4.4, { fill: WHITE, stroke: INK, sw: 0.45 });

  // дрель, патрон, крепление
  s += rect(76, 112, 18, 4, { fill: LIGHT, stroke: INK, sw: 0.45 }); // патрон
  s += rect(70, 116, 30, 34, { fill: LIGHT, stroke: INK, sw: 0.5, rx: 2 });
  s += rect(56, 124, 14, 6, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += rect(72, 143, 26, 4, { fill: 'url(#hatch)', stroke: INK, sw: 0.45 });
  // шнур и пуск
  s += path('M 70 147 C 56 152, 46 156, 38 159', { sw: 0.4 });
  s += rect(33, 155, 8, 6, { fill: WHITE, stroke: INK, sw: 0.45, rx: 0.8 });
  s += circle(37, 158, 1.1, { fill: RED, stroke: RED, sw: 0.2 });

  // шарик
  s += circle(100, 81, 2.4, { fill: WHITE, stroke: INK, sw: 0.4 });

  // зоны
  s += badge(70, 90, 1, RED);
  s += badge(78, 114, 2, RED);
  s += badge(48, 64, 3, AMBER);
  s += badge(36, 46, 4, RED);
  s += badge(74, 122, 5, AMBER);
  s += badge(100, 81, 6, AMBER);
  s += badge(40, 158, 7, RED);

  // короткие подписи зон
  const lbl = (tx, ty, ax, ay, str, anchor = 'start') =>
    text(tx, ty, str, { size: 2.2, anchor }) + line(tx, ty, ax, ay, { sw: 0.18 });

  s += lbl(101, 92, 74, 90, '1 кулачок');
  s += line(100, 103.4, 88, 112.4, { sw: 0.18 });
  s += text(101, 104, '2 патрон', { size: 2.2 });
  s += lbl(33, 58, 48, 64, '3 стол/пружины');
  s += lbl(33, 38, 36, 45, '4 плита/шпильки');
  s += lbl(104, 132, 97, 128, '5 дрель');
  s += lbl(103, 88, 100.6, 83.6, '6 шарик');
  s += lbl(44, 164, 40, 160, '7 пуск');

  // --- легенда ------------------------------------------------------------
  s += line(15, 192, 160, 192, { sw: 0.3 });
  s += text(15, 197.5, 'ЛЕГЕНДА', { size: 2.6, weight: 'bold' });

  const items = [
    ['1', 'кулачок', 'открытый привод, нет кожуха и E-stop', 'кожух с блокировкой, E-stop', RED],
    ['2', 'патрон', 'диск зажат в патроне дрели, осевой сдвиг', 'фланец + штифты, вал на 2 опорах', RED],
    ['3', 'стол/пружины', 'нет направляющих, пружины не рассчитаны', '4 пружины с поджимом, направляющие', AMBER],
    ['4', 'плита/шпильки', 'фанера в несущей цепи, шпильки коротки', 'стальная плита 8 мм, шпильки M10', RED],
    ['5', 'дрель', 'крепление только на трении, проворот', 'хомут с упором, штифты, страховка', AMBER],
    ['6', 'шарик', 'точечный контакт 3 мм, смятие лунки', 'твёрдая чаша, больший радиус лунки', AMBER],
    ['7', 'пуск', 'нет защиты, блокировок и заземления', 'пускатель, УЗО 30 мА, E-stop', RED],
  ];
  const cols = [15.5, 88];
  const yStart = [205, 205];
  const perCol = [4, 3];
  let idx = 0;
  for (let c = 0; c < 2; c++) {
    let y = yStart[c];
    for (let k = 0; k < perCol[c]; k++) {
      const it = items[idx++];
      s += text(cols[c], y, `${it[0]} ${it[1]}`, { size: 2.3, weight: 'bold', fill: it[4] });
      const d = wrap('опасность: ' + it[2], 2.05, 67);
      const m = wrap('мера: ' + it[3], 2.05, 67);
      let yy = y + 4.6;
      d.forEach((ln) => { s += text(cols[c], yy, ln, { size: 2.05 }); yy += 2.8; });
      m.forEach((ln) => { s += text(cols[c], yy, ln, { size: 2.05, fill: MID }); yy += 2.8; });
      y = yy + 2.4;
    }
  }

  // --- рекомендуемый привод ----------------------------------------------
  s += line(166, 34, 166, 148, { sw: 0.3, stroke: LIGHT });
  s += text(170, 38, 'РЕКОМЕНДУЕМЫЙ ПРИВОД', { size: 2.9, weight: 'bold' });

  // дрель
  s += rect(170, 60, 18, 30, { fill: LIGHT, stroke: INK, sw: 0.45, rx: 2 });
  s += rect(170, 86, 22, 5, { fill: LIGHT, stroke: INK, sw: 0.45, rx: 1 });
  s += poly([[188, 68], [196, 70], [196, 82], [188, 84]], { fill: LIGHT, sw: 0.45 });
  // муфта
  s += rect(197, 71, 4, 10, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += rect(203, 71, 4, 10, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += path('M 201 72 q 1.5 3 0 8', { sw: 0.3, dash: '1.2 0.9' });
  // вал и опоры
  s += line(207, 76, 236, 76, { sw: 0.9 });
  for (const bx of [211, 224]) {
    s += rect(bx - 2.6, 71.4, 5.2, 3.2, { fill: WHITE, stroke: INK, sw: 0.4 });
    s += rect(bx - 2.6, 77.4, 5.2, 3.2, { fill: WHITE, stroke: INK, sw: 0.4 });
  }
  // фланец и штифты
  s += rect(236, 69, 3.4, 14, { fill: LIGHT, stroke: INK, sw: 0.45 });
  s += circle(237.7, 71.5, 0.85, { fill: WHITE, stroke: INK, sw: 0.3 });
  s += circle(237.7, 80.5, 0.85, { fill: WHITE, stroke: INK, sw: 0.3 });
  // кулачок
  s += circle(246, 76, 10, { fill: LIGHT, stroke: INK, sw: 0.5 });
  s += circle(246, 76, 2.4, { fill: WHITE, stroke: INK, sw: 0.35 });
  // кожух
  s += rect(232, 58, 26, 36, { fill: 'none', stroke: INK, sw: 0.45, dash: '2.2 1.4', rx: 1.5 });
  s += text(236, 56.4, 'кожух', { size: 2.05, fill: MID });

  // подписи привода
  const pl = (tx, ty, ax, ay, str, size = 2.2) =>
    text(tx, ty, str, { size }) + line(tx, ty, ax, ay, { sw: 0.18 });

  s += pl(170, 100, 176, 92, 'дрель');
  s += pl(192, 108, 200, 82, 'муфта');
  s += pl(209, 100, 213, 81.8, '2 подшипника');
  s += pl(226, 108, 237, 83, 'фланец + штифты');
  s += pl(255, 100, 250, 85, 'кулачок', 2.2);
  s += pl(252, 118, 256, 88, 'кожух + блокировка', 2.15);
  s += text(170, 128, 'E-stop', { size: 2.2, weight: 'bold', fill: RED });
  s += circle(178, 127.4, 1.4, { fill: RED, stroke: RED, sw: 0.2 });
  s += text(170, 140, 'радиальная нагрузка на патрон = 0;', { size: 2.15 });
  s += text(170, 146, 'биение ≤ 0,05 мм', { size: 2.15 });

  // --- правая панель ------------------------------------------------------
  s += panel(268, 32, 142, 253, 'СВОДКА');

  const block = (y, title, color, rows, count) => {
    let out = rect(272, y - 4.5, 1.8, 40, { fill: color, stroke: 'none' });
    out += text(277, y, `${title} · ${count}`, { size: 2.9, weight: 'bold', fill: color });
    rows.forEach((r, i) => {
      out += text(277, y + 8.5 + i * 6.6, `${i + 1}. ${r}`, { size: 2.2 });
    });
    return out;
  };

  s += block(46, 'КРИТИЧНО', RED, CRIT, 7);
  s += block(116, 'ВАЖНО', AMBER, IMPORTANT, 14);
  s += block(193, 'ПОЖЕЛАНИЯ', BLUE, WISH, 9);

  s += line(272, 232, 406, 232, { sw: 0.3 });
  s += text(274, 238, 'Показаны главные пункты (7 / 8 / 6 из 30).', {
    size: 2.1,
    fill: MID,
  });
  s += rect(272, 262, 134, 15, { fill: LIGHT, stroke: 'none' });
  s += text(277, 268, 'Полный перечень и расчёты — Report.md.', { size: 2.2 });
  s += text(277, 273.4, 'Интервью и допущения — Interview.md.', { size: 2.1, fill: MID });

  return s;
}

// ---------------------------------------------------------------------------
function verify(name) {
  let bad = 0;
  for (const b of BOXES) {
    let x0 = b.x;
    const w = b.w;
    if (b.anchor === 'middle') x0 = b.x - w / 2;
    if (b.anchor === 'end') x0 = b.x - w;
    const x1 = x0 + w;
    const y0 = b.y - b.size / 2;
    const y1 = b.y + b.size / 2;
    if (x0 < 11 || x1 > 409 || y0 < 11 || y1 > 289) {
      console.error(
        `[${name}] вне листа: "${b.s}" x ${x0.toFixed(1)}..${x1.toFixed(1)} y ${y0.toFixed(1)}..${y1.toFixed(1)}`
      );
      bad++;
    }
  }
  return bad;
}

const files = [
  ['kinematics.svg', sheetKinematics(), 'Кинематика кулачок–ролики'],
  ['dynamics.svg', sheetDynamics(), 'Динамика подвески и контакт'],
  ['safety.svg', sheetSafety(), 'Карта рисков и рекомендуемая защита'],
];

const SUB = {
  'kinematics.svg':
    'Фактическая амплитуда стола: 3,26 / 6,52 / 10,87 мм при e = 1,5 / 3 / 5 мм',
  'dynamics.svg':
    'При 15 Гц и размахе 10 мм: ускорение 4,5g, сила 115,5 Н; без поджима ≥110 Н стол отрывается',
  'safety.svg': '7 критичных, 14 важных, 9 пожеланий; полный перечень — Report.md',
};

let totalBad = 0;
files.forEach(([file, body, title], i) => {
  BOXES.length = 0;
  const svg = sheet(title, SUB[file], i + 1, body);
  totalBad += verify(file);
  fs.writeFileSync(nodePath.join(OUT, file), svg, 'utf8');
  console.log(`${file}: ${(svg.length / 1024).toFixed(1)} КБ`);
});
if (totalBad) console.error(`Предупреждений: ${totalBad}`);
