"""Параметрическая модель «орочьего» вибростола fix10l (FreeCAD Part).

Ключевые решения:
  * 6 шпилек M10 вместо рамы; стол скользит по шпилькам;
  * стол 200x200 из фанеры 10 мм, накладка fix9 200x150 по центру;
  * верхняя платформа из фанеры с вырезом 120x120;
  * 4 пружины Ø17x1,5x60, установленная 36 мм;
  * нижние демпферы — резиновые кольца, без преднатяга;
  * вал привода M10 в двух поперечных балках 20x20x2;
  * кулачки fix9 R45/50 импортируются из предыдущего этапа;
  * кронштейн ролика — два уголка 2 мм на саморезах.
"""

import math
import os

import FreeCAD as App
import Part

from params import P

V = App.Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FIX9_STEP = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir,
                                          "fix9", "cad", "step"))

DENSITY = {
    "steel": 7.85e-3,      # г/мм3
    "plywood": 0.60e-3,    # 600 кг/м3
    "pla": 1.24e-3,
    "petg": 1.27e-3,
    "rubber": 1.15e-3,
    "bearing": 7.85e-3,
    "plastic": 1.00e-3,
    "drill": 0.0,          # масса дрели не входит в отчёт
}


# ----------------------------------------------------------------------------
# примитивы
# ----------------------------------------------------------------------------
def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0),
                        V(min(x0, x1), min(y0, y1), min(z0, z1)))


def cyl_x(r, x0, x1, y, z):
    return Part.makeCylinder(r, abs(x1 - x0), V(min(x0, x1), y, z),
                             V(1, 0, 0))


def cyl_y(r, y0, y1, x, z):
    return Part.makeCylinder(r, abs(y1 - y0), V(x, min(y0, y1), z),
                             V(0, 1, 0))


def cyl_z(r, z0, z1, x, y):
    return Part.makeCylinder(r, abs(z1 - z0), V(x, y, min(z0, z1)),
                             V(0, 0, 1))


def hex_prism_x(across_flats, x0, x1, y, z):
    r = across_flats / math.sqrt(3.0)
    pts = [V(min(x0, x1), y + r * math.cos(a), z + r * math.sin(a))
           for a in [math.radians(30 + 60 * i) for i in range(6)]]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(V(abs(x1 - x0), 0, 0))


def hex_prism_z(across_flats, z0, z1, x, y):
    r = across_flats / math.sqrt(3.0)
    pts = [V(x + r * math.cos(a), y + r * math.sin(a), min(z0, z1))
           for a in [math.radians(30 + 60 * i) for i in range(6)]]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(V(0, 0, abs(z1 - z0)))


def concat(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes:
        return None
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()


# ----------------------------------------------------------------------------
# трубы
# ----------------------------------------------------------------------------
def tube_x(x0, x1, yc, z0, size=None, wall=None):
    size = P["tube"] if size is None else size
    wall = P["wall"] if wall is None else wall
    y0 = yc - size / 2.0
    outer = box(x0, y0, z0, x1, y0 + size, z0 + size)
    inner = box(x0, y0 + wall, z0 + wall, x1, y0 + size - wall,
                z0 + size - wall)
    return outer.cut(inner)


def tube_y(y0, y1, xc, z0, size=None, wall=None):
    size = P["tube"] if size is None else size
    wall = P["wall"] if wall is None else wall
    x0 = xc - size / 2.0
    outer = box(x0, y0, z0, x0 + size, y1, z0 + size)
    inner = box(x0 + wall, y0, z0 + wall, x0 + size - wall, y1,
                z0 + size - wall)
    return outer.cut(inner)


# ----------------------------------------------------------------------------
# переиспользуемые детали fix9
# ----------------------------------------------------------------------------
def _read_step(name):
    fn = os.path.join(FIX9_STEP, name)
    if not os.path.exists(fn):
        return None
    return Part.read(fn)


def overlay():
    """Накладка fix9 200x150x6; сдвиг X на +20 (было −20…180)."""
    s = _read_step("04_overlay.step")
    if s is not None:
        return s.translated(V(20.0, 0, 0)).removeSplitter()
    # резервное построение, если STEP предыдущего этапа недоступен
    s = box(P["overlay_x0"], P["overlay_y0"], P["overlay_z0"],
            P["overlay_x1"], P["overlay_y1"], P["overlay_z1"])
    R = 1225.0
    cx, cy = 100.0, 100.0
    cz = P["overlay_z1"] - 2.0 + R
    s = s.cut(Part.makeSphere(R, V(cx, cy, cz)))
    for x in (P["overlay_screw_x"], P["overlay_screw_x2"]):
        for y in (P["overlay_screw_y1"], P["overlay_screw_y2"]):
            s = s.cut(cyl_z(2.1, P["overlay_z0"] - 1,
                            P["overlay_z1"] + 1, x, y))
            s = s.cut(Part.makeCone(4.0, 2.0, 2.5,
                                    V(x, y, P["overlay_z1"]),
                                    V(0, 0, -1)))
    return s


def _cam_radius(theta, stroke):
    rmax = P["cam_rmax"]
    e = stroke / 2.0
    return rmax - e - e * math.cos(2.0 * theta)


def _cam_wire(x, stroke, off=0.0, n=180):
    cy, cz = P["drive_y"], P["drive_z"]
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        r = _cam_radius(a, stroke) + off
        pts.append(V(x, cy + r * math.cos(a), cz + r * math.sin(a)))
    return Part.makePolygon(pts + [pts[0]])


def _cam_build(stroke):
    """Резервное построение кулачка, если STEP fix9 недоступен."""
    cy, cz = P["drive_y"], P["drive_z"]
    disk_x0, disk_x1 = 74.0, 86.0
    boss_x0, boss_x1 = 64.0, 74.0
    groove_w = 9.5
    flange_r = 52.0
    ft = (disk_x1 - disk_x0 - groove_w) / 2.0
    core = Part.Face(_cam_wire(disk_x0 + ft, stroke)).extrude(V(groove_w, 0, 0))
    left = Part.makeLoft([_cam_wire(disk_x0, stroke, flange_r - P["cam_rmax"]),
                          _cam_wire(disk_x0 + ft, stroke)], True, True)
    right = Part.makeLoft([_cam_wire(disk_x1 - ft, stroke),
                           _cam_wire(disk_x1, stroke,
                                     flange_r - P["cam_rmax"])], True, True)
    s = core.fuse(left).fuse(right)
    boss = cyl_x(20.0, boss_x0, boss_x1, cy, cz)
    s = s.fuse(boss)
    s = s.cut(hex_prism_x(17.1, boss_x0 - 1, disk_x1 + 1, cy, cz))
    hr = 5.0
    for i in range(8):
        a = math.radians(45.0 * i)
        s = s.cut(cyl_x(hr, disk_x0 - 1, disk_x1 + 1,
                        cy + 32.0 * math.cos(a), cz + 32.0 * math.sin(a)))
    return s.removeSplitter()


def cam_shape(stroke):
    s = _read_step("10_cam_%d.step" % int(stroke))
    if s is not None:
        return s.translated(V(20.0, 0, 0))
    return _cam_build(stroke).translated(V(20.0, 0, 0))


# ----------------------------------------------------------------------------
# фанера
# ----------------------------------------------------------------------------
def table():
    s = box(P["table_x0"], P["table_y0"], P["table_z0"],
            P["table_x1"], P["table_y1"], P["table_z1"])
    # отверстия под шпильки
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            s = s.cut(cyl_z(P["stud_hole_d"] / 2.0, P["table_z0"] - 1,
                            P["table_z1"] + 1, x, y))
    # глухие пилоты саморезов накладки (6 мм)
    for x in (P["overlay_screw_x"], P["overlay_screw_x2"]):
        for y in (P["overlay_screw_y1"], P["overlay_screw_y2"]):
            s = s.cut(cyl_z(2.1, P["table_z1"] - P["overlay_pilot_depth"],
                            P["table_z1"], x, y))
    # пилотные отверстия саморезов кронштейнов (снизу, Ø4,2)
    for x in (P["br_screw_x1"], P["br_screw_x2"],
              P["br_screw_x3"], P["br_screw_x4"]):
        for y in (P["br_screw_y1"], P["br_screw_y2"]):
            s = s.cut(cyl_z(2.1, P["table_z0"], P["table_z1"], x, y))
    # пилотные отверстия саморезов подкладок пружин (сверху, 7 мм)
    for x in (P["pad_screw_x1"], P["pad_screw_x2"], P["pad_screw_x3"]):
        for y in (P["pad_screw_y1"], P["pad_screw_y2"]):
            s = s.cut(cyl_z(2.1, P["table_z1"] - P["pad_pilot_depth"],
                            P["table_z1"], x, y))
    return s


def top_platform():
    s = box(P["plat_x0"], P["plat_y0"], P["plat_z0"],
            P["plat_x1"], P["plat_y1"], P["plat_z1"])
    s = s.cut(box(P["cut_x0"], P["cut_y0"], P["plat_z0"] - 1,
                  P["cut_x1"], P["cut_y1"], P["plat_z1"] + 1))
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            s = s.cut(cyl_z(P["stud_hole_d"] / 2.0, P["plat_z0"] - 1,
                            P["plat_z1"] + 1, x, y))
    return s


def base_plate():
    s = box(P["base_x0"], P["base_y0"], P["base_z0"],
            P["base_x1"], P["base_y1"], P["base_z1"])
    for x in (P["stud_x1"], P["stud_x2"], P["stud_x3"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            s = s.cut(cyl_z(P["stud_hole_d"] / 2.0, P["base_z0"] - 1,
                            P["base_z1"] + 1, x, y))
            s = s.cut(cyl_z(P["base_cbore_d"] / 2.0, P["base_z0"] - 1,
                            P["base_z0"] + P["base_cbore_h"], x, y))
    return s


def podstol():
    s = box(P["pod_x0"], P["pod_y0"], P["pod_z0"],
            P["pod_x1"], P["pod_y1"], P["pod_z1"])
    for y in (P["stud_y1"], P["stud_y2"]):
        s = s.cut(cyl_z(P["stud_hole_d"] / 2.0, P["pod_z0"] - 1,
                        P["pod_z1"] + 1, P["stud_x3"], y))
    for x in (P["ubolt_x1"], P["ubolt_x2"]):
        for y in (P["ubolt_y1"], P["ubolt_y2"]):
            s = s.cut(cyl_z(P["ubolt_hole_d"] / 2.0, P["pod_z0"] - 1,
                            P["pod_z1"] + 1, x, y))
    # отверстие под болт свободной части подстолья
    s = s.cut(cyl_z(P["stud_hole_d"] / 2.0, P["pod_z0"] - 1,
                    P["pod_z1"] + 1, P["pod_bolt_x"], P["pod_bolt_y"]))
    return s


def spring_pads():
    """Две полосы 200×25×5 от края стола до края накладки; 2 отверстия каждая."""
    out = []
    for y0, y1, yc in ((0.0, P["pad_w"], P["stud_y1"]),
                       (P["Y_max"] - P["pad_w"], P["Y_max"], P["stud_y2"])):
        p = box(0.0, y0, P["pad_z0"], P["pad_len"], y1, P["pad_z1"])
        for x in (P["stud_x1"], P["stud_x2"]):
            p = p.cut(cyl_z(P["pad_hole_d"] / 2.0, P["pad_z0"] - 1,
                            P["pad_z1"] + 1, x, yc))
        ys = P["pad_screw_y1"] if y0 == 0.0 else P["pad_screw_y2"]
        for x in (P["pad_screw_x1"], P["pad_screw_x2"], P["pad_screw_x3"]):
            p = p.cut(cyl_z(P["pad_screw_d"] / 2.0 + 0.1,
                            P["pad_z0"] - 1, P["pad_z1"] + 1, x, ys))
            p = p.cut(Part.makeCone(4.0, 2.0, 2.5,
                                    V(x, ys, P["pad_z1"]), V(0, 0, -1)))
        out.append(p)
    return out


# ----------------------------------------------------------------------------
# балки
# ----------------------------------------------------------------------------
def beams_long():
    out = []
    for yc in (P["lb_y1"], P["lb_y2"]):
        s = tube_x(P["lb_x0"], P["lb_x1"], yc, P["lb_z0"])
        holes = []
        for x in (P["stud_x1"], P["stud_x2"], P["stud_x3"]):
            holes.append(cyl_z(P["stud_hole_d"] / 2.0, P["lb_z0"] - 1,
                               P["lb_z1"] + 1, x, yc))
        if yc == P["lb_y1"]:
            holes.append(cyl_z(P["stud_hole_d"] / 2.0, P["lb_z0"] - 1,
                               P["lb_z1"] + 1, P["pod_bolt_x"], yc))
        s = s.cut(concat(holes))
        out.append(s)
    return out


def beams_trans():
    out = []
    for xc in (P["tb_x1"], P["tb_x2"]):
        s = tube_y(P["tb_y0"], P["tb_y1"], xc, P["tb_z0"])
        holes = []
        for y in (P["stud_y1"], P["stud_y2"]):
            holes.append(cyl_z(P["stud_hole_d"] / 2.0, P["tb_z0"] - 1,
                               P["tb_z1"] + 1, xc, y))
        holes.append(cyl_x(P["shaft_hole_d"] / 2.0, xc - P["tube"] / 2.0 - 1,
                           xc + P["tube"] / 2.0 + 1, P["drive_y"],
                           P["drive_z"]))
        s = s.cut(concat(holes))
        out.append(s)
    return out


def studs():
    out = []
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            out.append(cyl_z(P["stud_d"] / 2.0, 0.0, P["stud_len_vibro"], x, y))
    for y in (P["stud_y1"], P["stud_y2"]):
        out.append(cyl_z(P["stud_d"] / 2.0, 0.0, P["stud_len_rear"],
                         P["stud_x3"], y))
    return out


def washer_z(x, y, z0, od=None, d=None, t=None):
    od = P["washer_od"] if od is None else od
    d = P["washer_id"] if d is None else d
    t = P["washer_t"] if t is None else t
    s = cyl_z(od / 2.0, z0, z0 + t, x, y)
    return s.cut(cyl_z(d / 2.0, z0 - 1, z0 + t + 1, x, y))


def nut_z(x, y, z0, af=None, h=None, d=10.5):
    af = P["nut_af"] if af is None else af
    h = P["nut_h"] if h is None else h
    s = hex_prism_z(af, z0, z0 + h, x, y)
    return s.cut(cyl_z(d / 2.0, z0 - 1, z0 + h + 1, x, y))


def nyloc_z(x, y, z0, h=None):
    h = P["nyloc_h"] if h is None else h
    s = hex_prism_z(P["nut_af"], z0, z0 + h, x, y)
    return s.cut(cyl_z(P["washer_id"] / 2.0, z0 - 1, z0 + h + 1, x, y))


def jam_z(x, y, z0):
    return nut_z(x, y, z0, h=P["jam_h"])


def spring_washers():
    out = []
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            out.append(washer_z(x, y, P["spring_z0"] - P["sw_t"],
                                P["sw_od"], P["sw_id"], P["sw_t"]))
            out.append(washer_z(x, y, P["spring_z1"],
                                P["sw_od"], P["sw_id"], P["sw_t"]))
    return out


def spring(x, y, z0, h, turns=9.0):
    mean_r = (P["spring_od"] - P["spring_wire"]) / 2.0 + 0.1
    helix = Part.makeHelix(h / turns, h, mean_r)
    prof = Part.makeCircle(P["spring_wire"] / 2.0, V(mean_r, 0, 0),
                           V(0, 1, 0))
    sh = helix.makePipe(prof)
    caps = []
    for e in sh.Edges:
        if e.isClosed():
            try:
                caps.append(Part.Face(Part.Wire([e])))
            except Exception:
                pass
    if len(caps) >= 2:
        try:
            shell = Part.Shell(sh.Faces + caps)
            if shell.isClosed():
                sh = Part.Solid(shell)
        except Exception:
            pass
    return sh.translated(V(x, y, z0))


def springs():
    out = []
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            out.append(spring(x, y, P["spring_z0"], P["spring_inst"],
                              P["spring_turns"]))
    return out


def bumpers():
    out = []
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            s = cyl_z(P["bumper_od"] / 2.0, P["bumper_z0"],
                      P["bumper_z1"], x, y)
            s = s.cut(cyl_z(P["bumper_id"] / 2.0, P["bumper_z0"] - 1,
                            P["bumper_z1"] + 1, x, y))
            out.append(s)
    return out


def m10_hardware():
    """Гайки/шайбы шпилек: standard, тонкие контрагайки, nyloc."""
    nuts, jams, nylocs, washers = [], [], [], []

    def n(x, y, z0):
        nuts.append(nut_z(x, y, z0))

    def j(x, y, z0):
        jams.append(jam_z(x, y, z0))

    def nl(x, y, z0, h=None):
        nylocs.append(nyloc_z(x, y, z0, h))

    def w(x, y, z0):
        washers.append(washer_z(x, y, z0))

    # основание: снизу nyloc + контрагайка в цековке, сверху гайка + контрагайка
    for x in (P["stud_x1"], P["stud_x2"], P["stud_x3"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            w(x, y, 0.0)
            nl(x, y, 2.0, P["nyloc_h"])
            j(x, y, 2.0 + P["nyloc_h"])
            w(x, y, P["base_z1"])
            n(x, y, P["base_z1"] + 2.0)
            j(x, y, P["base_z1"] + 2.0 + P["nut_h"])

    # виброотсек
    for x in (P["stud_x1"], P["stud_x2"]):
        for y in (P["stud_y1"], P["stud_y2"]):
            # поперечная балка 130…150: снизу шайба+гайка+jam,
            # сверху гайка; общая тонкая контрагайка с продольной балкой
            w(x, y, P["tb_z0"] - 2.0)
            n(x, y, P["tb_z0"] - 10.0)
            j(x, y, P["tb_z0"] - 18.0)
            n(x, y, P["tb_z1"])
            j(x, y, P["tb_z1"] + P["nut_h"])
            # продольная балка 170…190: снизу гайка (общая контрагайка выше),
            # сверху шайба+гайка+jam
            n(x, y, P["lb_z0"] - P["nut_h"])
            w(x, y, P["lb_z1"])
            n(x, y, P["lb_z1"] + 2.0)
            j(x, y, P["lb_z1"] + 2.0 + P["nut_h"])
            # верхняя платформа: шайба + nyloc (оконцовка шпильки)
            w(x, y, P["plat_z1"])
            nl(x, y, P["plat_z1"] + 2.0, P["nyloc_low_h"])

    # задние шпильки: балка снизу, подстолье сверху (nyloc + jam)
    for y in (P["stud_y1"], P["stud_y2"]):
        n(P["stud_x3"], y, P["lb_z0"] - P["nut_h"])
        j(P["stud_x3"], y, P["lb_z0"] - P["nut_h"] - P["jam_h"])
        w(P["stud_x3"], y, P["pod_z1"])
        nl(P["stud_x3"], y, P["pod_z1"] + 2.0, P["nyloc_h"])

    return nuts, jams, nylocs, washers


def shaft_hardware():
    """Стопки вала: 2 шайбы + гайка + контрагайка с каждой стороны балки."""
    y, z = P["drive_y"], P["drive_z"]
    nuts, jams, washers = [], [], []

    def n(x0):
        nuts.append(hex_prism_x(P["nut_af"], x0, x0 + P["nut_h"], y, z))

    def j(x0):
        jams.append(hex_prism_x(P["nut_af"], x0, x0 + P["nut_h"], y, z))

    def w(x0):
        washers.append(washer_z(x0, y, z, P["washer_od"], P["washer_id"],
                                P["washer_t"]))

    # helper with bores
    def make(seq, x0, h):
        s = hex_prism_x(P["nut_af"], x0, x0 + h, y, z)
        return s.cut(cyl_x(P["washer_id"] / 2.0, x0 - 1, x0 + h + 1, y, z))

    nuts.clear()
    jams.clear()
    for x0 in (8.0, 44.0, 152.0, 189.0):
        nuts.append(make(nuts, x0, P["nut_h"]))
    for x0 in (0.0, 52.0, 144.0, 197.0):
        jams.append(make(jams, x0, P["jam_h"]))
    washers.clear()
    for x0 in (16.0, 18.0, 40.0, 42.0, 161.0, 163.0, 185.0, 187.0):
        s = cyl_x(P["washer_od"] / 2.0, x0, x0 + P["washer_t"], y, z)
        s = s.cut(cyl_x(P["washer_id"] / 2.0, x0 - 1,
                        x0 + P["washer_t"] + 1, y, z))
        washers.append(s)
    return nuts, jams, washers


# ----------------------------------------------------------------------------
# привод, кулачок, ролик
# ----------------------------------------------------------------------------
def drive_shaft():
    return cyl_x(P["shaft_d"] / 2.0, P["shaft_x0"], P["shaft_x1"],
                 P["drive_y"], P["drive_z"])


def weld_nut():
    """Гайка M10, приваренная к новому валу; кулачок садится на её грани."""
    s = hex_prism_x(P["weld_nut_af"], P["weld_nut_x0"], P["weld_nut_x1"],
                    P["drive_y"], P["drive_z"])
    return s.cut(cyl_x(P["shaft_hole_d"] / 2.0, P["weld_nut_x0"] - 1.0,
                       P["weld_nut_x1"] + 1.0,
                       P["drive_y"], P["drive_z"]))


def cam_washers():
    y, z = P["drive_y"], P["drive_z"]
    out = []
    for x0 in (P["cam_x0"] - 2.0, P["cam_x1"]):
        s = cyl_x(P["washer_od"] / 2.0, x0, x0 + P["washer_t"], y, z)
        s = s.cut(cyl_x(P["washer_id"] / 2.0, x0 - 1,
                        x0 + P["washer_t"] + 1, y, z))
        out.append(s)
    return out


def bracket(side):
    t = P["br_t"]
    w = P["br_w"]
    y0 = P["drive_y"] - w / 2.0
    y1 = P["drive_y"] + w / 2.0
    if side < 0:
        vx0, vx1 = P["br_leg_x1"], P["br_leg_x1b"]
        hx0, hx1 = P["br_fl1_x0"], P["br_leg_x1"]
        screws = (P["br_screw_x1"], P["br_screw_x2"])
    else:
        vx0, vx1 = P["br_leg_x2"], P["br_leg_x2b"]
        hx0, hx1 = P["br_leg_x2b"], P["br_fl2_x1"]
        screws = (P["br_screw_x3"], P["br_screw_x4"])
    vert = box(vx0, y0, P["br_z0"], vx1, y1, P["br_z1"])
    hor = box(hx0, y0, P["br_z1"] - t, hx1, y1, P["br_z1"])
    s = vert.fuse(hor)
    # отверстие оси
    s = s.cut(cyl_x(P["br_hole_d"] / 2.0, vx0 - 1, vx1 + 1,
                    P["drive_y"], P["roller_z"]))
    # отверстия саморезов в горизонтальной полке
    for x in screws:
        for y in (P["br_screw_y1"], P["br_screw_y2"]):
            s = s.cut(cyl_z(P["br_screw_d"] / 2.0 + 0.1,
                            P["br_z1"] - t - 1, P["br_z1"] + 1, x, y))
    return s


def roller():
    s = cyl_x(P["roller_od"] / 2.0, P["cam_axis_x"] - P["roller_w"] / 2.0,
              P["cam_axis_x"] + P["roller_w"] / 2.0, P["drive_y"],
              P["roller_z"])
    return s.cut(cyl_x(P["roller_id"] / 2.0 + 0.05,
                       P["cam_axis_x"] - P["roller_w"] / 2.0 - 1,
                       P["cam_axis_x"] + P["roller_w"] / 2.0 + 1,
                       P["drive_y"], P["roller_z"]))


def axle():
    return cyl_x(P["axle_d"] / 2.0, 78.0, 122.0, P["drive_y"],
                 P["roller_z"])


def roller_hardware():
    """Ось, 2 гайки, 6 шайб, 2 тонких кольца."""
    y, z = P["drive_y"], P["roller_z"]
    nuts = []
    for x0 in (78.0, 114.0):
        s = hex_prism_x(P["nut_af"], x0, x0 + P["nyloc_low_h"], y, z)
        s = s.cut(cyl_x(5.25, x0 - 1, x0 + P["nyloc_low_h"] + 1, y, z))
        nuts.append(s)
    washers = []
    for x0 in (86.0, 112.0, 90.0, 92.0, 106.0, 108.0):
        s = cyl_x(P["washer_od"] / 2.0, x0, x0 + P["washer_t"], y, z)
        s = s.cut(cyl_x(P["washer_id"] / 2.0, x0 - 1,
                        x0 + P["washer_t"] + 1, y, z))
        washers.append(s)
    shims = []
    for x0 in (94.0, 104.5):
        s = cyl_x(P["shim_d"] / 2.0, x0, x0 + P["shim_t"], y, z)
        s = s.cut(cyl_x(P["washer_id"] / 2.0, x0 - 1,
                        x0 + P["shim_t"] + 1, y, z))
        shims.append(s)
    return nuts, washers, shims


# ----------------------------------------------------------------------------
# крепёж: винты/саморезы
# ----------------------------------------------------------------------------
def table_screws():
    out = []
    for x in (P["overlay_screw_x"], P["overlay_screw_x2"]):
        for y in (P["overlay_screw_y1"], P["overlay_screw_y2"]):
            zt = P["overlay_z1"]
            head = Part.makeCone(4.0, 2.0, 2.5, V(x, y, zt), V(0, 0, -1))
            shank = cyl_z(2.0, zt - P["overlay_screw_len"], zt - 2.5, x, y)
            out.append(head.fuse(shank))
    return out


def pad_screws():
    """6 саморезов M4×12: 2 полосы пружин к столу."""
    out = []
    for x in (P["pad_screw_x1"], P["pad_screw_x2"], P["pad_screw_x3"]):
        for y in (P["pad_screw_y1"], P["pad_screw_y2"]):
            zt = P["pad_z1"]
            head = Part.makeCone(4.0, 2.0, 2.5, V(x, y, zt), V(0, 0, -1))
            shank = cyl_z(2.0, zt - P["pad_screw_len"], zt - 2.5, x, y)
            out.append(head.fuse(shank))
    return out


def bracket_screws():
    out = []
    for x in (P["br_screw_x1"], P["br_screw_x2"],
              P["br_screw_x3"], P["br_screw_x4"]):
        for y in (P["br_screw_y1"], P["br_screw_y2"]):
            zt = P["br_z1"] - P["br_t"]
            head = cyl_z(3.5, zt - 3.0, zt, x, y)
            shank = cyl_z(2.0, zt, P["table_z1"], x, y)
            out.append(head.fuse(shank))
    return out


# ----------------------------------------------------------------------------
# U-болты и дрель
# ----------------------------------------------------------------------------
def pod_bolt():
    """Болт M10×50 свободной части подстолья: головка сверху, гайка снизу."""
    y = P["pod_bolt_y"]
    head = hex_prism_z(P["pod_bolt_head_af"], P["pod_z1"],
                       P["pod_z1"] + P["pod_bolt_head_h"],
                       P["pod_bolt_x"], y)
    shank = cyl_z(P["pod_bolt_d"] / 2.0,
                  P["pod_z1"] - P["pod_bolt_len"], P["pod_z1"],
                  P["pod_bolt_x"], y)
    return head.fuse(shank)


def pod_bolt_nut():
    return nyloc_z(P["pod_bolt_x"], P["pod_bolt_y"],
                   P["lb_z0"] - P["pod_bolt_nut_h"] - P["pod_bolt_washer_t"],
                   P["pod_bolt_nut_h"])


def pod_bolt_washer():
    return washer_z(P["pod_bolt_x"], P["pod_bolt_y"],
                    P["lb_z0"] - P["pod_bolt_washer_t"], t=P["pod_bolt_washer_t"])


def ubolts():
    out = []
    for x in (P["ubolt_x1"], P["ubolt_x2"]):
        torus = Part.makeTorus(P["ubolt_r"], P["ubolt_d"] / 2.0,
                               V(x, P["drive_y"], P["drive_z"]),
                               V(1, 0, 0))
        torus = torus.cut(box(x - 20, 0, P["drive_z"] + 0.001,
                              x + 20, 200, 220))
        legs = []
        for y in (P["ubolt_y1"], P["ubolt_y2"]):
            legs.append(cyl_z(P["ubolt_d"] / 2.0, P["drive_z"],
                              P["pod_z1"], x, y))
        out.append(torus.fuse(concat(legs)))
    return out


def ubolt_hw():
    out = []
    for x in (P["ubolt_x1"], P["ubolt_x2"]):
        for y in (P["ubolt_y1"], P["ubolt_y2"]):
            w = washer_z(x, y, P["pod_z1"], od=12, d=6.5, t=1.5)
            n = nut_z(x, y, P["pod_z1"] + 1.5, af=10, h=5.0, d=6.2)
            out.extend([w, n])
    return out


def drill():
    y, z = P["drive_y"], P["drive_z"]
    body = cyl_x(P["drill_d"] / 2.0, P["drill_x0"], P["drill_x1"], y, z)
    chuck = cyl_x(P["chuck_d"] / 2.0, P["chuck_x0"], P["chuck_x1"], y, z)
    chuck = chuck.cut(cyl_x(P["shaft_hole_d"] / 2.0, P["chuck_x0"] - 1,
                            P["chuck_x1"] + 1, y, z))
    handle = box(P["handle_x0"], 75.0, 90.0, P["handle_x1"], 125.0, 190.0)
    return body.fuse(chuck).fuse(handle)


def drill_pads():
    """Полукольца между древью Ø100 и внутренней поверхностью U-болта."""
    out = []
    y, z = P["drive_y"], P["drive_z"]
    for xc in (P["ubolt_x1"], P["ubolt_x2"]):
        s = cyl_x(P["pad_drill_od"] / 2.0, xc - P["pad_drill_x"] / 2.0,
                  xc + P["pad_drill_x"] / 2.0, y, z)
        s = s.cut(cyl_x(P["pad_drill_id"] / 2.0,
                        xc - P["pad_drill_x"] / 2.0 - 1,
                        xc + P["pad_drill_x"] / 2.0 + 1, y, z))
        s = s.cut(box(xc - 20, 0, P["pad_drill_z1"] + 0.001,
                      xc + 20, 200, 220))
        out.append(s)
    return out


# ----------------------------------------------------------------------------
# сборка
# ----------------------------------------------------------------------------
def build_assembly():
    parts = {}
    cams = {"cam_3": cam_shape(3), "cam_5": cam_shape(5),
            "cam_10": cam_shape(10)}

    def add(name, shape, material, qty, group, spec_no, mass=True):
        parts[name] = dict(shape=shape, material=material, qty=qty,
                           group=group, spec_no=spec_no, mass=mass)

    add("studs", concat(studs()), "steel", 6, "steel", "1/2")
    add("beams_long", concat(beams_long()), "steel", 2, "steel", "12")
    add("beams_trans", concat(beams_trans()), "steel", 2, "steel", "13")
    add("table", table(), "plywood", 1, "wood", "6")
    add("overlay", overlay(), "pla", 1, "overlay", "7")
    add("top_platform", top_platform(), "plywood", 1, "wood", "9")
    add("base", base_plate(), "plywood", 1, "wood", "10")
    add("podstol", podstol(), "plywood", 1, "wood", "11")
    add("spring_pads", concat(spring_pads()), "plywood", 2, "wood", "8")
    add("springs", concat(springs()), "steel", 4, "spring", "15")
    add("spring_washers", concat(spring_washers()), "steel", 8, "steel", "5")
    add("bumpers", concat(bumpers()), "rubber", 4, "rubber", "16")

    nuts, jams, nylocs, washers = m10_hardware()
    add("nuts", concat(nuts), "steel", len(nuts), "steel", "3")
    add("jam_nuts", concat(jams), "steel", len(jams), "steel", "36")
    add("nyloc_nuts", concat(nylocs), "steel", len(nylocs), "steel", "35")
    add("washers", concat(washers), "steel", len(washers), "steel", "4")
    shn, shj, shw = shaft_hardware()
    add("shaft_nuts", concat(shn), "steel", len(shn), "steel", "3")
    add("shaft_jams", concat(shj), "steel", len(shj), "steel", "37")
    add("shaft_washers", concat(shw), "steel", len(shw), "steel", "4")

    add("drive_shaft", drive_shaft(), "steel", 1, "steel", "17")
    add("weld_nut", weld_nut(), "steel", 1, "steel", "18")
    add("cam", cams["cam_5"], "pla", 1, "cam", "19")
    add("cam_washers", concat(cam_washers()), "steel", 2, "steel", "20")
    cn = []
    for x0 in (74.0, 108.0):
        s = hex_prism_x(P["nut_af"], x0, x0 + P["nut_h"],
                        P["drive_y"], P["drive_z"])
        s = s.cut(cyl_x(5.25, x0 - 1, x0 + P["nut_h"] + 1,
                        P["drive_y"], P["drive_z"]))
        cn.append(s)
    add("cam_nuts", concat(cn), "steel", 2, "steel", "21")
    add("axle", axle(), "steel", 1, "steel", "22")
    add("roller", roller(), "bearing", 1, "bearing", "23")
    rn, rw, rs = roller_hardware()
    add("roller_nuts", concat(rn), "steel", 2, "steel", "24")
    add("roller_washers", concat(rw), "steel", 6, "steel", "25")
    add("roller_shims", concat(rs), "steel", 2, "steel", "26")
    add("brackets", concat([bracket(-1), bracket(1)]), "steel", 2,
        "steel", "27")
    add("bracket_screws", concat(bracket_screws()), "steel", 8, "steel", "28")
    add("table_screws", concat(table_screws()), "steel", 4, "steel", "29")
    add("pad_screws", concat(pad_screws()), "steel", 6, "steel", "29")
    add("pod_bolt", pod_bolt(), "steel", 1, "steel", "38")
    add("pod_bolt_nut", pod_bolt_nut(), "steel", 1, "steel", "38")
    add("pod_bolt_washer", pod_bolt_washer(), "steel", 1, "steel", "38")
    add("ubolts", concat(ubolts()), "steel", 2, "steel", "30")
    add("ubolt_hw", concat(ubolt_hw()), "steel", 8, "steel", "31")
    add("drill_pads", concat(drill_pads()), "rubber", 2, "rubber", "32")
    add("drill", drill(), "drill", 1, "drill", "33", mass=False)

    groups = {}
    for key, info in parts.items():
        groups.setdefault(info["group"], []).append(info["shape"])
    return parts, groups, cams


def mass_report(parts):
    rows = []
    total = 0.0
    for name, info in parts.items():
        if not info.get("mass", True):
            continue
        vol = info["shape"].Volume
        m = vol * DENSITY[info["material"]]
        total += m
        rows.append((name, info["spec_no"], info["material"], vol,
                     info["qty"], m))
    return rows, total
