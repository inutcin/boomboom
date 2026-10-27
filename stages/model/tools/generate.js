'use strict';
/*
 * Параметрический генератор листов этапа «Формирование модели устройства».
 * Запуск: node stages/model/tools/generate.js
 * Результат: stages/model/figs/side_view.svg, left_view.svg, isometric.svg
 *
 * Все размеры — в миллиметрах модели. Листы — A3, масштаб 1:5.
 */
const fs = require('fs');
const nodePath = require('path');

const OUT = nodePath.join(__dirname, '..', 'figs');
fs.mkdirSync(OUT, { recursive: true });

const W = 420;          // A3, мм
const H = 297;
const DPI = 200;
const PX = Math.round((W / 25.4) * DPI); // 3307
const PY = Math.round((H / 25.4) * DPI); // 2339
const S = 0.2;          // 1:5

const INK = '#171717';
const MID = '#6b6b6b';
const LIGHT = '#f2f2f2';
const MIDFILL = '#d8d8d8';
const DARKFILL = '#bdbdbd';
const RED = '#8f1d1d';

// ---------------------------------------------------------------------------
// Базовые SVG-хелперы (координаты листа, мм)
// ---------------------------------------------------------------------------
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
  })}/>`;
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
    fill: o.fill ?? 'none',
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

// Белая подложка под подпись (чтобы размерные линии не перечёркивали текст)
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
// Проекции
// ---------------------------------------------------------------------------
let V = { ox: 150, oy: 240, s: S, horiz: 'x' };

function setView(ox, oy, horiz = 'x') {
  V = { ox, oy, s: S, horiz };
}

// h — горизонтальная координата модели (X для вида сбоку, Z для вида слева)
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
function pathM(d, o = {}) {
  // d задаётся строками в координатах модели через отдельные сегменты; не используется
  return path(d, o);
}
function textM(h, y, s, o = {}) {
  return text(mx(h), my(y), s, o);
}

function arrowH(x, y, dir) {
  const L = 1.7, Wd = 0.65;
  const pts = dir < 0
    ? [[x, y], [x + L, y - Wd], [x + L, y + Wd]]
    : [[x, y], [x - L, y - Wd], [x - L, y + Wd]];
  return poly(pts, { fill: INK, stroke: INK, sw: 0.1 });
}
function arrowV(x, y, dir) {
  const L = 1.7, Wd = 0.65;
  const pts = dir < 0
    ? [[x, y], [x - Wd, y + L], [x + Wd, y + L]]
    : [[x, y], [x - Wd, y - L], [x + Wd, y - L]];
  return poly(pts, { fill: INK, stroke: INK, sw: 0.1 });
}

// Горизонтальный размер. h1,h2 — координаты модели; y — положение размерной линии.
function dimH(h1, h2, y, s, fromY) {
  const x1 = mx(h1), x2 = mx(h2), yy = my(y);
  let out = '';
  if (fromY !== undefined) {
    out += line(x1, my(fromY), x1, yy + (yy > my(fromY) ? 1.5 : -1.5), { sw: 0.25 });
    out += line(x2, my(fromY), x2, yy + (yy > my(fromY) ? 1.5 : -1.5), { sw: 0.25 });
  }
  out += line(x1, yy, x2, yy, { sw: 0.25 });
  out += arrowH(x1, yy, -1) + arrowH(x2, yy, 1);
  out += label((x1 + x2) / 2, yy - 1.9, s, { size: 3.1 });
  return out;
}

// Вертикальный размер.
function dimV(h, y1, y2, s, fromH) {
  const xx = mx(h), y1p = my(y1), y2p = my(y2);
  let out = '';
  if (fromH !== undefined) {
    out += line(mx(fromH), y1p, xx + (xx > mx(fromH) ? 1.5 : -1.5), y1p, { sw: 0.25 });
    out += line(mx(fromH), y2p, xx + (xx > mx(fromH) ? 1.5 : -1.5), y2p, { sw: 0.25 });
  }
  out += line(xx, y1p, xx, y2p, { sw: 0.25 });
  out += arrowV(xx, y1p, -1) + arrowV(xx, y2p, 1);
  out += label(xx - 1.9, (y1p + y2p) / 2, s, { size: 3.1, rot: -90 });
  return out;
}

function leader(h, y, lx, ly, num) {
  const x = mx(h), yy = my(y);
  return (
    line(x, yy, lx, ly, { sw: 0.25 }) +
    circle(lx, ly, 2.3, { fill: '#ffffff', stroke: INK, sw: 0.35 }) +
    text(lx, ly + 0.1, String(num), { size: 2.7, anchor: 'middle', weight: 'bold' }) +
    circle(x, yy, 0.65, { fill: INK, stroke: 'none' })
  );
}

function cross(h, y, size = 5) {
  const x = mx(h), yy = my(y);
  return (
    line(x - size, yy, x + size, yy, { sw: 0.25, dash: '2.2 1.2' }) +
    line(x, yy - size, x, yy + size, { sw: 0.25, dash: '2.2 1.2' })
  );
}

function centerlineH(h1, h2, y) {
  return lineM(h1, y, h2, y, { sw: 0.22, dash: '3 1 0.8 1' });
}
function centerlineV(h, y1, y2) {
  return lineM(h, y1, h, y2, { sw: 0.22, dash: '3 1 0.8 1' });
}

// Пружина в 2D (вертикальная, схематично)
function spring2D(h, y0, y1, od = 35, coils) {
  const x = mx(h), top = my(y1), bot = my(y0);
  const w = (od * V.s) / 2;
  const n = coils ?? Math.max(4, Math.round((y1 - y0) / 26));
  const step = (bot - top) / (n * 2);
  const pts = [[x - w, top]];
  for (let i = 1; i <= n * 2; i++) {
    pts.push([x + (i % 2 ? w : -w), top + step * i]);
  }
  let out = polyline(pts, { sw: 0.5 });
  out += line(x - w, top, x + w, top, { sw: 0.5 });
  out += line(x - w, bot, x + w, bot, { sw: 0.5 });
  out += circle(x - w, top, 0.35, { fill: INK, stroke: 'none' });
  out += circle(x + w, bot, 0.35, { fill: INK, stroke: 'none' });
  return out;
}

function nut2D(h, y, w = 19, hh = 9) {
  const x = mx(h), yy = my(y);
  return (
    rect(x - (w * V.s) / 2, yy - (hh * V.s) / 2, w * V.s, hh * V.s, {
      fill: MIDFILL,
      stroke: INK,
      sw: 0.4,
    }) +
    line(x - (w * V.s) / 2 + 0.6, yy - (hh * V.s) / 2, x - (w * V.s) / 2 + 0.6, yy + (hh * V.s) / 2, { sw: 0.25 }) +
    line(x + (w * V.s) / 2 - 0.6, yy - (hh * V.s) / 2, x + (w * V.s) / 2 - 0.6, yy + (hh * V.s) / 2, { sw: 0.25 })
  );
}

function stud2D(h, y0, y1) {
  return (
    rectM(h - 6, y0, h + 6, y1, { fill: LIGHT, stroke: INK, sw: 0.45 }) +
    lineM(h - 2.4, y0, h - 2.4, y1, { sw: 0.2, opacity: 0.55 }) +
    lineM(h + 2.4, y0, h + 2.4, y1, { sw: 0.2, opacity: 0.55 }) +
    centerlineV(h, y0 - 8, y1 + 8)
  );
}

function seat2D(h, y, w = 60, t = 6) {
  return rectM(h - w / 2, y, h + w / 2, y + t, { fill: MIDFILL, stroke: INK, sw: 0.4 });
}

// ---------------------------------------------------------------------------
// Параметры модели
// ---------------------------------------------------------------------------
const M = {
  frame: {
    x0: -300, x1: 300, z0: -250, z1: 250,
    h: 860, leg: 40, legX: 280, legZ: 230,
    topY0: 820, topY1: 860,
    plateY0: 802, plateY1: 820, plateX: 250, plateZ: 200,
    baseY0: 15, baseY1: 55, footY0: 0, footY1: 15,
  },
  table: { x: 250, z: 200, y0: 542, y1: 560 },
  sub: { x: 250, z: 200, y0: 432, y1: 450, winR: 125 },
  stud: { x: 220, z: 170, d: 12, y0: 432, y1: 830 },
  spring: { upperY0: 560, upperY1: 802, lowerY0: 450, lowerY1: 542, od: 35 },
  roller: { y: 515, z: 50, d: 35, w: 11, axle: 10 },
  cam: { cy: 394.5, R: 110, e: 3, t: 6, lobes: 2 },
  drill: {
    cy: 394.5,
    chuckX0: 3, chuckX1: 73, chuckD: 50,
    bodyX0: 73, bodyX1: 303, bodyD: 70,
    handleX0: 180, handleX1: 240, handleY0: 300, handleY1: 360,
  },
};

const camRmax = M.cam.R + M.cam.e;   // 113
const camRmin = M.cam.R - M.cam.e;   // 107
const camTop = M.cam.cy + camRmax;   // 507.5
const camBot = M.cam.cy - camRmax;   // 281.5

function camProfilePoints(steps = 240) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const ph = (2 * Math.PI * i) / steps;
    const r = M.cam.R + M.cam.e * Math.cos(M.cam.lobes * ph);
    pts.push([r * Math.sin(ph), M.cam.cy + r * Math.cos(ph)]);
  }
  return pts;
}

// ---------------------------------------------------------------------------
// Общие элементы листа
// ---------------------------------------------------------------------------
function borderAndBlocks(sheetTitle, sheetNo, viewName, body, opts = {}) {
  const tb = { x: 270, y: 205, w: 140, h: 82 };
  const lg = { x: 270, y: 12, w: 140, h: 188 };

  const legendItems = [
    'Столешница',
    'Подстолье',
    'Станина (рама)',
    'Шпилька M12',
    'Пружина верхняя',
    'Пружина нижняя',
    'Дрель',
    'Диск кулачковый',
    'Ролик 6202-2RS',
    'Кронштейн ролика',
    'Гайка / шайба',
    'Регулятор оборотов (в дрели)',
    'Опора резиновая',
    'Хомут дрели',
    'Оправка диска',
  ];

  let legend =
    rect(lg.x, lg.y, lg.w, lg.h, { fill: '#ffffff', stroke: INK, sw: 0.6 }) +
    text(lg.x + 6, lg.y + 8, 'ПОЗИЦИИ', { size: 4, weight: 'bold' });
  legendItems.forEach((name, i) => {
    const yy = lg.y + 20 + i * 10.6;
    legend +=
      circle(lg.x + 8, yy, 3.3, { fill: '#ffffff', stroke: INK, sw: 0.35 }) +
      text(lg.x + 8, yy + 0.1, String(i + 1), { size: 2.5, anchor: 'middle', weight: 'bold' }) +
      text(lg.x + 14, yy, name, { size: 2.85 });
  });

  const tx = tb.x, ty = tb.y;
  let title =
    rect(tx, ty, tb.w, tb.h, { fill: '#ffffff', stroke: INK, sw: 0.7 }) +
    line(tx, ty + 18, tx + tb.w, ty + 18, { sw: 0.45 }) +
    line(tx, ty + 33, tx + tb.w, ty + 33, { sw: 0.45 }) +
    line(tx, ty + 50, tx + tb.w, ty + 50, { sw: 0.45 }) +
    line(tx, ty + 65, tx + tb.w, ty + 65, { sw: 0.45 }) +
    line(tx + 88, ty + 33, tx + 88, ty + tb.h, { sw: 0.45 }) +
    text(tx + 6, ty + 11, 'ВИБРОСТОЛ', { size: 6.2, weight: 'bold' }) +
    text(tx + 6, ty + 27, 'Модель устройства', { size: 3.4 }) +
    text(tx + 6, ty + 42, 'Этап: формирование модели', { size: 2.8 }) +
    text(tx + 6, ty + 57, viewName, { size: 2.9, weight: 'bold' }) +
    text(tx + 6, ty + 72, 'Источник: эскиз stages/model/pics/common_idea.jpg', { size: 2.45 }) +
    text(tx + 92, ty + 39, 'Масштаб', { size: 2.5, fill: MID }) +
    text(tx + 92, ty + 46, '1:5', { size: 3.6, weight: 'bold' }) +
    text(tx + 92, ty + 57, 'Размеры, мм', { size: 2.35, fill: MID }) +
    text(tx + 92, ty + 73, `Лист ${sheetNo}`, { size: 3.2, weight: 'bold' }) +
    text(tx + 6, ty + 79, '27.10.2026   DeepSeek / OpenCode', { size: 2.35, fill: MID });

  let out = '';
  out += rect(5, 5, 410, 287, { fill: '#ffffff', stroke: INK, sw: 0.8 });
  out += rect(10, 10, 400, 277, { fill: 'none', stroke: INK, sw: 0.4 });
  out += text(135, opts.titleY ?? 25, sheetTitle, { size: 4.6, anchor: 'middle', weight: 'bold' });
  out += body;
  out += legend;
  out += title;
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

// ---------------------------------------------------------------------------
// Вид сбоку, разрез A–A (плоскость Z = 0, показана дальняя половина)
// ---------------------------------------------------------------------------
function drawSideView() {
  setView(150, 240, 'x');
  const g = [];

  // Рама: дальние стойки (Z = -230), верхняя обвязка, основание
  for (const x0 of [-300, 260]) {
    g.push(rectM(x0, M.frame.baseY1, x0 + 40, M.frame.topY1, { fill: '#fafafa', stroke: INK, sw: 0.55 }));
    g.push(rectM(x0, M.frame.footY0, x0 + 40, M.frame.footY1, { fill: MIDFILL, stroke: INK, sw: 0.45 }));
  }
  // верхняя балка вдоль X (дальняя)
  g.push(rectM(-300, M.frame.topY0, 300, M.frame.topY1, { fill: '#f6f6f6', stroke: INK, sw: 0.55 }));
  // нижняя балка вдоль X (дальняя)
  g.push(rectM(-300, M.frame.baseY0, 300, M.frame.baseY1, { fill: '#f6f6f6', stroke: INK, sw: 0.5 }));
  // верхняя плита (разрез)
  g.push(rectM(-250, M.frame.plateY0, 250, M.frame.plateY1, { fill: 'url(#hatch)', stroke: INK, sw: 0.55 }));

  // Шпильки и пружины (дальние, Z = -170)
  for (const h of [-220, 220]) {
    g.push(stud2D(h, M.stud.y0, M.stud.y1));
    g.push(nut2D(h, M.stud.y0, 19, 9));
    g.push(nut2D(h, M.stud.y1 - 5, 19, 9));
    g.push(seat2D(h, M.table.y0, 60, 6));
    g.push(seat2D(h, M.table.y0 - 24, 60, 6));
    g.push(seat2D(h, M.sub.y1, 60, 6));
    g.push(seat2D(h, M.frame.plateY0 - 6, 60, 6));
    g.push(spring2D(h, M.spring.upperY0, M.spring.upperY1, 35));
    g.push(spring2D(h, M.spring.lowerY0, M.spring.lowerY1, 35));
  }

  // Столешница (разрез)
  g.push(rectM(-250, M.table.y0, 250, M.table.y1, { fill: 'url(#hatch)', stroke: INK, sw: 0.7 }));
  g.push(lineM(-250, M.table.y0, 250, M.table.y0, { sw: 0.7 }));
  g.push(lineM(-250, M.table.y1, 250, M.table.y1, { sw: 0.7 }));

  // Подстолье: две части разреза вокруг окна Ø250
  g.push(rectM(-250, M.sub.y0, -M.sub.winR, M.sub.y1, { fill: 'url(#hatch)', stroke: INK, sw: 0.65 }));
  g.push(rectM(M.sub.winR, M.sub.y0, 250, M.sub.y1, { fill: 'url(#hatch)', stroke: INK, sw: 0.65 }));

  // Кам/диск в разрезе: тонкая пластина 6 мм, высота 2*Rmax
  g.push(rectM(-3, camBot, 3, camTop, { fill: 'url(#hatch)', stroke: INK, sw: 0.65 }));
  g.push(centerlineV(0, camBot - 12, camTop + 12));
  g.push(cross(0, M.cam.cy, 6));

  // Оправка и патрон дрели
  g.push(rectM(3, M.drill.cy - 25, M.drill.chuckX1, M.drill.cy + 25, { fill: '#eeeeee', stroke: INK, sw: 0.5 }));
  g.push(rectM(M.drill.bodyX0, M.drill.cy - 35, M.drill.bodyX1, M.drill.cy + 35, { fill: '#f7f7f7', stroke: INK, sw: 0.55 }));
  // задняя часть корпуса — скругление
  g.push(path(`M ${f(mx(303))} ${f(my(359.5))} Q ${f(mx(312))} ${f(my(394.5))} ${f(mx(303))} ${f(my(429.5))}`, { sw: 0.5, fill: 'none' }));
  g.push(centerlineV(0, M.drill.cy, M.drill.cy));
  // рукоятка
  g.push(polyM([[180, 360], [240, 360], [240, 305], [225, 295], [195, 295], [180, 305]], { fill: '#ededed', stroke: INK, sw: 0.5 }));
  g.push(rectM(205, 345, 222, 355, { fill: MIDFILL, stroke: INK, sw: 0.4 })); // курок
  g.push(circleM(232, 350, 4.5, { fill: '#ffffff', stroke: INK, sw: 0.45 })); // регулятор
  // хомут крепления дрели к подстолью
  g.push(rectM(130, 432, 166, 446, { fill: MIDFILL, stroke: INK, sw: 0.45 }));
  g.push(rectM(132, 429.5, 164, 432, { fill: LIGHT, stroke: INK, sw: 0.4 }));
  // шнур
  g.push(path(`M ${f(mx(310))} ${f(my(420))} C ${f(mx(335))} ${f(my(430))}, ${f(mx(340))} ${f(my(380))}, ${f(mx(320))} ${f(my(350))}`, { sw: 0.35, dash: '1.5 1' }));

  // Дальний ролик (Z = -50), виден в разрезе за диском
  const rY = M.roller.y;
  const rr = M.roller.d / 2;
  g.push(rectM(-5.5, rY - rr, 5.5, rY + rr, { fill: MIDFILL, stroke: INK, sw: 0.5 }));
  // скрытая нижняя часть ролика за диском
  g.push(rectM(-5.5, rY - rr, 5.5, camTop, { fill: '#ffffff', stroke: INK, sw: 0.35, dash: '1.6 1' }));
  g.push(circleM(0, rY, 2.5, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
  // кронштейн
  g.push(rectM(-22, 532.5, 22, 542, { fill: '#ececec', stroke: INK, sw: 0.45 }));
  g.push(lineM(0, rY, 0, 532.5, { sw: 0.3, dash: '1.5 1' }));

  // Подписи и размеры
  g.push(dimV(-320, 0, 860, '860', -300));
  g.push(dimV(-350, 0, 560, '560', -250));
  g.push(dimV(-380, 0, 450, '450', -250));
  g.push(dimV(-410, 0, 515, '515', -250));
  g.push(dimV(-440, 0, 394.5, '394,5', -250));
  g.push(dimH(-300, 300, -35, '600', 15));
  g.push(dimH(-250, 250, -60, '500', 432));
  g.push(dimH(-220, 220, -85, '440', 432));

  // Выноски
  const L = [
    [1, 200, 551, 245, 75],
    [2, 200, 441, 245, 92],
    [3, -280, 700, 32, 78],
    [4, -220, 650, 32, 125],
    [5, -220, 700, 32, 165],
    [6, -220, 490, 32, 200],
    [7, 280, 394.5, 245, 143],
    [8, 0, 430, 245, 177],
    [9, 0, 515, 245, 198],
    [10, 10, 535, 245, 217],
    [11, -220, 820, 32, 55],
    [12, 232, 350, 245, 160],
    [13, -280, 7, 32, 240],
    [14, 148, 432, 245, 126],
  ];
  for (const [num, h, y, lx, ly] of L) g.push(leader(h, y, lx, ly, num));

  return borderAndBlocks(
    'Вид сбоку. Разрез А–А',
    1,
    'Вид сбоку (разрез по оси)',
    g.join('')
  );
}

// ---------------------------------------------------------------------------
// Вид слева (взгляд вдоль оси дрели, со стороны патрона)
// ---------------------------------------------------------------------------
function drawLeftView() {
  setView(150, 240, 'z');
  const g = [];

  // Рама: стойки (передняя/задняя совпадают), верхняя обвязка, основание
  for (const z0 of [-250, 210]) {
    g.push(rectM(z0, M.frame.baseY1, z0 + 40, M.frame.topY1, { fill: '#fafafa', stroke: INK, sw: 0.55 }));
    g.push(rectM(z0, M.frame.footY0, z0 + 40, M.frame.footY1, { fill: MIDFILL, stroke: INK, sw: 0.45 }));
  }
  g.push(rectM(-250, M.frame.topY0, 250, M.frame.topY1, { fill: '#f6f6f6', stroke: INK, sw: 0.55 }));
  g.push(rectM(-250, M.frame.baseY0, 250, M.frame.baseY1, { fill: '#f6f6f6', stroke: INK, sw: 0.5 }));
  g.push(rectM(-200, M.frame.plateY0, 200, M.frame.plateY1, { fill: 'url(#hatch)', stroke: INK, sw: 0.55 }));

  // Шпильки и пружины
  for (const h of [-170, 170]) {
    g.push(stud2D(h, M.stud.y0, M.stud.y1));
    g.push(nut2D(h, M.stud.y0, 19, 9));
    g.push(nut2D(h, M.stud.y1 - 5, 19, 9));
    g.push(seat2D(h, M.table.y0, 60, 6));
    g.push(seat2D(h, M.table.y0 - 24, 60, 6));
    g.push(seat2D(h, M.sub.y1, 60, 6));
    g.push(seat2D(h, M.frame.plateY0 - 6, 60, 6));
    g.push(spring2D(h, M.spring.upperY0, M.spring.upperY1, 35));
    g.push(spring2D(h, M.spring.lowerY0, M.spring.lowerY1, 35));
  }

  // Столешница
  g.push(rectM(-200, M.table.y0, 200, M.table.y1, { fill: 'url(#hatch)', stroke: INK, sw: 0.7 }));
  g.push(lineM(-200, M.table.y0, 200, M.table.y0, { sw: 0.7 }));
  g.push(lineM(-200, M.table.y1, 200, M.table.y1, { sw: 0.7 }));

  // Подстолье: две части вокруг окна
  g.push(rectM(-200, M.sub.y0, -M.sub.winR, M.sub.y1, { fill: 'url(#hatch)', stroke: INK, sw: 0.65 }));
  g.push(rectM(M.sub.winR, M.sub.y0, 200, M.sub.y1, { fill: 'url(#hatch)', stroke: INK, sw: 0.65 }));

  // Дрель за диском (скрытая)
  g.push(circleM(0, M.cam.cy, 35, { stroke: INK, sw: 0.35, dash: '2 1.2' }));
  g.push(rectM(150, 300, 210, 360, { fill: 'none', stroke: INK, sw: 0.35, dash: '2 1.2' }));
  g.push(textM(0, 235, 'дрель за диском', { size: 2.8, anchor: 'middle', fill: MID }));

  // Диск: двухлепестковый профиль
  const prof = camProfilePoints(240);
  g.push(polyM(prof, { fill: '#e9e9e9', stroke: INK, sw: 0.75 }));
  g.push(circleM(0, M.cam.cy, 10, { fill: '#ffffff', stroke: INK, sw: 0.55 }));
  g.push(circleM(0, M.cam.cy, 3, { fill: INK, stroke: 'none' }));
  g.push(centerlineH(-150, 150, M.cam.cy));
  g.push(centerlineV(0, camBot - 25, camTop + 25));
  g.push(cross(0, M.cam.cy, 7));
  // метки лепестков
  g.push(textM(0, camTop + 16, 'max', { size: 2.7, anchor: 'middle', fill: RED, weight: 'bold' }));
  g.push(textM(0, camBot - 16, 'max', { size: 2.7, anchor: 'middle', fill: RED, weight: 'bold' }));
  g.push(textM(-camRmin - 20, M.cam.cy, 'min', { size: 2.7, anchor: 'middle', fill: RED }));
  g.push(textM(camRmin + 20, M.cam.cy, 'min', { size: 2.7, anchor: 'middle', fill: RED }));

  // Ролики с кронштейнами
  for (const h of [-M.roller.z, M.roller.z]) {
    // кронштейн
    g.push(rectM(h - 37, 475, h + 37, 542, { fill: '#f0f0f0', stroke: INK, sw: 0.5 }));
    g.push(circleM(h, M.roller.y, 36, { fill: 'none', stroke: INK, sw: 0.35, dash: '2 1.2' }));
    // ролик 6202
    g.push(circleM(h, M.roller.y, 17.5, { fill: MIDFILL, stroke: INK, sw: 0.55 }));
    g.push(circleM(h, M.roller.y, 7.5, { fill: '#ffffff', stroke: INK, sw: 0.45 }));
    g.push(circleM(h, M.roller.y, 2.5, { fill: INK, stroke: 'none' }));
    g.push(lineM(h - 37, 542, h + 37, 542, { sw: 0.5 }));
    // болт крепления кронштейна
    g.push(circleM(h - 28, 528, 2.2, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
    g.push(circleM(h + 28, 528, 2.2, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
  }

  // Размеры
  g.push(dimV(-310, 0, 860, '860', -270));
  g.push(dimV(-345, 0, 560, '560', -220));
  g.push(dimV(-380, 0, 450, '450', -220));
  g.push(dimV(-415, 0, 515, '515', -120));
  g.push(dimV(-450, 0, 394.5, '394,5', -120));
  g.push(dimH(-250, 250, -35, '500', 15));
  g.push(dimH(-200, 200, -60, '400', 432));
  g.push(dimH(-170, 170, -85, '340', 432));
  g.push(dimH(-50, 50, -110, '100', 475));
  g.push(dimH(-camRmin, camRmin, -135, '214', camBot));

  g.push(text(135, 33, '2 лепестка через 180°, центральная симметрия', { size: 2.9, anchor: 'middle', fill: MID }));
  g.push(text(135, 39, 'Aст = 3…10 мм;  Rmax/Rmin = 113/107;  e = 3 (средний диск)', { size: 2.9, anchor: 'middle', fill: MID }));
  g.push(text(135, 45, 'f = n/30;  150…450 об/мин', { size: 2.9, anchor: 'middle', fill: MID }));

  // Выноски
  const L = [
    [1, 170, 551, 245, 70],
    [2, 170, 441, 245, 88],
    [3, -230, 700, 32, 75],
    [4, -170, 650, 32, 120],
    [5, -170, 700, 32, 158],
    [6, -170, 490, 32, 195],
    [8, 0, 500, 245, 110],
    [9, 50, 515, 245, 145],
    [10, 50, 535, 245, 165],
    [11, -170, 820, 32, 50],
    [13, -230, 7, 32, 235],
  ];
  for (const [num, h, y, lx, ly] of L) g.push(leader(h, y, lx, ly, num));

  return borderAndBlocks('Вид слева', 2, 'Вид слева', g.join(''));
}

// ---------------------------------------------------------------------------
// Изометрия
// ---------------------------------------------------------------------------
const ISO = {
  elev: 0.60,
  target: { x: 0, y: 430, z: 0 },
  scale: 0.17,
  cx: 137,
  cy: 105,
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

// Камера: направление взгляда — к цели. Для каждого листа можно задать своё.
let viewF = vnorm({ x: -0.5, y: -ISO.elev, z: -1 });
let viewR = vnorm(vcross(viewF, { x: 0, y: 1, z: 0 }));
let viewU = vcross(viewR, viewF);

function setIsoCamera(elev, x = -0.5) {
  viewF = vnorm({ x, y: -elev, z: -1 });
  viewR = vnorm(vcross(viewF, { x: 0, y: 1, z: 0 }));
  viewU = vcross(viewR, viewF);
}

function isoRaw(p) {
  const q = vsub(p, ISO.target);
  return { x: vdot(q, viewR), y: -vdot(q, viewU) };
}

// авто-подгонка под область листа
let ISO_FIT = { s: ISO.scale, tx: ISO.cx, ty: ISO.cy };

function fitIso(points, opts = {}) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of points) {
    const q = isoRaw(p);
    minX = Math.min(minX, q.x); maxX = Math.max(maxX, q.x);
    minY = Math.min(minY, q.y); maxY = Math.max(maxY, q.y);
  }
  const availW = opts.w ?? 240;
  const availH = opts.h ?? 166;
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
    isoPoly(sideX, { fill: 'none', stroke: st, sw: o.sw ?? 0.4, dash: o.dash ?? '2 1.2' }) +
    isoPoly(sideZ, { fill: 'none', stroke: st, sw: o.sw ?? 0.4, dash: o.dash ?? '2 1.2' }) +
    isoPoly(top, { fill: 'none', stroke: st, sw: o.sw ?? 0.4, dash: o.dash ?? '2 1.2' })
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
  // боковая поверхность
  const band = [];
  for (let i = 0; i < a.length; i++) band.push(a[i]);
  for (let i = b.length - 1; i >= 0; i--) band.push(b[i]);
  out += isoPoly(band, { fill: o.side ?? MIDFILL, stroke: 'none', opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(a, { fill: o.front ?? '#fafafa', stroke: o.stroke ?? INK, sw: o.sw ?? 0.4, opacity: o.opacity, fillOpacity: o.fillOpacity });
  out += isoPoly(b, { fill: 'none', stroke: o.stroke ?? INK, sw: 0.3, dash: '1.4 1', opacity: 0.6 });
  return out;
}

function isoSpring(x, z, y0, y1, r, coils = 7) {
  const pts = [];
  const steps = coils * 24;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const a = t * coils * 2 * Math.PI;
    pts.push({ x: x + r * Math.cos(a), y: y0 + (y1 - y0) * t, z: z + r * Math.sin(a) });
  }
  return isoPath(pts, { sw: 0.55, stroke: INK });
}

function isoCam() {
  const frontX = -M.cam.t / 2;
  const backX = M.cam.t / 2;
  const prof = camProfilePoints(120);
  const front = prof.map(([z, y]) => ({ x: frontX, y, z }));
  const back = prof.map(([z, y]) => ({ x: backX, y, z }));
  let out = '';
  // боковая поверхность
  const rim = [];
  for (let i = 0; i < front.length; i++) rim.push(front[i]);
  for (let i = back.length - 1; i >= 0; i--) rim.push(back[i]);
  out += isoPoly(rim, { fill: '#b8b8b8', stroke: 'none' });
  out += isoPoly(front, { fill: '#ededed', stroke: INK, sw: 0.55 });
  // ступица/отверстие
  const hole = isoCirclePts(frontX - 0.4, M.cam.cy, 0, 10, 36);
  out += isoPoly(hole, { fill: '#ffffff', stroke: INK, sw: 0.4 });
  out += isoPoly(isoCirclePts(frontX - 0.5, M.cam.cy, 0, 3.2, 24), { fill: INK, stroke: 'none' });
  return out;
}

function drawIso() {
  setIsoCamera(0.6, -0.5);
  // Собираем точки для авто-масштаба
  const pts = [];
  const add = (x, y, z) => pts.push({ x, y, z });
  for (const x of [-300, 260]) for (const z of [-250, 210]) for (const y of [0, 860]) add(x + 20, y, z + 20);
  for (const x of [-250, 250]) for (const z of [-200, 200]) for (const y of [432, 560, 802]) add(x, y, z);
  add(-320, 0, -270); add(320, 0, 270);
  add(303, M.drill.cy + 35, 0); add(303, M.drill.cy - 35, 0);
  add(0, M.cam.cy + camRmax, 0); add(0, M.cam.cy - camRmax, 0);
  add(0, 515, 50); add(0, 515, -50);
  fitIso(pts, { h: 145, cy: 122 });

  const g = [];

  // Задние стойки и обвязка
  const legs = [
    [-300, -250], [260, -250], [-300, 210], [260, 210],
  ];
  // сортировка по глубине: дальние раньше
  legs.sort((a, b) => (a[0] + a[1]) - (b[0] + b[1]));
  for (const [x, z] of legs) {
    const ghost = x === 260 && z === 210;
    g.push(isoBox(x, x + 40, 0, 15, z, z + 40, { fill: 'none', top: MIDFILL, side: '#cfcfcf', side2: '#bdbdbd' }));
    if (ghost) {
      g.push(isoGhostBox(x, x + 40, 15, 860, z, z + 40, { sw: 0.42, dash: '2 1.2' }));
    } else {
      g.push(isoBox(x, x + 40, 15, 860, z, z + 40, { fill: 'none', top: '#f6f6f6', side: '#ededed', side2: '#d6d6d6' }));
    }
  }
  // верхняя обвязка
  g.push(isoBox(-300, 300, 820, 860, -250, -210, { top: '#f4f4f4', side: '#e6e6e6', side2: '#d2d2d2' }));
  g.push(isoBox(-300, 300, 820, 860, 210, 250, { top: '#f4f4f4', side: '#e6e6e6', side2: '#d2d2d2' }));
  g.push(isoBox(-300, -260, 820, 860, -210, 210, { top: '#f4f4f4', side: '#e6e6e6', side2: '#d2d2d2' }));
  g.push(isoBox(260, 300, 820, 860, -210, 210, { top: '#f4f4f4', side: '#e6e6e6', side2: '#d2d2d2' }));
  // нижняя обвязка
  g.push(isoBox(-300, 300, 15, 55, -250, -210, { top: '#f4f4f4', side: '#e6e6e6', side2: '#d2d2d2' }));
  g.push(isoBox(-300, 300, 15, 55, 210, 250, { top: '#f4f4f4', side: '#e6e6e6', side2: '#d2d2d2' }));

  // Верхняя плита
  g.push(isoBox(-250, 250, 802, 820, -200, 200, {
    top: '#e7eef7', side: '#cdd9e8', side2: '#b9c8dc', sw: 0.4,
  }));

  // Подстолье с окном — контуром, чтобы был виден привод
  g.push(isoGhostBox(-250, 250, 432, 450, -200, 200, { sw: 0.45 }));
  // контур окна на верхней плоскости
  const win = isoCirclePts(0, 450, 0, M.sub.winR, 64);
  g.push(isoPath(win, { sw: 0.35, dash: '2 1', stroke: MID }));

  // Шпильки, пружины, гайки
  for (const x of [-220, 220]) {
    for (const z of [-170, 170]) {
      g.push(isoBox(x - 6, x + 6, 432, 830, z - 6, z + 6, {
        top: '#ececec', side: '#d5d5d5', side2: '#c2c2c2', sw: 0.25,
      }));
      g.push(isoSpring(x, z, M.spring.upperY0, M.spring.upperY1, 17.5, 8));
      g.push(isoSpring(x, z, M.spring.lowerY0, M.spring.lowerY1, 17.5, 4));
      g.push(isoBox(x - 9.5, x + 9.5, 432, 441, z - 9.5, z + 9.5, { top: MIDFILL, side: '#c9c9c9', side2: '#b5b5b5' }));
      g.push(isoBox(x - 9.5, x + 9.5, 821, 830, z - 9.5, z + 9.5, { top: MIDFILL, side: '#c9c9c9', side2: '#b5b5b5' }));
    }
  }

  // Дрель под подстольем
  g.push(isoCylinderX(M.drill.bodyX0, M.drill.bodyX1, M.drill.cy, 0, 35, { front: '#fafafa', side: '#dcdcdc', sw: 0.45 }));
  g.push(isoCylinderX(M.drill.chuckX0, M.drill.chuckX1, M.drill.cy, 0, 25, { front: '#f0f0f0', side: '#cccccc', sw: 0.4 }));
  // рукоятка
  g.push(isoBox(180, 240, 300, 360, -22, 22, { top: '#f0f0f0', side: '#e0e0e0', side2: '#cccccc' }));
  // хомут
  g.push(isoBox(130, 166, 429, 446, -44, 44, { top: '#d9d9d9', side: '#c6c6c6', side2: '#b5b5b5' }));

  // Ролики и кронштейны: дальний, затем диск, затем ближний
  const rollerIso = (z) =>
    isoBox(-37, 37, 475, 542, z - 12, z + 12, {
      top: '#e8e8e8', side: '#d2d2d2', side2: '#bdbdbd', fillOpacity: 0.85, sw: 0.35,
    }) +
    isoCylinderX(-5.5, 5.5, M.roller.y, z, 17.5, { front: '#e6e6e6', side: '#c9c9c9', sw: 0.4 }) +
    isoCylinderX(-7, 7, M.roller.y, z, 4, { front: '#ffffff', side: '#dddddd', sw: 0.3 });

  g.push(rollerIso(-M.roller.z));
  g.push(isoCam());
  g.push(rollerIso(M.roller.z));

  // Столешница — контуром, чтобы был виден привод
  g.push(isoGhostBox(-250, 250, 542, 560, -200, 200, { sw: 0.5, dash: '2.4 1.4' }));

  // Выноски (координаты подписей — на листе)
  const callouts = [
    [1, 250, 551, 0, 238, 48],
    [2, 250, 441, 0, 238, 68],
    [3, -280, 700, -250, 42, 62],
    [4, -220, 650, -170, 42, 105],
    [5, -220, 700, -170, 42, 140],
    [6, -220, 490, -170, 42, 175],
    [7, 280, 394.5, 0, 248, 120],
    [8, 0, 500, 0, 248, 150],
    [9, 0, 515, 50, 248, 180],
    [10, 20, 535, 50, 248, 200],
    [11, -220, 826, -170, 42, 40],
    [12, 210, 350, 0, 248, 95],
    [13, -280, 8, -250, 42, 220],
    [14, 148, 435, 0, 248, 75],
    [15, 0, 420, 0, 248, 135],
  ];
  for (const [num, x, y, z, lx, ly] of callouts) {
    const p = iso({ x, y, z });
    g.push(line(p[0], p[1], lx, ly, { sw: 0.25 }));
    g.push(circle(lx, ly, 2.3, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
    g.push(text(lx, ly + 0.1, String(num), { size: 2.7, anchor: 'middle', weight: 'bold' }));
    g.push(circle(p[0], p[1], 0.65, { fill: INK, stroke: 'none' }));
  }

  g.push(text(135, 14, 'Изометрия. Столешница, подстолье и ближняя правая стойка — контуром', { size: 3.0, anchor: 'middle', fill: MID }));
  g.push(text(135, 20, 'М 1:5.  Размеры и параметры — в Report.md', { size: 2.9, anchor: 'middle', fill: MID }));

  return borderAndBlocks('Изометрия', 3, 'Изометрия', g.join(''));
}

// ---------------------------------------------------------------------------
// Изометрия узла привода (крупно)
// ---------------------------------------------------------------------------
function drawDriveIso() {
  setIsoCamera(0.9, -0.5);
  const pts = [];
  const add = (x, y, z) => pts.push({ x, y, z });
  for (const x of [-250, 250]) for (const z of [-200, 200]) for (const y of [432, 542, 560]) add(x, y, z);
  for (const x of [-220, 220]) for (const z of [-170, 170]) for (const y of [432, 560]) add(x, y, z);
  add(303, M.drill.cy + 35, 0); add(303, M.drill.cy - 35, 0);
  add(0, M.cam.cy + camRmax, 0); add(0, M.cam.cy - camRmax, 0);
  add(0, 515, 50); add(0, 515, -50);
  fitIso(pts, { h: 145, cy: 122 });

  const g = [];

  // Подстолье контуром
  g.push(isoGhostBox(-250, 250, 432, 450, -200, 200, { sw: 0.45 }));
  g.push(isoPath(isoCirclePts(0, 450, 0, M.sub.winR, 64), { sw: 0.35, dash: '2 1', stroke: MID }));

  // Шпильки, нижние пружины, гайки
  for (const x of [-220, 220]) {
    for (const z of [-170, 170]) {
      g.push(isoBox(x - 6, x + 6, 432, 560, z - 6, z + 6, {
        top: '#ececec', side: '#d5d5d5', side2: '#c2c2c2', sw: 0.25,
      }));
      g.push(isoSpring(x, z, M.spring.lowerY0, M.spring.lowerY1, 17.5, 5));
      g.push(isoBox(x - 9.5, x + 9.5, 432, 441, z - 9.5, z + 9.5, { top: MIDFILL, side: '#c9c9c9', side2: '#b5b5b5' }));
    }
  }

  // Дрель
  g.push(isoCylinderX(M.drill.bodyX0, M.drill.bodyX1, M.drill.cy, 0, 35, { front: '#fafafa', side: '#dcdcdc', sw: 0.45 }));
  g.push(isoCylinderX(M.drill.chuckX0, M.drill.chuckX1, M.drill.cy, 0, 25, { front: '#f0f0f0', side: '#cccccc', sw: 0.4 }));
  g.push(isoBox(180, 240, 300, 360, -22, 22, { top: '#f0f0f0', side: '#e0e0e0', side2: '#cccccc' }));
  g.push(isoBox(130, 166, 429, 446, -44, 44, { top: '#d9d9d9', side: '#c6c6c6', side2: '#b5b5b5' }));
  // регулятор на рукоятке
  g.push(isoCylinderX(228, 238, 350, 18, 5, { front: '#ffffff', side: '#dddddd', sw: 0.3 }));

  // Ролики/кронштейны и диск
  const rollerIso = (z) =>
    isoBox(-37, 37, 475, 542, z - 12, z + 12, {
      top: '#e8e8e8', side: '#d2d2d2', side2: '#bdbdbd', fillOpacity: 0.85, sw: 0.35,
    }) +
    isoCylinderX(-5.5, 5.5, M.roller.y, z, 17.5, { front: '#e6e6e6', side: '#c9c9c9', sw: 0.4 }) +
    isoCylinderX(-7, 7, M.roller.y, z, 4, { front: '#ffffff', side: '#dddddd', sw: 0.3 });

  g.push(rollerIso(-M.roller.z));
  g.push(isoCam());
  g.push(rollerIso(M.roller.z));

  // Столешница контуром
  g.push(isoGhostBox(-250, 250, 542, 560, -200, 200, { sw: 0.5, dash: '2.4 1.4' }));

  // Выноски
  const callouts = [
    [1, 250, 551, 0, 242, 55],
    [2, 250, 441, 0, 242, 75],
    [4, 220, 520, 170, 30, 95],
    [6, 220, 470, 170, 30, 130],
    [7, 280, 394.5, 0, 242, 112],
    [8, 0, 500, 0, 242, 150],
    [9, 0, 515, 50, 242, 180],
    [10, 20, 535, 50, 242, 200],
    [11, 220, 432, 170, 30, 55],
    [12, 232, 350, 18, 242, 92],
    [14, 148, 435, 0, 242, 105],
    [15, 0, 394.5, 0, 242, 132],
  ];
  for (const [num, x, y, z, lx, ly] of callouts) {
    const p = iso({ x, y, z });
    g.push(line(p[0], p[1], lx, ly, { sw: 0.25 }));
    g.push(circle(lx, ly, 2.3, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
    g.push(text(lx, ly + 0.1, String(num), { size: 2.7, anchor: 'middle', weight: 'bold' }));
    g.push(circle(p[0], p[1], 0.65, { fill: INK, stroke: 'none' }));
  }

  g.push(text(135, 33, 'Узел привода. Станина, верхние пружины и опоры не показаны', { size: 3.0, anchor: 'middle', fill: MID }));
  g.push(text(135, 39, 'Столешница и подстолье — контуром', { size: 2.9, anchor: 'middle', fill: MID }));

  return borderAndBlocks('Изометрия узла привода', 4, 'Изометрия узла привода', g.join(''));
}

// ---------------------------------------------------------------------------
// Изометрия узла привода: фрагмент столешницы/подстолья + привод
// ---------------------------------------------------------------------------
function drawDriveIsoDetail() {
  setIsoCamera(0.9, -0.5);
  const pts = [];
  const add = (x, y, z) => pts.push({ x, y, z });
  for (const x of [-200, 200]) for (const z of [-150, 150]) for (const y of [432, 542, 560]) add(x, y, z);
  add(303, M.drill.cy + 35, 0); add(303, M.drill.cy - 35, 0);
  add(0, M.cam.cy + camRmax, 0); add(0, M.cam.cy - camRmax, 0);
  add(0, 515, 50); add(0, 515, -50);
  fitIso(pts, { h: 145, cy: 122 });

  const g = [];

  // Фрагмент столешницы и подстолья — контуром
  g.push(isoGhostBox(-200, 200, 542, 560, -150, 150, { sw: 0.5, dash: '2.4 1.4' }));
  g.push(isoGhostBox(-200, 200, 432, 450, -150, 150, { sw: 0.45 }));
  g.push(isoPath(isoCirclePts(0, 450, 0, M.sub.winR, 64), { sw: 0.35, dash: '2 1', stroke: MID }));

  // Дрель
  g.push(isoCylinderX(M.drill.bodyX0, M.drill.bodyX1, M.drill.cy, 0, 35, { front: '#fafafa', side: '#dcdcdc', sw: 0.45 }));
  g.push(isoCylinderX(M.drill.chuckX0, M.drill.chuckX1, M.drill.cy, 0, 25, { front: '#f0f0f0', side: '#cccccc', sw: 0.4 }));
  g.push(isoBox(180, 240, 300, 360, -22, 22, { top: '#f0f0f0', side: '#e0e0e0', side2: '#cccccc' }));
  g.push(isoBox(130, 166, 429, 446, -44, 44, { top: '#d9d9d9', side: '#c6c6c6', side2: '#b5b5b5' }));
  g.push(isoCylinderX(228, 238, 350, 18, 5, { front: '#ffffff', side: '#dddddd', sw: 0.3 }));

  // Ролики/кронштейны и диск
  const rollerIso = (z) =>
    isoBox(-37, 37, 475, 542, z - 12, z + 12, {
      top: '#e8e8e8', side: '#d2d2d2', side2: '#bdbdbd', fillOpacity: 0.85, sw: 0.35,
    }) +
    isoCylinderX(-5.5, 5.5, M.roller.y, z, 17.5, { front: '#e6e6e6', side: '#c9c9c9', sw: 0.4 }) +
    isoCylinderX(-7, 7, M.roller.y, z, 4, { front: '#ffffff', side: '#dddddd', sw: 0.3 });

  g.push(rollerIso(-M.roller.z));
  g.push(isoCam());
  g.push(rollerIso(M.roller.z));

  // Выноски
  const callouts = [
    [1, 200, 551, 0, 245, 55],
    [2, 200, 441, 0, 245, 75],
    [7, 280, 394.5, 0, 245, 105],
    [8, 0, 500, 0, 245, 130],
    [9, 0, 515, 50, 245, 158],
    [10, 20, 535, 50, 245, 182],
    [12, 232, 350, 18, 245, 92],
    [14, 148, 435, 0, 245, 118],
    [15, 0, 394.5, 0, 245, 145],
  ];
  for (const [num, x, y, z, lx, ly] of callouts) {
    const p = iso({ x, y, z });
    g.push(line(p[0], p[1], lx, ly, { sw: 0.25 }));
    g.push(circle(lx, ly, 2.3, { fill: '#ffffff', stroke: INK, sw: 0.35 }));
    g.push(text(lx, ly + 0.1, String(num), { size: 2.7, anchor: 'middle', weight: 'bold' }));
    g.push(circle(p[0], p[1], 0.65, { fill: INK, stroke: 'none' }));
  }

  g.push(text(135, 33, 'Узел привода. Фрагменты столешницы и подстолья — контуром', { size: 3.0, anchor: 'middle', fill: MID }));
  g.push(text(135, 39, 'Пружины, станина и опоры не показаны', { size: 2.9, anchor: 'middle', fill: MID }));

  return borderAndBlocks('Изометрия узла привода', 4, 'Изометрия узла привода', g.join(''));
}

// ---------------------------------------------------------------------------
// Запись
// ---------------------------------------------------------------------------
const side = sheetSVG('Вибростол — вид сбоку', drawSideView());
const left = sheetSVG('Вибростол — вид слева', drawLeftView());
const isoSheet = sheetSVG('Вибростол — изометрия', drawIso());

fs.writeFileSync(nodePath.join(OUT, 'side_view.svg'), side, 'utf8');
fs.writeFileSync(nodePath.join(OUT, 'left_view.svg'), left, 'utf8');
fs.writeFileSync(nodePath.join(OUT, 'isometric.svg'), isoSheet, 'utf8');

console.log('written:');
for (const n of ['side_view.svg', 'left_view.svg', 'isometric.svg']) {
  console.log(' ', nodePath.join(OUT, n), fs.statSync(nodePath.join(OUT, n)).size, 'bytes');
}
