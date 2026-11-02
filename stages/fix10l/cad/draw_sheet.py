"""Листы эскизов A3 этапа fix10l.

Проекции строятся из модели (HLR FreeCAD), детальные листы и лист труб —
по параметрам модели. Запуск:

    freecadcmd draw_sheet.py [--force]

Кэш проекций: cad/cache/views_v10l.json.
"""

import csv
import json
import math
import os
import sys

import FreeCAD as App
import Drawing
import Part

import model
from params import P

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
STAGE = os.path.dirname(HERE)
FIG = os.path.join(STAGE, "fig")
CACHE = os.path.join(HERE, "cache")
os.makedirs(FIG, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

FORCE = "--force" in sys.argv
FONT = "DejaVu Sans, Arial, sans-serif"
S = 1.0 / 3.0

# страница
XA, XB, XT = 18.0, 110.0, 18.0
ZB, YT = 180.0, 285.0

VIEW_DEF = {
    "front": (-1, 0, 0),
    "side": (0, -1, 0),
    "top": (0, 0, 1),
    "iso": (-1, -1, 1),
}


# ----------------------------------------------------------------------------
# проекции
# ----------------------------------------------------------------------------
def _edges_to_polys(shape):
    out = Drawing.project(shape, None) if False else None
    return out


def project_all():
    fn = os.path.join(CACHE, "views_v10l.json")
    if os.path.exists(fn) and not FORCE:
        with open(fn, "r", encoding="utf-8") as f:
            return json.load(f)

    parts, groups, cams = model.build_assembly()
    mech_exclude = {"table", "overlay", "top_platform", "base", "podstol",
                    "spring_pads", "drill", "drill_pads"}
    sets = {
        "full": [i["shape"] for i in parts.values()],
        "open": [i["shape"] for k, i in parts.items()
                 if k not in ("top_platform", "drill")],
        "mech": [i["shape"] for k, i in parts.items()
                 if k not in mech_exclude],
    }
    data = {}
    for setname, shapes in sets.items():
        comp = Part.makeCompound(shapes)
        data[setname] = {}
        for name, d in VIEW_DEF.items():
            visible = Drawing.project(comp, App.Vector(*d))[0]
            polys = []
            for e in visible.Edges:
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
            print("projected", setname, name, len(polys), flush=True)
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


# ----------------------------------------------------------------------------
# svg helpers
# ----------------------------------------------------------------------------
def fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


def line(x1, y1, x2, y2, w=0.18, dash=None, color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
            'stroke-width="%s"%s/>'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), color, w, d))


def rect(x, y, w, h, sw=0.2, fill="none", color="#000"):
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" '
            'stroke="%s" stroke-width="%s"/>'
            % (fmt(x), fmt(y), fmt(w), fmt(h), fill, color, sw))


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
    w = max(2.0, len(str(s)) * size * 0.56)
    if anchor == "middle":
        x0 = x - w / 2
    elif anchor == "end":
        x0 = x - w
    else:
        x0 = x
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" '
            'stroke="none"/>' % (fmt(x0), fmt(y - size * 0.9), fmt(w),
                                 fmt(size * 1.15)))


def arrow(x, y, dx, dy, size=1.5):
    bx, by = x - dx * size, y - dy * size
    px, py = -dy * 0.45, dx * 0.45
    return ('<polygon points="%s,%s %s,%s %s,%s" fill="#000"/>'
            % (fmt(x), fmt(y), fmt(bx + px), fmt(by + py),
               fmt(bx - px), fmt(by - py)))


def dim_h(p1, p2, val, off, size=2.6):
    x1, y1 = p1
    x2, y2 = p2
    ym = (y1 + y2) / 2.0
    yd = ym + off
    sg = 1 if off >= 0 else -1
    out = [line(x1, y1, x1, yd + sg * 1.6, 0.12),
           line(x2, y2, x2, yd + sg * 1.6, 0.12),
           line(x1, yd, x2, yd, 0.16),
           arrow(x1, yd, -1 if x1 < x2 else 1, 0),
           arrow(x2, yd, 1 if x1 < x2 else -1, 0),
           txt_bg((x1 + x2) / 2, yd - 1.0, val, size),
           text((x1 + x2) / 2, yd - 1.0, val, size, "middle")]
    return "".join(out)


def dim_v(p1, p2, val, off, size=2.6):
    x1, y1 = p1
    x2, y2 = p2
    xm = (x1 + x2) / 2.0
    xd = xm + off
    sg = 1 if off >= 0 else -1
    ty = (y1 + y2) / 2
    out = [line(x1, y1, xd + sg * 1.6, y1, 0.12),
           line(x2, y2, xd + sg * 1.6, y2, 0.12),
           line(xd, y1, xd, y2, 0.16),
           arrow(xd, y1, 0, -1 if y1 < y2 else 1),
           arrow(xd, y2, 0, 1 if y1 < y2 else -1),
           txt_bg(xd - 1.0, ty, val, size),
           text(xd - 1.0, ty, val, size, "middle", rot=-90)]
    return "".join(out)


def centerline(x1, y1, x2, y2):
    return line(x1, y1, x2, y2, 0.14, dash="6 1.5 1 1.5", color="#444")


def p_front(Y, Z):
    return (XA + S * Y, ZB - S * Z)


def p_side(X, Z):
    return (XB + S * X, ZB - S * Z)


def p_top(X, Y):
    return (XT + S * X, YT - S * Y)


def map_front(u, v):
    return (XA + S * (-v), ZB + S * u)


def map_side(u, v):
    return (XB + S * v, ZB + S * u)


def map_top(u, v):
    return (XT + S * u, YT - S * v)


MAP = {"front": map_front, "side": map_side, "top": map_top}


def draw_view(out, polys, mp, sw=0.26):
    paths = []
    for poly in polys:
        pts = [mp(u, v) for u, v in poly]
        d = "M " + " L ".join("%s %s" % (fmt(x), fmt(y)) for x, y in pts)
        paths.append('<path d="%s"/>' % d)
    out.append('<g fill="none" stroke="#000" stroke-width="%s" '
               'stroke-linecap="round" stroke-linejoin="round">%s</g>'
               % (sw, "".join(paths)))


def page(title, subtitle=""):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="1680" '
           'height="1188" viewBox="0 0 420 297">',
           '<rect width="420" height="297" fill="#fff"/>',
           rect(4, 4, 412, 289, 0.5), rect(6, 6, 408, 285, 0.25),
           text(10, 13, title, 5.4, weight="bold"),
           text(410, 13, "A3 · 420×297", 4.0, "end"),
           line(8, 16.5, 412, 16.5, 0.35)]
    if subtitle:
        out.append(text(10, 22, subtitle, 3.2, color="#333"))
    return out


def save(fn, out):
    if not out or "</svg>" not in out[-1]:
        out.append("</svg>")
    with open(os.path.join(FIG, fn), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote", fn, flush=True)


# ----------------------------------------------------------------------------
# лист проекций
# ----------------------------------------------------------------------------
def sheet_views(views):
    out = page("ВИБРОСТОЛ «ОРОЧИЙ» fix10l — ОБЩИЙ ВИД. М 1:3",
               "Рама, LMK10UU, направляющие валы и опорные 6200 отсутствуют. "
               "Накладка и кулачки — переиспользование fix9.")
    vv = views["full"]

    for name in ("front", "side", "top"):
        draw_view(out, vv[name], MAP[name])

    out.append(text(XA - 2, 39, "Вид спереди (со стороны −X)", 4.0,
                    weight="bold"))
    out.append(text(XB - 2, 39, "Вид слева (со стороны −Y)", 4.0,
                    weight="bold"))
    out.append(text(XT - 2, 210, "Вид сверху (−Z)", 4.0, weight="bold"))

    # осевые
    for y in (15, 185):
        x, yy = p_front(y, 0)
        out.append(centerline(x, yy - 3, x, yy + 3))
        out.append(centerline(x, yy - 3, x, 70))
    x, y = p_front(100, 140)
    out.append(centerline(x - 8, y, x + 8, y))
    out.append(text(x + 9, y + 1, "вал Z=140", 2.2, color="#444"))
    for xx in (30, 175, 385):
        x0, y0 = p_side(xx, 0)
        out.append(centerline(x0, y0 - 2, x0, 66))
    x0, y0 = p_side(80, 0)
    out.append(centerline(x0, y0 - 2, x0, 78))
    out.append(text(x0 - 2, 80, "ось кулачка X=100", 2.1, color="#444"))

    for x in (30, 175, 385):
        for y in (15, 185):
            px, py = p_top(x, y)
            out.append(centerline(px - 2.5, py, px + 2.5, py))
            out.append(centerline(px, py - 2.5, px, py + 2.5))

    # размеры: спереди
    out.append(dim_v(p_front(0, 0), p_front(0, 300), 300, -9))
    out.append(dim_h(p_front(0, 0), p_front(200, 0), 200, 6))
    out.append(dim_h(p_front(0, 235), p_front(200, 235), 200, 4))
    out.append(dim_h(p_front(25, 241), p_front(175, 241), 150, -4))
    out.append(dim_h(p_front(40, 290), p_front(160, 290), 120, -4))
    out.append(dim_v(p_front(200, 225), p_front(200, 235), 10, 5))
    out.append(dim_v(p_front(200, 280), p_front(200, 290), 10, 5))
    out.append(text(p_front(100, 302)[0], p_front(100, 302)[1],
                    "вырез 120×120", 2.2, "middle", color="#444"))

    # размеры: слева
    out.append(dim_h(p_side(0, 0), p_side(400, 0), 400, 6))
    out.append(dim_h(p_side(0, 0), p_side(200, 0), 200, 13))
    out.append(dim_h(p_side(200, 0), p_side(400, 0), 200, 13))
    out.append(dim_v(p_side(400, 0), p_side(400, 300), 300, 7))
    out.append(dim_h(p_side(0, 241), p_side(200, 241), 200, -4))
    out.append(dim_h(p_side(0, 290), p_side(200, 290), 200, -4))
    for z, label in ((20, "20"), (130, "130"), (150, "150"),
                     (174, "174"), (194, "194"), (225, "225"),
                     (235, "235"), (241, "241"), (280, "280"),
                     (290, "290")):
        x, y = p_side(0, z)
        out.append(line(x - 2, y, x - 0.5, y, 0.15))
        out.append(text(x - 2.4, y + 0.8, label, 1.9, "end", color="#444"))

    # размеры: сверху
    out.append(dim_h(p_top(0, 0), p_top(400, 0), 400, 6))
    out.append(dim_v(p_top(0, 0), p_top(0, 200), 200, -8))
    out.append(dim_h(p_top(0, 200), p_top(200, 200), 200, 6))
    out.append(dim_v(p_top(200, 0), p_top(200, 200), 200, 4))
    out.append(dim_h(p_top(0, 25), p_top(200, 25), 200, 4))
    out.append(dim_v(p_top(200, 25), p_top(200, 175), 150, 4))
    out.append(dim_h(p_top(40, 40), p_top(160, 40), 120, 5))
    out.append(dim_v(p_top(40, 40), p_top(40, 160), 120, -5))
    for x in (30, 175, 385):
        for y in (15, 185):
            px, py = p_top(x, y)
            out.append(circle(px, py, 1.2, 0.2, fill="#fff"))
            out.append(text(px + 1.8, py + 1.0, "Ø11", 1.8, color="#444"))

    # выноски/подписи
    notes = [
        ("ОРОЧЬЯ ВЕРСИЯ", 6),
        ("1. 6 шпилек M10: 4 виброотсека + 2 подстолья.", 3),
        ("2. Стол 200×200, фанера 10; скользит по шпилькам.", 3),
        ("3. Накладка fix9 200×150 по центру; без отверстий под шпильки.", 3),
        ("4. Верхняя платформа: вырез 120×120.", 3),
        ("5. Пружины 4×Ø17×1,5×60; шайбы Ø20×2; 2 полосы 200×25×5.", 3),
        ("6. Нижние демпферы — резиновые кольца Ø30/12×2.", 3),
        ("7. Вал M10: 20 мм за балку; 2 шайбы + гайка + jam с каждой стороны.", 3),
        ("8. Кулачки fix9 R45/50; ход 3/5/10.", 3),
        ("9. Дрель Ø100 — условно; U-болты M6 R70.", 3),
        ("10. Подстолье: 2 nyloc + болт M10 с гайкой снизу.", 3),
        ("11. Габарит 400×200×300; масса без дрели ≈5,7 кг.", 3),
    ]
    yy = 226
    for s, sz in notes:
        out.append(text(258, yy, s, sz, weight="bold" if sz > 3 else "normal"))
        yy += 5.4 if sz > 3 else 4.6
    out.append(text(258, 224, "ПРИМЕЧАНИЯ", 3.2, weight="bold"))
    out.append(text(258, 288, "Смазать шпильки; проверить ход 3/5/10.",
                    2.6, color="#444"))

    save("vibrotable_views.svg", out)


def sheet_mechanism(views):
    out = page("ВИБРОСТОЛ fix10l — МЕХАНИЗМ БЕЗ СТОЛА И ОСНОВАНИЯ. М 1:3",
               "Показаны шпильки, балки, пружины, кулачок, ролик и вал.")
    vv = views["mech"]
    for name in ("front", "side"):
        draw_view(out, vv[name], MAP[name])
    out.append(text(XA - 2, 39, "Вид спереди", 4.0, weight="bold"))
    out.append(text(XB - 2, 39, "Вид слева", 4.0, weight="bold"))
    # основные уровни и оси
    for z, label in ((130, "130"), (150, "150"), (174, "174"),
                     (194, "194"), (205, "205"), (225, "225")):
        x, y = p_side(0, z)
        out.append(line(x - 2, y, x - 0.4, y, 0.16))
        out.append(text(x - 2.4, y + 0.8, label, 2.0, "end", color="#444"))
    x, y = p_front(100, 140)
    out.append(centerline(x - 8, y, x + 8, y))
    out.append(text(x + 9, y + 1, "ось вала Z=140", 2.2, color="#444"))
    x, y = p_front(100, 205)
    out.append(centerline(x - 8, y, x + 8, y))
    out.append(text(x + 9, y + 1, "ось ролика Z=205", 2.2, color="#444"))
    out.append(dim_v(p_front(0, 130), p_front(0, 225), 95, -8))
    out.append(dim_h(p_side(0, 0), p_side(400, 0), 400, 6))
    notes = [
        ("МЕХАНИЗМ", 5),
        ("1. Поперечные балки 20×20×2 — две опоры скольжения вала.", 3),
        ("2. Кулачок fix9 сидит на приваренной гайке M10.", 3),
        ("3. Ролик 6200 на оси M10 между двумя уголками 2 мм.", 3),
        ("4. Уголки крепятся к столу 4 саморезами M4×12.", 3),
        ("5. Пружины 4×Ø17×1,5×60; нижние демпферы — резина.", 3),
        ("6. Вал: 2 шайбы + гайка + jam с каждой стороны балки.", 3),
        ("7. Подстолье: болт M10, головка сверху, nyloc снизу.", 3),
    ]
    yy = 240
    for s, sz in notes:
        out.append(text(258, yy, s, sz, weight="bold" if sz > 3 else "normal"))
        yy += 6.0 if sz > 3 else 4.8
    save("mechanism.svg", out)


# ----------------------------------------------------------------------------
# детальный лист
# ----------------------------------------------------------------------------
def plate_panel(out, x, y, w, h, title, dims, note, holes=(), cuts=()):
    out.append(text(x, y - 4, title, 3.4, weight="bold"))
    out.append(rect(x, y, w, h, 0.3))
    for (cx, cy, r) in holes:
        out.append(circle(x + cx, y + cy, r, 0.22))
    for (cx, cy, cw, ch) in cuts:
        out.append(rect(x + cx, y + cy, cw, ch, 0.22))
    for d in dims:
        if d[0] == "h":
            out.append(dim_h((x + d[1], y + d[2]), (x + d[3], y + d[4]),
                             d[5], d[6], 2.2))
        else:
            out.append(dim_v((x + d[1], y + d[2]), (x + d[3], y + d[4]),
                             d[5], d[6], 2.2))
    out.append(text(x, y + h + 4.2, note, 2.3, color="#333"))


def sheet_details():
    out = page("ДЕТАЛИ, ТРЕБУЮЩИЕ ИЗГОТОВЛЕНИЯ (fix10l)",
               "Фанера 5/10/20 мм, труба 20×20×2, полоса 2×20. М 1:4 (плиты "
               "и полосы), 1:1 (уголок).")
    # основание 400x200, 1:4
    holes = []
    for x in (30, 175, 385):
        for y in (15, 185):
            holes.append((x * 0.25, y * 0.25, 11 * 0.25 / 2))
    plate_panel(out, 18, 40, 100, 50, "ОСНОВАНИЕ, фанера 24",
                [("h", 0, 0, 100, 0, 400, 6),
                 ("v", 100, 0, 100, 50, 200, 5)],
                "6×Ø11 + цековки Ø22×20 снизу; 400×200×24", holes)

    # стол 200x200, 1:4
    holes = []
    for x in (30, 175):
        for y in (15, 185):
            holes.append((x * 0.25, y * 0.25, 11 * 0.25 / 2))
    for x in (5, 195):
        for y in (30, 170):
            holes.append((x * 0.25, y * 0.25, 4.2 * 0.25 / 2))
    plate_panel(out, 140, 40, 50, 50, "СТОЛ, фанера 10",
                [("h", 0, 0, 50, 0, 200, 5),
                 ("v", 50, 0, 50, 50, 200, 4)],
                "4×Ø11 под шпильки; 4×Ø4,2×6 под накладку",
                holes)

    # платформа 200x200, вырез 120x120, 1:4
    holes = []
    for x in (30, 175):
        for y in (15, 185):
            holes.append((x * 0.25, y * 0.25, 11 * 0.25 / 2))
    plate_panel(out, 210, 40, 50, 50, "ПЛАТФОРМА, фанера 10",
                [("h", 0, 0, 50, 0, 200, 5),
                 ("v", 50, 0, 50, 50, 200, 4)],
                "вырез 120×120; 4×Ø11",
                holes, cuts=[(10, 10, 30, 30)])

    # подстолье 200x200, 1:4
    holes = []
    for y in (15, 185):
        holes.append(((385 - 200) * 0.25, y * 0.25, 11 * 0.25 / 2))
    for x in (240, 300):
        for y in (30, 170):
            holes.append(((x - 200) * 0.25, y * 0.25, 7 * 0.25 / 2))
    holes.append(((250 - 200) * 0.25, 15 * 0.25, 11 * 0.25 / 2))
    plate_panel(out, 280, 40, 50, 50, "ПОДСТОЛЬЕ, фанера 10",
                [("h", 0, 0, 50, 0, 200, 5),
                 ("v", 50, 0, 50, 50, 200, 4)],
                "2×Ø11 + 1×Ø11 болт; 4×Ø7; 200×200×10", holes)

    # уголок 50x50, 1:1 (профиль)
    x, y = 18, 135
    out.append(text(x, y - 4, "УГОЛОК 50×50×2", 3.4,
                    weight="bold"))
    out.append(line(x, y, x, y + 50, 0.35))
    out.append(line(x, y + 50, x + 50, y + 50, 0.35))
    out.append(line(x + 2, y, x + 2, y + 48, 0.35))
    out.append(line(x + 2, y + 48, x + 50, y + 48, 0.35))
    out.append(circle(x + 1, y + 20, 10.5 / 2, 0.25))
    for xx in (13, 38):
        for yy in (42, 48):
            out.append(circle(x + xx, y + yy, 4.2 / 2, 0.2))
    out.append(dim_h((x, y + 50), (x + 50, y + 50), 50, 6, 2.2))
    out.append(dim_v((x + 50, y), (x + 50, y + 50), 50, 5, 2.2))
    out.append(text(x, y + 62, "ширина 20; 2 шт.; отверстие оси Ø10,5 на 20 мм "
                    "ниже полки; 4×Ø4,2 под саморез M4×12", 2.3, color="#333"))

    # подкладка 20x20, 2:1
    x, y = 105, 150
    out.append(text(x, y - 4, "ПОДКЛАДКА 2 шт., 1:4", 3.4,
                    weight="bold"))
    out.append(rect(x, y, 50, 6.25, 0.3))
    for xx in (7.5, 43.75):
        out.append(circle(x + xx, y + 3.125, 1.5, 0.25))
    for xx in (15.0, 25.0, 35.0):
        out.append(circle(x + xx, y + 3.125, 0.525, 0.2))
    out.append(dim_h((x, y + 6.25), (x + 50, y + 6.25), 200, 6, 2.2))
    out.append(dim_v((x + 50, y), (x + 50, y + 6.25), 25, 5, 2.2))
    out.append(text(x, y + 16, "фанера 5; 2×Ø12; 3×Ø4,2; 2 шт.", 2.3,
                    color="#333"))

    # таблица отверстий
    out.append(text(165, 130, "ОТВЕРСТИЯ И ПОСАДКИ", 3.3, weight="bold"))
    rows = [
        ("Стол", "4×Ø11", "X=30/175; Y=15/185"),
        ("Стол", "4×Ø4,2×6", "X=5/195; Y=30/170; глухие"),
        ("Платформа", "4×Ø11", "X=30/175; Y=15/185"),
        ("Платформа", "вырез 120×120", "X=40…160; Y=40…160"),
        ("Основание", "6×Ø11", "X=30/175/385; Y=15/185"),
        ("Основание", "6×Ø22×20", "цековки снизу"),
        ("Подстолье", "2×Ø11", "X=385; Y=15/185"),
        ("Подстолье", "4×Ø7", "X=240/300; Y=30/170"),
        ("Подстолье", "1×Ø11", "X=250; Y=15; болт M10"),
        ("Подкладки", "2×Ø12", "X=30/175; Y=15/185"),
        ("Подкладки", "3×Ø4,2", "X=60/100/140; Y=12,5/187,5"),
        ("Балки", "Ø10,2", "вал: X=30/175; Y=100; Z=140"),
    ]
    yy = 137
    for a, b, c in rows:
        out.append(text(165, yy, a, 2.2))
        out.append(text(205, yy, b, 2.2))
        out.append(text(245, yy, c, 2.2))
        yy += 4.8

    out.append(text(165, 193, "ПЕРЕИСПОЛЬЗОВАНИЕ", 3.3, weight="bold"))
    out.append(text(165, 200, "Накладка fix9 200×150×6 — без изменений.", 2.4))
    out.append(text(165, 205, "Кулачки fix9 cam_3/5/10 — без изменений.", 2.4))
    out.append(text(165, 210, "Новых печатных деталей нет.", 2.4))
    out.append(text(165, 218, "Трубы и шпильки — см. beam_cut.csv / лист труб.",
                    2.4, color="#333"))
    out.append(text(165, 228, "Все острые кромки фанеры и труб притупить.",
                    2.4, color="#333"))
    save("details.svg", out)


# ----------------------------------------------------------------------------
# лист труб
# ----------------------------------------------------------------------------
def sheet_beams():
    out = page("ЛИСТ ТРУБ И ОТРЕЗОВ ШПИЛЕК (fix10l)",
               "Труба 20×20×2; все резы 90°. Отверстия — по месту/кондуктору.")
    rows = [
        ("B01", "Продольная (Y=15)", "20×20×2", "400", "1", "4×Ø11: 30/175/385 + 250 болт"),
        ("B02", "Продольная (Y=185)", "20×20×2", "400", "1", "3×Ø11: 30/175/385"),
        ("B03", "Поперечная", "20×20×2", "200", "1", "2×Ø11 + Ø10,2"),
        ("B04", "Поперечная", "20×20×2", "200", "1", "2×Ø11 + Ø10,2"),
        ("R01", "Шпилька M10", "Ø10", "300", "4", "резьба M10"),
        ("R02", "Шпилька M10", "Ø10", "220", "2", "резьба M10"),
    ]
    x0, y0 = 10, 24
    cols = (10, 32, 92, 132, 160, 190)
    out.append(text(x0, y0, "№", 2.4, weight="bold"))
    out.append(text(cols[1], y0, "Элемент", 2.4, weight="bold"))
    out.append(text(cols[2], y0, "Сечение", 2.4, weight="bold"))
    out.append(text(cols[3], y0, "L, мм", 2.4, weight="bold"))
    out.append(text(cols[4], y0, "Кол.", 2.4, weight="bold"))
    out.append(text(cols[5], y0, "Отверстия / примечание", 2.4,
                    weight="bold"))
    out.append(line(x0, y0 + 1.5, 410, y0 + 1.5, 0.2))
    yy = y0 + 7
    for r in rows:
        out.append(text(cols[0], yy, r[0], 2.2))
        out.append(text(cols[1], yy, r[1], 2.2))
        out.append(text(cols[2], yy, r[2], 2.2))
        out.append(text(cols[3], yy, r[3], 2.2))
        out.append(text(cols[4], yy, r[4], 2.2))
        out.append(text(cols[5], yy, r[5], 2.2))
        yy += 5.2

    # B01 продольная, 1:2.5 (0.4)
    sc = 0.40
    x, y = 20, 90
    out.append(text(x, y - 4, "B01 — с болтом 250; B02 — без него; 400 мм, 1:2,5", 3.2,
                    weight="bold"))
    out.append(rect(x, y, 400 * sc, 20 * sc, 0.3))
    for xx in (30, 175, 250, 385):
        out.append(circle(x + xx * sc, y + 10 * sc, 11 * sc / 2, 0.22))
        out.append(text(x + xx * sc - 4, y - 1, str(xx), 1.9, color="#444"))
    out.append(dim_h((x, y + 20 * sc), (x + 400 * sc, y + 20 * sc), 400, 6,
                     2.2))
    out.append(text(x, y + 18, "Ø11 — шпильки 30/175/385; болт 250 только в B01 (Y=15)", 2.1, color="#333"))

    # B03 поперечная, 0.4
    x, y = 20, 125
    out.append(text(x, y - 4, "B03/B04 — поперечная балка 200 мм, 1:2,5", 3.2,
                    weight="bold"))
    out.append(rect(x, y, 200 * sc, 20 * sc, 0.3))
    for yy2 in (15, 185):
        out.append(circle(x + yy2 * sc, y + 10 * sc, 11 * sc / 2, 0.22))
    out.append(circle(x + 100 * sc, y + 10 * sc, 10.2 * sc / 2, 0.25))
    out.append(dim_h((x, y + 20 * sc), (x + 200 * sc, y + 20 * sc), 200, 6,
                     2.2))
    out.append(text(x, y + 18, "Ø11 — шпильки Y=15/185; Ø10,2 — вал Y=100, "
                    "Z=140", 2.1, color="#333"))

    # сечение 20x20x2, 2:1
    x, y = 270, 90
    out.append(text(x, y - 4, "Сечение трубы 20×20×2, 2:1", 3.2,
                    weight="bold"))
    out.append(rect(x, y, 40, 40, 0.3))
    out.append(rect(x + 4, y + 4, 32, 32, 0.3))
    out.append(dim_h((x, y + 40), (x + 40, y + 40), 20, 6, 2.2))
    out.append(dim_v((x + 40, y), (x + 40, y + 40), 20, 5, 2.2))
    out.append(text(x, y + 52, "стенка 2 мм", 2.2, color="#333"))

    # план балок, 1:4
    x, y = 250, 150
    out.append(text(x, y - 4, "План балок и шпилек, 1:4", 3.2, weight="bold"))
    out.append(rect(x, y, 100, 50, 0.25))
    out.append(rect(x + 50, y, 50, 50, 0.15, color="#888"))
    # продольные
    for yy2 in (15, 185):
        out.append(rect(x, y + yy2 * 0.25 - 2.5, 100, 5, 0.3,
                        fill="#e8e8e8"))
    # поперечные
    for xx in (20, 165):
        out.append(rect(x + xx * 0.25 - 2.5, y, 5, 50, 0.3, fill="#e8e8e8"))
    for xx in (30, 175, 385):
        for yy2 in (15, 185):
            out.append(circle(x + xx * 0.25, y + yy2 * 0.25, 1.2, 0.25))
    out.append(text(x + 20, y + 55, "B01/B02 — Y=15/185; B03/B04 — X=20…40/165…185",
                    2.2, color="#333"))

    out.append(text(10, 235, "ПРИМЕЧАНИЯ", 3.2, weight="bold"))
    notes = [
        "1. Все резы труб — 90°, без стыков 45°.",
        "2. Отверстия Ø11 сверлить по кондуктору после резки; сначала "
        "собрать на шпильках.",
        "3. Подстолье: 2 задние шпильки + болт M10 в свободной части "
        "(X=250, Y=15).",
        "4. Шпильки M10 — резьба по всей длине; торцы обработать напильником.",
        "5. Заглушки торцов не применяются; торцы обработать.",
    ]
    yy = 242
    for s in notes:
        out.append(text(10, yy, s, 2.5))
        yy += 5.0
    save("beams.svg", out)


# ----------------------------------------------------------------------------
# лист сборки
# ----------------------------------------------------------------------------
def sheet_assembly():
    out = page("СБОРКА ВИБРОСТОЛА fix10l — ПОСЛЕДОВАТЕЛЬНОСТЬ",
               "Подробно — Assembly.md; моменты — torque.csv.")
    steps = [
        ("1. ОСНОВАНИЕ", [
            "6 шпилек M10 в отверстия 400×200.",
            "Снизу — шайба + гайка в цековку.",
            "Сверху — шайба + гайка; проверить",
            "параллельность шпилек.",
        ]),
        ("2. БАЛКИ И ВАЛ", [
            "Поперечные балки 20×20×2 на шпильки",
            "X=30/175, Z=130…150.",
            "Вставить вал M10 в оба отверстия Ø10,2.",
            "Шайбы/гайки; кулачок на приваренную гайку.",
        ]),
        ("3. ПРОДОЛЬНЫЕ БАЛКИ", [
            "Продольные балки Y=15/185, Z=174…194.",
            "Закрепить гайками сверху/снизу.",
            "Поставить подстолье 200×200 на балки.",
            "2 задние nyloc; болт M10 в свободной части.",
        ]),
        ("4. СТОЛ И ПРУЖИНЫ", [
            "Накладку fix9 — 4 саморезами M4×12.",
            "Стол надеть на 4 шпильки.",
            "2 полосы 200×25×5, 6 саморезов; шайбы Ø20×2, пружины.",
            "Верхняя платформа; гайки сверху.",
        ]),
        ("5. РОЛИК И ДРЕЛЬ", [
            "Два уголка 50×50×2 на 4 самореза.",
            "Ось M10, 6200, шайбы/кольца, гайки.",
            "Дрель под подстолье, U-болты M6.",
            "Резиновые полукольца; патрон на вал.",
        ]),
        ("6. ПРОВЕРКА", [
            "Ход 3/5/10 на всех кулачках.",
            "Контакт ролика, зазор демпфера 13.",
            "Пружины 36 мм; гайки по torque.csv.",
            "Смазать шпильки; кожух — отдельно (C1).",
        ]),
    ]
    pos = [(12, 30), (148, 30), (284, 30), (12, 120), (148, 120), (284, 120)]
    for (title, lines), (x, y) in zip(steps, pos):
        out.append(rect(x, y, 124, 82, 0.35))
        out.append(text(x + 4, y + 7, title, 3.4, weight="bold"))
        yy = y + 15
        for s in lines:
            out.append(text(x + 4, yy, s, 2.5))
            yy += 5.0
        # условный эскиз
        if title.startswith("1"):
            out.append(rect(x + 20, y + 52, 84, 8, 0.3, fill="#eee"))
            for xx in (25, 45, 75, 95):
                out.append(line(x + xx, y + 44, x + xx, y + 68, 0.5))
        elif title.startswith("2"):
            out.append(rect(x + 20, y + 52, 84, 6, 0.3, fill="#ddd"))
            out.append(line(x + 20, y + 66, x + 104, y + 66, 0.5))
            out.append(circle(x + 62, y + 66, 8, 0.3))
        elif title.startswith("3"):
            out.append(rect(x + 20, y + 56, 84, 8, 0.3, fill="#eee"))
            out.append(rect(x + 20, y + 46, 84, 6, 0.3, fill="#ddd"))
        elif title.startswith("4"):
            out.append(rect(x + 20, y + 50, 84, 6, 0.3, fill="#ddd"))
            for xx in (28, 96):
                out.append(line(x + xx, y + 58, x + xx, y + 70, 0.6))
                out.append(line(x + xx - 4, y + 64, x + xx + 4, y + 64, 0.6))
        elif title.startswith("5"):
            out.append(rect(x + 30, y + 52, 60, 18, 0.3, fill="#ddd"))
            out.append(circle(x + 42, y + 60, 6, 0.25))
        else:
            out.append(text(x + 6, y + 58, "✓", 22, color="#2a7"))
    save("assembly_steps.svg", out)


# ----------------------------------------------------------------------------
# изометрия
# ----------------------------------------------------------------------------
def sheet_iso(views):
    out = page("ВИБРОСТОЛ fix10l — ИЗОМЕТРИЯ (HLR)", "Без кожуха; дрель условно.")
    polys = views["full"]["iso"]
    pts = [(u, v) for poly in polys for u, v in poly]
    if not pts:
        save("iso.svg", out)
        return
    umin = min(p[0] for p in pts)
    umax = max(p[0] for p in pts)
    vmin = min(p[1] for p in pts)
    vmax = max(p[1] for p in pts)
    sc = min(300.0 / max(1e-6, umax - umin),
             170.0 / max(1e-6, vmax - vmin))
    ox = 30 - umin * sc
    oy = 250 + vmin * sc

    def mp(u, v):
        return (ox + u * sc, oy - v * sc)

    draw_view(out, polys, mp, 0.22)
    out.append(text(10, 28, "Габарит 400×200×300; масса без дрели ≈5,7 кг.",
                    2.8, color="#333"))
    out.append(text(10, 275, "Накладка и кулачки — fix9. Стол 200×200; "
                    "вырез платформы 120×120; 6 шпилек M10.", 2.6,
                    color="#333"))
    save("iso.svg", out)


# ----------------------------------------------------------------------------
# спецификация
# ----------------------------------------------------------------------------
def sheet_spec():
    out = page("СПЕЦИФИКАЦИЯ ДЕТАЛЕЙ fix10l",
               "Позиции и количество; полные данные — spec.csv.")
    fn = os.path.join(STAGE, "spec.csv")
    rows = []
    if os.path.exists(fn):
        with open(fn, newline="", encoding="utf-8") as f:
            r = csv.reader(f, delimiter=";")
            next(r, None)
            rows = list(r)
    x0, y0 = 10, 30
    widths = (12, 105, 22, 45, 85, 125)
    heads = ("Поз.", "Наименование", "Кол.", "Материал", "Размеры",
             "Примечание")
    xx = x0
    for w, h in zip(widths, heads):
        out.append(text(xx, y0, h, 2.6, weight="bold"))
        xx += w
    out.append(line(x0, y0 + 1.5, 410, y0 + 1.5, 0.25))
    yy = y0 + 7
    for r in rows:
        if not r:
            continue
        vals = [r[0], r[1], r[2], r[3], r[4], r[6] if len(r) > 6 else ""]
        xx = x0
        for w, val in zip(widths, vals):
            s = str(val)
            if len(s) > 46:
                s = s[:45] + "…"
            out.append(text(xx, yy, s, 2.15))
            xx += w
        yy += 5.4
        if yy > 280:
            break
    save("spec.svg", out)


def main():
    print("draw fix10l...", flush=True)
    views = project_all()
    sheet_views(views)
    sheet_mechanism(views)
    sheet_details()
    sheet_beams()
    sheet_assembly()
    sheet_iso(views)
    sheet_spec()


main()
