"""Листы эскизов A3 этапа fix7: проекции из модели (HLR FreeCAD), размеры,
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
    cache = os.path.join(CACHE, "views_v7.json")
    if os.path.exists(cache) and not FORCE:
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    parts, groups, cams = model.build_assembly()
    sets = {
        "full": [i["shape"] for i in parts.values()],
        "open": [i["shape"] for k, i in parts.items() if k not in HIDE_OPEN],
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
                    "ЭСКИЗНАЯ КОМПОНОВКА (fix7, без кожуха). М 1:3", 6.0,
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
    out.append(dim_h(p_side(-20, 0), p_side(360, 0), 380, 5))
    out.append(dim_h(p_side(0, 0), p_side(160, 0), 160, 11))
    out.append(dim_h(p_side(160, 0), p_side(360, 0), 200, 11))
    out.append(dim_v(p_side(360, 0), p_side(360, 300), 300, 6))
    out.append(dim_h(p_side(-20, 241), p_side(180, 241), 200, -4))
    # сверху
    out.append(dim_v(p_top(0, 0), p_top(0, 200), 200, -8))
    out.append(dim_h(p_top(-20, 0), p_top(360, 0), 380, 5))
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
    out.append(text(255, 156, "ПРИМЕЧАНИЯ (fix7)", 4.0, weight="bold"))
    notes = [
        "1. Кулачок: r(θ)=r0+e·cos2θ, 2 макс. и 2 мин.; верх стола 241;",
        "   ход 3/5/10 вниз; частота стола = 2 × вал (150…450 об/мин).",
        "2. Облегчение — 8×Ø10 на R32 (2 макс, 2 мин, 4 между); центр —",
        "   шестигранник 17,1 под гайку M10; буртик Ø40×10; насечек нет.",
        "3. Гайка M10 приварена к шпильке X=74…82; шайбы Ø40 с двух",
        "   сторон, с каждой стороны гайка + контргайка.",
        "4. Кожух — PC 5 мм: 2 панели 160×300 + 2 наружных бортика до",
        "   Z=246; внутренних нет; вынос открыт; 22 самореза M4×16.",
        "5. 4 буфера в углах «поперечина — стойка» (3 мм до стола,",
        "   5 мм до пружины); 4 кольца Ø18/Ø10,5×7 на валах.",
        "6. Оба опорных 6200 поджаты с двух сторон конусами Ø12→Ø16;",
        "   каждая из 4 конусных гаек законтрена гайкой M10 nyloc.",
        "7. Кулачок, вал и 6200 — блок (поз. 35); смена после снятия",
        "   балок 21 и опускания блока на 44 мм, без разбора вала.",
        "8. Рама PETG 360×200×300, 26 галтелей R10; стол 200×150×10;",
        "   балка 21 с 8 уголками; подстолье 160×200×12.",
        "9. Габарит 380×215×308; масса ≈6,39 кг без дрели.",
    ]
    y = 162
    for s in notes:
        out.append(text(255, y, s, 2.45))
        y += 4.2

    # ---- штамп ----
    out.append(rect(250, 246, 162, 45, 0.3))
    out.append(line(250, 254, 412, 254, 0.25))
    out.append(text(254, 252, "ВИБРОСТОЛ — ЭСКИЗ СБОРКИ (fix7)", 7.0,
                    weight="bold"))
    out.append(text(254, 260,
                    "Этап fix7: первая корректировка после второй экспертизы", 3.4))
    out.append(text(254, 267,
                    "Масштаб 1:3      Лист 1/2      Формат A3", 3.5))
    out.append(text(254, 274,
                    "Единицы: мм. Масса ≈6,39 кг (без дрели)", 3.5))
    out.append(text(254, 281,
                    "Модель: cad/step/vibrotable_assembly.step", 3.3))
    out.append(text(254, 287, "Спецификация: spec.csv (36 поз.)", 3.3))
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
                "ВИБРОСТОЛ (fix7) — СПЕЦИФИКАЦИЯ И ПАРАМЕТРЫ", 7.2,
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
        out.append(text(cols[3], y, clip(mat, 12), 2.2))
        out.append(text(cols[4], y, clip(size, 30), 2.15))
        out.append(text(cols[5], y, clip(make, 36), 1.9))
        y += 3.35
    out.append(line(10, y - 1.4, 248, y - 1.4, 0.2))

    px = 252
    out.append(text(px, 23, "ОСНОВНЫЕ ПАРАМЕТРЫ", 4.6, weight="bold"))
    prm = [
        ("Габарит рамы", "360×200×300"),
        ("Габарит сборки", "380×215×308"),
        ("Виброотсек / вынос", "160 / 200"),
        ("Стол / накладка", "200×150×10 / 200×150×6"),
        ("Ход стола", "3 / 5 / 10; верх 241"),
        ("Пружина", "4 × Ø12×1,0; L0=70; уст. 36"),
        ("Кулачок", "2 лепестка; R40…50; 8×Ø10 R32"),
        ("Кулачок — фиксация", "гайка M10 приварена + 2 шайбы + 2+2 гайки"),
        ("Кулачок — отверстие", "шестигранник 17,1; буртик Ø40×10"),
        ("Частота стола", "2 × вал; 150…450 об/мин"),
        ("Кожух", "PC 5 мм; 2 панели + 2 бортика"),
        ("Кожух — бортик", "низ Z=246; стол 241 + 5"),
        ("Кожух — крепёж", "22 самореза M4×16, шляпка Ø8"),
        ("Буферы", "4 × 20×19×36; 3 мм до стола"),
        ("Кольца на валах", "4 × Ø10,5/Ø18×7; 3 мм до LMK"),
        ("Галтели", "26 × R10; 6 в выносе"),
        ("Блок кулачка", "вал + кулачок + 2×6200 + 4 конуса"),
        ("Зажим 6200", "2 конуса Ø12→Ø16 + 2 гайки M10 на каждый"),
        ("Вал привода", "Ø10, X=−10…215; 6200 в X=10/150"),
        ("Подстолье", "160×200×12; 4×M6×45"),
        ("Дрель", "Ø100; против часовой"),
    ]
    yy = 30
    for k, v in prm:
        out.append(text(px, yy, k, 2.6))
        out.append(text(408, yy, v, 2.6, "end"))
        yy += 4.2

    out.append(text(px, 124, "МАССА, г", 4.2, weight="bold"))
    labels = [("petg", "PETG (рама, балка 21, подстолье)"),
              ("pla", "PLA (стол, накладка, кулачок)"),
              ("pc", "Поликарбонат (кожух)"),
              ("rubber", "Резина (буферы, кольца)"),
              ("steel", "Сталь (валы, крепёж, уголки)"),
              ("bearing", "Подшипники (LMK, 6200)")]
    yy = 130
    for key, label in labels:
        out.append(text(px, yy, label, 2.5))
        out.append(text(408, yy, "%.0f" % mat_sum.get(key, 0.0), 2.5, "end"))
        yy += 4.9
    out.append(line(252, yy - 1.8, 410, yy - 1.8, 0.2))
    out.append(text(px, yy + 4, "ИТОГО (без дрели)", 3.0, weight="bold"))
    out.append(text(408, yy + 4, total, 3.0, "end", weight="bold"))

    out.append(text(10, 167, "ПРОВЕРКИ И ПРИНЯТЫЕ РЕШЕНИЯ (fix7)", 4.2,
                    weight="bold"))
    checks = [
        "Оба опорных 6200 поджаты с двух сторон конусами Ø12→Ø16",
        "(4 шт.); каждая конусная гайка законтрена гайкой M10 nyloc.",
        "6200 №1: гайка −8…0 | конус 0…5,5 | 6200 5,5…14,5 | конус",
        "14,5…20 | гайка 20…28. 6200 №2: 132…140 | 140…145,5 |",
        "145,5…154,5 | 154,5…160 | 160…168. Пересечений 0.",
        "Конусы прижаты малым торцом к внутреннему кольцу 6200;",
        "контргайка отстоит от подшипника на 5,5 мм (конус).",
        "Кулачок: 2 макс. и 2 мин.; верх стола 241; ход 3/5/10 вниз;",
        "8×Ø10 на R32; центр — шестигранник 17,1; буртик Ø40×10.",
        "Гайка M10 приварена к шпильке; шайбы Ø40 с двух сторон.",
        "Кожух PC 5 мм: 2 панели + 2 наружных бортика; 22 самореза.",
        "4 буфера в углах (3 мм до стола); 4 кольца на валах.",
        "Проверки: 239/241 OK; предупреждения — пружина ID 10,0 и",
        "стенка 3 мм у отверстия R32 на минимуме диска 10.",
        "В раме 26 галтелей R10 (20 + 6 в выносе).",
        "Картридж: снять балки 21, опустить блок на 44 мм, выдвинуть.",
        "Частота стола 2× частота вала; 5…15 Гц → 150…450 об/мин.",
        "Испытание: шарик 20/33 г; протокол — Report.md, checks.csv.",
    ]
    yy = 173
    for s in checks:
        out.append(text(10, yy, s, 2.35))
        yy += 3.6

    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "ВИБРОСТОЛ — СПЕЦИФИКАЦИЯ (fix7)", 6.0,
                    weight="bold"))
    out.append(text(253, 266, "Этап fix7. Лист 2/2. Формат A3", 3.4))
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
           text(10, 13, "ВИБРОСТОЛ (fix4) — КОЖУХ ИЗ ПОЛИКАРБОНАТА 5 мм",
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
    out.append(text(255, 80, "X=0…160, Z=0…300; 2 × 160×300×5 —",
                    2.5))
    out.append(text(255, 85, "«большой кожух». Внутренние бортики —",
                    2.5))
    out.append(text(255, 90, "4 стороны, низ Z=246 (стол 241 + 5):",
                    2.5))
    out.append(text(255, 95, "шарик не уходит под раму. Наружные",
                    2.5))
    out.append(text(255, 100, "бортики X=−5…0 и 160…165 закрывают",
                    2.5))
    out.append(text(255, 105, "большую часть пружин. Вынос X>165",
                    2.5))
    out.append(text(255, 110, "открыт. 34 самореза M4×16 со шляпкой",
                    2.5))
    out.append(text(255, 115, "Ø8; пилоты Ø3,5 в PETG.", 2.5))
    out.append(text(255, 122, "Стол 241 — верхняя точка хода; бортик",
                    2.5))
    out.append(text(255, 127, "246; буферы 244 (3 мм до стола).",
                    2.5))
    out.append(text(255, 134, "Для смены блока кулачка панели снимаются",
                    2.5))
    out.append(text(255, 139, "на саморезах; балки 21 освобождают 6200.",
                    2.5))
    out.append(text(255, 30, "КОЖУХ — СПЕЦИФИКАЦИЯ", 4.2, weight="bold"))
    rows = [
        ("29", "Кожух PC 5 мм", "1 компл.", "8 пластин"),
        ("30", "Саморез M4×16", "34", "шляпка Ø8"),
        ("31", "Буфер резиновый", "8", "20×13×36"),
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
    out.append(text(255, 160, "открыты. Крепление — саморезы с",
                    2.5))
    out.append(text(255, 165, "прижимной шляпкой; для доступа к",
                    2.5))
    out.append(text(255, 170, "балкам и кулачку панели снимаются.",
                    2.5))
    out.append(rect(250, 245, 162, 46, 0.3))
    out.append(text(253, 253, "ВИБРОСТОЛ — КОЖУХ (fix4)", 6.0,
                    weight="bold"))
    out.append(text(253, 261, "Этап fix4. Лист 2/4. Формат A3", 3.4))
    out.append(text(253, 269, "Поликарбонат 5 мм; 8 пластин", 3.2))
    out.append(text(253, 277, "Масса кожуха ≈0,87 кг", 3.2))
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
    out.append(text(253, 253, "КУЛАЧОК — ДЕТАЛЬ (fix4)", 6.0,
                    weight="bold"))
    out.append(text(253, 261, "Лист 3/4. Формат A3. М 1,4:1", 3.4))
    out.append(text(253, 269, "Диски 3/5/10; R50/R40…45", 3.2))
    out.append(text(253, 277, "STL: cam_3/5/10.stl; 100 % заполнения",
                    3.0))
    out.append(text(253, 285, "Материал: PLA/PETG; 4×Ø12", 3.0))
    out.append("</svg>")
    with open(os.path.join(FIG, "cam_symmetric.svg"), "w",
              encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
def main():
    views = project_all()
    svg = sheet(views)
    fn = os.path.join(FIG, "vibrotable_views.svg")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(svg)
    iso_svg(views["full"]["iso"], "iso.svg")
    iso_svg(views["open"]["iso"], "iso_open.svg")
    spec_sheet()
    print("written", fn, flush=True)


main()
