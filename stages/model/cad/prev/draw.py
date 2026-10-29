#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2D deliverables of the "model" stage.

    PYTHONPATH=/tmp/opencode/cadlibs python3 draw.py [--force]

Produces
    ../fig/vibrotable_views.svg   A3 landscape, HLR projections + dimensions
    ../fig/vibrotable_spec.svg    A3 landscape, parts + parameters tables
    ../pic/views_sheet.png        preview, 110 dpi
    ../pic/spec_sheet.png         preview, 110 dpi

HLR helpers are the verified ones from /tmp/opencode/hlr_test/probe.py (copied).
"""
import csv
import json
import math
import os
import sys
import time

import cadquery as cq

from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.dirname(HERE)
FIG = os.path.join(STAGE, "fig")
PIC = os.path.join(STAGE, "pic")
CACHE = "/tmp/opencode/boomboom_hlr"

sys.path.insert(0, HERE)
import model        # noqa: E402
import params       # noqa: E402

FONT = "DejaVu Sans"
PAGE_W, PAGE_H = 420.0, 297.0
S = 0.4                      # 1:2.5
DEFL = 0.12


# ------------------------------------------------------------------ HLR io
def edges(shape):
    """Unique edges of a shape, deduplicated by TShape+Location."""
    if shape is None:
        return []
    shp = getattr(shape, "wrapped", shape)
    if shp.IsNull():
        return []
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shp, TopAbs_EDGE, m)
    return [TopoDS.Edge_s(m.FindKey(i)) for i in range(1, m.Extent() + 1)]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def run_hlr(shapes, eye, xdir=None, up=(0, 0, 1)):
    """HLR. gp_Ax2(P, N, Vx): N points toward the EYE, Vx = image X."""
    if xdir is None:
        xdir = cross(up, eye)
    t0 = time.perf_counter()
    algo = HLRBRep_Algo()
    for s in shapes:
        algo.Add(getattr(s, "wrapped", s))
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*eye),
                                            gp_Dir(*xdir))))
    algo.Update()
    algo.Hide()
    dt = time.perf_counter() - t0
    return HLRBRep_HLRToShape(algo), dt, xdir


def polylines(shape):
    """Discretize all edges -> [[(x, y), ...], ...] (projector plane)."""
    out = []
    for e in edges(shape):
        try:
            c = BRepAdaptor_Curve(e)
            d = GCPnts_QuasiUniformDeflection(c, DEFL)
        except Exception:
            continue
        if d.IsDone() and d.NbPoints() > 1:
            out.append([(d.Value(i).X(), d.Value(i).Y())
                        for i in range(1, d.NbPoints() + 1)])
    return out


VIEWS = [
    # key      eye             xdir        u range          v range        origin
    dict(key="front", eye=(-1, 0, 0), xdir=None,
         u=(-100.0, 100.0), v=(0.0, 313.0), o=(24.0, 36.0)),
    dict(key="side", eye=(0, -1, 0), xdir=None,
         u=(-30.0, 455.0), v=(0.0, 313.0), o=(140.0, 36.0)),
    dict(key="top", eye=(0, 0, 1), xdir=(1, 0, 0),
         u=(-30.0, 455.0), v=(-100.0, 100.0), o=(24.0, 176.0)),
]


def hlr_view(parts, view, force=False):
    """HLR for one view, cached in /tmp by model.py mtime + part count."""
    os.makedirs(CACHE, exist_ok=True)
    stamp = "%d_%d" % (os.path.getmtime(os.path.join(HERE, "model.py")),
                       len(parts))
    fn = os.path.join(CACHE, "%s_%s.json" % (view.key, stamp))
    if os.path.exists(fn) and not force:
        with open(fn, encoding="utf-8") as f:
            d = json.load(f)
        print("  %-5s cached  vis=%d hid=%d  (HLR %.1f s)"
              % (view.key, len(d["vis"]), len(d["hid"]), d["sec"]))
        return d["vis"], d["hid"], d["sec"]

    comp = cq.Compound.makeCompound([p[2] for p in parts])
    h, dt, _ = run_hlr([comp], view.eye, view.xdir)
    vis = polylines(cq.Shape.cast(h.VCompound()))
    vis += polylines(cq.Shape.cast(h.OutLineVCompound()))
    hid = polylines(cq.Shape.cast(h.HCompound()))
    hid += polylines(cq.Shape.cast(h.OutLineHCompound()))
    d = dict(vis=vis, hid=hid, sec=dt)
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(d, f)
    return vis, hid, dt


# ------------------------------------------------------------------ primitives
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


try:                                         # real DejaVu metrics
    from PIL import ImageFont
    _FNT = {}

    def text_w(s, size, bold=False):
        path = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-%s.ttf"
                % ("Bold" if bold else "Book"))
        if not os.path.exists(path):
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if path not in _FNT:
            _FNT[path] = ImageFont.truetype(path, 200)
        return _FNT[path].getlength(str(s)) * size / 200.0
except Exception:                            # conservative fallback
    def text_w(s, size, bold=False):
        w = 0.0
        for ch in str(s):
            if ch in " .,:;!|`'":
                k = 0.30
            elif ch in "iljI1()[]/\\-–":
                k = 0.38
            elif ch in "mwMWШЩЖЮшщжюфы":
                k = 0.92
            elif ch.isupper():
                k = 0.66
            elif ch.isdigit():
                k = 0.58
            else:
                k = 0.58
            w += k
        return w * size * (1.04 if bold else 1.0)


def fit(s, width, size, bold=False):
    """Truncate with ellipsis so that s fits into width (mm)."""
    s = str(s)
    if text_w(s, size, bold) <= width:
        return s
    while s and text_w(s + "…", size, bold) > width:
        s = s[:-1]
    return s.rstrip() + "…"


class Sheet:
    def __init__(self, w=PAGE_W, h=PAGE_H):
        self.w, self.h = w, h
        self.items = []

    def add(self, s):
        self.items.append(s)

    def line(self, x1, y1, x2, y2, w=0.2, dash=None, color="#000",
             cap="round"):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" '
                 'stroke="%s" stroke-width="%.2f" stroke-linecap="%s"%s/>'
                 % (x1, y1, x2, y2, color, w, cap, d))

    def polyline(self, pts, w=0.3, dash=None, color="#000"):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        p = " ".join("%.2f,%.2f" % (x, y) for x, y in pts)
        self.add('<polyline points="%s" fill="none" stroke="%s" '
                 'stroke-width="%.2f" stroke-linejoin="round" '
                 'stroke-linecap="round"%s/>' % (p, color, w, d))

    def rect(self, x, y, w_, h_, sw=0.3, fill="none", color="#000"):
        self.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" '
                 'fill="%s" stroke="%s" stroke-width="%.2f"/>'
                 % (x, y, w_, h_, fill, color, sw))

    def circle(self, x, y, r, sw=0.25, fill="none", color="#000"):
        self.add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" '
                 'stroke="%s" stroke-width="%.2f"/>'
                 % (x, y, r, fill, color, sw))

    def dot(self, x, y, r=0.4):
        self.add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#000"/>'
                 % (x, y, r))

    def text(self, x, y, s, size=3.2, anchor="start", bold=False,
             rot=None, color="#000", italic=False, halo=0.0):
        if halo:
            w = text_w(s, size, bold)
            x0 = x - (0.0 if anchor == "start" else
                      w if anchor == "end" else w / 2.0)
            tr = (' transform="rotate(%.2f %.2f %.2f)"' % (rot, x, y)
                  if rot is not None else "")
            self.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" '
                     'fill="#fff"%s/>' % (x0 - halo, y - size * 0.78 - halo,
                                          w + 2 * halo, size * 0.9 + 2 * halo,
                                          tr))
        st = 'font-family="%s" font-size="%.2f"' % (FONT, size)
        if bold:
            st += ' font-weight="bold"'
        if italic:
            st += ' font-style="italic"'
        tr = (' transform="rotate(%.2f %.2f %.2f)"' % (rot, x, y)
              if rot is not None else "")
        self.add('<text x="%.2f" y="%.2f" text-anchor="%s" fill="%s" %s%s>'
                 '%s</text>' % (x, y, anchor, color, st, tr, esc(s)))

    def arrow(self, x, y, ang, L=2.2, W=0.7):
        """Filled arrowhead, tip at (x, y), pointing along ang (rad)."""
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = -dy, dx
        p = [(x, y),
             (x - L * dx + W / 2 * px, y - L * dy + W / 2 * py),
             (x - L * dx - W / 2 * px, y - L * dy - W / 2 * py)]
        self.add('<polygon points="%s" fill="#000" stroke="none"/>'
                 % " ".join("%.2f,%.2f" % q for q in p))

    def save(self, path):
        hdr = ('<svg xmlns="http://www.w3.org/2000/svg" width="420mm" '
               'height="297mm" viewBox="0 0 420 297">\n'
               '<rect width="420" height="297" fill="#ffffff"/>\n')
        with open(path, "w", encoding="utf-8") as f:
            f.write(hdr + "\n".join(self.items) + "\n</svg>\n")


# ------------------------------------------------------------------ views
class View:
    def __init__(self, d):
        self.key = d["key"]
        self.u0, self.u1 = d["u"]
        self.v0, self.v1 = d["v"]
        self.ox, self.oy = d["o"]
        self.eye, self.xdir = d["eye"], d["xdir"]

    def X(self, u):
        return self.ox + S * (u - self.u0)

    def Y(self, v):
        return self.oy + S * (self.v1 - v)

    def page(self, u, v):
        return self.X(u), self.Y(v)


FRONT = View(VIEWS[0])
SIDE = View(VIEWS[1])
TOP = View(VIEWS[2])
VIEW_BY_KEY = {v.key: v for v in (FRONT, SIDE, TOP)}


# ------------------------------------------------------------------ dimensions
def _ext(sh, x1, y1, x2, y2, gap, over):
    """Extension line from geometry point toward the dimension line."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    sh.line(x1 + ux * gap, y1 + uy * gap, x2 + ux * over, y2 + uy * over,
            w=0.13)


def dim_h(sh, view, u1, u2, v_geom, v_dim, txt, side="above",
          tsize=3.0, tx=None, ty=None, halo=0.0):
    x1, x2 = view.X(u1), view.X(u2)
    yg, yd = view.Y(v_geom), view.Y(v_dim)
    _ext(sh, x1, yg, x1, yd, 0.8, 1.6)
    _ext(sh, x2, yg, x2, yd, 0.8, 1.6)
    sh.line(x1, yd, x2, yd, w=0.15)
    sh.arrow(x1, yd, math.pi)
    sh.arrow(x2, yd, 0.0)
    cx = tx if tx is not None else (x1 + x2) / 2.0
    if ty is not None:
        base = ty
    else:
        base = yd - 1.0 if side == "above" else yd + 3.2
    sh.text(cx, base, txt, tsize, "middle", halo=halo)


def dim_v(sh, view, u, v1, v2, u_dim, txt, side="left", tsize=3.0,
          ty=None, horizontal=False, tx=None, halo=0.0):
    x, xd = view.X(u), view.X(u_dim)
    y1, y2 = view.Y(v1), view.Y(v2)
    _ext(sh, x, y1, xd, y1, 0.8, 1.6)
    _ext(sh, x, y2, xd, y2, 0.8, 1.6)
    sh.line(xd, y1, xd, y2, w=0.15)
    short = abs(y2 - y1) < 8.0
    if short:                     # arrows outside, pointing at the ends
        sh.arrow(xd, y1, -math.pi / 2)
        sh.arrow(xd, y2, math.pi / 2)
    else:
        sh.arrow(xd, y1, math.pi / 2)
        sh.arrow(xd, y2, -math.pi / 2)
    cy = ty if ty is not None else (y1 + y2) / 2.0
    if horizontal:
        xt = tx if tx is not None else (xd + 2.0 if side == "right"
                                        else xd - 2.0)
        sh.text(xt, cy + 1.1, txt, tsize,
                "start" if side == "right" else "end", halo=halo)
    else:
        tx = xd - 0.9 if side == "left" else xd + 3.0
        sh.text(tx, cy, txt, tsize, "middle", rot=-90, halo=0.45)


def leader(sh, target, x_t, y_t, txt, anchor="start", tsize=2.9,
           arrow=True, gap=1.4):
    """Leader from a text position to a target point (arrow at the target)."""
    tx, ty = target
    if anchor == "start":
        x0, y0 = x_t - gap, y_t - 1.0
    elif anchor == "end":
        x0, y0 = x_t + gap, y_t - 1.0
    else:
        x0, y0 = x_t, y_t + 1.6
    sh.line(x0, y0, tx, ty, w=0.2)
    if arrow:
        ang = math.atan2(ty - y0, tx - x0)
        sh.arrow(tx, ty, ang, L=2.0, W=0.65)
    sh.text(x_t, y_t, txt, tsize, anchor, halo=0.4)


def centre_line(sh, view, p1, p2):
    sh.line(*view.page(*p1), *view.page(*p2), w=0.15,
            dash="6,1.5,1.2,1.5", color="#444")


# ------------------------------------------------------------------ balloons
BALLOON_FRONT_LEFT = [26, 25, 5, 19, 17]
FRONT_LEFT_Y = [61.0, 78.0, 91.0, 104.0, 117.0]
BALLOON_FRONT_RIGHT = [28, 18, 23, 16, 15]
BALLOON_SIDE = [21, 30, 24, 11, 6, 22, 1]

# Explicit targets (view, number) -> model (u, v) where a part's bbox centre
# is ambiguous / falls into a hollow or onto another part.
TARGETS = {
    ("front", 26): (-88.0, 250.0),    # left frame post (bbox centre = cam hub)
    ("front", 18): (60.0, 239.0),     # overlay, right half (4 mm from #28)
    ("front", 15): (-30.0, 222.5),    # bracket upper horizontal leg
    ("side", 21): (300.0, 196.0),     # subtable
    ("side", 24): (300.0, 179.0),     # drill spacer
    ("side", 6): (30.0, 150.0),       # drive shaft, left part
    ("side", 22): (120.0, 150.0),     # second shaft bearing (x = 120)
    ("side", 1): (80.0, 142.5),       # clamp beam at x = 80 (not x = 120)
}

BALLOON_NAMES = {
    26: "Рама сварная",
    28: "Стол (фанера 10)",
    18: "Накладка вогнутая (3D печать)",
    5: "Вал Ø10×120",
    19: "Ограничитель вала",
    17: "Линейный подшипник LMF10UU",
    25: "Пружина прижимная",
    15: "Кронштейн угловой 40×40×20×2",
    23: "Подшипник-ролик 6200",
    16: "Кулачковый диск (3D печать)",
    6: "Вал привода — шпилька М10",
    22: "Подшипник вала 6200",
    1: "Балка фиксации подшипника",
    21: "Подстолье (фанера 12)",
    11: "Дрель (условно, покупная)",
    30: "Хомут U-образный М6",
    24: "Прокладка под дрель",
}


def part_centres(parts, view):
    """{name: [(page x, page y), ...]} projected bbox centres per occurrence."""
    out = {}
    for name, _local, placed, _mat, _q in parts:
        bb = placed.BoundingBox()
        cx, cy, cz = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2,
                      (bb.zmin + bb.zmax) / 2)
        if view.key == "front":
            u, v = -cy, cz
        elif view.key == "side":
            u, v = cx, cz
        else:
            u, v = cx, cy
        out.setdefault(name, []).append(view.page(u, v))
    return out


def balloon(sh, x, y, num, target, r=3.0):
    dx, dy = target[0] - x, target[1] - y
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    sh.line(x + ux * r, y + uy * r, target[0], target[1], w=0.2)
    sh.dot(target[0], target[1], 0.4)
    sh.circle(x, y, r, sw=0.25, fill="#fff")
    sh.text(x, y + 1.15, str(num), 3.2, "middle", bold=True)


# ------------------------------------------------------------------ sheet 1
def draw_views_sheet(parts, data):
    sh = Sheet()
    sh.rect(5, 5, 410, 287, sw=0.5)

    # ---------- geometry
    for view in (FRONT, SIDE, TOP):
        vis, hid, _ = data[view.key]
        for pl in hid:
            sh.polyline([view.page(u, v) for u, v in pl], w=0.15,
                        dash="1.2,1.2", color="#555")
        for pl in vis:
            sh.polyline([view.page(u, v) for u, v in pl], w=0.3)

    # ---------- centre lines
    centre_line(sh, FRONT, (0, 132), (0, 258))
    centre_line(sh, FRONT, (-100, 150), (100, 150))
    centre_line(sh, TOP, (100, -100), (100, 100))
    centre_line(sh, TOP, (-30, 0), (455, 0))

    # ---------- header
    sh.text(16, 12, "ВИБРОСТОЛ ДЛЯ ФИЗИЧЕСКОГО ЭКСПЕРИМЕНТА — "
            "ЭСКИЗНАЯ КОМПОНОВКА", 5, bold=True)
    sh.text(415, 12, "A3 · 420×297", 3.2, "end")

    # ---------- balloons (under dimensions, so texts stay legible)
    cfront = part_centres(parts, FRONT)
    cside = part_centres(parts, SIDE)
    bl = []

    def target(view, centres, n, x, y):
        t = TARGETS.get((view.key, n))
        if t is not None:
            return view.page(*t)
        return min(centres[BALLOON_NAMES[n]],
                   key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)

    for i, n in enumerate(BALLOON_FRONT_LEFT):
        x, y = 9.5, FRONT_LEFT_Y[i]
        tgt = target(FRONT, cfront, n, x, y)
        bl.append((FRONT.key, n, x, y, tgt))
        balloon(sh, x, y, n, tgt)
    for i, n in enumerate(BALLOON_FRONT_RIGHT):
        x, y = 118.0, 50.0 + 16.0 * i
        tgt = target(FRONT, cfront, n, x, y)
        bl.append((FRONT.key, n, x, y, tgt))
        balloon(sh, x, y, n, tgt)
    for i, n in enumerate(BALLOON_SIDE):
        x, y = 360.0, 45.0 + 15.0 * i
        tgt = target(SIDE, cside, n, x, y)
        bl.append((SIDE.key, n, x, y, tgt))
        balloon(sh, x, y, n, tgt)

    # ---------- front view dimensions
    dim_h(sh, FRONT, -100, 100, 0, -22, "200")
    dim_v(sh, FRONT, -118, 0, 300, -118, "300", "left")
    dim_h(sh, FRONT, -78, 78, 234, 247.5, "156", tx=52)
    dim_h(sh, FRONT, -54, 54, 224, 214, "108", halo=0.3)
    dim_h(sh, FRONT, 0, 54, 224, 206, "54", tx=60.5, ty=80.3, halo=0.3)
    dim_v(sh, FRONT, 118, 0, 150, 118, "150", "right")
    dim_v(sh, FRONT, 78, 224, 234, 88, "10", "right", horizontal=True,
          tx=100.2, halo=0.35)
    dim_v(sh, FRONT, 75, 234, 244, 88, "10", "right", horizontal=True,
          tx=100.2, halo=0.35)

    # ---------- side view dimensions
    dim_h(sh, SIDE, -30, 455, 313, 325, "485")
    dim_h(sh, SIDE, 0, 200, 0, -12, "200")
    dim_h(sh, SIDE, 200, 400, 0, -12, "200")
    dim_h(sh, SIDE, 0, 400, 0, -26, "400")
    dim_v(sh, SIDE, 470, 0, 300, 470, "300", "right")
    dim_v(sh, SIDE, 482, 0, 313, 482, "313 (с гайками)", "right", tsize=2.8)
    dim_v(sh, SIDE, -42, 0, 200, -42, "200", "right")
    dim_v(sh, SIDE, -55, 0, 150, -55, "150", "left")
    dim_h(sh, SIDE, 46, 154, 224, 246, "108")
    dim_v(sh, SIDE, 178, 224, 234, 182, "10", "right", horizontal=True,
          tx=226.6, halo=0.35)
    dim_v(sh, SIDE, 175, 234, 244, 182, "10", "right", horizontal=True,
          tx=226.6, halo=0.35)

    # ---------- top view dimensions
    dim_h(sh, TOP, 0, 400, -100, -120, "400")
    dim_v(sh, TOP, -42, -100, 100, -42, "200", "left")
    dim_h(sh, TOP, 22, 178, 78, 105, "156")
    dim_h(sh, TOP, 205, 395, 95, 105, "190", tx=131)
    dim_h(sh, TOP, 46, 154, -54, -74, "108", tx=64, halo=0.3)
    dim_h(sh, TOP, 100, 154, -54, -66, "54", side="above", halo=0.3)
    dim_v(sh, TOP, 118, -30, 30, 118, "60", "right")

    # ---------- leaders
    leader(sh, FRONT.page(0, 197), 69.5, 55.5, "⌀95 (R45…R50)", anchor="end")
    leader(sh, FRONT.page(30, 207), 86, 86, "⌀30")
    leader(sh, FRONT.page(-54, 280), 10, 44, "⌀10")
    leader(sh, SIDE.page(100, 197), 320, 120, "⌀95")
    leader(sh, SIDE.page(100, 207), 320, 128, "⌀30 (ролик)")

    # ---------- view labels
    sh.text(64, 28, "Вид спереди (со стороны привода, −X)", 4, "middle")
    sh.text(246, 22, "Вид сбоку (слева, −Y)", 4, "start")
    sh.text(120, 273, "Вид сверху (−Z)", 4, "middle")

    # ---------- notes
    sh.rect(232, 176, 183, 56, sw=0.3, fill="#fff")
    sh.text(237, 182.5, "ПРИМЕЧАНИЯ", 3.6, bold=True)
    notes = [
        "Ход 5 мм (R45…R50); амплитуда в допуске 3…10 мм, закон близок "
        "к гармоническому.",
        "Частота 5…15 Гц задаётся оборотами дрели.",
        "4 прижимные пружины Ø18, монтажная длина 56 мм (сжатие 20 %).",
        "Рама: труба 20×20×1,5, сварная; крепление струбцинами к станине.",
        "Накладка и кулачок — 3D-печать (PLA); крепёж — покупной.",
        "Позиции деталей — см. лист 2 (спецификация).",
    ]
    for i, s in enumerate(notes):
        sh.text(237, 188.5 + 7.0 * i, s, 3.2)

    # ---------- title block
    sh.rect(232, 236, 183, 54, sw=0.3, fill="#fff")
    sh.text(236, 245, "ВИБРОСТОЛ — ЭСКИЗ СБОРКИ", 8, bold=True)
    sh.text(236, 251, "Назначение: колебания стола для эксперимента "
            "с шариком", 3.2)
    tb = ["Этап: формирование эскизов по рисунку от руки",
          "Масштаб 1:2,5 · Лист 1/1 · A3",
          "Единицы: мм · Масса ≈ 8,3 кг",
          "Модель: cad/step/assembly.step · проекции HLR"]
    for i, s in enumerate(tb):
        sh.text(236, 258 + 6.5 * i, s, 3.2)

    sh.save(os.path.join(FIG, "vibrotable_views.svg"))
    return bl


# ------------------------------------------------------------------ checks
def _seg_dist(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return math.hypot(px - ax, py - ay), (ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    q = (ax + t * dx, ay + t * dy)
    return math.hypot(px - q[0], py - q[1]), q


def check_balloons(bl, data):
    """Distinct target dots >= 6 mm apart; every dot near a drawn stroke."""
    print("balloon -> target (sheet mm):")
    for key, n, x, y, t in bl:
        print("  #%-2d %-5s balloon (%5.1f, %5.1f)  target (%6.1f, %5.1f)"
              % (n, key, x, y, t[0], t[1]))
    worst = None
    for i in range(len(bl)):
        for j in range(i + 1, len(bl)):
            (k1, n1, _x1, _y1, t1) = bl[i]
            (k2, n2, _x2, _y2, t2) = bl[j]
            d = math.hypot(t1[0] - t2[0], t1[1] - t2[1])
            if worst is None or d < worst[0]:
                worst = (d, n1, n2)
            if d < 6.0:
                print("  WARN targets #%d and #%d only %.1f mm apart"
                      % (n1, n2, d))
    print("  min distance between target dots: %.1f mm (#%d/#%d)"
          % worst)
    print("distance from each target to the nearest drawn stroke:")
    for key, n, _x, _y, t in bl:
        vis, hid, _ = data[key]
        best = (1e9, None)
        for pl in vis:
            pts = [VIEW_BY_KEY[key].page(u, v) for u, v in pl]
            for a, b in zip(pts, pts[1:]):
                d, q = _seg_dist(t, a, b)
                if d < best[0]:
                    best = (d, q)
        print("  #%-2d %-5s %4.1f mm  nearest stroke point (%5.1f, %5.1f)"
              % (n, key, best[0], best[1][0], best[1][1]))
    return worst[0]


# ------------------------------------------------------------------ sheet 2
def read_spec():
    with open(os.path.join(HERE, "spec.csv"), encoding="utf-8") as f:
        return list(csv.reader(f, delimiter=";"))


def draw_spec_sheet():
    rows = read_spec()
    head, body = rows[0], rows[1:]
    sh = Sheet()
    sh.rect(5, 5, 410, 287, sw=0.5)

    sh.text(210, 16, "СПЕЦИФИКАЦИЯ ДЕТАЛЕЙ", 8, "middle", bold=True)
    sh.text(210, 23, "Вибростол · этап «модель» · единицы: мм", 3.4,
            "middle")

    # ----- parts table
    cols = [("№", 10), ("Наименование", 100), ("Кол-во", 14),
            ("Материал", 32), ("Масса, г", 20), ("Примечание", 46)]
    x0, y0, rh = 10.0, 30.0, 6.5
    total = 0.0
    x = x0
    for name, w in cols:
        sh.rect(x, y0, w, rh, sw=0.25, fill="#e8e8e8")
        sh.text(x + 1.2, y0 + 4.4, fit(name, w - 2, 2.6), 2.6)
        x += w
    y = y0 + rh
    for i, row in enumerate(body):
        vals = list(row) + [""] * (6 - len(row))
        if "Дрель" in vals[1]:
            vals[3] = "—"
            vals[5] = "покупное, условно"
        mass = float(vals[4]) if vals[4] else 0.0
        qty = int(float(vals[2])) if vals[2] else 0
        total += mass * qty
        if i % 2:
            sh.rect(x0, y, sum(w for _, w in cols), rh, sw=0,
                    fill="#f6f6f6")
        x = x0
        for (name, w), v in zip(cols, vals):
            if name == "№":
                sh.text(x + w / 2, y + 4.4, v, 2.8, "middle")
            elif name in ("Кол-во", "Масса 1 шт, г"):
                sh.text(x + w / 2, y + 4.4, v, 2.8, "middle")
            else:
                sh.text(x + 1.2, y + 4.4, fit(v, w - 2.4, 2.8), 2.8)
            x += w
        y += rh
    # grid
    x = x0
    for name, w in cols:
        sh.line(x, y0, x, y, w=0.18)
        x += w
    sh.line(x, y0, x, y, w=0.18)
    for k in range(len(body) + 2):
        sh.line(x0, y0 + k * rh, x0 + sum(w for _, w in cols),
                y0 + k * rh, w=0.18)

    # ----- parameters table
    px, py, prh = 245.0, 30.0, 4.9
    pcols = [("Параметр", 55), ("Обозначение", 22), ("Значение", 16),
             ("Ед.", 10), ("Примечание", 55)]
    x = px
    for name, w in pcols:
        sh.rect(x, py, w, prh, sw=0.25, fill="#e8e8e8")
        sh.text(x + 1.0, py + 3.5, name, 2.6)
        x += w
    yy = py + prh
    for i, p in enumerate(params.PARAMS):
        if i % 2:
            sh.rect(px, yy, sum(w for _, w in pcols), prh, sw=0,
                    fill="#f6f6f6")
        v = p[2]
        if isinstance(v, float):
            v = ("%d" % v) if abs(v - round(v)) < 1e-9 else ("%g" % v)
        vals = [p[0], p[1], v, p[3], p[4]]
        x = px
        for (name, w), val in zip(pcols, vals):
            size = 2.6
            txt = fit(val, w - 1.4, size)
            if txt != str(val) and name == "Значение":
                for size in (2.4, 2.2, 2.0):
                    txt = fit(val, w - 1.4, size)
                    if txt == str(val):
                        break
            sh.text(x + 1.0, yy + 3.5, txt, size)
            x += w
        yy += prh
    x = px
    for name, w in pcols:
        sh.line(x, py, x, yy, w=0.18)
        x += w
    sh.line(x, py, x, yy, w=0.18)
    for k in range(len(params.PARAMS) + 2):
        sh.line(px, py + k * prh, px + sum(w for _, w in pcols),
                py + k * prh, w=0.18)

    # ----- footers
    fy = 252.0
    sh.text(10, fy, "Итого масса сборки: %.2f кг (сумма масс 1 шт × "
            "количество)." % (total / 1000.0), 3.2)
    sh.text(10, fy + 6, "Материалы: сталь S235/S355, фанера 10/12 мм, PLA; "
            "крепёж по ГОСТ/ISO.", 3.2)
    sh.text(10, fy + 12, "Массы расчётные (по объёму STEP и плотности); "
            "дрель учтена условно.", 3.2)
    sh.text(415, 290, "Лист 2/2 · A3 · 420×297", 3.2, "end")
    sh.save(os.path.join(FIG, "vibrotable_spec.svg"))
    return total


# ------------------------------------------------------------------ main
def main():
    force = "--force" in sys.argv
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(PIC, exist_ok=True)

    t0 = time.perf_counter()
    parts = model.build()
    print("build(): %d placed parts in %.1f s" % (len(parts),
                                                  time.perf_counter() - t0))

    data = {}
    for view in (FRONT, SIDE, TOP):
        vis, hid, dt = hlr_view(parts, view, force)
        pts = [p for pl in vis + hid for p in pl]
        bb = (min(p[0] for p in pts), max(p[0] for p in pts),
              min(p[1] for p in pts), max(p[1] for p in pts))
        data[view.key] = (vis, hid, dt)
        print("%-5s  visible %4d polylines, hidden %4d polylines, "
              "HLR %5.1f s, bbox u %7.1f…%7.1f  v %6.1f…%6.1f"
              % (view.key, len(vis), len(hid), dt,
                 bb[0], bb[1], bb[2], bb[3]))

    bl = draw_views_sheet(parts, data)
    total = draw_spec_sheet()

    import cairosvg
    for svg, png in (("vibrotable_views.svg", "views_sheet.png"),
                     ("vibrotable_spec.svg", "spec_sheet.png")):
        cairosvg.svg2png(url=os.path.join(FIG, svg),
                         write_to=os.path.join(PIC, png), dpi=110)
    print("masses: %.2f kg" % (total / 1000.0))
    check_balloons(bl, data)


if __name__ == "__main__":
    main()
