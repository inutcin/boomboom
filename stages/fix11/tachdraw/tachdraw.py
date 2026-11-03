#!/usr/bin/env python3
"""Чертёж детали по STEP-модели (пробный лист: поджимная балка 21).

Лист A4, портрет, рамка с основной надписью, масштаб 1:2, две проекции:
  * главный вид — вдоль оси X (длина L x высота 20);
  * вид сверху  — вдоль оси Z (длина L x ширина 20).
Выход — только PDF (A4, 210 x 297 мм).

Размеры на листе:
  * габариты 159,6 x 20 x 20;
  * расстояния от краёв до центров отверстий Ø10 и Ø4,5;
  * расстояния от краёв до кромок выреза-седла R15;
  * диаметры отверстий и примечания по вырезу.

Исходник — только STEP (`cad/step/21_retainer_one.step`): контур, отверстия
и вырез берутся из проекций и цилиндрических граней тела, а не из params.py.

Запуск:
    freecadcmd tachdraw.py [--step FILE] [--out FILE]
"""

import math
import os
import sys

import cairosvg
import FreeCAD as App
import Drawing
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.dirname(HERE)
DEFAULT_STEP = os.path.join(STAGE, "cad", "step", "21_retainer_one.step")
DEFAULT_OUT = os.path.join(HERE, "pdf", "21_beam.pdf")
os.makedirs(os.path.dirname(DEFAULT_OUT), exist_ok=True)

S = 0.5                     # 1:2
PW, PH = 210.0, 297.0       # A4 портрет, мм
FONT = "DejaVu Sans, Arial, sans-serif"

# положение видов на листе (мм бумаги)
MAIN_X0, MAIN_YTOP = 65.0, 50.0     # главный вид: Zmax -> MAIN_YTOP
TOP_X0, TOP_YTOP = 65.0, 105.0      # вид сверху: Xmin -> TOP_YTOP


# ----------------------------------------------------------------------------
# svg helpers
# ----------------------------------------------------------------------------
def fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


def num(x, nd=2):
    """Число в русской записи: 159.6 -> 159,6; 80.0 -> 80."""
    s = ("%." + str(nd) + "f") % x
    s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace(".", ",")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def line(x1, y1, x2, y2, w=0.18, dash=None, color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
            'stroke-width="%s" stroke-linecap="round"%s/>'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), color, w, d))


def rect(x, y, w, h, sw=0.2, fill="none"):
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" '
            'stroke="#000" stroke-width="%s"/>'
            % (fmt(x), fmt(y), fmt(w), fmt(h), fill, sw))


def circle(cx, cy, r, sw=0.3, dash=None, fill="none", color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" '
            'stroke-width="%s"%s/>'
            % (fmt(cx), fmt(cy), fmt(r), fill, color, sw, d))


def text(x, y, s, size=3.0, anchor="start", weight="normal", rot=0,
         color="#000"):
    tr = ' transform="rotate(%s %s %s)"' % (rot, fmt(x), fmt(y)) if rot else ""
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" '
            'font-weight="%s" text-anchor="%s" fill="%s"%s>%s</text>'
            % (fmt(x), fmt(y), FONT, size, weight, anchor, color, tr,
               esc(s)))


def txt_bg(x, y, s, size=2.5, anchor="middle"):
    w = max(1.6, len(s) * size * 0.60)
    if anchor == "middle":
        x0 = x - w / 2.0
    elif anchor == "end":
        x0 = x - w
    else:
        x0 = x
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" '
            'stroke="none"/>'
            % (fmt(x0), fmt(y - size * 0.92), fmt(w), fmt(size * 1.2)))


def arrow(x, y, dx, dy, size=1.3):
    bx, by = x - dx * size, y - dy * size
    px, py = -dy * 0.42, dx * 0.42
    return ('<polygon points="%s,%s %s,%s %s,%s" fill="#000"/>'
            % (fmt(x), fmt(y), fmt(bx + px), fmt(by + py),
               fmt(bx - px), fmt(by - py)))


def centerline(x1, y1, x2, y2):
    return line(x1, y1, x2, y2, 0.13, dash="6 1.4 1.2 1.4", color="#333")


# ----------------------------------------------------------------------------
# размеры
# ----------------------------------------------------------------------------
def hdim(x1, x2, y_from, y_dim, label, size=2.5, tight=None,
         y_from1=None, y_from2=None):
    """Горизонтальный размер между x1 и x2 на уровне y_dim."""
    if tight is None:
        tight = abs(x2 - x1) < 9.0
    f1 = y_from if y_from1 is None else y_from1
    f2 = y_from if y_from2 is None else y_from2
    sgn = 1.0 if y_dim >= y_from else -1.0
    o = [line(x1, f1, x1, y_dim + sgn * 2.0, 0.13),
         line(x2, f2, x2, y_dim + sgn * 2.0, 0.13),
         line(x1, y_dim, x2, y_dim, 0.15)]
    if not tight:
        o.append(arrow(x1, y_dim, -1 if x1 < x2 else 1, 0))
        o.append(arrow(x2, y_dim, 1 if x1 < x2 else -1, 0))
    else:
        o.append(arrow(x1, y_dim, 1 if x1 < x2 else -1, 0))
        o.append(arrow(x2, y_dim, -1 if x1 < x2 else 1, 0))
    tx = (x1 + x2) / 2.0
    o.append(txt_bg(tx, y_dim - 0.9, label, size))
    o.append(text(tx, y_dim - 0.9, label, size, "middle"))
    return "".join(o)


def vdim(y1, y2, x_from, x_dim, label, size=2.5, tight=None):
    """Вертикальный размер между y1 и y2 на уровне x_dim."""
    if tight is None:
        tight = abs(y2 - y1) < 9.0
    sgn = 1.0 if x_dim >= x_from else -1.0
    o = [line(x_from, y1, x_dim + sgn * 2.0, y1, 0.13),
         line(x_from, y2, x_dim + sgn * 2.0, y2, 0.13),
         line(x_dim, y1, x_dim, y2, 0.15)]
    if not tight:
        o.append(arrow(x_dim, y1, 0, -1 if y1 < y2 else 1))
        o.append(arrow(x_dim, y2, 0, 1 if y1 < y2 else -1))
    else:
        o.append(arrow(x_dim, y1, 0, 1 if y1 < y2 else -1))
        o.append(arrow(x_dim, y2, 0, -1 if y1 < y2 else 1))
    ty = (y1 + y2) / 2.0
    o.append(txt_bg(x_dim - 1.0, ty, label, size))
    o.append(text(x_dim - 1.0, ty, label, size, "middle", rot=-90))
    return "".join(o)


def leader(px, py, tx, ty, label, size=2.8, anchor="start", dot=True):
    """Выноска из точки (px,py) к тексту у (tx,ty)."""
    o = [line(px, py, tx, ty, 0.14)]
    if dot:
        o.append(circle(px, py, 0.45, 0.0, fill="#000", color="#000"))
    if anchor == "start":
        o.append(text(tx + 1.0, ty + 0.9, label, size, "start"))
    elif anchor == "end":
        o.append(text(tx - 1.0, ty + 0.9, label, size, "end"))
    else:
        o.append(text(tx, ty + 0.9, label, size, "middle"))
    return "".join(o)


# ----------------------------------------------------------------------------
# STEP -> проекции
# ----------------------------------------------------------------------------
def load_shape(fn):
    return Part.read(fn)


def project_edges(shape, direction):
    """Видимые рёбра проекции: список ('circle', c, r) / ('poly', pts)."""
    vis = Drawing.project(shape, App.Vector(*direction))[0]
    out = []
    for e in vis.Edges:
        c = e.Curve
        if c.__class__.__name__ == "Circle" and e.isClosed():
            out.append(("circle", (c.Center.x, c.Center.y), c.Radius))
            continue
        n = 2 if c.__class__.__name__ == "Line" else 40
        pts = e.discretize(n)
        if len(pts) < 2:
            continue
        out.append(("poly", [(p.x, p.y) for p in pts]))
    return out


class View(object):
    """Перевод координат проекции в координаты листа."""

    def __init__(self, kind, bb, x0, ytop):
        self.kind = kind
        self.x0 = x0
        self.ytop = ytop
        self.xmin, self.xmax = bb.XMin, bb.XMax
        self.ymin, self.ymax = bb.YMin, bb.YMax
        self.zmin, self.zmax = bb.ZMin, bb.ZMax

    def pt(self, p):
        if self.kind == "main":          # проекция (Z, -Y)
            Y = -p[1]
            Z = p[0]
            return (self.x0 + (Y - self.ymin) * S,
                    self.ytop + (self.zmax - Z) * S)
        # top: проекция (X, Y)
        X = p[0]
        Y = p[1]
        return (self.x0 + (Y - self.ymin) * S,
                self.ytop + (X - self.xmin) * S)

    def m(self, a, b):
        """Модельные координаты вида -> лист. main: (Y,Z); top: (X,Y)."""
        if self.kind == "main":
            Y, Z = a, b
            return (self.x0 + (Y - self.ymin) * S,
                    self.ytop + (self.zmax - Z) * S)
        X, Y = a, b
        return (self.x0 + (Y - self.ymin) * S,
                self.ytop + (X - self.xmin) * S)

    def draw(self, edges, width=0.4):
        o = []
        for e in edges:
            if e[0] == "circle":
                cx, cy = self.pt(e[1])
                o.append(circle(cx, cy, e[2] * S, width))
            else:
                pts = [self.pt(p) for p in e[1]]
                d = "M " + " L ".join("%s %s" % (fmt(x), fmt(y))
                                      for x, y in pts)
                o.append('<path d="%s" fill="none" stroke="#000" '
                         'stroke-width="%s" stroke-linejoin="round"/>'
                         % (d, width))
        return "".join(o)

    def circle_center(self, p):
        return self.pt(p)


# ----------------------------------------------------------------------------
# признаки детали из STEP
# ----------------------------------------------------------------------------
def features(shape, tol=0.05):
    """Отверстия и вырез по цилиндрическим граням."""
    holes45, holes10 = [], []
    saddle = None
    for f in shape.Faces:
        c = f.Surface
        if c.__class__.__name__ != "Cylinder":
            continue
        axis = c.Axis
        ax = (abs(axis.x), abs(axis.y), abs(axis.z))
        r = c.Radius
        bb = f.BoundBox
        if abs(r - 2.25) < tol and ax[0] > 0.99:      # 4 x Ø4,5, ось X
            holes45.append((c.Center.y, c.Center.z))
        elif abs(r - 5.0) < tol and ax[2] > 0.99:     # 2 x Ø10, ось Z
            holes10.append((c.Center.x, c.Center.y))
        elif abs(r - 15.0) < tol and ax[0] > 0.99:    # седло R15, ось X
            saddle = dict(r=r, yc=c.Center.y, zc=c.Center.z,
                          x0=bb.XMin, x1=bb.XMax)
    holes45 = sorted(set((round(a, 3), round(b, 3)) for a, b in holes45))
    holes10 = sorted(set((round(a, 3), round(b, 3)) for a, b in holes10))
    if saddle:
        dz = shape.BoundBox.ZMax - saddle["zc"]
        half = math.sqrt(max(0.0, saddle["r"] ** 2 - dz ** 2))
        saddle["y0"] = saddle["yc"] - half
        saddle["y1"] = saddle["yc"] + half
        saddle["depth"] = saddle["r"] - abs(dz)
    return holes45, holes10, saddle


# ----------------------------------------------------------------------------
# рамка и основная надпись
# ----------------------------------------------------------------------------
def frame(mass_kg=None):
    o = [rect(20, 5, 185, 287, 0.7)]
    o.append(text(24, 14, "БАЛКА 21 — ПОДЖИМНАЯ БАЛКА", 5.2, weight="bold"))
    o.append(text(24, 20.2,
                  "Пробный чертёж детали по STEP-модели · две проекции · "
                  "М 1:2 · формат A4", 3.0))
    o.append(line(24, 22.5, 200, 22.5, 0.3))

    # основная надпись 185 x 55 (по внутренней рамке A4)
    x0, y0, w, h = 20.0, 237.0, 185.0, 55.0
    o.append(rect(x0, y0, w, h, 0.5))
    # левая графа
    o.append(line(x0 + 60, y0, x0 + 60, y0 + h, 0.35))
    for i in (1, 2, 3, 4):
        o.append(line(x0, y0 + i * 11.0, x0 + 60, y0 + i * 11.0, 0.2))
    for i, s in enumerate(("Разраб.", "Пров.", "Т. контр.", "Н. контр.",
                           "Утв.")):
        o.append(text(x0 + 2, y0 + 7.6 + i * 11.0, s, 2.3))
    # правая часть
    o.append(line(x0 + 60, y0 + 16, x0 + w, y0 + 16, 0.2))
    o.append(line(x0 + 60, y0 + 30, x0 + w, y0 + 30, 0.2))
    o.append(line(x0 + 60, y0 + 42, x0 + w, y0 + 42, 0.2))
    o.append(line(x0 + 155, y0 + 42, x0 + 155, y0 + h, 0.2))
    o.append(text(x0 + 65, y0 + 9.0, "Балка 21 (поджимная)", 4.4,
                  weight="bold"))
    o.append(text(x0 + 65, y0 + 13.6, "поз. 21 · 2 шт. на сборку", 2.6))
    o.append(text(x0 + 65, y0 + 21.5, "Труба 20×20×2, L = 159,6", 2.8))
    o.append(text(x0 + 65, y0 + 26.5, "сталь, ГОСТ 8639-82", 2.6))
    o.append(text(x0 + 65, y0 + 36.0, "М 1:2", 3.6, weight="bold"))
    o.append(text(x0 + 65, y0 + 40.0, "масштаб", 2.3))
    o.append(text(x0 + 160, y0 + 36.0, "Лист 1/1", 2.8))
    o.append(text(x0 + 160, y0 + 40.0, "Формат A4", 2.6))
    o.append(text(x0 + 65, y0 + 48.0, "fix11.TD.B21", 3.2, weight="bold"))
    o.append(text(x0 + 65, y0 + 52.3, "tachdraw · исходник "
                  "21_retainer_one.step", 2.2))
    o.append(text(x0 + 160, y0 + 48.0,
                  "Масса %s кг" % num(mass_kg, 3) if mass_kg else "—", 2.5))
    o.append(text(x0 + 160, y0 + 52.3, "М 1:2", 2.5))
    return "".join(o)


# ----------------------------------------------------------------------------
# пробный лист: балка 21
# ----------------------------------------------------------------------------
def sheet_beam21(step=DEFAULT_STEP, out=None):
    shape = load_shape(step)
    bb = shape.BoundBox
    Ymin, Ymax = bb.YMin, bb.YMax
    Zmin, Zmax = bb.ZMin, bb.ZMax
    Xmin, Xmax = bb.XMin, bb.XMax

    main = View("main", bb, MAIN_X0, MAIN_YTOP)
    top = View("top", bb, TOP_X0, TOP_YTOP)

    holes45, holes10, saddle = features(shape)

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" '
         'height="297mm" viewBox="0 0 210 297">',
         '<rect width="210" height="297" fill="#fff"/>',
         frame(shape.Volume * 7.85e-6)]

    # --- виды -------------------------------------------------------------
    o.append(main.draw(project_edges(shape, (1, 0, 0))))
    o.append(top.draw(project_edges(shape, (0, 0, 1))))

    o.append(text(24, 43, "ВИД СБОКУ", 3.4, weight="bold"))
    o.append(text(24, 47.5, "(вдоль оси X) · М 1:2", 2.6))
    o.append(text(24, 98, "ВИД СВЕРХУ", 3.4, weight="bold"))
    o.append(text(24, 102.5, "(вдоль оси Z) · М 1:2", 2.6))

    # --- габариты ---------------------------------------------------------
    yb = main.m(Ymin, Zmin)[1]              # низ главного вида
    yt = main.m(Ymin, Zmax)[1]              # верх главного вида
    xl = main.m(Ymin, Zmin)[0]
    xr = main.m(Ymax, Zmin)[0]
    o.append(hdim(xl, xr, yb, yb + 13.0, num(Ymax - Ymin), size=3.0))
    o.append(vdim(yt, yb, xl, xl - 11.0, num(Zmax - Zmin), size=3.0))

    yb_t = top.m(Xmax, Ymin)[1]             # низ вида сверху
    yt_t = top.m(Xmin, Ymin)[1]             # верх вида сверху
    o.append(vdim(yt_t, yb_t, xl, xl - 24.0, num(Xmax - Xmin), size=3.0))

    # --- отверстия Ø4,5 (главный вид) ------------------------------------
    ys45 = sorted(set(y for y, z in holes45))
    z45 = holes45[0][1]
    for y in ys45:
        cx, cy = main.m(y, z45)
        o.append(centerline(cx, yt - 2.5, cx, yb + 2.5))
    o.append(centerline(xl - 3.0, main.m(Ymin, z45)[1],
                        xr + 3.0, main.m(Ymin, z45)[1]))

    # положение по длине: по 9,8 и 24,8 от торцов
    yA, yB = yt - 9.0, yt - 18.0
    yext = yt - 2.5                       # верх осевой отверстий
    d1 = ys45[0] - Ymin
    d2 = ys45[1] - Ymin
    o.append(hdim(main.m(Ymin, Zmax)[0], main.m(ys45[0], Zmax)[0],
                  yt, yA, num(d1), y_from1=yt, y_from2=yext))
    o.append(hdim(main.m(Ymax, Zmax)[0], main.m(ys45[3], Zmax)[0],
                  yt, yA, num(Ymax - ys45[3]), y_from1=yt, y_from2=yext))
    o.append(hdim(main.m(Ymin, Zmax)[0], main.m(ys45[1], Zmax)[0],
                  yt, yB, num(d2), y_from1=yt, y_from2=yext))
    o.append(hdim(main.m(Ymax, Zmax)[0], main.m(ys45[2], Zmax)[0],
                  yt, yB, num(Ymax - ys45[2]), y_from1=yt, y_from2=yext))

    # высота центров от нижней кромки
    xh = xr + 16.0
    o.append(vdim(main.m(Ymin, z45)[1], yb, xr, xh, num(z45 - Zmin)))
    # Ø4,5
    hx, hy = main.m(ys45[3], z45)
    o.append(leader(hx + 2.25 * S * 0.95, hy - 2.25 * S * 0.31,
                    166.0, 42.0,
                    "4 отв. Ø%s" % num(2 * 2.25, 1), size=2.8))

    # --- отверстия Ø10 (вид сверху) --------------------------------------
    xs10 = sorted(set(y for x, y in holes10))
    x10 = holes10[0][0]
    for y in xs10:
        cx, cy = top.m(x10, y)
        o.append(centerline(cx - 3.0, cy, cx + 3.0, cy))
        o.append(centerline(cx, cy - 6.0, cx, cy + 2.5))
    # продольная осевая на X=10: через оба отверстия и центр выреза
    o.append(centerline(xl - 3.0, top.m(x10, Ymin)[1],
                        xr + 3.0, top.m(x10, Ymin)[1]))
    # положение по длине: 39,8 / 80 / 39,8
    yT = yt_t - 8.0
    yext_t = top.m(x10, xs10[0])[1] - 6.0
    o.append(hdim(top.m(x10, Ymin)[0], top.m(x10, xs10[0])[0],
                  yt_t, yT, num(xs10[0] - Ymin),
                  y_from1=yt_t, y_from2=yext_t))
    o.append(hdim(top.m(x10, xs10[0])[0], top.m(x10, xs10[1])[0],
                  yt_t, yT, num(xs10[1] - xs10[0]),
                  y_from1=yext_t, y_from2=yext_t))
    o.append(hdim(top.m(x10, xs10[1])[0], top.m(x10, Ymax)[0],
                  yt_t, yT, num(Ymax - xs10[1]),
                  y_from1=yext_t, y_from2=yt_t))
    # положение центров по ширине: 10 от передней кромки
    o.append(vdim(yt_t, top.m(x10, Ymin)[1], xr, xr + 7.0,
                  num(x10 - Xmin), size=2.5, tight=True))
    # Ø10
    cx10, cy10 = top.m(x10, xs10[0])
    o.append(leader(cx10 - 5.0 * S * 0.89, cy10 - 5.0 * S * 0.45,
                    24.0, 80.0, "2 отв. Ø%s" % num(2 * 5.0, 1), size=2.8))

    # --- вырез-седло (вид сверху) ----------------------------------------
    sy0, sy1 = saddle["y0"], saddle["y1"]
    yslot = yb_t + 9.0
    y_slot_edge = top.m(saddle["x1"], Ymin)[1]   # нижняя кромка выреза по X
    o.append(hdim(top.m(Xmin, Ymin)[0], top.m(Xmin, sy0)[0],
                  yb_t, yslot, num(sy0 - Ymin),
                  y_from1=yb_t, y_from2=y_slot_edge))
    o.append(hdim(top.m(Xmin, sy0)[0], top.m(Xmin, sy1)[0],
                  yb_t, yslot, num(sy1 - sy0),
                  y_from1=y_slot_edge, y_from2=y_slot_edge))
    o.append(hdim(top.m(Xmin, sy1)[0], top.m(Xmin, Ymax)[0],
                  yb_t, yslot, num(Ymax - sy1),
                  y_from1=y_slot_edge, y_from2=yb_t))

    # выноска к вырезу не нужна: вырез описан в примечании 4

    # --- примечания -------------------------------------------------------
    notes = [
        "ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ",
        "1. Материал — труба стальная 20×20×2 (ГОСТ 8639-82).",
        "2. 2 отв. Ø10 — сквозные через верхнюю и нижнюю стенки.",
        "3. 4 отв. Ø4,5 — сквозные через боковые стенки, по центру высоты.",
        "4. Вырез-седло под подшипник 6200: R15, ширина 9,4",
        "    (по 5,3 от боковых граней), глубина 5; ось выреза —",
        "    по центру длины (на 79,8 от торца).",
        "5. Острые кромки притупить, заусенцы удалить.",
        "6. Неуказанные предельные отклонения ±0,5 мм.",
    ]
    ny = 165.0
    for i, s in enumerate(notes):
        cont = s.startswith("  ")
        o.append(text(30.0 if cont else 24.0, ny + i * 6.0, s.strip(),
                      3.0 if i == 0 else 2.7,
                      weight="bold" if i == 0 else "normal"))

    o.append(text(24, 219.0,
                  "Исходник: cad/step/21_retainer_one.step · "
                  "проекции и размеры получены из STEP", 2.4, color="#444"))
    o.append("</svg>")

    out = out or DEFAULT_OUT
    cairosvg.svg2pdf(bytestring="".join(o).encode("utf-8"), write_to=out)
    return out


def main():
    step = DEFAULT_STEP
    out = None
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--step" and i + 1 < len(argv):
            step = argv[i + 1]
        elif a == "--out" and i + 1 < len(argv):
            out = argv[i + 1]
    fn = sheet_beam21(step, out)
    print("written", fn)


if __name__ == "__main__":
    main()
