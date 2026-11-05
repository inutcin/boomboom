#!/usr/bin/env python3
"""Пакет чертежей деталей fix11 по STEP: A4 портрет, М 1:2, PDF.

Один PDF на деталь. Отдельно — вал 02_shaft (L=176, M10×15).
Для каждой детали:
  * две проекции (выбираются по видимым отверстиям/вырезам и габариту);
  * габаритные размеры;
  * таблица отверстий: Ø и расстояния от левого/нижнего краёв до центра;
  * вырезы: расстояния от краёв до кромок (по проекции) + примечания.
Источник — STEP; для T13/T14/T17/T18 (сверление/прорезь после резки)
берётся пересечение STEP рамы с габаритом отрезка.

Запуск:
    freecadcmd batch.py [--only NAME]
"""

import math
import os
import sys

import cairosvg
import FreeCAD as App
import Part
import Drawing

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.dirname(HERE)
STEP = os.path.join(STAGE, "cad", "step")
OUT = os.path.join(HERE, "pdf")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, HERE)
import tachdraw as td  # noqa: E402

S = 0.5
FONT = td.FONT
DENS = {"steel": 7.85, "pla": 1.24, "petg": 1.27, "pc": 1.20,
        "rubber": 1.20, "plastic": 1.20, "al": 2.70}


# ----------------------------------------------------------------------------
# 3D -> projection 2D
# ----------------------------------------------------------------------------
def proj_uv(d, p):
    if d == "X":
        return (p.z, -p.y)
    if d == "Y":
        return (p.z, p.x)
    if d == "-Z":
        return (-p.x, p.y)
    return (p.x, p.y)


def axis_val(d, axis, u, v):
    """Модельная координата axis из (u,v) проекции вдоль d."""
    if d == "X":
        return {2: u, 1: -v}[axis]
    if d == "Y":
        return {2: u, 0: v}[axis]
    if d == "-Z":
        return {0: -u, 1: v}[axis]
    return {0: u, 1: v}[axis]


DIRVEC = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1),
          "-Z": (0, 0, -1)}
SPAN = {("X", 2): "u", ("X", 1): "v", ("Y", 2): "u", ("Y", 0): "v",
        ("Z", 0): "u", ("Z", 1): "v"}


# ----------------------------------------------------------------------------
# признаки
# ----------------------------------------------------------------------------
def cyl_features(shape):
    """Полные вогнутые цилиндры -> отверстия; частичные -> вырезы."""
    holes = {}
    grooves = []
    for f in shape.Faces:
        c = f.Surface
        if c.__class__.__name__ != "Cylinder":
            continue
        rng = f.ParameterRange
        du = abs(rng[1] - rng[0])
        ax = App.Vector(c.Axis.x, c.Axis.y, c.Axis.z)
        pts = [v.Point for v in f.Vertexes]
        if not pts:
            continue
        p = pts[0]
        rel = p - c.Center
        rad = rel - ax * rel.dot(ax)
        if rad.Length < 1e-9:
            continue
        rad.normalize()
        u, v = c.parameter(p)
        try:
            n = f.normalAt(u, v)
        except Exception:
            continue
        if n.dot(rad) >= 0:
            continue                          # наружная поверхность
        ai = max(range(3), key=lambda i: abs((ax.x, ax.y, ax.z)[i]))
        cc = c.Center
        perp = tuple(round((cc.x, cc.y, cc.z)[i], 2)
                     for i in range(3) if i != ai)
        if du > 1.5 * math.pi:
            key = (ai, perp)
            holes.setdefault(key, {"axis": "XYZ"[ai], "pt": cc,
                                   "r": set()})["r"].add(round(c.Radius, 2))
        else:
            grooves.append({"axis": "XYZ"[ai], "pt": cc,
                            "r": round(c.Radius, 2)})
    return holes, grooves


def outer_cylinders(shape):
    """Наружные цилиндры (валы) для дорисовки силуэта в боковом виде."""
    out = []
    for f in shape.Faces:
        c = f.Surface
        if c.__class__.__name__ != "Cylinder":
            continue
        ax = App.Vector(c.Axis.x, c.Axis.y, c.Axis.z)
        p = f.Vertexes[0].Point if f.Vertexes else f.CenterOfMass
        rel = p - c.Center
        rad = rel - ax * rel.dot(ax)
        if rad.Length < 1e-9:
            continue
        rad.normalize()
        u, v = c.parameter(p)
        try:
            n = f.normalAt(u, v)
        except Exception:
            continue
        if n.dot(rad) <= 0:
            continue
        ai = max(range(3), key=lambda i: abs((ax.x, ax.y, ax.z)[i]))
        bb = f.BoundBox
        out.append({"axis": ai, "r": c.Radius, "c": c.Center, "bb": bb})
    return out


def pick_solid(shape, idx):
    ss = shape.Solids
    return ss[idx] if len(ss) > idx else ss[0]


def preweld_notch(plain, bbox):
    """Отрезок T17/T18: прорезь R15 в STEP рамы, без посватарочных отв."""
    global _FRAME
    if _FRAME is None:
        _FRAME = Part.read(os.path.join(STEP, "22_frame.step"))
    for f in _FRAME.Faces:
        c = f.Surface
        if c.__class__.__name__ != "Cylinder" or abs(c.Radius - 15.0) > 0.01:
            continue
        ax = c.Axis
        if abs(ax.x) < 0.99:
            continue
        bb = f.BoundBox
        if bb.XMax <= bbox.XMin or bb.XMin >= bbox.XMax:
            continue
        if bb.YMax <= bbox.YMin or bb.YMin >= bbox.YMax:
            continue
        cyl = Part.makeCylinder(15.0, bb.XMax - bb.XMin,
                                App.Vector(bb.XMin, c.Center.y, c.Center.z),
                                App.Vector(1, 0, 0))
        return plain.cut(cyl)
    return plain


def frame_tube(bbox):
    """Пересечение STEP рамы с габаритом отрезка: отверстия/прорезь."""
    global _FRAME
    if _FRAME is None:
        _FRAME = Part.read(os.path.join(STEP, "22_frame.step"))
    box = Part.makeBox(bbox.XMax - bbox.XMin, bbox.YMax - bbox.YMin,
                       bbox.ZMax - bbox.ZMin,
                       App.Vector(bbox.XMin, bbox.YMin, bbox.ZMin))
    return _FRAME.common(box)


_FRAME = None


def projected(d, shape):
    edges = td.project_edges(shape, DIRVEC[d])
    xs, ys = [], []
    for e in edges:
        if e[0] == "circle":
            (u, v), r = e[1], e[2]
            xs += [u - r, u + r]
            ys += [v - r, v + r]
        else:
            xs += [p[0] for p in e[1]]
            ys += [p[1] for p in e[1]]
    return edges, (min(xs), max(xs), min(ys), max(ys))


def internal_cutout(edges, uvbb):
    """Не-круговые видимые рёбра строго внутри проекции -> вырез."""
    u0, u1, v0, v1 = uvbb
    pts = []
    for e in edges:
        if e[0] == "circle":
            continue
        pp = e[1]
        if all(u0 + 0.3 < x < u1 - 0.3 and
               v0 + 0.3 < y < v1 - 0.3 for x, y in pp):
            pts += pp
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cb = (min(xs), max(xs), min(ys), max(ys))
    area = (cb[1] - cb[0]) * (cb[3] - cb[2])
    parea = max(1e-6, (u1 - u0) * (v1 - v0))
    if area / parea > 0.35:
        return None
    return cb


def view_info(d, shape, holes, auto_cut=False):
    edges, uvbb = projected(d, shape)
    n_h = sum(1 for k in holes if holes[k]["axis"] == d.lstrip("-"))
    cut = internal_cutout(edges, uvbb) if auto_cut else None
    ax = {"X": [1, 2], "Y": [0, 2], "Z": [0, 1],
          "-Z": [0, 1]}[d]
    ext = [(abs(shape.BoundBox.__getattribute__("XYZ"[i] + "Max") -
                shape.BoundBox.__getattribute__("XYZ"[i] + "Min")), i)
           for i in ax]
    ext.sort(reverse=True)
    area = ext[0][0] * ext[1][0]
    score = n_h * 100 + (20 if cut else 0) + area / 1000.0
    return {"d": d, "edges": edges, "uvbb": uvbb, "holes": n_h,
            "cut": cut, "ext": ext, "area": area, "score": score}


def pick_views(shape, holes, auto_cut=False, dirs=("X", "Y", "Z")):
    infos = {d: view_info(d, shape, holes, auto_cut) for d in dirs}
    prim = max(infos.values(), key=lambda x: (x["score"], x["area"]))
    rest = [x for x in infos.values() if x["d"] != prim["d"]]
    sec = max(rest, key=lambda x: (x["score"], x["area"]))
    # длинная гладкая деталь (шпилька/вал/труба): вторая проекция — торец
    bb = shape.BoundBox
    dims = sorted([(bb.XMax - bb.XMin, 0), (bb.YMax - bb.YMin, 1),
                   (bb.ZMax - bb.ZMin, 2)], reverse=True)
    if (prim["holes"] == 0 and prim["cut"] is None and
            dims[0][0] > 4.0 * dims[1][0] and "Z" in infos):
        sec = infos.get("XYZ"[dims[0][1]])
        if sec is None or sec["d"] == prim["d"]:
            sec = max(rest, key=lambda x: (x["score"], x["area"]))
    return prim, sec


# ----------------------------------------------------------------------------
# вид на листе
# ----------------------------------------------------------------------------
def _hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1]) -
                (a[1] - o[1]) * (b[0] - o[0]))

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


class GView(object):
    def __init__(self, info, bb, x0, ytop):
        self.info = info
        self.d = info["d"]
        self.bb = bb
        self.x0 = x0
        self.ytop = ytop
        # две оси проекции
        e = info["ext"]
        self.H = e[0][1]
        self.V = e[1][1]
        self.wm = e[0][0]
        self.hm = e[1][0]
        # длинную деталь (>135 мм на бумаге) кладём вертикально
        if self.wm * S > 135.0:
            self.H, self.V = self.V, self.H
            self.wm, self.hm = self.hm, self.wm
        self.hmin = getattr(bb, "XYZ"[self.H] + "Min")
        self.hmax = getattr(bb, "XYZ"[self.H] + "Max")
        self.vmin = getattr(bb, "XYZ"[self.V] + "Min")
        self.vmax = getattr(bb, "XYZ"[self.V] + "Max")
        self.w = (self.hmax - self.hmin) * S
        self.h = (self.vmax - self.vmin) * S

    def hv(self, uv):
        return (axis_val(self.d, self.H, *uv),
                axis_val(self.d, self.V, *uv))

    def scr(self, h, v):
        return (self.x0 + (h - self.hmin) * S,
                self.ytop + (self.vmax - v) * S)

    def scr_uv(self, uv):
        return self.scr(*self.hv(uv))

    def pt3(self, p):
        return self.scr_uv(proj_uv(self.d, p))

    def draw(self):
        o = []
        edges = self.info["edges"]
        # тонкий вид с большим числом рёбер (фасеточная боковая поверхность):
        # оставляем только контур, иначе получается «штриховка»
        thin = max(self.wm, self.hm) > 3.0 * max(1e-6, min(self.wm, self.hm))
        cull = thin and len(edges) > 40
        for e in edges:
            if e[0] == "circle":
                (u, v) = e[1]
                x, y = self.scr_uv((u, v))
                o.append(td.circle(x, y, e[2] * S, 0.35))
                continue
            pts = [self.scr_uv(p) for p in e[1]]
            if len(pts) < 2:
                continue
            if cull:
                continue
            o.append('<path d="M %s" fill="none" stroke="#000" '
                     'stroke-width="0.4" stroke-linejoin="round"/>'
                     % " L ".join("%s %s" % (td.fmt(x), td.fmt(y))
                                  for x, y in pts))
        if cull:
            # силуэт фасеточной детали: выпуклая оболочка проекции
            pts = []
            for e in edges:
                if e[0] == "circle":
                    (u, v), r = e[1], e[2]
                    pts += [(u + r, v), (u - r, v), (u, v + r), (u, v - r)]
                else:
                    pts += e[1]
            hull = _hull([self.hv(p) for p in pts])
            if len(hull) >= 3:
                xy = [self.scr(h, v) for h, v in hull]
                o.append('<path d="M %s Z" fill="none" stroke="#000" '
                         'stroke-width="0.4" stroke-linejoin="round"/>'
                         % " L ".join("%s %s" % (td.fmt(x), td.fmt(y))
                                      for x, y in xy))
        return "".join(o)

    def hole_xy(self, hole):
        uv = proj_uv(self.d, hole["pt"])
        h, v = self.hv(uv)
        return (h - self.hmin, v - self.vmin)

    def cut_edges(self):
        if not self.info["cut"]:
            return None
        u0, u1, v0, v1 = self.info["cut"]
        pts = [self.hv(p) for p in ((u0, v0), (u0, v1),
                                    (u1, v0), (u1, v1))]
        hs = [p[0] for p in pts]
        vs = [p[1] for p in pts]
        h0, h1 = min(hs) - self.hmin, max(hs) - self.hmin
        v0d, v1d = min(vs) - self.vmin, max(vs) - self.vmin
        return (h0, (self.hmax - self.hmin) - h1,
                v0d, (self.vmax - self.vmin) - v1d,
                h1 - h0, v1d - v0d)


# ----------------------------------------------------------------------------
# оформление
# ----------------------------------------------------------------------------
def frame_generic(name, pos, qty, material, mass, code="", sub=""):
    o = [td.rect(20, 5, 185, 287, 0.7)]
    o.append(td.text(24, 13.5, name.upper(), 4.6, weight="bold"))
    o.append(td.text(24, 19.5,
                     sub or "Чертёж детали по STEP · A4 · М 1:2", 2.8))
    o.append(td.line(24, 22.0, 200, 22.0, 0.3))
    x0, y0, w, h = 20.0, 237.0, 185.0, 55.0
    o.append(td.rect(x0, y0, w, h, 0.5))
    o.append(td.line(x0 + 60, y0, x0 + 60, y0 + h, 0.35))
    for i in (1, 2, 3, 4):
        o.append(td.line(x0, y0 + i * 11.0, x0 + 60, y0 + i * 11.0, 0.2))
    for i, s in enumerate(("Разраб.", "Пров.", "Т. контр.", "Н. контр.",
                           "Утв.")):
        o.append(td.text(x0 + 2, y0 + 7.6 + i * 11.0, s, 2.3))
    o.append(td.line(x0 + 60, y0 + 16, x0 + w, y0 + 16, 0.2))
    o.append(td.line(x0 + 60, y0 + 30, x0 + w, y0 + 30, 0.2))
    o.append(td.line(x0 + 60, y0 + 42, x0 + w, y0 + 42, 0.2))
    o.append(td.line(x0 + 155, y0 + 42, x0 + 155, y0 + h, 0.2))
    o.append(td.text(x0 + 65, y0 + 9.0, name, 4.0, weight="bold"))
    o.append(td.text(x0 + 65, y0 + 13.6, "поз. %s · %s шт." % (pos, qty),
                     2.6))
    o.append(td.text(x0 + 65, y0 + 21.5, material, 2.7))
    o.append(td.text(x0 + 65, y0 + 26.5, "по STEP-модели", 2.5))
    o.append(td.text(x0 + 65, y0 + 36.0, "М 1:2", 3.6, weight="bold"))
    o.append(td.text(x0 + 65, y0 + 40.0, "масштаб", 2.3))
    o.append(td.text(x0 + 160, y0 + 36.0, "Лист 1/1", 2.8))
    o.append(td.text(x0 + 160, y0 + 40.0, "Формат A4", 2.6))
    o.append(td.text(x0 + 65, y0 + 48.0, code or ("fix11.TD.%s" % pos),
                     3.0, weight="bold"))
    o.append(td.text(x0 + 65, y0 + 52.3, "tachdraw · batch.py", 2.2))
    if mass is not None:
        o.append(td.text(x0 + 160, y0 + 48.0,
                         "Масса %s кг" % td.num(mass, 3), 2.4))
    return "".join(o)


def hdim(x1, x2, y_src, y_dim, val, size=2.8):
    return td.hdim(x1, x2, y_src, y_dim, td.num(val), size=size)


def vdim(y1, y2, x_src, x_dim, val, size=2.8):
    return td.vdim(y1, y2, x_src, x_dim, td.num(val), size=size)


def _uniq(vals):
    out = []
    for v in sorted(vals):
        if not out or abs(v - out[-1]) > 1e-6:
            out.append(v)
    return out


def draw_ordinates(o, v, rows, cut, tall):
    xs = _uniq([r[2] for r in rows if r[0] == v.d])
    ys = _uniq([r[3] for r in rows if r[0] == v.d])
    if len(xs) > 6:
        vals = [0.0] + xs + [v.wm]
        yd = v.ytop + v.h + (10.0 if tall else 24.0)
        for i in range(len(vals) - 1):
            d = vals[i + 1] - vals[i]
            if d < 0.05:
                continue
            o.append(td.hdim(v.x0 + vals[i] * S,
                             v.x0 + vals[i + 1] * S,
                             v.ytop + v.h, yd, td.num(d), size=1.9,
                             tight=(d * S < 9)))
    else:
        base = v.ytop + v.h + (10.0 if tall else 18.0)
        off = 15.0 if cut else 0.0
        for i, x in enumerate(xs):
            sx = v.x0 + x * S
            o.append(td.hdim(v.x0, sx, v.ytop + v.h,
                             base + off + i * 4.2, td.num(x), size=2.1,
                             tight=(x * S < 9)))
    if len(ys) > 6:
        vals = [0.0] + ys + [v.hm]
        xd = v.x0 + v.w + 12.0
        for i in range(len(vals) - 1):
            d = vals[i + 1] - vals[i]
            if d < 0.05:
                continue
            o.append(td.vdim(v.ytop + v.h - vals[i] * S,
                             v.ytop + v.h - vals[i + 1] * S,
                             v.x0 + v.w, xd, td.num(d), size=1.9,
                             tight=(d * S < 9)))
    else:
        bx = v.x0 + v.w + 8.0
        off = 15.0 if cut else 0.0
        for i, y in enumerate(ys):
            sy = v.ytop + v.h - y * S
            o.append(td.vdim(v.ytop + v.h, sy, v.x0 + v.w,
                             bx + off + i * 4.2, td.num(y), size=2.1,
                             tight=(y * S < 9)))


def draw_cut_dims(o, v, cut):
    x1, x2, y1, y2, w, h = cut
    base = v.ytop + v.h + 18.0
    o.append(td.hdim(v.x0, v.x0 + x1 * S, v.ytop + v.h,
                     base, td.num(x1), size=2.1))
    o.append(td.hdim(v.x0 + x1 * S, v.x0 + (x1 + w) * S,
                     v.ytop + v.h, base + 5.0, td.num(w), size=2.1))
    o.append(td.hdim(v.x0 + (x1 + w) * S, v.x0 + v.w,
                     v.ytop + v.h, base + 10.0, td.num(x2), size=2.1))
    bx = v.x0 + v.w + 8.0
    yb = v.ytop + v.h
    o.append(td.vdim(yb, yb - y1 * S, v.x0 + v.w, bx,
                     td.num(y1), size=2.1))
    o.append(td.vdim(yb - (y1 + h) * S, yb - y1 * S,
                     v.x0 + v.w, bx + 5.0, td.num(h), size=2.1))
    o.append(td.vdim(v.ytop, yb - (y1 + h) * S, v.x0 + v.w,
                     bx + 10.0, td.num(y2), size=2.1))


def draw_dia(o, v, rows, tall):
    if tall:
        return
    groups = {}
    for r in rows:
        if r[0] != v.d:
            continue
        key = tuple(sorted(round(x, 2) for x in r[1]["r"]))
        groups.setdefault(key, []).append(r)
    items = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    n = max(1, len(items))
    for i, (key, g) in enumerate(items):
        ds = "/".join(td.num(2.0 * x) for x in key)
        label = ("%d×Ø%s" % (len(g), ds)) if len(g) > 1 else ("Ø%s" % ds)
        if tall:
            tx = v.x0 + v.w + 45.0
            ty = v.ytop + 12.0 + i * 6.0
            if tx > 188.0:
                tx = v.x0 - 35.0
        else:
            tx = v.x0 + 8.0 + (i + 0.5) * (v.w - 16.0) / n
            ty = v.ytop - 12.0
        rep = min(g, key=lambda r: abs((v.x0 + r[2] * S) - tx) +
                  abs((v.ytop + v.h - r[3] * S) - ty))
        sx = v.x0 + rep[2] * S
        sy = v.ytop + v.h - rep[3] * S
        o.append(td.leader(sx, sy, tx, ty, label, size=2.3,
                           anchor="middle"))


def draw_bolt(o, v, rows):
    if not rows:
        return
    cx = sum(r[2] for r in rows) / len(rows)
    cy = sum(r[3] for r in rows) / len(rows)
    sx = v.x0 + cx * S
    sy = v.ytop + v.h - cy * S
    R = sum(math.hypot(r[2] - cx, r[3] - cy) for r in rows) / len(rows)
    o.append(td.circle(sx, sy, R * S, 0.2, dash="4 2"))
    o.append(td.centerline(sx - 5, sy, sx + 5, sy))
    o.append(td.centerline(sx, sy - 5, sx, sy + 5))
    base = v.ytop + v.h + 18.0
    bx = v.x0 + v.w + 8.0
    o.append(td.hdim(v.x0, sx, v.ytop + v.h, base, td.num(cx), size=2.2))
    o.append(td.vdim(v.ytop + v.h, sy, v.x0 + v.w, bx,
                     td.num(cy), size=2.2))
    rep = rows[0]
    px = v.x0 + rep[2] * S
    py = v.ytop + v.h - rep[3] * S
    o.append(td.leader(px, py, v.x0 + v.w + 30.0, v.ytop - 12.0,
                       "R%s" % td.num(R), size=2.4, anchor="middle"))
    r0 = next(iter(rep[1]["r"]))
    o.append(td.leader(px, py, v.x0 - 8.0, v.ytop - 12.0,
                       "%d×Ø%s" % (len(rows), td.num(2 * r0)),
                       size=2.3, anchor="middle"))


def draw_generic(ent):
    path = ent.get("step_abs") or os.path.join(STEP, ent["step"])
    shape = td.load_shape(path)
    if ent.get("preweld_notch"):
        shape = preweld_notch(shape, shape.BoundBox)
    elif "from_frame" in ent:
        shape = frame_tube(shape.BoundBox)
    elif ent.get("pick") is not None:
        shape = pick_solid(shape, ent["pick"])
    bb = shape.BoundBox
    holes, grooves = cyl_features(shape)
    prim, sec = pick_views(shape, holes, ent.get("auto_cut", False),
                           ent.get("dirs", ("X", "Y", "Z")))

    v1m = GView(prim, bb, 0.0, 0.0)
    v2m = GView(sec, bb, 0.0, 0.0)
    has_feat = bool(holes) or (prim.get("cut") is not None) or \
        (sec.get("cut") is not None)
    tall = max(v1m.h, v2m.h) > 140.0
    ytop0 = 30.0 if tall else 42.0
    v1 = GView(prim, bb, 38.0, ytop0)
    if tall or v1.w + 30.0 + v2m.w + 38.0 <= (145.0 if has_feat else 195.0):
        v2 = GView(sec, bb, 38.0 + v1.w + 30.0, ytop0)
        stacked = False
    else:
        v2 = GView(sec, bb, 38.0, ytop0 + v1.h + 50.0)
        stacked = True

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" '
         'height="297mm" viewBox="0 0 210 297">',
         '<rect width="210" height="297" fill="#fff"/>']
    dens = ent.get("density")
    mass = (shape.Volume * dens * 1e-6) if dens else None
    o.append(frame_generic(ent["name"], ent["pos"], ent["qty"],
                           ent["material"], mass,
                           ent.get("code", "")))
    o.append(v1.draw())
    o.append(v2.draw())
    oc = outer_cylinders(shape)
    for v in (v1, v2):
        if (max(v.wm, v.hm) > 3.0 * max(1e-6, min(v.wm, v.hm)) and
                len(v.info["edges"]) > 40):
            continue
        for cy in oc:
            ai = cy["axis"]
            if v.d.lstrip("-") == "XYZ"[ai]:
                continue
            r = cy["r"]
            c = cy["c"]
            bb = cy["bb"]
            def bmin(i):
                return getattr(bb, "XYZ"[i] + "Min")

            def bmax(i):
                return getattr(bb, "XYZ"[i] + "Max")

            def cv(i):
                return (c.x, c.y, c.z)[i]

            if ai == v.H:
                h0, h1 = bmin(ai), bmax(ai)
                vv = cv(v.V)
                for dv in (-r, r):
                    x1, y1 = v.scr(h0, vv + dv)
                    x2, y2 = v.scr(h1, vv + dv)
                    o.append(td.line(x1, y1, x2, y2, 0.4))
            elif ai == v.V:
                v0, v1v = bmin(ai), bmax(ai)
                hh = cv(v.H)
                for dh in (-r, r):
                    x1, y1 = v.scr(hh + dh, v0)
                    x2, y2 = v.scr(hh + dh, v1v)
                    o.append(td.line(x1, y1, x2, y2, 0.4))

    # подписи видов
    o.append(td.text(v1.x0, v1.ytop - 5.0,
                     "ВИД %s" % v1.d, 3.0, weight="bold"))
    o.append(td.text(v2.x0, v2.ytop - 5.0,
                     "ВИД %s" % v2.d, 3.0, weight="bold"))

    # габариты
    if not tall:
        o.append(hdim(v1.x0, v1.x0 + v1.w, v1.ytop + v1.h,
                      v1.ytop + v1.h + 10, v1.wm))
    o.append(vdim(v1.ytop, v1.ytop + v1.h, v1.x0,
                  v1.x0 - 10, v1.hm))
    o.append(hdim(v2.x0, v2.x0 + v2.w, v2.ytop + v2.h,
                  v2.ytop + v2.h + 10, v2.wm))
    if stacked:
        o.append(vdim(v2.ytop, v2.ytop + v2.h, v2.x0,
                      v2.x0 - 10, v2.hm))
    else:
        o.append(vdim(v2.ytop, v2.ytop + v2.h, v2.x0 + v2.w,
                      v2.x0 + v2.w + 10, v2.hm))

    # отверстия и вырезы
    rows = []
    for h in holes.values():
        for v in (v1, v2):
            if h["axis"] != v.d.lstrip("-"):
                continue
            x, y = v.hole_xy(h)
            rows.append((v.d, h, x, y))
            uv = proj_uv(v.d, h["pt"])
            sx, sy = v.scr_uv(uv)
            for rr in sorted(h["r"]):
                o.append(td.circle(sx, sy, rr * S, 0.35))
            ext = max(3.0, max(h["r"]) * S + 1.5)
            o.append(td.centerline(sx - ext, sy, sx + ext, sy))
            o.append(td.centerline(sx, sy - ext, sx, sy + ext))
            break

    bolt = ent.get("hole_dim") == "bolt"
    for v in (v1, v2):
        cut = v.cut_edges()
        if cut:
            draw_cut_dims(o, v, cut)
        if bolt:
            if any(r[0] == v.d for r in rows):
                draw_bolt(o, v, [r for r in rows if r[0] == v.d])
        else:
            draw_ordinates(o, v, rows, cut, tall)
            draw_dia(o, v, rows, tall)

    # примечания
    notes = ent.get("notes", []) + ent.get("extra_cuts", [])
    notes_x = 24.0
    if tall:
        notes_x, ny = 150.0, 40.0
    else:
        ny = 200.0
    o.append(td.text(notes_x, ny, "ПРИМЕЧАНИЯ", 2.6, weight="bold"))
    fixed = ["Размеры — по STEP; кромки притупить.",
             "Неуказанные отклонения ±0,5 мм.",
             "Размеры отверстий — от левого/нижнего края."]
    nsize = 2.0 if notes_x == 150.0 else 2.3
    for i, s in enumerate(notes + fixed):
        o.append(td.text(notes_x, ny + 5 + i * 4.6, s, nsize))

    o.append("</svg>")
    fn = os.path.join(OUT, ent["file"])
    cairosvg.svg2pdf(bytestring="".join(o).encode("utf-8"), write_to=fn)
    print("written", fn)
    return fn


# ----------------------------------------------------------------------------
# вал направляющий: отдельный лист с резьбой
# ----------------------------------------------------------------------------
def draw_shaft(out):
    """A4 portrait: вал Ø10 h6, L=176, резьба M10×15 на концах."""
    L, D = 176.0, 10.0
    THR = 15.0
    minor = 8.376          # M10, внутренний Ø резьбы
    x0, yc = 55.0, 76.0    # главный вид, 1:2
    x1 = x0 + L * S
    yt, yb = yc - D * S / 2.0, yc + D * S / 2.0
    tl = THR * S

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" '
         'height="297mm" viewBox="0 0 210 297">',
         '<rect width="210" height="297" fill="#fff"/>']
    o.append(frame_generic("Вал направляющий", "2", 4,
                           "сталь Ø10 h6, шлифованная",
                           0.109, code="fix11.TD.2"))

    o.append(td.text(24, 32, "ГЛАВНЫЙ ВИД · М 1:2", 3.2, weight="bold"))
    o.append(td.text(24, 37, "резьба M10×15 — на обоих концах", 2.5))

    # контур вала
    o.append(td.rect(x0, yt, L * S, D * S, 0.45, fill="#f4f4f4"))
    o.append(td.centerline(x0 - 4, yc, x1 + 4, yc))
    # резьба: тонкие линии впадин и границы участков
    for a, b in ((x0, x0 + tl), (x1 - tl, x1)):
        for dy in (-minor / 2.0 * S, minor / 2.0 * S):
            o.append(td.line(a, yc + dy, b, yc + dy, 0.18))
        o.append(td.line(b, yc + minor / 2.0 * S,
                         b, yc - minor / 2.0 * S, 0.18))
    o.append(td.line(x0, yt, x0, yb, 0.45))
    o.append(td.line(x1, yt, x1, yb, 0.45))

    # размеры главного вида
    o.append(td.hdim(x0, x1, yt, yt - 10.0, "176", size=3.0))
    o.append(td.hdim(x0, x0 + tl, yb, yb + 10.0, "15", size=2.4,
                     tight=True))
    o.append(td.hdim(x0 + tl, x1 - tl, yb, yb + 10.0, "146", size=2.4))
    o.append(td.hdim(x1 - tl, x1, yb, yb + 10.0, "15", size=2.4,
                     tight=True))
    o.append(td.leader(x1, yc, x1 + 12, yc - 17,
                       "Ø10 h6", size=2.9, anchor="start"))
    o.append(td.leader(x0, yc, 24, 52,
                       "2× M10×15", size=2.9, anchor="start"))

    # --- деталь А: резьбовой конец 2:1 ------------------------------------
    bx, by, bw, bh = 28.0, 108.0, 155.0, 70.0
    o.append(td.rect(bx, by, bw, bh, 0.35))
    o.append(td.text(bx + 2, by + 3.0,
                     "ДЕТАЛЬ А — РЕЗЬБА M10×15 (2:1)", 2.6,
                     weight="bold"))

    ax, ayc = 40.0, 145.0
    athr = THR * 1.0                 # 2:1 -> 30 мм
    ar = D * 1.0                     # 2:1 -> Ø20
    aminor = minor * 1.0
    at, ab = ayc - ar / 2.0, ayc + ar / 2.0
    o.append(td.rect(ax, at, athr, ar, 0.45, fill="#f4f4f4"))
    o.append(td.centerline(ax - 3, ayc, ax + athr + 3, ayc))
    for dy in (-aminor / 2.0, aminor / 2.0):
        o.append(td.line(ax, ayc + dy, ax + athr, ayc + dy, 0.18))
    o.append(td.line(ax + athr, at, ax + athr, ab, 0.45))
    o.append(td.line(ax, at, ax, ab, 0.45))
    o.append(td.hdim(ax, ax + athr, ab, ab + 7.0, "15", size=2.4,
                     tight=True))
    o.append(td.leader(ax + 8.0, at, ax + 8.0, at - 8.0,
                       "M10", size=2.8, anchor="middle"))
    o.append(td.text(ax, ab + 12.0, "резьба правая", 2.0))

    # вид с торца 2:1
    ecx, ecy, er = 160.0, 140.0, D * 1.0 / 2.0
    o.append(td.circle(ecx, ecy, er, 0.45, fill="#f4f4f4"))
    o.append(td.centerline(ecx - er - 3, ecy, ecx + er + 3, ecy))
    o.append(td.centerline(ecx, ecy - er - 3, ecx, ecy + er + 3))
    o.append(td.text(ecx, ecy + er + 6, "Ø10 h6", 2.5, "middle"))
    o.append(td.text(ecx, ecy + er + 9.5, "2:1", 2.0, "middle"))

    # --- примечания -------------------------------------------------------
    notes = [
        "ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ",
        "1. Материал — сталь Ø10 h6, шлифованная; 4 шт.",
        "2. Длина 176 = 166 + 5 мм с каждого торца.",
        "3. Резьба M10×15 на обоих концах; правая.",
        "4. Фаска 0,5×45°; заусенцы снять; поверхность h6 не повреждать.",
        "5. Крепление: гайка M10 (17 AF) + шайба Ø18/Ø10,5×1,5",
        "   снаружи средней и верхней поперечин; затяжка 8 Н·м.",
        "6. Неуказанные отклонения ±0,5 мм; биение по h6 ≤0,05 мм.",
    ]
    yy = 188.0
    for i, s in enumerate(notes):
        o.append(td.text(24 if not s.startswith("  ") else 28, yy, s.strip(),
                         2.2 if i else 2.6,
                         weight="bold" if i == 0 else "normal"))
        yy += 4.2

    o.append(td.text(24, 231,
                     "Исходник: cad/step/02_shaft.step · резьба и гайки — "
                     "по spec.csv", 2.1, color="#444"))
    o.append("</svg>")
    cairosvg.svg2pdf(bytestring="".join(o).encode("utf-8"), write_to=out)
    print("written", out)


# ----------------------------------------------------------------------------
# список деталей
# ----------------------------------------------------------------------------
TUBES = [
    ("T01", "Стойка высокая", 260, 1), ("T02", "Стойка высокая", 260, 1),
    ("T03", "Стойка высокая", 260, 1), ("T04", "Стойка высокая", 260, 1),
    ("T05", "Стойка задняя", 150, 1), ("T06", "Стойка задняя", 150, 1),
    ("T07", "Нижняя продольная", 360, 1), ("T08", "Нижняя продольная", 360, 1),
    ("T09", "Верхняя виброотсека", 160, 1),
    ("T10", "Верхняя виброотсека", 160, 1),
    ("T11", "Верхняя выноса", 200, 1), ("T12", "Верхняя выноса", 200, 1),
    ("T13", "Нижняя поперечина", 160, 1),
    ("T14", "Нижняя поперечина", 160, 1),
    ("T15", "Верхняя поперечина", 160, 1),
    ("T16", "Верхняя поперечина", 160, 1),
    ("T17", "Средняя поперечина", 160, 1),
    ("T18", "Средняя поперечина", 160, 1),
]


def build_entries():
    e = []
    e.append(dict(step="04_overlay.step", file="04_overlay.pdf",
                  name="Накладка вогнутая", pos="4", qty=1,
                  material="PLA", density=DENS["pla"],
                  extra_cuts=["Сферич. углубление Ø140, глубина 2 "
                              "(по центру)."],
                  notes=["Сфера Ø140, h=2; 4 отв. Ø12; 4 отв. M4."]))
    e.append(dict(step="05_table.step", file="05_table.pdf",
                  name="Стол", pos="5", qty=1, material="PLA",
                  density=DENS["pla"],
                  extra_cuts=["4 шестигр. углубления 7,2×5 под гайки M4 "
                              "(по углам)."],
                  notes=["16×Ø5; 4×Ø11 под LMK; 4×M4;",
                         "2×Ø5 + углубления Ø8×5 под кронштейны."]))
    e.append(dict(step="06_bracket.step", file="06_bracket.pdf",
                  name="Кронштейн ролика", pos="6", qty=2,
                  material="сталь 2 мм", density=DENS["steel"], pick=0,
                  auto_cut=True,
                  notes=["Паз 10×5; отв. Ø10,1 под ось;",
                         "по STEP 42×40×20×2; спец. 40×40 — проверить."]))
    for k in ("3", "5", "10"):
        e.append(dict(step="10_cam_%s.step" % k, file="10_cam_%s.pdf" % k,
                      name="Кулачковый диск (ход %s)" % k, pos="10",
                      qty=1, material="PLA", density=DENS["pla"],
                      extra_cuts=["S17,1; Ø40×10; ложбинка 1…2 мм; "
                                  "боковой вид — силуэт."],
                      notes=["2 лепестка R40…50; 8×Ø10 на R32 "
                             "через 45°."],
                      hole_dim="bolt"))
    e.append(dict(step="11_podstol.step", file="11_podstol.pdf",
                  name="Подстолье", pos="11", qty=1, material="PETG",
                  density=DENS["petg"],
                  extra_cuts=["Зенковка M6 Ø12×3 — 4 шт."],
                  notes=["4×M6 с зенковкой Ø12×3;",
                         "4 отв. Ø6,6 под U-хомут; 160×200×12."]))
    e.append(dict(step="14_angle.step", file="14_angle.pdf",
                  name="Накладка-уголок балки 21", pos="14", qty=8,
                  material="сталь 2 мм", density=DENS["steel"],
                  notes=["Ширина 25, t=2; 2×Ø4,5 под M4;",
                         "по STEP 55×50; спец. 50×50 — проверить;",
                         "упор в стойку 20 мм без крепления."]))
    pos_map = {"T01": "22.2", "T02": "22.2", "T03": "22.2",
               "T04": "22.2", "T05": "22.5", "T06": "22.5",
               "T07": "22.1", "T08": "22.1"}
    for t, name, ln, qty in TUBES:
        ent = dict(step="22_%s.step" % t, file="22_%s.pdf" % t,
                   name="%s (%s)" % (name, t), pos=pos_map.get(t, "22.4"),
                   qty=qty, material="труба 20×20×2",
                   density=DENS["steel"],
                   notes=["Труба 20×20×2; L=%s; рез 90°; стенка 2." % ln])
        if t in ("T13", "T14"):
            ent["notes"] = ["Труба 20×20×2; L=160; рез 90°;",
                            "2×Ø10 только в верхней стенке (Y=60/140)."]
        elif t in ("T15", "T16"):
            ent["notes"] = ["Труба 20×20×2; L=160; рез 90°;",
                            "2×Ø10,5 (сквозь) и 3×Ø4,5 — по STEP."]
        elif t in ("T17", "T18"):
            ent["dirs"] = ("X", "Y", "-Z")
            ent["auto_cut"] = True
            ent["notes"] = ["Труба 20×20×2; L=160; рез 90°;",
                            "прорезь-седло R15, ширина 9,4, глубина 5;",
                            "2×Ø10,5 — по STEP."]
        elif t in ("T01", "T02"):
            ent["notes"] = ["Труба 20×20×2; L=%s; рез 90°;" % ln,
                            "2×Ø4,5 — по STEP."]
        elif t in ("T07", "T08", "T09", "T10"):
            ent["notes"] = ["Труба 20×20×2; L=%s; рез 90°;" % ln,
                            "3×Ø4,5 — по STEP."]
        elif t in ("T11", "T12"):
            ent["notes"] = ["Труба 20×20×2; L=%s; рез 90°;" % ln,
                            "4×Ø6,6 — по STEP."]
        e.append(ent)
    return e


def main():
    only = os.environ.get("TACHDRAW_ONLY")
    if only is None or only in ("02", "02_shaft"):
        draw_shaft(os.path.join(OUT, "02_shaft.pdf"))
    if only is None or only in ("21", "21_beam"):
        td.sheet_beam21(os.path.join(STEP, "21_retainer_one.step"),
                        os.path.join(OUT, "21_beam.pdf"))
    for ent in build_entries():
        if only and only not in ent["file"]:
            continue
        try:
            draw_generic(ent)
        except Exception as exc:
            print("FAIL", ent["file"], repr(exc))


if __name__ == "__main__":
    main()
