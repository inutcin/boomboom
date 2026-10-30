"""Лист эскиза A3 этапа fix3: проекции из модели (HLR FreeCAD), размеры,
выноски, спецификация.

Запуск:
    freecadcmd draw_sheet.py [--force]

Кэш проекций: cad/cache/views_v5.json.
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
def project_all():
    cache = os.path.join(CACHE, "views_v5.json")
    if os.path.exists(cache) and not FORCE:
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    parts, groups, cams = model.build_assembly()
    comp = Part.makeCompound([i["shape"] for i in parts.values()])
    data = {}
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
        data[name] = polys
        print("projected", name, len(polys), "edges", flush=True)
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
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
               'height="1188" viewBox="0 0 420 297">')
    out.append('<rect width="420" height="297" fill="#fff"/>')
    out.append(rect(4, 4, 412, 289, 0.5))
    out.append(rect(6, 6, 408, 285, 0.25))
    out.append(text(10, 13,
                    "ВИБРОСТОЛ ДЛЯ ФИЗИЧЕСКОГО ЭКСПЕРИМЕНТА — "
                    "ЭСКИЗНАЯ КОМПОНОВКА (fix3). М 1:3", 6.0, weight="bold"))
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
        for poly in views[name]:
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
        (16, p_side(80, 140), 250, 104),
        (24, p_side(0, 68), 250, 116),
        (23, p_side(50, 213), 250, 128),
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
    out.append(rect(252, 150, 158, 88, 0.25))
    out.append(text(255, 156, "ПРИМЕЧАНИЯ", 4.0, weight="bold"))
    notes = [
        "1. Ход стола 5 мм (R45…50); сменные диски 3/10 мм — диапазон",
        "   3…10 мм; закон близок к гармоническому.",
        "2. Рама 360×200×300 — PETG, сплошное 20×20, печать одним куском.",
        "3. Виброотсек 160, вынос 200; поперечин в выносе нет — жёсткость",
        "   даёт подстолье; верхние продольные балки выноса 140…360.",
        "4. Стол 200×150×10 и накладка 200×150×6 — PLA; отверстия под",
        "   валы Ø11 (стол) и Ø12 (накладка).",
        "5. Балка 21 — PETG, карман 6200 9,4 мм; 8 накладок-уголков 2 мм:",
        "   полка 60×20 на боковой грани балки (2 болта M4 насквозь), вниз",
        "   по стойке — 2 паза 20 мм и 2 прижимных болта M4 на пару.",
        "   Допускается замена покупной краб-системой «угол» 20×20.",
        "6. Кулачок: ложбинка 2 мм, бортик скошен 58°, фаска 1×45° на",
        "   отверстии, 8 отверстий Ø10 на R32; диски 3/5/10 мм.",
        "7. Подстолье 160×200×12 без рёбер, X=200…360; болты M6×45 с",
        "   головкой сверху, гайки снизу верхних балок.",
        "8. Дрель: против часовой, мягкий пуск, регулировка, курок; Ø100.",
        "9. Габарит сборки 380×200×308; масса ≈5,5 кг без дрели.",
    ]
    y = 162
    for s in notes:
        out.append(text(255, y, s, 2.55))
        y += 4.5

    # ---- штамп ----
    out.append(rect(250, 246, 162, 45, 0.3))
    out.append(line(250, 254, 412, 254, 0.25))
    out.append(text(254, 252, "ВИБРОСТОЛ — ЭСКИЗ СБОРКИ (fix3)", 7.0,
                    weight="bold"))
    out.append(text(254, 260,
                    "Этап fix3: третье устранение замечаний", 3.4))
    out.append(text(254, 267,
                    "Масштаб 1:3      Лист 1/2      Формат A3", 3.5))
    out.append(text(254, 274,
                    "Единицы: мм. Масса ≈5,5 кг (без дрели)", 3.5))
    out.append(text(254, 281,
                    "Модель: cad/step/vibrotable_assembly.step", 3.3))
    out.append(text(254, 287, "Спецификация: spec.csv (28 поз.)", 3.3))
    out.append(text(410, 287, "М 1:3", 4.0, "end"))

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
                "ВИБРОСТОЛ (fix3) — СПЕЦИФИКАЦИЯ И ПАРАМЕТРЫ", 7.2,
                weight="bold"),
           line(8, 16.5, 412, 16.5, 0.35)]
    out.append(text(10, 23, "СПЕЦИФИКАЦИЯ", 4.6, weight="bold"))
    cols = [10, 24, 110, 124, 156, 200]
    heads = ["Поз.", "Наименование", "Кол.", "Материал", "Размеры",
             "Изготовление"]
    for x, h in zip(cols, heads):
        out.append(text(x, 29, h, 3.2, weight="bold"))
    out.append(line(10, 30.5, 248, 30.5, 0.2))
    y = 35
    for row in spec:
        no, name, qty, mat, size, make, note = (row + [""] * 7)[:7]
        out.append(text(cols[0], y, no, 2.7))
        out.append(text(cols[1], y, clip(name, 33), 2.7))
        out.append(text(cols[2], y, clip(qty, 9), 2.7))
        out.append(text(cols[3], y, clip(mat, 11), 2.4))
        out.append(text(cols[4], y, clip(size, 28), 2.35))
        out.append(text(cols[5], y, clip(make, 34), 2.0))
        y += 4.15
    out.append(line(10, y - 1.4, 248, y - 1.4, 0.2))

    px = 252
    out.append(text(px, 23, "ОСНОВНЫЕ ПАРАМЕТРЫ", 4.6, weight="bold"))
    prm = [
        ("Габарит рамы", "360×200×300"),
        ("Сечение рамы", "20×20 сплошное, PETG"),
        ("Виброотсек / вынос", "160 / 200"),
        ("Стол", "200×150×10 (X=−20…180)"),
        ("Накладка", "200×150×6; сфера Ø140, h2"),
        ("Шаги валов X×Y", "140×100"),
        ("Валы", "4 × Ø10, L=166"),
        ("LMK10UU", "4 × Ø10/Ø19, фланец 40×40"),
        ("Пружины", "4 × Ø12×1,0 + 8 шайб"),
        ("Ход стола", "5 (диски 3/10)"),
        ("Кулачок", "R45…50; ложб. 2; бортик 58°"),
        ("Кулачок — облегчение", "8 × Ø10 на R32"),
        ("Карман 6200", "9,4 мм; плечо 5,3; зазор 0,2"),
        ("Накладки балки 21", "8 × сталь 2; полка 60×20"),
        ("Вал привода", "M10, X=−10…215, ось Z=140"),
        ("Подстолье", "160×200×12 без рёбер, X=200…360"),
        ("Дрель", "Ø100; против часовой"),
    ]
    yy = 30
    for k, v in prm:
        out.append(text(px, yy, k, 2.6))
        out.append(text(408, yy, v, 2.6, "end"))
        yy += 4.7

    out.append(text(px, 114, "МАССА, г", 4.2, weight="bold"))
    labels = [("petg", "PETG (рама, балка 21, подстолье)"),
              ("pla", "PLA (стол, накладка, кулачок)"),
              ("steel", "Сталь (валы, крепёж, уголки)"),
              ("bearing", "Подшипники (LMK, 6200)")]
    yy = 120
    for key, label in labels:
        out.append(text(px, yy, label, 2.6))
        out.append(text(408, yy, "%.0f" % mat_sum.get(key, 0.0), 2.6, "end"))
        yy += 5.2
    out.append(line(252, yy - 1.8, 410, yy - 1.8, 0.2))
    out.append(text(px, yy + 4, "ИТОГО (без дрели)", 3.0, weight="bold"))
    out.append(text(408, yy + 4, total, 3.0, "end", weight="bold"))

    out.append(text(10, 160, "ПРОВЕРКИ И ПРИНЯТЫЕ РЕШЕНИЯ", 4.2,
                    weight="bold"))
    checks = [
        "Рама — одно тело, 360×200×300; виброотсек 160 мм. Средние боковые",
        "балки, центральная балка с окном, задние поперечины удалены.",
        "В выносе поперечин нет: только 2 верхние продольные балки 140…360,",
        "опирающиеся на граничную поперечину; жёсткость даёт подстолье.",
        "Стол 200×150 выступает на 20 мм спереди и у выноса; зазор 5 мм",
        "до стоек; отверстия под валы Ø11 (стол) и Ø12 (накладка).",
        "Карманы 6200 — 9,4 мм в центральной части поперечин и балок 21;",
        "осевой зазор 0,2 мм, плечо 5,3 мм; вал зажат гайками с двух сторон.",
        "Балка 21 в распор между стойками; 8 накладок-уголков 2 мм: полка",
        "60×20 на боковой грани балки (2 болта M4), вниз по стойке — 2 паза",
        "20 мм и 2 прижимных болта M4 на пару; ход опускания 15 мм.",
        "Кулачок: конический бортик ложбинки 2 мм — самоцентровка ролика;",
        "фаска 1×45°; 8 отверстий Ø10 на R32; диски 3/5/10 мм.",
        "Подстолье 160×200×12 без рёбер, X=200…360; крепление 4 болтами",
        "M6×45 с головкой сверху, гайки снизу верхних балок.",
        "Проверки: 143/144 OK; предупреждение — пружина 12×1,0 даёт ID 10,0",
        "при вале Ø10; в модели ID 10,2 (при сборке притереть).",
        "Дрель: против часовой стрелки, мягкий пуск, регулировка оборотов,",
        "фиксируемый курок. Испытание: шарик 20/33 г, 5…15 Гц.",
    ]
    yy = 167
    for s in checks:
        out.append(text(10, yy, s, 2.5))
        yy += 4.0

    out.append(rect(250, 250, 162, 41, 0.3))
    out.append(text(253, 258, "ВИБРОСТОЛ — СПЕЦИФИКАЦИЯ (fix3)", 6.0,
                    weight="bold"))
    out.append(text(253, 266, "Этап fix3. Лист 2/2. Формат A3", 3.4))
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
