"""Листы эскизов A3 этапа fix11: проекции из модели (HLR FreeCAD), размеры,
выноски, спецификация, кожух и кулачок.

Запуск:
    freecadcmd draw_sheet.py [--force]

Кэш проекций: cad/cache/views_v7.json (наборы full и open).
"""

import csv
import json
import math
import os
import sys

import FreeCAD as App
import Part
import Drawing

import model
from params import P

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
STAGE = os.path.dirname(HERE)
FIG = os.path.join(STAGE, "fig")
PIC = os.path.join(STAGE, "pic")
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(FIG, exist_ok=True)
os.makedirs(PIC, exist_ok=True)

FORCE = "--force" in sys.argv
S = 1.0 / 3.0      # 1:3
FONT = "DejaVu Sans, Arial, sans-serif"

# геометрия листа
XA, ZBASE = 26.0, 144.67         # передний вид: X экрана, база Z=0
XB = 112.0                       # вид слева: начало по X
XT, YT = 24.0, 252.0             # вид сверху: начало и база Y=0

VIEW_DEF = {
    "front": dict(dir=(-1, 0, 0)),
    "side":  dict(dir=(0, -1, 0)),
    "top":   dict(dir=(0, 0, 1)),
    "iso":   dict(dir=(-1, -1, 1)),
}


# ----------------------------------------------------------------------------
# проекции (кэш)
# ----------------------------------------------------------------------------
HIDE_OPEN = ("shield", "shield_screws")


def project_all():
    cache = os.path.join(CACHE, "views_v9.json")
    if os.path.exists(cache) and not FORCE:
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    parts, groups, cams = model.build_assembly()
    sets = {
        "full": [i["shape"] for i in parts.values()],
        "open": [i["shape"] for k, i in parts.items() if k not in HIDE_OPEN],
        "frame": [parts["frame"]["shape"]],
    }
    data = {}
    for setname, shapes in sets.items():
        comp = Part.makeCompound(shapes)
        data[setname] = {}
        for name, vd in VIEW_DEF.items():
            out = Drawing.project(comp, App.Vector(*vd["dir"]))
            vis = out[0]
            polys = []
            for e in vis.Edges:
                try:
                    cname = e.Curve.__class__.__name__
                    if cname == "Line":
                        n = 2
                    elif e.isClosed():
                        n = 48
                    else:
                        n = 20
                    pts = e.discretize(n)
                except Exception:
                    continue
                if len(pts) < 2:
                    continue
                polys.append([[round(p.x, 3), round(p.y, 3)] for p in pts])
            data[setname][name] = polys
            print("projected", setname, name, len(polys), "edges", flush=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


# ----------------------------------------------------------------------------
# координаты листа
# ----------------------------------------------------------------------------
def p_front(Y, Z):
    return (XA + S * Y, ZBASE - S * Z)


def p_side(X, Z):
    return (XB + S * X, ZBASE - S * Z)


def p_top(X, Y):
    return (XT + S * X, YT - S * Y)


def map_uv_front(u, v):
    # проекция вдоль +X (вид со стороны −X): (u,v)=(-Z,-Y)
    return (XA + S * (-v), ZBASE + S * u)


def map_uv_side(u, v):
    # проекция вдоль +Y (вид слева, −Y): (u,v)=(-Z,X)
    return (XB + S * v, ZBASE + S * u)


def map_uv_top(u, v):
    return (XT + S * u, YT - S * v)


MAP = {"front": map_uv_front, "side": map_uv_side, "top": map_uv_top}


# ----------------------------------------------------------------------------
# svg helpers
# ----------------------------------------------------------------------------
def fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


def clip(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


def line(x1, y1, x2, y2, w=0.18, dash=None, color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
            'stroke-width="%s"%s/>'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), color, w, d))


def rect(x, y, w, h, sw=0.2, fill="none"):
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" '
            'stroke="#000" stroke-width="%s"/>'
            % (fmt(x), fmt(y), fmt(w), fmt(h), fill, sw))


def circle(cx, cy, r, sw=0.25, dash=None, fill="none", color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" '
            'stroke-width="%s"%s/>'
            % (fmt(cx), fmt(cy), fmt(r), fill, color, sw, d))


def text(x, y, s, size=3.2, anchor="start", weight="normal", rot=0,
         color="#000"):
    tr = ' transform="rotate(%s %s %s)"' % (rot, fmt(x), fmt(y)) if rot else ""
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" '
            'font-weight="%s" text-anchor="%s" fill="%s"%s>%s</text>'
            % (fmt(x), fmt(y), FONT, size, weight, anchor, color, tr, s))


def txt_bg(x, y, s, size=3.0, anchor="middle"):
    w = max(2.0, len(s) * size * 0.58)
    if anchor == "middle":
        x0 = x - w / 2
    elif anchor == "end":
        x0 = x - w
    else:
        x0 = x
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" '
            'stroke="none"/>'
            % (fmt(x0), fmt(y - size * 0.9), fmt(w), fmt(size * 1.15)))


def arrow(x, y, dx, dy, size=1.5):
    bx, by = x - dx * size, y - dy * size
    px, py = -dy * 0.45, dx * 0.45
    return ('<polygon points="%s,%s %s,%s %s,%s" fill="#000"/>'
            % (fmt(x), fmt(y), fmt(bx + px), fmt(by + py),
               fmt(bx - px), fmt(by - py)))


def dim_h(p1, p2, val, off, size=2.8, color="#000"):
    x1, y1 = p1
    x2, y2 = p2
    ym = (y1 + y2) / 2.0
    yd = ym + off
    sgn = 1 if off >= 0 else -1
    out = []
    out.append(line(x1, y1, x1, yd + sgn * 1.6, 0.12, color=color))
    out.append(line(x2, y2, x2, yd + sgn * 1.6, 0.12, color=color))
    out.append(line(x1, yd, x2, yd, 0.16, color=color))
    out.append(arrow(x1, yd, -1 if x1 < x2 else 1, 0))
    out.append(arrow(x2, yd, 1 if x1 < x2 else -1, 0))
    out.append(txt_bg((x1 + x2) / 2, yd - 1.0, str(val), size))
    out.append(text((x1 + x2) / 2, yd - 1.0, str(val), size, "middle",
                    color=color))
    return "".join(out)


def dim_v(p1, p2, val, off, size=2.8, color="#000"):
    x1, y1 = p1
    x2, y2 = p2
    xm = (x1 + x2) / 2.0
    xd = xm + off
    sgn = 1 if off >= 0 else -1
    out = []
    out.append(line(x1, y1, xd + sgn * 1.6, y1, 0.12, color=color))
    out.append(line(x2, y2, xd + sgn * 1.6, y2, 0.12, color=color))
    out.append(line(xd, y1, xd, y2, 0.16, color=color))
    out.append(arrow(xd, y1, 0, -1 if y1 < y2 else 1))
    out.append(arrow(xd, y2, 0, 1 if y1 < y2 else -1))
    ty = (y1 + y2) / 2
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" '
               'stroke="none"/>'
               % (fmt(xd - size * 0.6),
                  fmt(ty - len(str(val)) * size * 0.3),
                  fmt(size * 1.2), fmt(len(str(val)) * size * 0.6)))
    out.append(text(xd - 1.0, ty, str(val), size, "middle", rot=-90))
    return "".join(out)


def centerline(x1, y1, x2, y2):
    return line(x1, y1, x2, y2, 0.15, dash="7 1.6 1.2 1.6", color="#333")


def callout(px, py, cx, cy, num, r=3.4):
    dx, dy = px - cx, py - cy
    d = math.hypot(dx, dy)
    if d > 1e-6:
        k = r / d
        sx, sy = cx + dx * k, cy + dy * k
    else:
        sx, sy = cx, cy
    return "".join([
        line(sx, sy, px, py, 0.15),
        '<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke="#000" '
        'stroke-width="0.22"/>' % (fmt(cx), fmt(cy), fmt(r)),
        '<circle cx="%s" cy="%s" r="0.45" fill="#000"/>' % (fmt(px), fmt(py)),
        text(cx, cy + 1.05, str(num), 3.0, "middle", "bold"),
    ])


# ----------------------------------------------------------------------------
# лист
# ----------------------------------------------------------------------------
def sheet(views):
    vv = views["open"]
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
               'height="1188" viewBox="0 0 420 297">')
    out.append('<rect width="420" height="297" fill="#fff"/>')
    out.append(rect(4, 4, 412, 289, 0.5))
    out.append(rect(6, 6, 408, 285, 0.25))
    out.append(text(10, 13,
                    "ВИБРОСТОЛ ДЛЯ ФИЗИЧЕСКОГО ЭКСПЕРИМЕНТА — "
                    "ЭСКИЗНАЯ КОМПОНОВКА (fix11, без кожуха). М 1:3", 6.0,
                    weight="bold"))
    out.append(text(410, 13, "A3 · 420×297", 4.2, "end"))
    out.append(line(8, 16.5, 412, 16.5, 0.35))

    titles = {
        "front": ("Вид спереди (со стороны −X)", XA - 2, 39),
        "side": ("Вид слева (со стороны −Y)", XB - 2, 39),
        "top": ("Вид сверху (−Z)", XT - 2, 180),
    }
    for name in ("front", "side", "top"):
        mp = MAP[name]
        paths = []
        for poly in vv[name]:
            pts = [mp(u, v) for u, v in poly]
            d = "M " + " L ".join("%s %s" % (fmt(x), fmt(y))
                                  for x, y in pts)
            paths.append('<path d="%s"/>' % d)
        out.append('<g fill="none" stroke="#000" stroke-width="0.26" '
                   'stroke-linecap="round" stroke-linejoin="round">%s</g>'
                   % "".join(paths))
        t, tx, ty = titles[name]
        out.append(text(tx, ty, t, 4.2, weight="bold"))

    # ---- осевые ----
    cx, cy = p_front(100, 140)
    out.append(centerline(cx - 9, cy, cx + 9, cy))
    out.append(centerline(cx, cy - 9, cx, cy + 9))
    out.append(text(cx + 10, cy + 1.0, "Z=140", 2.6, color="#333"))
    x0, y0 = p_side(0, 140)
    x1, y1 = p_side(215, 140)
    out.append(centerline(x0, y0, x1, y1))
    out.append(text(x0 + 1.5, y0 - 1.8, "вал привода", 2.6, color="#333"))
    xa, ya = p_top(0, 100)
    xb, yb = p_top(360, 100)
    out.append(centerline(xa, ya, xb, yb))
    for gx in (10, 150):
        for gy in (50, 150):
            p = p_top(gx, gy)
            out.append(centerline(p[0] - 3, p[1], p[0] + 3, p[1]))
            out.append(centerline(p[0], p[1] - 3, p[0], p[1] + 3))

    # ---- размеры ----
    # спереди
    out.append(dim_v(p_front(0, 0), p_front(0, 300), 300, -9))
    out.append(dim_h(p_front(0, 0), p_front(200, 0), 200, 5))
    out.append(dim_h(p_front(25, 241), p_front(175, 241), 150, 4))
    # слева
    out.append(dim_h(p_side(-20, 0), p_side(362, 0), 382, 5))
    out.append(dim_h(p_side(0, 0), p_side(160, 0), 160, 11))
    out.append(dim_h(p_side(160, 0), p_side(360, 0), 200, 11))
    out.append(dim_v(p_side(360, 0), p_side(360, 300), 300, 6))
    out.append(dim_h(p_side(-20, 241), p_side(180, 241), 200, -4))
    # сверху
    out.append(dim_v(p_top(0, 0), p_top(0, 200), 200, -8))
    out.append(dim_h(p_top(-20, 0), p_top(362, 0), 382, 5))
    out.append(dim_h(p_top(-20, 0), p_top(180, 0), 200, 11))
    out.append(dim_h(p_top(10, 0), p_top(150, 0), 140, 17))
    out.append(dim_h(p_top(200, 0), p_top(360, 0), 160, 23))
    out.append(dim_v(p_top(180, 25), p_top(180, 175), 150, 3))

    # ---- фантом дрели ----
    dz = [(p_side(210, 90), p_side(340, 90)),
          (p_side(210, 190), p_side(340, 190)),
          (p_side(210, 90), p_side(210, 190)),
          (p_side(340, 90), p_side(340, 190))]
    for a, b in dz:
        out.append(line(*a, *b, 0.2, dash="4 2", color="#666"))
    out.append(text(p_side(245, 85)[0], p_side(245, 85)[1] + 3.5,
                    "дрель условно", 2.6, color="#555"))
    dz = [(p_top(210, 50), p_top(340, 50)),
          (p_top(210, 150), p_top(340, 150)),
          (p_top(210, 50), p_top(210, 150)),
          (p_top(340, 50), p_top(340, 150))]
    for a, b in dz:
        out.append(line(*a, *b, 0.2, dash="4 2", color="#666"))

    # ---- выноски: спереди (слева) ----
    co = [
        (1, p_front(50, 304), 10, 44),
        (25, p_front(50, 279), 10, 52),
        (3, p_front(50, 260), 10, 60),
        (4, p_front(60, 238), 10, 68),
        (5, p_front(60, 230), 10, 76),
        (8, p_front(50, 205), 10, 84),
        (22, p_front(5, 60), 10, 126),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))
    # спереди (между видами)
    co = [
        (2, p_front(150, 300), 101, 46),
        (6, p_front(105, 200), 101, 62),
        (9, p_front(100, 140), 101, 78),
        (10, p_front(145, 142), 101, 94),
        (21, p_front(110, 116), 101, 110),
        (14, p_front(30, 90), 101, 126),
        (31, p_front(32, 255), 101, 140),
        (32, p_front(50, 176), 101, 148),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))
    # слева
    co = [
        (11, p_side(280, 196), 250, 44),
        (12, p_side(250, 130), 250, 56),
        (20, p_side(180, 140), 250, 68),
        (7, p_side(80, 205), 250, 80),
        (18, p_side(220, 206), 250, 92),
        (33, p_side(87, 140), 250, 104),
        (34, p_side(93, 140), 250, 112),
        (35, p_side(80, 140), 250, 120),
        (24, p_side(0, 68), 250, 132),
        (23, p_side(50, 213), 250, 140),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))
    # сверху
    co = [
        (1, p_top(10, 50), 160.0, 190),
        (2, p_top(150, 150), 160.0, 200),
        (5, p_top(-20, 25), 160.0, 210),
        (4, p_top(80, 100), 160.0, 220),
        (11, p_top(280, 100), 160.0, 230),
        (8, p_top(150, 50), 160.0, 240),
        (14, p_top(160, 10), 160.0, 250),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))

    # ---- примечания ----
    out.append(rect(252, 150, 158, 92, 0.25))
    out.append(text(255, 156, "ПРИМЕЧАНИЯ (fix11)", 4.0, weight="bold"))
    notes = [
        "1. Рама — сварная сталь 20×20×2, 18 отрезков; все резы 90°;",
        "   стойки одним куском; верхние балки виброотсека на стойках.",
        "2. Седла 6200 — прорези R15×5 в стенке трубы (рама и балка 21),",
        "   без вкладышей; осевой зазор 0,2 мм; проверить кромку 2 мм.",
        "3. Балка 21 — стальная труба 20×20×2; 2×Ø10 под шпильки,",
        "   4×Ø4,5 под накладки; 4 втулки 16×16×2 L=16; заглушки.",
        "4. Накладки — 8 шт., 50×50, ширина 25, 2 мм; к балке M4×35;",
        "   к стойкам не крепятся, лепесток 50 упирается в стойку (20 мм).",
        "5. LMK — M4×12, головка Ø7×4 в цековке фланца, гайка nyloc",
        "   в столе 7,2×5 на клей; кронштейн ролика — M4×16, Ø8×5.",
        "6. Кожух — PC 5 мм, 22 винта M4×10 с головкой Ø7×4; резьба",
        "   M4 в стенке рамы 2 мм; вынос открыт.",
        "7. Подстолье — 4 потайных M6×60; гайки M6 приварены снизу",
        "   верхних балок выноса; U-хомуты M6.",
        "8. Шпильки поджима — 4×M10, L=117, строительные 4.6; снизу",
        "   шайба+гайка, под балкой шайба+гайка; сверху ≤5 мм.",
        "9. Кулачок/6200 — блок (поз. 35); смена после опускания балок",
        "   на 20 мм и блока на 44 мм.",
        "10. Габарит 382×218×308; масса ≈9,3 кг без дрели.",
    ]
    y = 162
    for s in notes:
        out.append(text(255, y, s, 2.45))
        y += 4.2

    # ---- штамп ----
    out.append(rect(250, 246, 162, 45, 0.3))
    out.append(line(250, 254, 412, 254, 0.25))
    out.append(text(254, 252, "ВИБРОСТОЛ — ЭСКИЗ СБОРКИ (fix11)", 7.0,
                    weight="bold"))
    out.append(text(254, 260,
                    "Этап fix11: стальная рама, крепёж по замечаниям", 3.4))
    out.append(text(254, 267,
                    "Масштаб 1:3      Лист 1/8      Формат A3", 3.5))
    out.append(text(254, 274,
                    "Единицы: мм. Масса ≈9,3 кг (без дрели)", 3.5))
    out.append(text(254, 281,
                    "Модель: cad/step/vibrotable_assembly.step", 3.3))
    out.append(text(254, 287, "Спецификация: spec.csv (44 поз.)", 3.3))
    out.append(text(410, 287, "М 1:3", 4.0, "end"))

    out.append("</svg>")
    return "".join(out)


# ----------------------------------------------------------------------------
# изометрия (отдельный файл)
# ----------------------------------------------------------------------------
def iso_svg(polys, fn):
    pts = [[u, v] for poly in polys for u, v in poly]
    if not pts:
        return
    umin = min(p[0] for p in pts); umax = max(p[0] for p in pts)
    vmin = min(p[1] for p in pts); vmax = max(p[1] for p in pts)
    w = umax - umin; h = vmax - vmin
    sc = min(150.0 / w, 150.0 / h)
    ox = (170 - w * sc) / 2 - umin * sc
    oy = (170 + h * sc) / 2 + vmin * sc
    paths = []
    for poly in polys:
        d = "M " + " L ".join("%.2f %.2f" % (ox + u * sc, oy - v * sc)
                              for u, v in poly)
        paths.append('<path d="%s"/>' % d)
    svg = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<svg xmlns="http://www.w3.org/2000/svg" width="680" '
           'height="680" viewBox="0 0 170 170">'
           '<rect width="170" height="170" fill="#fff"/>'
           '<g fill="none" stroke="#000" stroke-width="0.35" '
           'stroke-linejoin="round">%s</g>'
           '<text x="85" y="164" font-family="%s" font-size="4" '
           'text-anchor="middle">Изометрия (HLR). М 1:3</text></svg>'
           ) % ("".join(paths), FONT)
    with open(os.path.join(FIG, fn), "w", encoding="utf-8") as f:
        f.write(svg)


# ----------------------------------------------------------------------------
# лист спецификации
# ----------------------------------------------------------------------------
def spec_sheet():
    spec = []
    with open(os.path.join(STAGE, "spec.csv"), encoding="utf-8") as f:
        r = csv.reader(f, delimiter=";")
        next(r)
        for row in r:
            spec.append(row)
    mat_sum = {}
    total = "0"
    with open(os.path.join(HERE, "mass.csv"), encoding="utf-8") as f:
        r = csv.reader(f, delimiter=";")
        next(r)
        for row in r:
            if row[0] == "ИТОГО":
                total = row[5]
            else:
                mat_sum[row[2]] = mat_sum.get(row[2], 0.0) + float(row[5])
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13,
                "ВИБРОСТОЛ (fix11) — СПЕЦИФИКАЦИЯ И ПАРАМЕТРЫ", 7.2,
                weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    out.append(text(10, 23, "СПЕЦИФИКАЦИЯ", 4.6, weight="bold"))
    cols = [10, 24, 110, 124, 156, 200]
    heads = ["Поз.", "Наименование", "Кол.", "Материал", "Размеры",
             "Изготовление"]
    for x, h in zip(cols, heads):
        out.append(text(x, 29, h, 3.2, weight="bold"))
    out.append(line(10, 30.5, 248, 30.5, 0.2))
    y = 34
    for row in spec:
        no, name, qty, mat, size, make, note = (row + [""] * 7)[:7]
        out.append(text(cols[0], y, no, 2.5))
        out.append(text(cols[1], y, clip(name, 36), 2.5))
        out.append(text(cols[2], y, clip(qty, 9), 2.5))
        out.append(text(cols[3], y, clip(mat, 18), 2.1))
        out.append(text(cols[4], y, clip(size, 30), 2.15))
        out.append(text(cols[5], y, clip(make, 36), 1.9))
        y += 2.7
    out.append(line(10, y - 1.4, 248, y - 1.4, 0.2))

    px = 252
    out.append(text(px, 23, "ОСНОВНЫЕ ПАРАМЕТРЫ", 4.6, weight="bold"))
    prm = [
        ("Габарит рамы", "360×200×300"),
        ("Габарит сборки", "382×218×308"),
        ("Виброотсек / вынос", "160 / 200"),
        ("Рама", "сварная сталь 20×20×2; 18 отрезков"),
        ("Стол / накладка", "200×150×10 / 200×150×6"),
        ("Ход стола", "3 / 5 / 10; верх 241"),
        ("Пружина", "4 × Ø17×1,5; L0=60; уст. 36"),
        ("Кулачок", "2 лепестка; R40…50; 8×Ø10 R32"),
        ("Кулачок — фиксация", "гайка M10 приварена + 2 шайбы + 2+2 гайки"),
        ("Кулачок — отверстие", "шестигранник 17,1; буртик Ø40×10"),
        ("Частота стола", "2 × вал; 150…450 об/мин"),
        ("Балка 21", "сталь 20×20×2; R15×5; 2×Ø10; 4×Ø4,5; 4 втулки"),
        ("Накладки", "8 × 50×50, ширина 25, 2 мм; M4×35; упор 20; ход 20"),
        ("Шпильки поджима", "4 × M10, L=117; снизу и под балкой шайба+гайка"),
        ("Кожух", "PC 5 мм; 2 панели + 2 бортика"),
        ("Кожух — крепёж", "22 × M4×10, головка Ø7×4"),
        ("LMK — крепёж", "M4×12; гайка в столе 7,2×5"),
        ("Подстолье", "160×200×12; 4×M6×60; гайки приварены"),
        ("Заглушки", "6×20×20 + 4×16×16 (рама) + 4×16×16 (балка)"),
        ("Блок кулачка", "вал + кулачок + 2×6200 + 4 конуса"),
        ("Вал привода", "3 компл. (1+2 запасных); Ø10; 6200 X=10/150"),
        ("Дрель", "Ø100; против часовой"),
    ]
    yy = 30
    for k, v in prm:
        out.append(text(px, yy, k, 2.6))
        out.append(text(408, yy, v, 2.6, "end"))
        yy += 4.2

    out.append(text(px, 124, "МАССА, г", 4.2, weight="bold"))
    labels = [("petg", "PETG (подстолье)"),
              ("pla", "PLA (стол, накладка, кулачок)"),
              ("pc", "Поликарбонат (кожух)"),
              ("rubber", "Резина (буферы, кольца)"),
              ("steel", "Сталь (рама, балка, уголки, крепёж)"),
              ("bearing", "Подшипники (LMK, 6200)"),
              ("plastic", "Пластик (заглушки)")]
    yy = 130
    for key, label in labels:
        out.append(text(px, yy, label, 2.5))
        out.append(text(408, yy, "%.0f" % mat_sum.get(key, 0.0), 2.5, "end"))
        yy += 4.9
    out.append(line(252, yy - 1.8, 410, yy - 1.8, 0.2))
    out.append(text(px, yy + 4, "ИТОГО (без дрели)", 3.0, weight="bold"))
    out.append(text(408, yy + 4, total, 3.0, "end", weight="bold"))

    out.append(text(10, 176, "ПРОВЕРКИ И ПРИНЯТЫЕ РЕШЕНИЯ (fix11)", 4.2,
                    weight="bold"))
    checks = [
        "Рама — сварная сталь 20×20×2, 18 отрезков; все резы 90°;",
        "стойки одним куском; верхние балки виброотсека лежат на стойках.",
        "Седла 6200 — прорези R15×5 в стенке 2 мм (рама и балка 21),",
        "без вкладышей; осевой зазор 0,2 мм; контакт по кромке —",
        "предупреждение, проверить после обкатки.",
        "LMK — M4×12; цековка фланца Ø7,2×4,2; гайка в столе 7,2×5;",
        "зацепление 5 мм; остаток фланца 1,8 мм.",
        "Кожух — 22 винта M4×10; резьба в стенке 2 мм — предупреждение.",
        "Подстолье — 4 потайных M6×60; гайки M6 приварены снизу балок.",
        "Накладки — 8 × 50×50, ширина 25, 2 мм; к балке M4×35; к стойкам",
        "не крепятся; лепесток 50 — упор/направляющая; ход 20.",
        "Шпильки поджима — 4 × M10, L=117, строительные 4.6; снизу",
        "шайба+гайка, под балкой шайба+гайка; вылет 5; вал/ось — 8.8.",
        "Балка 21 — стальная труба; 2×Ø10; 4×Ø4,5; 4 втулки 16×16×2.",
        "Проверки: 198/201 OK; предупреждения — седло, f_соб,",
        "резьба кожуха.",
        "Картридж: опустить балки на 20 мм, блок на 44 мм, выдвинуть.",
        "Частота стола 2× частота вала; 5…15 Гц → 150…450 об/мин.",
        "Испытание: шарик 20/33 г; протокол — Report.md, checks.csv.",
    ]
    yy = 182
    for s in checks:
        out.append(text(10, yy, s, 2.2))
        yy += 3.5

    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "ВИБРОСТОЛ — СПЕЦИФИКАЦИЯ (fix11)", 6.0,
                    weight="bold"))
    out.append(text(253, 266, "Этап fix11. Лист 2/8. Формат A3", 3.4))
    out.append(text(253, 274,
                    "Данные: spec.csv, params.csv, cad/checks.csv", 3.2))
    out.append(text(253, 281,
                    "Модель: cad/step/vibrotable_assembly.step", 3.2))
    out.append(text(253, 288, "Единицы: мм", 3.2))
    out.append("</svg>")
    with open(os.path.join(FIG, "vibrotable_spec.svg"), "w",
              encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
# лист кожуха: полная сборка (HLR)
# ----------------------------------------------------------------------------
def shield_sheet(views):
    vv = views["full"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "ВИБРОСТОЛ (fix11) — КОЖУХ ИЗ ПОЛИКАРБОНАТА 5 мм",
                6.4, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    for name, tx, ty in (("front", 18, 30), ("side", 120, 30),
                         ("top", 18, 180)):
        mp = MAP[name]
        paths = []
        for poly in vv[name]:
            pts = [mp(u, v) for u, v in poly]
            d = "M " + " L ".join("%s %s" % (fmt(x), fmt(y))
                                  for x, y in pts)
            paths.append('<path d="%s"/>' % d)
        out.append('<g fill="none" stroke="#000" stroke-width="0.22" '
                   'stroke-linejoin="round">%s</g>' % "".join(paths))
        out.append(text(tx, ty, {"front": "Вид спереди",
                                 "side": "Вид слева",
                                 "top": "Вид сверху"}[name], 4.0,
                        weight="bold"))
    # габариты
    out.append(dim_h(p_front(0, 0), p_front(200, 0), 200, 6, 2.5))
    out.append(dim_v(p_front(0, 0), p_front(0, 300), 300, -8, 2.5))
    out.append(dim_h(p_side(0, 0), p_side(160, 0), 160, 8, 2.5))
    out.append(text(255, 75, "Боковые панели: Y=−5…0 и 200…205,",
                    2.5))
    out.append(text(255, 80, "X=0…160, Z=0…300; 2 × 160×300×5.",
                    2.5))
    out.append(text(255, 85, "Внутренних бортиков нет (fix5 п.8):",
                    2.5))
    out.append(text(255, 90, "защита — резиновые буферы в углах.",
                    2.5))
    out.append(text(255, 95, "Наружные бортики X=−5…0 и 160…165",
                    2.5))
    out.append(text(255, 100, "закрывают пружины; низ Z=246.",
                    2.5))
    out.append(text(255, 105, "Вынос X>165 открыт.", 2.5))
    out.append(text(255, 110, "22 винта M4×10 с цилиндрической",
                    2.5))
    out.append(text(255, 115, "головкой Ø7×4; резьба M4 в стенке 2 мм.",
                    2.5))
    out.append(text(255, 122, "Стол 241 — верхняя точка хода; бортик",
                    2.5))
    out.append(text(255, 127, "246; буферы 244 (3 мм до стола).",
                    2.5))
    out.append(text(255, 134, "Для смены блока кулачка панели снимаются",
                    2.5))
    out.append(text(255, 139, "на винтах; балки 21 освобождают 6200.",
                    2.5))
    out.append(text(255, 30, "КОЖУХ — СПЕЦИФИКАЦИЯ", 4.2, weight="bold"))
    rows = [
        ("29", "Кожух PC 5 мм", "1 компл.", "4 пластины"),
        ("30", "Винт M4×10", "22", "головка Ø7×4"),
        ("31", "Буфер резиновый", "4", "20×19×36"),
        ("32", "Кольцо на вал", "4", "Ø10,5/Ø18×7"),
    ]
    y = 37
    for no, nm, q, sz in rows:
        out.append(text(255, y, no, 2.8))
        out.append(text(265, y, nm, 2.6))
        out.append(text(352, y, q, 2.6))
        out.append(text(408, y, sz, 2.4, "end"))
        y += 5.0
    out.append(line(255, y - 2, 410, y - 2, 0.2))
    out.append(text(255, 150, "Кожух закрывает только виброотсек;",
                    2.5))
    out.append(text(255, 155, "подстолье, дрель, хомуты и вынос —",
                    2.5))
    out.append(text(255, 160, "открыты. Крепление — винты M4×10",
                    2.5))
    out.append(text(255, 165, "с головкой Ø7×4; для доступа к",
                    2.5))
    out.append(text(255, 170, "балкам и кулачку панели снимаются.",
                    2.5))
    out.append(rect(250, 245, 162, 46, 0.3))
    out.append(text(253, 253, "ВИБРОСТОЛ — КОЖУХ (fix11)", 6.0,
                    weight="bold"))
    out.append(text(253, 261, "Этап fix11. Лист 5/8. Формат A3", 3.4))
    out.append(text(253, 269, "Поликарбонат 5 мм; 4 пластины", 3.2))
    out.append(text(253, 277, "22 винта M4×10; головка Ø7×4", 3.2))
    out.append(text(253, 285, "Вынос не закрыт", 3.2))
    out.append("</svg>")
    with open(os.path.join(FIG, "vibrotable_shield.svg"), "w",
              encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
# лист кулачка: профиль, отверстия, насечки, осевой стек
# ----------------------------------------------------------------------------
def cam_sheet():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "КУЛАЧОК fix4 — 2 ЛЕПЕСТКА, КОНТАКТНАЯ ШАЙБА, "
                        "ОСЕВОЙ СТЕК", 6.2, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    cx, cy, SC = 110.0, 120.0, 1.4
    # три профиля
    for s, dash, col in ((10, "5 2", "#888"), (5, None, "#000"),
                         (3, "2 2", "#aaa")):
        pts = []
        for i in range(0, 360):
            a = math.radians(i)
            r = 50.0 - s / 2.0 - (s / 2.0) * math.cos(2 * a)
            pts.append((cx + r * math.cos(a) * SC,
                        cy - r * math.sin(a) * SC))
        d = "M " + " L ".join("%.2f %.2f" % p for p in pts) + " Z"
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="0.3"%s/>'
                   % (d, col,
                      ' stroke-dasharray="%s"' % dash if dash else ""))
    out.append(circle(cx, cy, 5.1 * SC))
    # отверстия облегчения
    for a_deg, rr in ((90, 38), (270, 38), (0, 28), (180, 28)):
        a = math.radians(a_deg)
        hx = cx + rr * math.cos(a) * SC
        hy = cy - rr * math.sin(a) * SC
        out.append(circle(hx, hy, 6.0 * SC, 0.22, fill="#eee"))
    # насечки (8, смещены на 22,5°)
    for i in range(8):
        a = math.radians((i + 0.5) * 360.0 / 8)
        r0, r1 = 5.1 * SC, 35.1 * SC
        out.append(line(cx + r0 * math.cos(a), cy - r0 * math.sin(a),
                        cx + r1 * math.cos(a), cy - r1 * math.sin(a),
                        0.18, dash="1 1"))
    out.append(circle(cx, cy, 35.0 * SC, 0.2, dash="4 2", color="#06c"))
    out.append(circle(cx, cy, 5.25 * SC, 0.2, color="#06c"))
    out.append(centerline(cx - 55 * SC, cy, cx + 55 * SC, cy))
    out.append(centerline(cx, cy - 55 * SC, cx, cy + 55 * SC))
    out.append(text(cx, cy - 53 * SC, "R50 (макс.)", 2.8, "middle"))
    out.append(text(cx + 42 * SC, cy + 2, "R45", 2.6))
    out.append(text(cx, cy + 53 * SC, "R40 (диск 10)", 2.6, "middle"))
    out.append(text(cx + 8 * SC, cy - 20 * SC, "Ø12 на R38", 2.3))
    out.append(text(cx + 8 * SC, cy + 5 * SC, "Ø12 на R28", 2.3))
    out.append(text(cx - 55 * SC, cy - 50 * SC, "Насечки 8 × 3×30×0,5",
                    2.5))
    out.append(text(cx - 55 * SC, cy - 45 * SC, "Шайба Ø70/Ø10,5×2,5",
                    2.5))
    out.append(text(cx - 55 * SC, cy - 40 * SC, "Фаски на отверстии нет",
                    2.5))

    # осевой стек (вид сбоку, X-Z), масштаб 1,7
    zx, zy = 260.0, 170.0
    scl = 1.0
    out.append(line(zx - 5, zy, zx + 75, zy, 0.2, dash="6 1.5 1 1.5"))
    stack = [
        (70.5, 74.0, 8.0, "буртик Ø16", "#fff"),
        (74.0, 86.0, 50.0, "кулачок", "#eee"),
        (86.0, 88.5, 35.0, "шайба Ø70", "#fff"),
        (88.5, 96.5, 8.5, "гайка", "#ddd"),
        (96.5, 104.5, 8.5, "контргайка", "#ddd"),
    ]
    for x0, x1, r, nm, fill in stack:
        out.append(rect(zx + (x0 - 70.5) * scl, zy - r * scl,
                        (x1 - x0) * scl, 2 * r * scl, 0.22, fill))
    out.append(dim_h((zx + 3.5 * scl, zy + 55 * scl),
                     (zx + 15.5 * scl, zy + 55 * scl), 12, 5, 2.4))
    out.append(dim_h((zx + 15.5 * scl, zy + 55 * scl),
                     (zx + 18.0 * scl, zy + 55 * scl), 2.5, 9, 2.2))
    out.append(text(zx, zy - 60, "ОСЕВОЙ СТЕК (X, мм)", 4.0, weight="bold"))
    out.append(text(zx, zy + 62, "X=70,5…104,5; шайба 86…88,5;", 2.4))
    out.append(text(zx, zy + 66, "гайка 88,5…96,5; контргайка 96,5…104,5.",
                    2.4))
    out.append(text(20, 200, "Профиль r(θ)=r0+e·cos2θ; r0=50−s/2, e=s/2.",
                    3.0, weight="bold"))
    out.append(text(20, 206, "Два максимума (R50) и два минимума (R45 для",
                    2.6))
    out.append(text(20, 211, "диска 5) — r(θ)=r(θ+π). Верх стола 241 мм",
                    2.6))
    out.append(text(20, 216, "для всех дисков; ход вниз 3/5/10 мм.",
                    2.6))
    out.append(text(20, 222, "Частота стола = 2 × частота вала:",
                    2.6))
    out.append(text(20, 227, "5…15 Гц → 150…450 об/мин.", 2.6))
    out.append(text(20, 234, "Кулачок прижат к буртику вала шайбой с",
                    2.6))
    out.append(text(20, 239, "8 рёбрами и двумя гайками — осевой",
                    2.6))
    out.append(text(20, 244, "люфт 0, проворот исключён насечками.",
                    2.6))
    out.append(rect(250, 245, 162, 46, 0.3))
    out.append(text(253, 253, "КУЛАЧОК — ДЕТАЛЬ (fix11)", 6.0,
                    weight="bold"))
    out.append(text(253, 261, "Лист 4/8. Формат A3. М 1,4:1", 3.4))
    out.append(text(253, 269, "Диски 3/5/10; R50/R40…45", 3.2))
    out.append(text(253, 277, "STL: cam_3/5/10.stl; 100 % заполнения",
                    3.0))
    out.append(text(253, 285, "Материал: PLA/PETG; 4×Ø12", 3.0))
    out.append("</svg>")
    with open(os.path.join(FIG, "cam_symmetric.svg"), "w",
              encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
# лист рамы: 3 проекции + деталировка отрезков + сварка
# ----------------------------------------------------------------------------
def frame_tubes_sheet(views):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "РАМА fix11 — ОТРЕЗКИ ТРУБ 20×20×2 И СХЕМА СВАРКИ",
                6.0, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    # три проекции рамы (HLR), М 1:4
    SC = 0.25
    vframe = views["frame"]
    panels = [
        ("side", 24.0, 154.0, "Вид слева (X-Z)"),
        ("front", 160.0, 154.0, "Вид спереди (Y-Z)"),
        ("top", 24.0, 255.0, "Вид сверху (X-Y)"),
    ]
    for name, ox, oy, title in panels:
        polys = []
        for poly in vframe[name]:
            pts = []
            for u, v in poly:
                if name == "side":
                    x, y = ox + v * SC, oy + u * SC
                elif name == "front":
                    x, y = ox - v * SC, oy + u * SC
                else:
                    x, y = ox + u * SC, oy - v * SC
                pts.append((x, y))
            if not pts:
                continue
            d = "M " + " L ".join("%.2f %.2f" % p for p in pts)
            polys.append('<path d="%s"/>' % d)
        out.append('<g fill="none" stroke="#000" stroke-width="0.24" '
                   'stroke-linejoin="round">%s</g>' % "".join(polys))
        out.append(text(ox, oy + (18 if name != "top" else 8), title, 3.6,
                        weight="bold"))
    # номера труб на виде сверху (основные)
    labels = [
        ("T01", 10, 10), ("T02", 10, 190), ("T03", 150, 10),
        ("T04", 150, 190), ("T05", 350, 10), ("T06", 350, 190),
        ("T07", 180, 10), ("T08", 180, 190), ("T09", 80, 10),
        ("T10", 80, 190), ("T11", 260, 10), ("T12", 260, 190),
        ("T13", 10, 100), ("T14", 150, 100), ("T15", 10, 100),
        ("T16", 150, 100), ("T17", 10, 100), ("T18", 150, 100),
    ]
    for nm, x, y in labels:
        px = 24.0 + x * SC
        py = 255.0 - y * SC
        out.append(text(px, py, nm, 2.2, "middle", color="#06c"))
    # таблица отрезков
    out.append(text(252, 24, "ДЕТАЛИРОВКА ОТРЕЗКОВ", 4.2, weight="bold"))
    cols = [252, 268, 300, 318, 334, 356]
    heads = ["№", "Элемент", "L, мм", "Кол.", "Положение", "Рез"]
    for x, h in zip(cols, heads):
        out.append(text(x, 30, h, 2.4, weight="bold"))
    out.append(line(252, 31.5, 408, 31.5, 0.2))
    y = 35
    try:
        with open(os.path.join(STAGE, "tube_cut.csv"), encoding="utf-8") as f:
            r = csv.reader(f, delimiter=";")
            next(r)
            for row in r:
                no, nm, sec, length, qty, pos, cut, note = (row + [""] * 8)[:8]
                out.append(text(cols[0], y, no, 1.9))
                out.append(text(cols[1], y, clip(nm, 20), 1.9))
                out.append(text(cols[2], y, length, 1.9))
                out.append(text(cols[3], y, qty, 1.9))
                out.append(text(cols[4], y, clip(pos, 22), 1.5))
                out.append(text(cols[5], y, cut, 1.7))
                y += 3.35
    except Exception as e:
        out.append(text(252, y, "tube_cut.csv: %s" % e, 2.2, color="#c00"))
    out.append(line(252, y - 1.4, 408, y - 1.4, 0.2))
    # сварка
    yy = y + 5
    out.append(text(252, yy, "СВАРКА", 4.0, weight="bold"))
    welds = [
        "1. Все резы труб — 90°, стыки 45° не допускаются.",
        "2. Стойки — один кусок без разрезов; верхние балки",
        "   виброотсека лежат на стойках; стойки — на нижних балках.",
        "3. Балки выноса лежат на задних коротких стойках; к средней",
        "   высокой стойке — Т-стык без разреза стойки.",
        "4. Шов угловой, катет 3 мм, по периметру стыка; сварка",
        "   симметрично, от центра к краям, с контролем диагоналей.",
        "5. После сварки: отверстия Ø10,5 под валы — по кондуктору;",
        "   прорези R15×5 — фрезеровка; 4×Ø10 в верхней стенке T13/T14",
        "   (Y=60/140) — низ не сверлить; M4 под кожух.",
        "6. Грунт/покраска; заглушки 20×20 — 10 шт.",
    ]
    yy += 5
    for s in welds:
        out.append(text(252, yy, s, 2.25))
        yy += 3.6
    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "РАМА — fix11", 6.0, weight="bold"))
    out.append(text(253, 266, "18 отрезков 20×20×2; лист 3/8", 3.4))
    out.append(text(253, 274, "Седла 6200 — прорези R15×5 в стенке 2 мм",
                    3.0))
    out.append(text(253, 281, "Заглушки: 6×20×20 + 4×16×16 (рама); втулки — 8",
                    3.0))
    out.append(text(253, 288, "Все резы 90°; стойки одним куском", 3.0))
    out.append("</svg>")
    with open(os.path.join(FIG, "frame_tubes.svg"), "w",
              encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
# лист деталей: стол, подстолье, балка, уголок, седло, кронштейн
# ----------------------------------------------------------------------------
def details_sheet():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "ДЕТАЛИ fix11 — ЭСКИЗЫ С РАЗМЕРАМИ (М 1:2…1:4)",
                6.0, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]

    def panel_title(x, y, s):
        out.append(text(x, y, s, 3.4, weight="bold"))

    # 1. Стол — вид сверху, М 1:4
    panel_title(20, 26, "СТОЛ 5 — 200×150×10 (вид сверху)")
    sx, sy, sc = 24.0, 88.0, 0.28
    out.append(rect(sx, sy - 150 * sc, 200 * sc, 150 * sc, 0.35))
    for gx in (10, 150):
        for gy in (50, 150):
            px = sx + (gx - P["table_x0"]) * sc
            py = sy - (gy - P["table_y0"]) * sc
            out.append(circle(px, py, 11 / 2 * sc, 0.25, fill="#eee"))
            for dx in (-16, 16):
                for dy in (-16, 16):
                    out.append(circle(px + dx * sc, py - dy * sc,
                                      P["table_lmk_hole_d"] / 2 * sc, 0.18))
    for bx in (45, 110):
        out.append(circle(sx + (bx - P["table_x0"]) * sc,
                          sy - (100 - P["table_y0"]) * sc, 4 * sc, 0.25))
    out.append(dim_h((sx, sy + 5), (sx + 200 * sc, sy + 5), 200, 3, 2.2))
    out.append(dim_v((sx - 5, sy), (sx - 5, sy - 150 * sc), 150, -4, 2.2))
    out.append(text(sx, sy + 12, "16×Ø5 + углубления 7,2×5 под гайки M4;",
                    2.1))
    out.append(text(sx, sy + 15.5, "2×Ø5 + Ø8×5 под кронштейны; Ø11 валы",
                    2.1))

    # 2. Подстолье — вид сверху, М 1:4
    panel_title(150, 26, "ПОДСТОЛЬЕ 11 — 160×200×12")
    px, py, psc = 154.0, 88.0, 0.28
    out.append(rect(px, py - 200 * psc, 160 * psc, 200 * psc, 0.35))
    for x in (220 - 200, 320 - 200):
        for y in (10, 190):
            out.append(circle(px + x * psc, py - y * psc, 3.3 * psc, 0.2,
                              fill="#eee"))
    for x in (250 - 200, 300 - 200):
        for y in (47, 153):
            out.append(circle(px + x * psc, py - y * psc, 3.3 * psc, 0.2))
    out.append(dim_h((px, py + 5), (px + 160 * psc, py + 5), 160, 3, 2.2))
    out.append(dim_v((px - 5, py), (px - 5, py - 200 * psc), 200, -4, 2.2))
    out.append(text(px, py + 12, "4×M6×60 потайной (X=220/320, Y=10/190);",
                    2.1))
    out.append(text(px, py + 15.5, "4×Ø6,6 U-хомута (X=250/300, Y=47/153)",
                    2.1))

    # 3. Балка 21 — вид сбоку, М 1:2
    panel_title(20, 130, "БАЛКА 21 — труба 20×20×2, L=159,6")
    bx0, by0, bsc = 24.0, 160.0, 0.45
    out.append(rect(bx0, by0 - 20 * bsc, 159.6 * bsc, 20 * bsc, 0.35))
    out.append(circle(bx0 + 100 * bsc, by0 - 10 * bsc, 15 * bsc, 0.22,
                      dash="3 1.5"))
    out.append(dim_h((bx0, by0 + 5), (bx0 + 159.6 * bsc, by0 + 5), 159.6,
                     3, 2.2))
    out.append(text(bx0, by0 + 11, "Прорезь-седло R15×5, ширина 9,4;",
                    2.1))
    out.append(text(bx0, by0 + 14.5, "2×Ø10 сквозь верх/низ: Y=60/140;",
                    2.1))
    out.append(text(bx0, by0 + 18, "4×Ø4,5 по X: Y=30/45/155/170; втулки 4",
                    2.1))

    # 4. Накладка-уголок 50×50, ширина 25, t=2
    panel_title(150, 130, "НАКЛАДКА 14 — 50×50, ширина 25, t=2")
    ax, ay, asc = 154.0, 220.0, 0.55   # ay — уровень Z=0
    # вертикальный лепесток Y=0…25, Z=80…130 (50)
    out.append(rect(ax, ay - 130 * asc, 25 * asc, 50 * asc, 0.35,
                    fill="#f4f4f4"))
    # горизонтальный лепесток Y=0…50, Z=110…135 (50)
    out.append(rect(ax, ay - 135 * asc, 50 * asc, 25 * asc,
                    0.35, fill="#e8e8e8"))
    for yy in (30, 45):
        out.append(circle(ax + yy * asc, ay - 120 * asc,
                          2.25 * asc, 0.2, fill="#fff"))
    out.append(dim_h((ax, ay - 135 * asc - 5),
                     (ax + 50 * asc, ay - 135 * asc - 5), 50, 3, 2.2))
    out.append(dim_v((ax - 5, ay - 80 * asc),
                     (ax - 5, ay - 130 * asc), 50, -4, 2.2))
    out.append(text(ax + 27 * asc, ay - 138 * asc, "25", 2.2))
    out.append(text(ax, ay - 50 * asc + 9,
                    "2×Ø4,5 под M4×35; лепесток 50 перекрывает", 2.0))
    out.append(text(ax, ay - 50 * asc + 12.5,
                    "стойку на 20 мм; крепления к стойке нет", 2.0))

    # 5. Седло 6200 — разрез трубы 20×20×2
    panel_title(20, 222, "СЕДЛО 6200 — ПРОРЕЗЬ В СТЕНКЕ 2 мм")
    ex, ey, esc = 24.0, 270.0, 1.2
    out.append(rect(ex, ey - 20 * esc, 20 * esc, 20 * esc, 0.35))
    out.append(rect(ex + 2 * esc, ey - 18 * esc, 16 * esc, 16 * esc, 0.22,
                    fill="#fff"))
    out.append(circle(ex + 10 * esc, ey - 20 * esc, 15 * esc, 0.3,
                      dash="3 1.5"))
    out.append(dim_h((ex + 5.3 * esc, ey + 5), (ex + 14.7 * esc, ey + 5),
                     9.4, 3, 2.0))
    out.append(text(ex, ey + 11, "R15; глубина 5; стенка 2; без вкладыша",
                    2.1))
    out.append(text(ex, ey + 14.5, "контакт по кромке — проверить", 2.1))

    # 6. Кронштейн ролика и заглушки
    panel_title(150, 222, "КРОНШТЕЙН 6 — 40×40×20×2; ЗАГЛУШКИ")
    kx, ky, ksc = 154.0, 250.0, 0.55
    out.append(rect(kx, ky - 40 * ksc, 40 * ksc, 40 * ksc, 0.35,
                    fill="#f4f4f4"))
    out.append(rect(kx + 15 * ksc, ky - 20 * ksc, 10 * ksc, 5 * ksc, 0.22,
                    fill="#fff"))
    out.append(circle(kx + 20 * ksc, ky - 35 * ksc, 5.05 * ksc, 0.2))
    out.append(dim_h((kx, ky + 5), (kx + 40 * ksc, ky + 5), 40, 3, 2.0))
    out.append(text(kx, ky + 11, "Паз 10×5; отв. оси Ø10,1;", 2.1))
    out.append(text(kx, ky + 14.5, "заглушки 20×20×6 — 10, 16×16×5 — 4",
                    2.1))
    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "ДЕТАЛИ — fix11", 6.0, weight="bold"))
    out.append(text(253, 266, "Лист 6/8. Формат A3. М 1:2…1:4", 3.4))
    out.append(text(253, 274, "Стол, подстолье, балка 21, накладка,", 3.0))
    out.append(text(253, 281, "седло 6200, кронштейн, заглушки", 3.0))
    out.append(text(253, 288, "Размеры — по params.csv и spec.csv", 3.0))
    out.append("</svg>")
    with open(os.path.join(FIG, "details.svg"), "w", encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
# лист сборки: 6 шагов + моменты
# ----------------------------------------------------------------------------
def assembly_steps_sheet():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "ИНСТРУКЦИЯ ПО СБОРКЕ fix11 — 6 ШАГОВ", 6.0,
                weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    steps = [
        ("1. СТОЛ", [
            "LMK: 4×M4×12 снизу в цековку фланца; гайки M4 nyloc",
            "в углубления 7,2×5 стола на клей, заподлицо.",
            "Накладка: 4 потайных M4. Кронштейны ролика: M4×16",
            "в Ø8×5 и паз 10×5, гайки снизу.",
        ]),
        ("2. СТОЛ НА ВАЛЫ", [
            "Валы снизу: средняя поперечина → резиновое кольцо",
            "(демпфер) → стол с LMK → шайба → пружина → шайба",
            "→ верхняя поперечина. Ограничители: нижний под",
            "поперечиной, верхний над верхней. Пружина 36 мм.",
        ]),
        ("3. БАЛКА 21, НАКЛАДКИ, ШПИЛЬКИ", [
            "8 накладок 50×50: 2 винта M4×35 на конец балки,",
            "втулки 16×16×2 L=16; к стойкам не крепить — упор.",
            "Шпильки M10 L=117 в Ø10 нижних поперечин (Y=60/140);",
            "снизу шайба+гайка, под балкой шайба+гайка; вылет 5.",
            "Балка: верх 130, прорезь R15×5, ход вниз 20 мм.",
        ]),
        ("4. КАРТРИДЖ", [
            "Шпилька → 6200 №1 (X=10) → конусы/гайки M10;",
            "6200 №2 (X=150) → конусы/гайки; кулачок на",
            "приваренную гайку X=74…82; шайбы Ø40, гайки,",
            "контргайки с двух сторон. Осевой люфт 0.",
        ]),
        ("5. КАРТРИДЖ В РАМУ", [
            "Опустить балки 21 на 20 мм; отдать поджимные гайки;",
            "вставить картридж в седла R15×5; поднять балки, затянуть",
            "поджим; проверить контакт ролика.",
            "Смена: опустить балки на 20, блок на 44 мм, выдвинуть.",
        ]),
        ("6. ПОДСТОЛЬЕ И ДРЕЛЬ", [
            "Подстолье на балки выноса; 4 потайных M6×60",
            "в приварные гайки; U-хомуты M6, шайбы, гайки.",
            "Дрель Ø100; ось совместить с валом; резиновая",
            "подкладка; проверить биение и крепление.",
        ]),
    ]
    for i, (title, lines) in enumerate(steps):
        col = i % 3
        row = i // 3
        x = 12 + col * 136
        y = 28 + row * 122
        out.append(rect(x - 2, y - 8, 128, 112, 0.25))
        out.append(text(x, y, title, 4.0, weight="bold"))
        yy = y + 7
        for s in lines:
            out.append(text(x, yy, s, 2.15))
            yy += 4.2
    out.append(text(12, 276, "МОМЕНТЫ: LMK M4×12 — 1,5; кожух M4×10 — 1,0; "
                 "кронштейн M4×16 — 1,5; подстолье M6×60 — 5;", 2.4))
    out.append(text(12, 281, "накладки M4×35 — 2,5; шпильки M10 — 10; U-хомут M6 — 5; "
                 "конус 6200 — 5; гайка/контргайка 6200 — 8; кулачок M10 — 8;", 2.4))
    out.append(text(12, 286, "ограничитель WCS10FR — 4 Н·м. Фиксатор резьбы — "
                 "LMK, кожух, подстолье, кулачок. Проверки — checks.csv.",
                 2.4))
    out.append("</svg>")
    with open(os.path.join(FIG, "assembly_steps.svg"), "w",
              encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
# лист кулачка fix11 (актуальная геометрия)
# ----------------------------------------------------------------------------
def cam_detail_sheet():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "КУЛАЧОК fix11 — 2 ЛЕПЕСТКА, 8×Ø10 R32, БУРТИК Ø40",
                6.0, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    cx, cy, SC = 100.0, 120.0, 1.35
    for s, dash, col in ((10, "5 2", "#888"), (5, None, "#000"),
                         (3, "2 2", "#aaa")):
        pts = []
        for i in range(0, 360):
            a = math.radians(i)
            r = 50.0 - s / 2.0 - (s / 2.0) * math.cos(2 * a)
            pts.append((cx + r * math.cos(a) * SC,
                        cy - r * math.sin(a) * SC))
        d = "M " + " L ".join("%.2f %.2f" % p for p in pts) + " Z"
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="0.3"%s/>'
                   % (d, col,
                      ' stroke-dasharray="%s"' % dash if dash else ""))
    # 8 отверстий Ø10 на R32
    for i in range(8):
        a = math.radians(45.0 * i)
        hx = cx + 32.0 * math.cos(a) * SC
        hy = cy - 32.0 * math.sin(a) * SC
        out.append(circle(hx, hy, 5.0 * SC, 0.22, fill="#eee"))
    # центральный шестигранник 17,1 AF
    hexpts = []
    for i in range(6):
        a = math.radians(30 + 60 * i)
        hexpts.append((cx + 9.87 * math.cos(a) * SC,
                       cy - 9.87 * math.sin(a) * SC))
    out.append('<polygon points="%s" fill="#fff" stroke="#06c" '
               'stroke-width="0.25"/>'
               % " ".join("%.2f,%.2f" % p for p in hexpts))
    out.append(circle(cx, cy, 20.0 * SC, 0.22, dash="4 2", color="#06c"))
    out.append(centerline(cx - 55 * SC, cy, cx + 55 * SC, cy))
    out.append(centerline(cx, cy - 55 * SC, cx, cy + 55 * SC))
    out.append(text(cx, cy - 53 * SC, "R50 (макс.)", 2.8, "middle"))
    out.append(text(cx + 42 * SC, cy + 2, "R45", 2.6))
    out.append(text(cx, cy + 53 * SC, "R40 (диск 10)", 2.6, "middle"))
    out.append(text(cx + 8 * SC, cy - 20 * SC, "8×Ø10 на R32", 2.4))
    out.append(text(cx - 55 * SC, cy - 50 * SC, "Профиль r(θ)=r0+e·cos2θ;",
                    2.5))
    out.append(text(cx - 55 * SC, cy - 46 * SC, "центр — шестигранник 17,1;",
                    2.5))
    out.append(text(cx - 55 * SC, cy - 42 * SC, "буртик Ø40×10 слева;",
                    2.5))
    out.append(text(cx - 55 * SC, cy - 38 * SC, "насечек нет.", 2.5))
    # осевой стек
    zx, zy, scl = 250.0, 160.0, 1.0
    out.append(text(zx, zy - 60, "ОСЕВОЙ СТЕК (X, мм)", 4.0, weight="bold"))
    out.append(line(zx - 5, zy, zx + 70, zy, 0.2, dash="6 1.5 1 1.5"))
    stack = [
        (45.5, 53.5, 8.5, "контргайка", "#ddd"),
        (53.5, 61.5, 8.0, "гайка", "#ddd"),
        (61.5, 64.0, 20.0, "шайба Ø40", "#fff"),
        (64.0, 74.0, 20.0, "буртик Ø40", "#eee"),
        (74.0, 86.0, 50.0, "кулачок", "#eee"),
        (86.0, 88.5, 20.0, "шайба Ø40", "#fff"),
        (88.5, 96.5, 8.0, "гайка", "#ddd"),
        (96.5, 104.5, 8.5, "контргайка", "#ddd"),
    ]
    x0 = 61.5
    for xa, xb, r, nm, fill in stack:
        out.append(rect(zx + (xa - x0) * scl, zy - r * scl,
                        (xb - xa) * scl, 2 * r * scl, 0.22, fill))
    out.append(dim_h((zx + (74 - x0) * scl, zy + 58),
                     (zx + (86 - x0) * scl, zy + 58), 12, 5, 2.4))
    out.append(text(zx, zy + 65, "X=45,5…104,5; буртик 64…74;", 2.4))
    out.append(text(zx, zy + 69, "шайбы Ø40/Ø10,5×2,5; гайки M10", 2.4))
    out.append(text(zx, zy + 73, "и контргайки с двух сторон.", 2.4))
    out.append(rect(250, 245, 162, 46, 0.3))
    out.append(text(253, 253, "КУЛАЧОК — ДЕТАЛЬ (fix11)", 6.0,
                    weight="bold"))
    out.append(text(253, 261, "Лист 4/8. Формат A3. М 1,35:1", 3.4))
    out.append(text(253, 269, "Диски 3/5/10; R50/R40…45", 3.2))
    out.append(text(253, 277, "STL: cam_3/5/10.stl; 100 % заполнения",
                    3.0))
    out.append(text(253, 285, "PLA; 8×Ø10 R32; шестигранник 17,1", 3.0))
    out.append("</svg>")
    with open(os.path.join(FIG, "cam.svg"), "w", encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# лист узла поджима: балка, шпильки, стек, накладки
# ----------------------------------------------------------------------------
def clamp_sheet():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "УЗЕЛ ПОДЖИМА БАЛКИ 21 (fix11) — ШПИЛЬКИ M10, "
                "ОПОРА, ПОДЖИМ, НАКЛАДКИ", 6.0, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]

    # --- A. балка 21, вид сбоку (Y-Z) ---
    out.append(text(20, 26, "БАЛКА 21 — ВИД СБОКУ (Y-Z), М 1:3", 3.6,
                    weight="bold"))
    bx, by, sc = 20.0, 70.0, 0.35
    y0 = P["ret_y0"]
    out.append(rect(bx, by - 20 * sc, (P["ret_y1"] - y0) * sc, 20 * sc,
                    0.35))
    out.append(circle(bx + (100 - y0) * sc, by - 20 * sc, 15 * sc, 0.22,
                      dash="3 1.5"))
    for yy in (P["clamp_stud_y1"], P["clamp_stud_y2"]):
        xx = bx + (yy - y0) * sc
        out.append(line(xx, by, xx, by - 20 * sc, 0.3, dash="2 1"))
        out.append(text(xx, by - 22 * sc, "Ø10", 2.2, "middle"))
    for yy in (P["pad_bolt_y1"], P["pad_bolt_y2"],
               P["W_frame"] - P["pad_bolt_y1"],
               P["W_frame"] - P["pad_bolt_y2"]):
        xx = bx + (yy - y0) * sc
        out.append(circle(xx, by - 10 * sc, 2.25 * sc, 0.22, fill="#fff"))
    out.append(dim_h((bx, by + 5), (bx + (P["ret_y1"] - y0) * sc, by + 5),
                     159.6, 3, 2.2))
    out.append(dim_h((bx + (P["clamp_stud_y1"] - y0) * sc, by - 28 * sc),
                     (bx + (P["clamp_stud_y2"] - y0) * sc, by - 28 * sc),
                     80, -3, 2.0))
    out.append(text(bx, by + 12,
                    "Прорезь-седло R15×5, ширина 9,4;", 2.1))
    out.append(text(bx, by + 15.5,
                    "2×Ø10 сквозь верх/низ (Y=60/140);", 2.1))
    out.append(text(bx, by + 19,
                    "4×Ø4,5 по X (Y=30/45/155/170); 4 втулки", 2.1))

    # --- B. разрез по шпильке (X-Z) ---
    out.append(text(250, 26, "РАЗРЕЗ ПО ШПИЛЬКЕ (X-Z), М 1:1,25", 3.6,
                    weight="bold"))
    sx, sz, ss = 262.0, 160.0, 0.8

    def px(x):
        return sx + x * ss

    def pz(z):
        return sz - z * ss

    # нижняя поперечина 20x20 и прижимная балка 20x20
    out.append(rect(px(0), pz(20), 20 * ss, 20 * ss, 0.35, fill="#eee"))
    out.append(rect(px(0), pz(130), 20 * ss, 20 * ss, 0.35, fill="#eee"))
    # шпилька 18…135
    out.append(line(px(10), pz(18), px(10), pz(135), 0.45))
    # опора: шайба 20…21,5 + гайка 21,5…29,5
    out.append(rect(px(2), pz(21.5), 16 * ss, 1.5 * ss, 0.25, fill="#ddd"))
    out.append(rect(px(2), pz(29.5), 16 * ss, 8 * ss, 0.3, fill="#ddd"))
    # поджим: шайба 108,5…110 + гайка 100,5…108,5
    out.append(rect(px(2), pz(110), 16 * ss, 1.5 * ss, 0.25, fill="#ddd"))
    out.append(rect(px(2), pz(108.5), 16 * ss, 8 * ss, 0.3, fill="#ddd"))
    # размеры
    out.append(dim_v((px(-3), pz(18)), (px(-3), pz(135)), 117, -4, 2.2))
    out.append(dim_v((px(23), pz(110)), (px(23), pz(130)), 20, 5, 2.0))
    out.append(dim_v((px(28), pz(130)), (px(28), pz(135)), 5, 5, 2.0))
    out.append(dim_v((px(33), pz(0)), (px(33), pz(20)), 20, 5, 2.0))
    out.append(text(px(36), pz(26), "опора: шайба 44 + nyloc 42", 1.9))
    out.append(text(px(36), pz(20), "на верхней грани T13/T14", 1.9))
    out.append(text(px(36), pz(105), "поджим: шайба 44 + гайка 43", 1.9))
    out.append(text(px(36), pz(99), "снизу балки; сверху ничего", 1.9))
    out.append(text(px(36), pz(134), "вылет 5", 1.9))
    out.append(text(px(0), pz(150), "шпилька 41: M10, L=117,", 1.9))
    out.append(text(px(0), pz(154), "строительная 4.6", 1.9))

    # --- C. нижняя поперечина, вид сверху ---
    out.append(text(20, 112, "НИЖНЯЯ ПОПЕРЕЧИНА T13/T14 — ОТВЕРСТИЯ",
                    3.6, weight="bold"))
    lx, ly, lsc = 20.0, 150.0, 0.35
    out.append(rect(lx, ly - 20 * lsc, 160 * lsc, 20 * lsc, 0.35,
                    fill="#f4f4f4"))
    for yy in (P["clamp_stud_y1"], P["clamp_stud_y2"]):
        xx = lx + (yy - 20) * lsc
        out.append(circle(xx, ly - 10 * lsc, 5 * lsc, 0.25, fill="#fff"))
        out.append(text(xx, ly - 10 * lsc - 3, "Ø10", 2.0, "middle"))
    out.append(dim_h((lx + 40 * lsc, ly + 4), (lx + 120 * lsc, ly + 4),
                     80, 3, 2.0))
    out.append(dim_h((lx + 80 * lsc, ly - 16 * lsc),
                     (lx + 120 * lsc, ly - 16 * lsc), 40, -3, 1.9))
    out.append(dim_h((lx, ly + 9), (lx + 160 * lsc, ly + 9), 160, 3, 2.0))
    out.append(text(lx, ly + 15, "X=10; Y=60/140; сверлить после сварки;",
                    2.0))
    out.append(text(lx, ly + 18.5, "нижнюю грань не сверлить", 2.0))

    # --- D. накладка 50x50 ---
    out.append(text(300, 166, "НАКЛАДКА 14 — 50×50, ширина 25, t=2",
                    3.6, weight="bold"))
    ax, ay, asc = 330.0, 245.0, 0.55
    out.append(rect(ax, ay - 130 * asc, 25 * asc, 50 * asc, 0.35,
                    fill="#f4f4f4"))
    out.append(rect(ax, ay - 135 * asc, 50 * asc, 25 * asc, 0.35,
                    fill="#e8e8e8"))
    for yy in (30, 45):
        out.append(circle(ax + yy * asc, ay - 120 * asc, 2.25 * asc,
                          0.22, fill="#fff"))
    out.append(dim_h((ax, ay - 135 * asc - 5),
                     (ax + 50 * asc, ay - 135 * asc - 5), 50, 3, 2.0))
    out.append(dim_v((ax - 5, ay - 80 * asc), (ax - 5, ay - 130 * asc),
                     50, -4, 2.0))
    out.append(text(ax + 27 * asc, ay - 138 * asc, "25", 2.1))
    out.append(text(ax, ay - 37,
                    "2×Ø4,5 под M4×35; лепесток 50 —", 1.9))
    out.append(text(ax, ay - 33.5,
                    "упор в стойку 20 мм; крепления нет", 1.9))

    # --- примечания ---
    notes = [
        "1. Накладки 14 — 8 шт., сталь 2 мм, 50×50, ширина 25; к балке",
        "   2 винта M4×35 с nyloc на конец; к стойкам не крепятся.",
        "2. Шпильки 41 — 4 шт., M10×117, строительные 4.6; Y=60/140;",
        "   низ 18 в гнезде Ø10 верхней стенки T13/T14; низ не сверлить.",
        "3. Опора: шайба 44 + гайка nyloc 42 на верхней грани T13/T14",
        "   (Z=20); шпилька опирается на гайку, а не на дно балки.",
        "4. Поджим: шайба 44 + гайка 43 снизу прижимной балки",
        "   (Z=100,5…110); сверху на шпильку ничего не накручено.",
        "5. Верх шпильки Z=135 — не более 5 мм над балкой (Z=130);",
        "   до ограничителей валов (Z=142) — 7 мм.",
        "6. Съём: отдать гайку 43, опустить балку на 20 мм, поднять",
        "   её со шпильками на 2 мм и наклонить вперёд; снять гайку 42.",
    ]
    yy = 252
    for t in notes:
        out.append(text(10, yy, t, 2.1))
        yy += 3.5

    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "УЗЕЛ ПОДЖИМА — fix11", 6.0, weight="bold"))
    out.append(text(253, 266, "Лист 8/8. Формат A3. М 1:3…1:1,25", 3.4))
    out.append(text(253, 274, "Балка 21, шпильки M10, опора, поджим",
                    3.0))
    out.append(text(253, 281, "Проверки: cad/checks.csv; моменты: torque.csv",
                    3.0))
    out.append(text(253, 288, "Размеры — params.csv, spec.csv", 3.0))
    out.append("</svg>")
    with open(os.path.join(FIG, "clamp.svg"), "w", encoding="utf-8") as f:
        f.write("".join(out))


def main():
    views = project_all()
    svg = sheet(views)
    fn = os.path.join(FIG, "vibrotable_views.svg")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(svg)
    iso_svg(views["full"]["iso"], "iso.svg")
    iso_svg(views["open"]["iso"], "iso_open.svg")
    spec_sheet()
    frame_tubes_sheet(views)
    details_sheet()
    assembly_steps_sheet()
    clamp_sheet()
    cam_detail_sheet()
    shield_sheet(views)
    print("written", fn, flush=True)


main()
