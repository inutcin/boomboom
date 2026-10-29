"""Лист эскиза A3: проекции из модели (HLR FreeCAD), размеры, выноски, спецификация.

Запуск:
    freecadcmd draw_sheet.py [--force]

Кэш проекций: cad/cache/views.json (пересчёт ~3 мин).
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
S = 0.4            # 1:2.5
FONT = "DejaVu Sans, Arial, sans-serif"

VIEW_DEF = {
    "front": dict(dir=(-1, 0, 0), ox=30, oy=163),
    "side":  dict(dir=(0, -1, 0), ox=150, oy=163),
    "top":   dict(dir=(0, 0, 1), ox=30, oy=282),
    "iso":   dict(dir=(-1, -1, 1), ox=0, oy=0),
}


# ----------------------------------------------------------------------------
# проекции (кэш)
# ----------------------------------------------------------------------------
def project_all():
    cache = os.path.join(CACHE, "views_v3.json")
    if os.path.exists(cache) and not FORCE:
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    data = {}
    variants = {"front": "front", "side": "side", "top": False, "iso": False}
    comps = {}
    for v in set(str(x) for x in variants.values()):
        parts, groups, cams = model.build_assembly(draw=(False if v == "False" else v))
        comps[v] = Part.makeCompound([i["shape"] for i in parts.values()])
    for name, vd in VIEW_DEF.items():
        comp = comps[str(variants[name])]
        out = Drawing.project(comp, App.Vector(*vd["dir"]))
        vis = Part.makeCompound([out[0], out[1]])
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
        data[name] = polys
        print("projected", name, len(polys), "edges", flush=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


# ----------------------------------------------------------------------------
# координаты листа
# ----------------------------------------------------------------------------
def p_front(X, Y, Z):
    return (30 + S * (Y + 20), 163 - S * Z)


def p_side(X, Y, Z):
    return (150 + S * X, 163 - S * Z)


def p_top(X, Y, Z):
    return (30 + S * X, 282 - S * (Y + 20))


def map_uv_front(u, v):
    # проекция вдоль +X (вид со стороны -X): (u,v)=(-Z,-Y)
    return (30 + S * (-v + 20), 163 + S * u)


def map_uv_side(u, v):
    # проекция вдоль +Y (вид слева, -Y): (u,v)=(-Z,X)
    return (150 + S * v, 163 + S * u)


def map_uv_top(u, v):
    return (30 + S * u, 282 - S * (v + 20))


MAP = {"front": map_uv_front, "side": map_uv_side, "top": map_uv_top}


# ----------------------------------------------------------------------------
# svg helpers
# ----------------------------------------------------------------------------
def fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


def line(x1, y1, x2, y2, w=0.18, dash=None, color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), color, w, d))


def rect(x, y, w, h, sw=0.2, fill="none"):
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="#000" stroke-width="%s"/>'
            % (fmt(x), fmt(y), fmt(w), fmt(h), fill, sw))


def text(x, y, s, size=3.2, anchor="start", weight="normal", rot=0, color="#000"):
    tr = ' transform="rotate(%s %s %s)"' % (rot, fmt(x), fmt(y)) if rot else ""
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" '
            'text-anchor="%s" fill="%s"%s>%s</text>'
            % (fmt(x), fmt(y), FONT, size, weight, anchor, color, tr, s))


def txt_bg(x, y, s, size=3.0, anchor="middle"):
    w = max(2.0, len(s) * size * 0.58)
    if anchor == "middle":
        x0 = x - w / 2
    elif anchor == "end":
        x0 = x - w
    else:
        x0 = x
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" stroke="none"/>'
            % (fmt(x0), fmt(y - size * 0.9), fmt(w), fmt(size * 1.15)))


def arrow(x, y, dx, dy, size=1.5):
    bx, by = x - dx * size, y - dy * size
    px, py = -dy * 0.45, dx * 0.45
    return ('<polygon points="%s,%s %s,%s %s,%s" fill="#000"/>'
            % (fmt(x), fmt(y), fmt(bx + px), fmt(by + py), fmt(bx - px), fmt(by - py)))


def dim_h(p1, p2, val, off, size=3.0, color="#000"):
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
    out.append(txt_bg((x1 + x2) / 2, yd - 1.1, str(val), size))
    out.append(text((x1 + x2) / 2, yd - 1.1, str(val), size, "middle", color=color))
    return "".join(out)


def dim_v(p1, p2, val, off, size=3.0, color="#000"):
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
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" stroke="none"/>'
               % (fmt(xd - size * 0.6), fmt(ty - len(str(val)) * size * 0.3),
                  fmt(size * 1.2), fmt(len(str(val)) * size * 0.6)))
    out.append(text(xd - 1.1, ty, str(val), size, "middle", rot=-90))
    return "".join(out)


def cross(x, y, r=2.0, w=0.4):
    return (line(x - r, y, x + r, y, w) + line(x, y - r, x, y + r, w))


def centerline(x1, y1, x2, y2):
    return line(x1, y1, x2, y2, 0.15, dash="7 1.6 1.2 1.6", color="#333")


def callout(px, py, cx, cy, num, r=3.6):
    dx, dy = px - cx, py - cy
    d = math.hypot(dx, dy)
    if d > 1e-6:
        k = r / d
        sx, sy = cx + dx * k, cy + dy * k
    else:
        sx, sy = cx, cy
    return ("".join([
        line(sx, sy, px, py, 0.16),
        '<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke="#000" stroke-width="0.22"/>'
        % (fmt(cx), fmt(cy), fmt(r)),
        '<circle cx="%s" cy="%s" r="0.5" fill="#000"/>' % (fmt(px), fmt(py)),
        text(cx, cy + 1.15, str(num), 3.4, "middle", "bold"),
    ]))


# ----------------------------------------------------------------------------
# лист
# ----------------------------------------------------------------------------
def sheet(views):
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="1188" '
               'viewBox="0 0 420 297">')
    out.append('<rect width="420" height="297" fill="#fff"/>')
    # рамка
    out.append(rect(4, 4, 412, 289, 0.5))
    out.append(rect(6, 6, 408, 285, 0.25))
    # заголовок
    out.append(text(10, 13, "ВИБРОСТОЛ ДЛЯ ФИЗИЧЕСКОГО ЭКСПЕРИМЕНТА — ЭСКИЗНАЯ КОМПОНОВКА",
                    7.2, weight="bold"))
    out.append(text(410, 13, "A3 · 420×297", 4.5, "end"))
    out.append(line(8, 16.5, 412, 16.5, 0.35))

    # виды
    titles = {
        "front": ("Вид спереди (со стороны −X)", 40, 37),
        "side": ("Вид сбоку (слева, −Y)", 150, 37),
        "top": ("Вид сверху (−Z)", 30, 175),
    }
    for name in ("front", "side", "top"):
        mp = MAP[name]
        polys = views[name]
        paths = []
        for poly in polys:
            pts = [mp(u, v) for u, v in poly]
            d = "M " + " L ".join("%s %s" % (fmt(x), fmt(y)) for x, y in pts)
            paths.append('<path d="%s"/>' % d)
        out.append('<g fill="none" stroke="#000" stroke-width="0.28" '
                   'stroke-linecap="round" stroke-linejoin="round">%s</g>' % "".join(paths))
        t, tx, ty = titles[name]
        out.append(text(tx, ty, t, 4.6, weight="bold"))

    # ---- осевые ----
    # спереди: ось кулачка/привода
    cx, cy = p_front(0, 100, 140)
    out.append(centerline(cx - 12, cy, cx + 12, cy))
    out.append(centerline(cx, cy - 12, cx, cy + 12))
    out.append(text(cx + 13, cy + 1.2, "Z=140", 3.0, color="#333"))
    # сбоку: ось привода и кулачка
    x0, y0 = p_side(0, 100, 140)
    x1, y1 = p_side(255, 100, 140)
    out.append(centerline(x0, y0, x1, y1))
    x2, y2 = p_side(100, 100, 88)
    x3, y3 = p_side(100, 100, 200)
    out.append(centerline(x2, y2, x3, y3))
    out.append(text(x0 + 2, y0 - 2, "вал привода", 3.0, color="#333"))
    # сверху: ось привода и центры валов
    xa, ya = p_top(0, 100, 0)
    xb, yb = p_top(400, 100, 0)
    out.append(centerline(xa, ya, xb, yb))
    for gx in (50, 150):
        for gy in (15, 185):
            p = p_top(gx, gy, 0)
            out.append(centerline(p[0] - 4, p[1], p[0] + 4, p[1]))
            out.append(centerline(p[0], p[1] - 4, p[0], p[1] + 4))
    # ---- размеры: спереди ----
    out.append(dim_v(p_front(0, 0, 0), p_front(0, 0, 300), 300, -12))
    out.append(dim_h(p_front(0, 0, 0), p_front(0, 200, 0), 200, 7))
    out.append(dim_h(p_front(0, -20, 241), p_front(0, 220, 241), 240, -36))
    out.append(text(126.5, 64, "Ø10", 3.0, "start", color="#333"))
    # ---- размеры: сбоку ----
    out.append(dim_h(p_side(0, 0, 0), p_side(400, 0, 0), 400, 7))
    out.append(dim_h(p_side(0, 0, 0), p_side(200, 0, 0), 200, 14))
    out.append(dim_h(p_side(200, 0, 0), p_side(400, 0, 0), 200, 14))
    out.append(dim_v(p_side(400, 0, 0), p_side(400, 0, 300), 300, 8))
    out.append(dim_v(p_side(400, 0, 0), p_side(400, 0, 200), 200, 16))
    out.append(text(236, 130, "дрель условно", 3.0, color="#555"))
    # ---- размеры: сверху ----
    out.append(dim_h(p_top(0, -20, 0), p_top(400, -20, 0), 400, 7))
    out.append(dim_v(p_top(0, 0, 0), p_top(0, 200, 0), 200, -12))
    out.append(dim_v(p_top(400, -20, 0), p_top(400, 220, 0), 240, 8))
    out.append(dim_h(p_top(25, 220, 0), p_top(175, 220, 0), 150, -5))
    out.append(dim_h(p_top(50, 100, 0), p_top(150, 100, 0), 100, 7, size=2.8))
    out.append(dim_v(p_top(100, 15, 0), p_top(100, 185, 0), 170, 7, size=2.8))
    out.append(dim_v(p_top(300, 20, 0), p_top(300, 180, 0), 160, 4, size=2.8))

    # ---- фантом дрели ----
    out.append(line(*p_side(240, 100, 90), *p_side(380, 100, 90), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_side(240, 100, 190), *p_side(380, 100, 190), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_side(240, 100, 90), *p_side(240, 100, 190), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_side(380, 100, 90), *p_side(380, 100, 190), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_top(240, 50, 0), *p_top(380, 50, 0), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_top(240, 150, 0), *p_top(380, 150, 0), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_top(240, 50, 0), *p_top(240, 150, 0), 0.2, dash="4 2", color="#666"))
    out.append(line(*p_top(380, 50, 0), *p_top(380, 150, 0), 0.2, dash="4 2", color="#666"))

    # ---- выноски ----
    # спереди
    co = [
        (1, p_front(0, 15, 304), 8, 50),
        (3, p_front(0, 15, 260), 8, 72),
        (4, p_front(0, 60, 238), 8, 94),
        (5, p_front(0, 60, 230), 8, 112),
        (8, p_front(0, 50, 205), 8, 132),
        (22, p_front(0, 5, 60), 8, 152),
        (2, p_front(0, 185, 300), 135, 52),
        (6, p_front(0, 111, 200), 135, 76),
        (10, p_front(0, 150, 140), 135, 100),
        (21, p_front(0, 110, 116), 135, 124),
        (14, p_front(0, 60, 136), 135, 148),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))
    # сбоку
    co = [
        (11, p_side(300, 100, 195), 340, 46),
        (12, p_side(290, 47, 120), 356, 62),
        (20, p_side(220, 100, 140), 372, 78),
        (9, p_side(140, 100, 140), 388, 96),
        (7, p_side(100, 100, 205), 340, 120),
        (23, p_side(50, 15, 213), 372, 142),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))
    # сверху
    co = [
        (1, p_top(50, 15, 0), 9, 194),
        (2, p_top(150, 185, 0), 9, 214),
        (5, p_top(25, -20, 0), 9, 250),
        (4, p_top(100, 100, 0), 210, 196),
        (11, p_top(300, 100, 0), 210, 220),
    ]
    for num, p, cx, cy in co:
        out.append(callout(*p, cx, cy, num))

    # ---- примечания ----
    out.append(rect(250, 178, 162, 60, 0.25))
    out.append(text(253, 184, "ПРИМЕЧАНИЯ", 4.2, weight="bold"))
    notes = [
        "1. Ход стола 5 мм (R45…50); сменные диски 3 и 10 мм —",
        "   диапазон 3…10 мм. Закон близок к гармоническому.",
        "2. 4 пружины Ø12×1,0, L0≈55; установленная 34…44 мм.",
        "3. Рама — труба 20×20×1,5, сварная; крепление струбцинами.",
        "4. Накладка и кулачки — PLA; стол и подстолье — фанера 10.",
        "5. Дрель условно Ø100, ось Z=140; 2 U-хомута M6.",
        "6. Поз. 21–24 добавлены к эскизу; см. spec.csv.",
        "7. Габарит 400×240×308; масса ≈8,0 кг без дрели.",
        "8. Передняя (X=0) и ближняя (Y=0…25) рамы на видах условно не показаны.",
    ]
    y = 190
    for s in notes:
        out.append(text(253, y, s, 2.9))
        y += 5.2

    # ---- штамп ----
    out.append(rect(230, 245, 182, 47, 0.3))
    out.append(line(230, 254, 412, 254, 0.25))
    out.append(text(234, 252, "ВИБРОСТОЛ — ЭСКИЗ СБОРКИ", 8.0, weight="bold"))
    out.append(text(234, 261, "Этап: формирование эскизов по рисунку от руки", 3.6))
    out.append(text(234, 268, "Масштаб 1:2,5      Лист 1/1      Формат A3", 3.6))
    out.append(text(234, 275, "Единицы: мм. Масса ≈8,0 кг (без дрели)", 3.6))
    out.append(text(234, 282, "Модель: cad/step/vibrotable_assembly.step", 3.4))
    out.append(text(234, 288, "Спецификация: spec.csv (24 поз.)", 3.4))
    out.append(text(410, 288, "М 1:2,5", 4.0, "end"))

    out.append("</svg>")
    return "".join(out)


# ----------------------------------------------------------------------------
# изометрия (отдельный файл)
# ----------------------------------------------------------------------------
def iso_svg(views):
    polys = views["iso"]
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
        d = "M " + " L ".join("%.2f %.2f" % (ox + u * sc, oy - v * sc) for u, v in poly)
        paths.append('<path d="%s"/>' % d)
    svg = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<svg xmlns="http://www.w3.org/2000/svg" width="680" height="680" viewBox="0 0 170 170">'
           '<rect width="170" height="170" fill="#fff"/>'
           '<g fill="none" stroke="#000" stroke-width="0.35" stroke-linejoin="round">%s</g>'
           '<text x="85" y="164" font-family="%s" font-size="4" text-anchor="middle">'
           'Изометрия (HLR). М 1:2,5</text></svg>') % ("".join(paths), FONT)
    with open(os.path.join(FIG, "iso.svg"), "w", encoding="utf-8") as f:
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
    mass = []
    with open(os.path.join(HERE, "mass.csv"), encoding="utf-8") as f:
        r = csv.reader(f, delimiter=";")
        next(r)
        for row in r:
            if row[0] == "ИТОГО":
                total = row[5]
            else:
                mass.append(row)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="1188" '
           'viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, "ВИБРОСТОЛ — СПЕЦИФИКАЦИЯ И ПАРАМЕТРЫ", 7.2, weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    # спецификация
    out.append(text(10, 24, "СПЕЦИФИКАЦИЯ", 4.6, weight="bold"))
    cols = [10, 24, 112, 124, 160, 205]
    heads = ["Поз.", "Наименование", "Кол.", "Материал", "Размеры", "Изготовление"]
    for x, h in zip(cols, heads):
        out.append(text(x, 30, h, 3.2, weight="bold"))
    out.append(line(10, 31.5, 244, 31.5, 0.2))
    y = 37
    for row in spec:
        no, name, qty, mat, size, make, note = (row + [""] * 7)[:7]
        out.append(text(cols[0], y, no, 2.9))
        out.append(text(cols[1], y, name, 2.9))
        out.append(text(cols[2], y, qty, 2.9))
        out.append(text(cols[3], y, mat, 2.6))
        out.append(text(cols[4], y, size, 2.6))
        out.append(text(cols[5], y, make, 2.3))
        y += 4.55
    out.append(line(10, y - 1.6, 244, y - 1.6, 0.2))

    # параметры
    px = 250
    out.append(text(px, 24, "ОСНОВНЫЕ ПАРАМЕТРЫ", 4.6, weight="bold"))
    prm = [
        ("Габарит рамы", "400×200×300"),
        ("Труба рамы", "20×20×1,5"),
        ("Виброотсек / вынос", "200 / 200"),
        ("Стол", "150×240×10"),
        ("Накладка", "6; сфера Ø140, h2"),
        ("Шаги валов X×Y", "100×170"),
        ("Валы", "4 × Ø10, L=166"),
        ("LMF10UU", "4 × Ø10/Ø19"),
        ("Пружины", "4 × Ø12×1,0"),
        ("Ход стола", "5 (диски 3/10)"),
        ("Кулачок", "R45…50; ложб. 2"),
        ("Вал привода", "M10, ось Z=140"),
        ("Подстолье", "200×160, Z=190…200"),
        ("Дрель (условно)", "Ø100, X=250…380"),
        ("Масса без дрели", "≈8,0 кг"),
    ]
    yy = 30
    for k, v in prm:
        out.append(text(px, yy, k, 2.8))
        out.append(text(374, yy, v, 2.8, "end"))
        yy += 5.4

    # проверки / примечания
    out.append(text(10, 156, "ПРОВЕРКИ И ПРИНЯТЫЕ РЕШЕНИЯ", 4.2, weight="bold"))
    checks = [
        "Габарит рамы 400×200×300 — выполнен; габарит сборки 400×240×308",
        "(выступ стола по Y и ограничители валов по Z).",
        "Фланцы LMF10UU полностью на столе: запас 5 мм по X и 15 мм по Y.",
        "Зазор стол–рама при ходе вниз: 16 мм (низ стола 220, верх балки 170).",
        "Кулачок проходит в окно средней балки с зазором 2 мм.",
        "Контакт ролика с кулачком обеспечивают 4 пружины; ход 3/5/10 мм —",
        "сменными дисками. Пружина 12×1,0 номинально даёт ID 10,0 при вале Ø10;",
        "в модели принят ID 10,2 — при сборке проверить/притереть вал.",
        "Подстолье 200×160 не задевает фланцы LMF10UU (зазор ≥20 мм по Y).",
        "Крабы 14 — Т-образные, с выносом ~80 мм на угловые стойки.",
        "Поз. 21, 22 — балки фиксации и рама; 23, 24 — крепёж (добавлены).",
        "Испытание: шарик 20/33 г, частота 5…15 Гц (300…900 об/мин дрели).",
    ]
    yy = 163
    for s in checks:
        out.append(text(10, yy, s, 2.7))
        yy += 4.6

    # масса
    out.append(text(250, 122, "МАССА, г", 4.2, weight="bold"))
    out.append(text(250, 128, "Рама (22)", 2.7))
    out.append(text(374, 128, "4879", 2.7, "end"))
    out.append(text(250, 133.4, "Балки 21", 2.7))
    out.append(text(374, 133.4, "423", 2.7, "end"))
    out.append(text(250, 138.8, "Стол + подстолье + накладка", 2.7))
    out.append(text(374, 138.8, "715", 2.7, "end"))
    out.append(text(250, 144.2, "Привод и ролик (с покупными)", 2.7))
    out.append(text(374, 144.2, "960", 2.7, "end"))
    out.append(text(250, 149.6, "Крепёж и прочее", 2.7))
    out.append(text(374, 149.6, "1050", 2.7, "end"))
    out.append(line(250, 152, 404, 152, 0.2))
    out.append(text(250, 156.5, "ИТОГО (без дрели)", 3.0, weight="bold"))
    out.append(text(374, 156.5, total, 3.0, "end", weight="bold"))

    # штамп
    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "ВИБРОСТОЛ — СПЕЦИФИКАЦИЯ", 6.2, weight="bold"))
    out.append(text(253, 266, "Этап 1. Лист 2/2. Формат A3", 3.4))
    out.append(text(253, 274, "Данные: spec.csv, params.csv, cad/checks.csv", 3.2))
    out.append(text(253, 281, "Модель: cad/step/vibrotable_assembly.step", 3.2))
    out.append(text(253, 288, "Единицы: мм", 3.2))
    out.append("</svg>")
    with open(os.path.join(FIG, "vibrotable_spec.svg"), "w", encoding="utf-8") as f:
        f.write("".join(out))


# ----------------------------------------------------------------------------
def main():
    views = project_all()
    svg = sheet(views)
    fn = os.path.join(FIG, "vibrotable_views.svg")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(svg)
    iso_svg(views)
    spec_sheet()
    print("written", fn, flush=True)


main()
