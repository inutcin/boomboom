"""Параметрическая модель вибростола, этап fix11 (FreeCAD Part).

Ключевые решения fix11 (по README этапа):
  * база fix9: сварная рама 20x20x2, стальная балка 21, седла 6200;
  * балка 21 удерживается 4 шпильками M10 (2 на балку), гайки/шайбы
    образуют стек 90 мм (верх) / 70 мм (низ);
  * накладки-уголки 50x50, ширина 25, 2 мм; к балке M4x35, к стойкам
    не крепятся — только упираются (направляющая);
  * шпильки поджима — строительные 4.6; вал привода и ось ролика — 8.8;
  * шпилек вала привода с приваренной гайкой — 3 комплекта;
  * направляющие валы — Ø10 h6, L=176, резьба M10×15 на концах;
    крепление гайками M10 с шайбами Ø18, кольца WCS10FR удалены.
"""

import math
import FreeCAD as App
import Part

from params import P

V = App.Vector

DENSITY = {
    "steel": 7.85e-3,      # г/мм3
    "petg": 1.27e-3,
    "pla": 1.24e-3,
    "pc": 1.20e-3,         # поликарбонат
    "rubber": 1.15e-3,     # EPDM/NBR
    "bearing": 7.85e-3,    # оценка по стали
    "plastic": 1.00e-3,    # заглушки
}

FRAME_TUBES = []           # заполняется frame(); для STEP/разреза
BEAM_TUBES = []            # заполняется retainer_beam()


# ----------------------------------------------------------------------------
# примитивы
# ----------------------------------------------------------------------------
def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(
        abs(x1 - x0), abs(y1 - y0), abs(z1 - z0),
        V(min(x0, x1), min(y0, y1), min(z0, z1)),
    )


def cyl_x(r, x0, x1, y, z):
    return Part.makeCylinder(r, abs(x1 - x0), V(min(x0, x1), y, z), V(1, 0, 0))


def cyl_y(r, y0, y1, x, z):
    return Part.makeCylinder(r, abs(y1 - y0), V(x, min(y0, y1), z), V(0, 1, 0))


def cyl_z(r, z0, z1, x, y):
    return Part.makeCylinder(r, abs(z1 - z0), V(x, y, min(z0, z1)), V(0, 0, 1))


def cyl_axis(r, x, y, z, dx, dy, dz, length):
    return Part.makeCylinder(r, length, V(x, y, z), V(dx, dy, dz))


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
    if not shapes:
        return None
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()


# ----------------------------------------------------------------------------
# трубы и рама (fix9)
# ----------------------------------------------------------------------------
def tube_pair(axis, a0, a1, c1, c2, size=20.0, wall=2.0):
    """Возвращает (outer, inner) квадратной трубы.

    axis='x': a — координата X, c1/c2 — Y/Z низа сечения;
    axis='y': a — координата Y, c1/c2 — X/Z низа сечения;
    axis='z': a — координата Z, c1/c2 — X/Y низа сечения.
    """
    if axis == "x":
        outer = box(a0, c1, c2, a1, c1 + size, c2 + size)
        inner = box(a0, c1 + wall, c2 + wall, a1, c1 + size - wall,
                    c2 + size - wall)
    elif axis == "y":
        outer = box(c1, a0, c2, c1 + size, a1, c2 + size)
        inner = box(c1 + wall, a0, c2 + wall, c1 + size - wall, a1,
                    c2 + size - wall)
    else:
        outer = box(c1, c2, a0, c1 + size, c2 + size, a1)
        inner = box(c1 + wall, c2 + wall, a0, c1 + size - wall,
                    c2 + size - wall, a1)
    return outer, inner


def frame_layout():
    """18 отрезков рамы: (имя, axis, a0, a1, c1, c2, описание)."""
    out = []
    # высокие стойки 4 шт. (Z=20…280)
    for x in (0.0, 140.0):
        for y in (0.0, 180.0):
            out.append(("T%02d" % (len(out) + 1), "z", 20.0, 280.0, x, y,
                        "стойка высокая X=%.0f Y=%.0f" % (x, y)))
    # задние короткие стойки 2 шт. (Z=20…170)
    for y in (0.0, 180.0):
        out.append(("T%02d" % (len(out) + 1), "z", 20.0, 170.0, 340.0, y,
                    "стойка задняя Y=%.0f" % y))
    # нижние продольные 2 шт.
    for y in (0.0, 180.0):
        out.append(("T%02d" % (len(out) + 1), "x", 0.0, 360.0, y, 0.0,
                    "нижняя продольная Y=%.0f" % y))
    # верхние балки виброотсека 2 шт.
    for y in (0.0, 180.0):
        out.append(("T%02d" % (len(out) + 1), "x", 0.0, 160.0, y, 280.0,
                    "верхняя виброотсека Y=%.0f" % y))
    # верхние балки выноса 2 шт.
    for y in (0.0, 180.0):
        out.append(("T%02d" % (len(out) + 1), "x", 160.0, 360.0, y, 170.0,
                    "верхняя выноса Y=%.0f" % y))
    # нижние поперечины 2 шт.
    for x in (0.0, 140.0):
        out.append(("T%02d" % (len(out) + 1), "y", 20.0, 180.0, x, 0.0,
                    "нижняя поперечина X=%.0f" % x))
    # верхние поперечины 2 шт.
    for x in (0.0, 140.0):
        out.append(("T%02d" % (len(out) + 1), "y", 20.0, 180.0, x, 280.0,
                    "верхняя поперечина X=%.0f" % x))
    # средние поперечины 2 шт. (сёдла 6200)
    for x in (0.0, 140.0):
        out.append(("T%02d" % (len(out) + 1), "y", 20.0, 180.0, x, 150.0,
                    "средняя поперечина X=%.0f" % x))
    return out


def frame_holes():
    holes = []
    # отверстия направляющих валов (верхние и средние поперечины)
    for gx in (P["guide_x1"], P["guide_x2"]):
        for gy in (P["guide_y1"], P["guide_y2"]):
            holes.append(cyl_z(P["guide_hole_d"] / 2.0, 279.0, 301.0, gx, gy))
            holes.append(cyl_z(P["guide_hole_d"] / 2.0, 149.0, 171.0, gx, gy))
    # прорези-сёдла 6200 в нижней стенке средних поперечин
    for bx in (P["bearing_x1"], P["bearing_x2"]):
        holes.append(cyl_x(P["saddle_r"], bx - P["saddle_w"] / 2.0,
                           bx + P["saddle_w"] / 2.0, P["drive_y"], P["drive_z"]))
    # Ø10 под шпильки поджима — только в верхней стенке нижних поперечин
    for x in (0.0, 140.0):
        for y in (P["clamp_stud_y1"], P["clamp_stud_y2"]):
            holes.append(cyl_z(P["clamp_lower_hole_d"] / 2.0, 17.0, 21.0,
                               x + P["clamp_stud_x_off"], y))
    # отверстия M6 под подстолье в верхних балках выноса
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            holes.append(cyl_z(P["podstol_hole_d"] / 2.0, 169.0, 191.0, x, y))
    # резьба M4 под винты кожуха (в стенке 2 мм)
    for (hx, hy, hz, dx, dy, dz, t) in shield_screw_layout():
        fx, fy, fz = hx + dx * t, hy + dy * t, hz + dz * t
        # в модели отверстие под винт (резьба M4 не моделируется)
        holes.append(cyl_axis(P["shield_hole_d"] / 2.0,
                              fx - dx * 0.5, fy - dy * 0.5, fz - dz * 0.5,
                              dx, dy, dz, P["shield_tap_depth"]))
    return holes


def frame_weld_parts():
    """Приварные гайки M6 подстолья и распорные втулки в стойках."""
    out = []
    # 4 гайки M6 снизу верхних балок выноса
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            n = hex_prism_z(P["podstol_weldnut_af"], 165.0, 170.0, x, y)
            n = n.cut(cyl_z(P["podstol_hole_d"] / 2.0 + 0.1, 164.0, 171.0, x, y))
            out.append(n)
    return out


def frame():
    """Сварная рама: 18 труб + приварные гайки/втулки; прорези и holes."""
    global FRAME_TUBES
    outers, inners = [], []
    FRAME_TUBES = []
    for (name, axis, a0, a1, c1, c2, note) in frame_layout():
        outer, inner = tube_pair(axis, a0, a1, c1, c2,
                                 P["tube"], P["frame_wall"])
        outers.append(outer)
        inners.append(inner)
        FRAME_TUBES.append(dict(
            name=name, axis=axis, a0=a0, a1=a1, c1=c1, c2=c2,
            length=abs(a1 - a0), note=note,
            shape=outer.cut(inner)))
    s = concat(outers).cut(concat(inners))
    s = s.cut(concat(frame_holes()))
    s = s.fuse(concat(frame_weld_parts()))
    return s.removeSplitter()


def frame_plugs():
    """10 пластиковых заглушек 20x20 в открытые торцы рамы."""
    out = []
    specs = [
        # (x_end, dir, y, z, cap)
        (0.0, -1, 0.0, 0.0, True), (360.0, +1, 0.0, 0.0, True),
        (0.0, -1, 180.0, 0.0, True), (360.0, +1, 180.0, 0.0, True),
        # верхние торцы виброотсека под кожухом — только вставка внутри
        (0.0, -1, 0.0, 280.0, False), (160.0, +1, 0.0, 280.0, False),
        (0.0, -1, 180.0, 280.0, False), (160.0, +1, 180.0, 280.0, False),
        (360.0, +1, 0.0, 170.0, True), (360.0, +1, 180.0, 170.0, True),
    ]
    for x_end, dr, y, z, cap_on in specs:
        if dr > 0:
            if cap_on:
                out.append(box(x_end, y, z, x_end + 2.0, y + 20.0, z + 20.0))
            out.append(box(x_end - 4.0, y + 2.0, z + 2.0, x_end,
                           y + 18.0, z + 18.0))
        else:
            if cap_on:
                out.append(box(x_end - 2.0, y, z, x_end, y + 20.0, z + 20.0))
            out.append(box(x_end, y + 2.0, z + 2.0, x_end + 4.0,
                           y + 18.0, z + 18.0))
    return concat(out)


# ----------------------------------------------------------------------------
# кожух: точки саморезов/винтов
# ----------------------------------------------------------------------------
def shield_screw_layout():
    t = P["shield_t"]
    out = []
    for yface, sy in ((-t, +1.0), (P["W_frame"] + t, -1.0)):
        for x in (10.0, 80.0, 150.0):
            out.append((x, yface, 15.0, 0.0, sy, 0.0, t))
            out.append((x, yface, 285.0, 0.0, sy, 0.0, t))
        for z in (80.0, 200.0):
            out.append((10.0, yface, z, 0.0, sy, 0.0, t))
    for y in (40.0, 100.0, 160.0):
        out.append((-t, y, 285.0, +1.0, 0.0, 0.0, t))
        out.append((P["L_vibro"] + t, y, 285.0, -1.0, 0.0, 0.0, t))
    return out


def _points_for(sel):
    return [p for p in shield_screw_layout() if sel(p)]


# ----------------------------------------------------------------------------
# стол, накладка
# ----------------------------------------------------------------------------
def table():
    s = box(P["table_x0"], P["table_y0"], P["table_z0"],
            P["table_x1"], P["table_y1"], P["table_z1"])
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(P["table_hole_d"] / 2.0, P["table_z0"] - 1,
                            P["table_z1"] + 1, x, y))
            # 4 крепления LMK: отверстие 5 + шестигранное углубление 7,2x5
            for dx in (-16.0, 16.0):
                for dy in (-16.0, 16.0):
                    xx, yy = x + dx, y + dy
                    s = s.cut(cyl_z(P["table_lmk_hole_d"] / 2.0,
                                    P["table_z0"] - 1, P["table_z1"] + 1,
                                    xx, yy))
                    s = s.cut(hex_prism_z(P["lmk_nut_recess_af"],
                                          P["table_z1"] - P["lmk_nut_recess_h"],
                                          P["table_z1"], xx, yy))
    # кронштейны ролика: отверстие 5 + углубление 8x5 сверху
    for x in (P["bracket_slot_x1"], P["bracket_slot_x2"]):
        s = s.cut(cyl_z(P["bracket_table_hole_d"] / 2.0,
                        P["table_z0"] - 1, P["table_z1"] + 1, x, 100.0))
        s = s.cut(cyl_z(P["bracket_recess_d"] / 2.0,
                        P["table_z1"] - P["bracket_recess_h"],
                        P["table_z1"] + 1, x, 100.0))
    # 4 угловых отверстия накладки
    for x in (P["table_x0"] + P["overlay_inset"],
              P["table_x1"] - P["overlay_inset"]):
        for y in (P["table_y0"] + P["overlay_inset"],
                  P["table_y1"] - P["overlay_inset"]):
            s = s.cut(cyl_z(2.1, P["table_z0"] - 1, P["table_z1"] + 1, x, y))
    return s


def overlay():
    s = box(P["table_x0"], P["table_y0"], P["overlay_z0"],
            P["table_x1"], P["table_y1"], P["overlay_z1"])
    R = 1225.0
    cx = (P["table_x0"] + P["table_x1"]) / 2.0
    cz = P["overlay_z1"] - P["dish_depth"] + R
    s = s.cut(Part.makeSphere(R, V(cx, 100, cz)))
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(P["overlay_hole_d"] / 2.0, P["overlay_z0"] - 1,
                            P["overlay_z1"] + 1, x, y))
    for x in (P["table_x0"] + P["overlay_inset"],
              P["table_x1"] - P["overlay_inset"]):
        for y in (P["table_y0"] + P["overlay_inset"],
                  P["table_y1"] - P["overlay_inset"]):
            s = s.cut(cyl_z(2.1, P["overlay_z0"] - 1, P["overlay_z1"] + 1, x, y))
            s = s.cut(Part.makeCone(4.0, 2.0, 2.5, V(x, y, P["overlay_z1"]),
                                    V(0, 0, -1)))
    return s


# ----------------------------------------------------------------------------
# LMK10UU и 6200
# ----------------------------------------------------------------------------
def lmk10uu(x, y):
    z0, z1 = P["lmk_z0"], P["lmk_z1"]
    zf = z1 - P["lmk_flange_t"]
    body = cyl_z(P["lmk_body_d"] / 2.0, z0, zf, x, y)
    f = P["lmk_flange"] / 2.0
    flange = box(x - f, y - f, zf, x + f, y + f, z1)
    s = body.fuse(flange)
    s = s.cut(cyl_z(5.05, z0 - 1, z1 + 1, x, y))
    for dx in (-P["lmk_hole_pitch"] / 2.0, P["lmk_hole_pitch"] / 2.0):
        for dy in (-P["lmk_hole_pitch"] / 2.0, P["lmk_hole_pitch"] / 2.0):
            xx, yy = x + dx, y + dy
            s = s.cut(cyl_z(P["lmk_hole_d"] / 2.0, zf - 1, z1 + 1, xx, yy))
            # fix9: цековка снизу фланца под головку M4 Ø7x4
            s = s.cut(cyl_z(P["lmk_cbore_d"] / 2.0, zf - 1,
                            zf + P["lmk_cbore_h"], xx, yy))
    return s


def bearing_6200(x0, x1, y, z):
    s = cyl_x(P["b6200_od"] / 2.0, x0, x1, y, z)
    s = s.cut(cyl_x(P["b6200_id"] / 2.0 + 0.05, x0 - 1, x1 + 1, y, z))
    return s


# ----------------------------------------------------------------------------
# валы, гайки/шайбы валов, пружины, шайбы
# ----------------------------------------------------------------------------
def shaft(x, y):
    return cyl_z(P["shaft_d"] / 2.0, P["shaft_z0"], P["shaft_z1"], x, y)


def shaft_nut(x, y, z0):
    return hex_nut_z(x, y, z0, af=P["shaft_nut_af"], h=P["shaft_nut_h"],
                     d=P["shaft_nut_id"])


def shaft_washer(x, y, z0):
    return washer_z(x, y, z0, od=P["shaft_washer_od"],
                    d=P["shaft_washer_id"], t=P["shaft_washer_t"])


def spring(x, y):
    z0 = P["overlay_z1"] + P["spring_washer_t"]
    h = P["spring_inst"]
    turns = int(P["spring_turns"])
    mean_r = (P["spring_od"] - P["spring_wire"]) / 2.0 + 0.1
    helix = Part.makeHelix(h / turns, h, mean_r)
    prof = Part.makeCircle(P["spring_wire"] / 2.0, V(mean_r, 0, 0), V(0, 1, 0))
    spring_shell = helix.makePipe(prof)
    caps = []
    for e in spring_shell.Edges:
        if e.isClosed():
            try:
                caps.append(Part.Face(Part.Wire([e])))
            except Exception:
                pass
    if len(caps) >= 2:
        try:
            sh = Part.Shell(spring_shell.Faces + caps)
            if sh.isClosed():
                spring_shell = Part.Solid(sh)
        except Exception:
            pass
    return spring_shell.translated(V(x, y, z0))


def washer_z(x, y, z0, od=None, d=None, t=None):
    od = P["spring_washer_od"] if od is None else od
    d = P["spring_washer_id"] if d is None else d
    t = P["spring_washer_t"] if t is None else t
    s = cyl_z(od / 2.0, z0, z0 + t, x, y)
    s = s.cut(cyl_z(d / 2.0, z0 - 1, z0 + t + 1, x, y))
    return s


# ----------------------------------------------------------------------------
# привод: вал, гайки, кулачок, ролик
# ----------------------------------------------------------------------------
def cam_radius(theta, stroke):
    rmax = P["cam_rmax"]
    e = stroke / 2.0
    return rmax - e - e * math.cos(2.0 * theta)


def cam_wire(x, stroke, off=0.0, n=240):
    cy, cz = P["drive_y"], P["drive_z"]
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        r = cam_radius(a, stroke) + off
        pts.append(V(x, cy + r * math.cos(a), cz + r * math.sin(a)))
    return Part.makePolygon(pts + [pts[0]])


def cam(stroke):
    cy, cz = P["drive_y"], P["drive_z"]
    gx0, gx1 = P["cam_x0"], P["cam_x1"]
    gw = P["cam_groove_w"]
    ft = (gx1 - gx0 - gw) / 2.0
    core = Part.Face(cam_wire(gx0 + ft, stroke)).extrude(V(gw, 0, 0))
    left = Part.makeLoft([cam_wire(gx0, stroke, 2.0),
                          cam_wire(gx0 + ft, stroke, 0.0)], True, True)
    right = Part.makeLoft([cam_wire(gx1 - ft, stroke, 0.0),
                           cam_wire(gx1, stroke, 2.0)], True, True)
    s = core.fuse(left).fuse(right)
    boss = cyl_x(P["cam_boss_d"] / 2.0, P["cam_boss_x0"],
                 P["cam_boss_x1"], cy, cz)
    s = s.fuse(boss)
    s = s.cut(hex_prism_x(P["cam_hex_af"], P["cam_boss_x0"] - 1,
                          gx1 + 1, cy, cz))
    hr = P["cam_hole_d"] / 2.0
    rr = P["cam_hole_r"]
    for i in range(8):
        a = math.radians(45.0 * i)
        s = s.cut(cyl_x(hr, gx0 - 1, gx1 + 1,
                        cy + rr * math.cos(a), cz + rr * math.sin(a)))
    return s.removeSplitter()


def cam_washer(x0, x1):
    s = cyl_x(P["cam_washer_od"] / 2.0, x0, x1, P["drive_y"], P["drive_z"])
    return s.cut(cyl_x(P["cam_washer_id"] / 2.0, x0 - 1, x1 + 1,
                       P["drive_y"], P["drive_z"]))


def conical_nut(x0, x1, small_at_right=True, z=None):
    z = P["drive_z"] if z is None else z
    r_big = P["shaft_cone_big_d"] / 2.0
    r_small = P["shaft_cone_small_d"] / 2.0
    if small_at_right:
        cone = Part.makeCone(r_big, r_small, abs(x1 - x0), V(x0, 100, z),
                             V(1, 0, 0))
    else:
        cone = Part.makeCone(r_small, r_big, abs(x1 - x0), V(x0, 100, z),
                             V(1, 0, 0))
    return cone.cut(cyl_x(5.1, min(x0, x1) - 1, max(x0, x1) + 1, 100, z))


def locknut(x0, x1, z=None):
    z = P["drive_z"] if z is None else z
    s = hex_prism_x(17.0, x0, x1, 100, z)
    return s.cut(cyl_x(5.1, min(x0, x1) - 1, max(x0, x1) + 1, 100, z))


def bearing_clamp(bx):
    half = P["b6200_w"] / 2.0
    cl = P["shaft_fix_nut_len"]
    w = P["shaft_lock_w"]
    return {
        "cone_l": (bx - half - cl, bx - half),
        "lock_l": (bx - half - cl - w, bx - half - cl),
        "cone_r": (bx + half, bx + half + cl),
        "lock_r": (bx + half + cl, bx + half + cl + w),
    }


def shaft_clamps():
    return {"b1": bearing_clamp(P["bearing_x1"]),
            "b2": bearing_clamp(P["bearing_x2"])}


def drive_shaft():
    s = cyl_x(P["shaft_d"] / 2.0, P["shaft_x0"], P["shaft_x1"],
              100, P["drive_z"])
    nut = hex_prism_x(P["weld_nut_af"], P["weld_nut_x0"],
                      P["weld_nut_x1"], 100, P["drive_z"])
    return s.fuse(nut).removeSplitter()


def bracket(side):
    t = P["bracket_t"]
    w = P["bracket_w"]
    z_bottom = 185.0
    z_top = P["table_z0"]
    if side < 0:
        vx0 = P["bracket_plate_x1"]
        vx1 = vx0 + t
        hx0, hx1 = P["bracket_leg_x1"], P["bracket_plate_x1"]
        xm = P["bracket_slot_x1"]
    else:
        vx1 = P["bracket_plate_x2"]
        vx0 = vx1 - t
        hx0, hx1 = P["bracket_plate_x2"], P["bracket_leg_x2"]
        xm = P["bracket_slot_x2"]
    vert = box(vx0, 90, z_bottom, vx1, 90 + w, z_top)
    hor = box(hx0, 90, z_top - t, hx1, 90 + w, z_top)
    s = vert.fuse(hor)
    s = s.cut(cyl_x(5.05, vx0 - 1, vx1 + 1, 100, P["roller_z"]))
    s = s.cut(box(xm - 5, 97.5, z_top - t - 1, xm + 5, 102.5, z_top + 1))
    return s


def roller():
    cx = P["cam_axis_x"]
    b = bearing_6200(cx - 4.5, cx + 4.5, 100, P["roller_z"])
    axle = cyl_x(P["axle_d"] / 2.0, cx - P["axle_len"] / 2.0,
                 cx + P["axle_len"] / 2.0, 100, P["roller_z"])
    parts = [b, axle]
    parts.append(conical_nut(cx - 10.0, cx - 4.5, True, z=P["roller_z"]))
    parts.append(conical_nut(cx + 4.5, cx + 10.0, False, z=P["roller_z"]))
    parts.append(locknut(cx - 20.0, cx - 12.0, z=P["roller_z"]))
    parts.append(locknut(cx + 12.0, cx + 20.0, z=P["roller_z"]))
    return parts


# ----------------------------------------------------------------------------
# балка 21 и плоские уголки (fix9)
# ----------------------------------------------------------------------------
def retainer_beam(x0):
    """Стальная труба 20x20x2, L=159,6; прорезь-седло 6200 в верхней стенке."""
    global BEAM_TUBES
    x1 = x0 + P["tube"]
    y0, y1 = P["ret_y0"], P["ret_y1"]
    z0, z1 = P["ret_z0"], P["ret_z1"]
    outer = box(x0, y0, z0, x1, y1, z1)
    inner = box(x0 + P["beam_wall"], y0, z0 + P["beam_wall"],
                x1 - P["beam_wall"], y1, z1 - P["beam_wall"])
    s = outer.cut(inner)
    # прорезь-седло в верхней стенке
    bx = x0 + 10.0
    s = s.cut(cyl_x(P["saddle_r"], bx - P["saddle_w"] / 2.0,
                    bx + P["saddle_w"] / 2.0, P["drive_y"], P["drive_z"]))
    # 2 сквозных Ø10 под шпильки поджима (верхняя и нижняя грани)
    for y in (P["clamp_stud_y1"], P["clamp_stud_y2"]):
        s = s.cut(cyl_z(P["clamp_beam_hole_d"] / 2.0, z0 - 1.0, z1 + 1.0,
                        x0 + P["clamp_stud_x_off"], y))
    # 4 отверстия Ø4,5 под винты накладок (вдоль X)
    for y in (P["pad_bolt_y1"], P["pad_bolt_y2"],
              P["W_frame"] - P["pad_bolt_y1"],
              P["W_frame"] - P["pad_bolt_y2"]):
        s = s.cut(cyl_x(P["pad_bolt_hole_d"] / 2.0, x0 - 1, x1 + 1,
                        y, P["pad_hor_z0"] + 10.0))
    BEAM_TUBES.append(dict(name="B%02d" % (len(BEAM_TUBES) + 1),
                           x0=x0, x1=x1, length=P["ret_len"],
                           shape=s, note="балка 21"))
    return s


def beam_spacers(x0):
    """8 распорных втулок 16x16x2 L=16 в балке 21 (по 4 на балку)."""
    out = []
    for y in (P["pad_bolt_y1"], P["pad_bolt_y2"],
              P["W_frame"] - P["pad_bolt_y1"],
              P["W_frame"] - P["pad_bolt_y2"]):
        xs, xe = x0 + 2.0, x0 + 18.0
        z = P["pad_hor_z0"] + 10.0
        outer = box(xs, y - 8.0, z - 8.0, xe, y + 8.0, z + 8.0)
        inner = box(xs, y - 6.0, z - 6.0, xe, y + 6.0, z + 6.0)
        sp = outer.cut(inner)
        sp = sp.cut(cyl_x(P["pad_bolt_hole_d"] / 2.0, xs - 1.0,
                          xe + 1.0, y, z))
        out.append(sp)
    return out


def beam_plugs(x0):
    """2 заглушки 16x16x5 в торцы балки 21."""
    out = []
    for y0 in (P["ret_y0"], P["ret_y1"] - 5.0):
        out.append(box(x0 + 2.0, y0, P["ret_z0"] + 2.0,
                       x0 + 18.0, y0 + 5.0, P["ret_z1"] - 2.0))
    return out


def angle_bracket(side, rear_beam, xb_face):
    """Плоская накладка-уголок 50x50, ширина 25, t=2 (fix11).

    Вертикальный лепесток 25x50 (Z=80…130), горизонтальный 50x25
    (Z=110…135). Лепесток 50 перекрывает стойку на 20 мм и упирается в
    неё; крепления к стойке нет. К балке — 2 винта M4x35 через пару
    накладок и втулку 16x16x2 L=16.
    """
    t = P["pad_t"]
    w = P["pad_w"]
    arm = P["pad_arm"]
    xa = 0.0 if not rear_beam else P["L_vibro"] - P["tube"]
    xb = xa + P["tube"]
    if not xb_face:
        lx0, lx1 = xa - t, xa
    else:
        lx0, lx1 = xb, xb + t
    if side < 0:
        vert_y0, vert_y1 = 0.0, w
        hor_y0, hor_y1 = 0.0, arm
        by = (P["pad_bolt_y1"], P["pad_bolt_y2"])
    else:
        vert_y0, vert_y1 = P["W_frame"] - w, P["W_frame"]
        hor_y0, hor_y1 = P["W_frame"] - arm, P["W_frame"]
        by = (P["W_frame"] - P["pad_bolt_y1"],
              P["W_frame"] - P["pad_bolt_y2"])
    vert = box(lx0, vert_y0, P["pad_vert_z0"], lx1, vert_y1,
               P["pad_vert_z1"])
    hor = box(lx0, hor_y0, P["pad_hor_z0"], lx1, hor_y1,
              P["pad_hor_z1"])
    s = vert.fuse(hor)
    for y in by:
        s = s.cut(cyl_x(P["pad_bolt_hole_d"] / 2.0, lx0 - 1, lx1 + 1,
                        y, P["pad_hor_z0"] + 10.0))
    return s


def m4_bolt_x(x_head0, y, z, length, nut_x0):
    """Винт M4x35 с цилиндрической головкой, шайбами и гайкой nyloc."""
    wt = P["pad_washer_t"]
    wr = P["pad_washer_od"] / 2.0
    head_r = 3.5
    head_h = 4.0
    head = cyl_x(head_r, x_head0 - head_h, x_head0, y, z)
    wash_head = cyl_x(wr, x_head0 - wt, x_head0, y, z)
    wash_head = wash_head.cut(cyl_x(2.2, x_head0 - wt - 1,
                                    x_head0 + 1, y, z))
    shank = cyl_x(P["pad_bolt_d"] / 2.0, x_head0, x_head0 + length, y, z)
    bolt = head.fuse(wash_head).fuse(shank)
    wash_nut = cyl_x(wr, nut_x0, nut_x0 + wt, y, z)
    wash_nut = wash_nut.cut(cyl_x(2.2, nut_x0 - 1, nut_x0 + wt + 1, y, z))
    nut = hex_prism_x(7.0, nut_x0 + wt, nut_x0 + wt + P["pad_nyloc_h"],
                      y, z)
    nut = nut.cut(cyl_x(2.2, nut_x0 + wt - 1,
                        nut_x0 + wt + P["pad_nyloc_h"] + 1, y, z))
    return bolt.fuse(wash_nut), nut


def beam_bolt(side, rear_beam):
    """2 винта M4x35 пары накладок через балку 21 (вдоль X)."""
    T = P["tube"]
    t = P["pad_t"]
    xa = 0.0 if not rear_beam else P["L_vibro"] - T
    x_out = xa - t
    x_in = xa + T + t
    z = P["pad_hor_z0"] + 10.0
    if side < 0:
        ys = (P["pad_bolt_y1"], P["pad_bolt_y2"])
    else:
        ys = (P["W_frame"] - P["pad_bolt_y1"],
              P["W_frame"] - P["pad_bolt_y2"])
    bolts, nuts = [], []
    for y in ys:
        b, n = m4_bolt_x(x_out, y, z, P["pad_bolt_len"], x_in)
        bolts.append(b)
        nuts.append(n)
    return bolts, nuts


# ----------------------------------------------------------------------------
# шпильки поджима балки 21 (fix11)
# ----------------------------------------------------------------------------
def clamp_stud(x, y):
    """Строительная шпилька M10: низ 18 (в гнезде), верх 135."""
    return cyl_z(P["clamp_stud_d"] / 2.0 - 0.1,
                 P["clamp_stud_bottom"], P["clamp_stud_top"], x, y)


def clamp_bottom(x, y):
    """Опорная шайба и гайка nyloc на верхней грани нижней балки."""
    out = [washer_z(x, y, P["clamp_bottom_z"],
                    od=P["clamp_washer_od"],
                    d=P["clamp_stud_d"] + 0.5,
                    t=P["clamp_washer_t"])]
    out.append(hex_nut_z(x, y, P["clamp_bottom_z"] + P["clamp_washer_t"],
                         af=P["clamp_nut_af"], h=P["clamp_nyloc_h"],
                         d=P["clamp_stud_d"] + 0.4))
    return out


def clamp_press(x, y):
    """Шайба и гайка снизу прижимной балки (Z=110)."""
    z = P["clamp_press_z"] - P["clamp_washer_t"]
    out = [washer_z(x, y, z, od=P["clamp_washer_od"],
                    d=P["clamp_stud_d"] + 0.5, t=P["clamp_washer_t"])]
    out.append(hex_nut_z(x, y, z - P["clamp_nut_h"],
                         af=P["clamp_nut_af"], h=P["clamp_nut_h"],
                         d=P["clamp_stud_d"] + 0.4))
    return out


def podstol():
    s = box(P["podstol_x0"], P["podstol_y0"], P["podstol_z0"],
            P["podstol_x1"], P["podstol_y1"], P["podstol_z1"])
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            s = s.cut(cyl_z(P["podstol_hole_d"] / 2.0, P["podstol_z0"] - 1,
                            P["podstol_z1"] + 1, x, y))
            s = s.cut(Part.makeCone(P["podstol_cs_d"] / 2.0,
                                    P["podstol_hole_d"] / 2.0,
                                    P["podstol_cs_depth"],
                                    V(x, y, P["podstol_z1"]), V(0, 0, -1)))
    for x in (P["ubolt_x1"], P["ubolt_x2"]):
        for y in (47.0, 153.0):
            s = s.cut(cyl_z(3.3, P["podstol_z0"] - 1,
                            P["podstol_z1"] + 1, x, y))
    return s


def ubolt(xc):
    z = P["drive_z"]
    R = P["ubolt_inner"] / 2.0 + P["ubolt_d"] / 2.0
    tor = Part.makeTorus(R, P["ubolt_d"] / 2.0, V(xc, 100, z), V(1, 0, 0))
    tor = tor.cut(box(xc - 20, 0, z, xc + 20, 200, z + 100))
    legs = []
    for y in (100 - R, 100 + R):
        legs.append(cyl_z(P["ubolt_d"] / 2.0, z, z + P["ubolt_leg"], xc, y))
    s = tor
    for leg in legs:
        s = s.fuse(leg)
    return s


def hex_nut_z(x, y, z0, af=10.0, h=5.0, d=6.2):
    s = hex_prism_z(af, z0, z0 + h, x, y)
    return s.cut(cyl_z(d / 2.0, z0 - 1, z0 + h + 1, x, y))


def bolt_m6_z(x, y, z_head, z_end):
    head = hex_prism_z(10.0, z_head, z_head + 4.0, x, y)
    shank = cyl_z(3.0, z_head, z_end, x, y)
    return head.fuse(shank)


def screw_m4_z(x, y, z_head, z_end, countersunk=False, head_top=None):
    shank = cyl_z(2.0, min(z_head, z_end), max(z_head, z_end), x, y)
    if countersunk:
        top = head_top if head_top is not None else z_head + 2.5
        head = Part.makeCone(4.0, 2.0, 2.5, V(x, y, top), V(0, 0, -1))
        return shank.fuse(head)
    head = cyl_z(3.5, z_head - 1.8, z_head, x, y)
    return shank.fuse(head)


def screw_socket_m4_z(x, y, z_top, z_end):
    """Винт M4 с цилиндрической головкой Ø7x4, ось Z."""
    head = cyl_z(P["lmk_screw_head_d"] / 2.0, z_top - P["lmk_screw_head_h"],
                 z_top, x, y)
    shank = cyl_z(P["pad_bolt_d"] / 2.0,
                  z_top - P["lmk_screw_head_h"], z_end, x, y)
    return head.fuse(shank)


def lmk_screw_z(x, y):
    """Винт M4x12 снизу LMK: головка 219…223, резьба 223…235."""
    z_top = P["lmk_z1"] - P["lmk_flange_t"]          # 219
    head = cyl_z(P["lmk_screw_head_d"] / 2.0, z_top,
                 z_top + P["lmk_screw_head_h"], x, y)
    shank = cyl_z(2.0, z_top + P["lmk_screw_head_h"],
                  z_top + P["lmk_screw_len"], x, y)
    return head.fuse(shank)


def screw_m6_cs_z(x, y, z_top, z_end):
    """Потайной M6x60: головка Ø12/90° сверху, резьба вниз."""
    head = Part.makeCone(P["podstol_cs_d"] / 2.0,
                         P["podstol_hole_d"] / 2.0,
                         P["podstol_cs_depth"],
                         V(x, y, z_top), V(0, 0, -1))
    shank = cyl_z(3.0, z_top - P["podstol_cs_depth"], z_end, x, y)
    return head.fuse(shank)


# ----------------------------------------------------------------------------
# кожух, резиновые буферы и кольца
# ----------------------------------------------------------------------------
def _shield_plate(x0, y0, z0, x1, y1, z1, sel):
    s = box(x0, y0, z0, x1, y1, z1)
    for (hx, hy, hz, dx, dy, dz, t) in _points_for(sel):
        s = s.cut(cyl_axis(P["shield_hole_d"] / 2.0,
                           hx - dx * 0.5, hy - dy * 0.5, hz - dz * 0.5,
                           dx, dy, dz, t + 1.0))
    return s


def shield_parts():
    t = P["shield_t"]
    Lv = P["L_vibro"]
    W = P["W_frame"]
    zt = P["table_top_max"] + P["shield_skirt_gap"]
    return [
        _shield_plate(0, -t, 0, Lv, 0, P["top_z1"],
                      lambda p: abs(p[1] + t) < 1e-6),
        _shield_plate(0, W, 0, Lv, W + t, P["top_z1"],
                      lambda p: abs(p[1] - (W + t)) < 1e-6),
        _shield_plate(-t, 0, zt, 0, W, P["top_z1"],
                      lambda p: abs(p[0] + t) < 1e-6 and p[3] > 0),
        _shield_plate(Lv, 0, zt, Lv + t, W, P["top_z1"],
                      lambda p: abs(p[0] - (Lv + t)) < 1e-6 and p[3] < 0),
    ]


def shield_screws():
    """22 винта M4x10 с цилиндрической головкой Ø7x4 (fix9 п.2)."""
    out = []
    for (hx, hy, hz, dx, dy, dz, t) in shield_screw_layout():
        head = cyl_axis(P["shield_screw_head_d"] / 2.0,
                        hx - dx * P["shield_screw_head_h"],
                        hy - dy * P["shield_screw_head_h"],
                        hz - dz * P["shield_screw_head_h"],
                        dx, dy, dz, P["shield_screw_head_h"])
        shank = cyl_axis(P["shield_screw_d"] / 2.0 - 0.2,
                         hx, hy, hz, dx, dy, dz, P["shield_screw_len"])
        out.append(head.fuse(shank))
    return concat(out)


def rubber_pads():
    out = []
    for x0 in (0.0, P["L_vibro"] - P["tube"]):
        for y0 in (P["tube"], P["W_frame"] - P["tube"] - P["rubber_pad_w"]):
            out.append(box(x0, y0, P["rubber_pad_z0"],
                           x0 + P["rubber_pad_x"], y0 + P["rubber_pad_w"],
                           P["rubber_pad_z1"]))
    return out


def rubber_ring(x, y):
    s = cyl_z(P["ring_od"] / 2.0, P["ring_z0"], P["ring_z1"], x, y)
    return s.cut(cyl_z(P["ring_id"] / 2.0, P["ring_z0"] - 1,
                       P["ring_z1"] + 1, x, y))


# ----------------------------------------------------------------------------
# сборка
# ----------------------------------------------------------------------------
def build_assembly(drill=False, draw=False):
    parts = {}

    def add(name, shape, material, qty, group, spec_no):
        parts[name] = dict(shape=shape, material=material, qty=qty,
                           group=group, spec_no=spec_no)

    add("frame", frame(), "steel", 1, "frame", "22")
    add("frame_plugs", frame_plugs(), "plastic", 10, "plastic", "22.7")
    add("table", table(), "pla", 1, "table", "5")
    add("overlay", overlay(), "pla", 1, "overlay", "4")
    add("podstol", podstol(), "petg", 1, "table", "11")

    sh, sn, sw, spr, wa = [], [], [], [], []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            sh.append(shaft(x, y))
            # нижний узел: гайка + шайба под средней поперечиной;
            # верхний: шайба + гайка над верхней поперечиной
            sw.append(shaft_washer(
                x, y, P["mid_z0"] - P["shaft_washer_t"]))
            sn.append(shaft_nut(
                x, y, P["mid_z0"] - P["shaft_washer_t"] - P["shaft_nut_h"]))
            sw.append(shaft_washer(x, y, P["top_z1"]))
            sn.append(shaft_nut(
                x, y, P["top_z1"] + P["shaft_washer_t"]))
            spr.append(spring(x, y))
            wa.append(washer_z(x, y, P["overlay_z1"]))
            wa.append(washer_z(x, y, P["top_z0"] - P["spring_washer_t"]))
    add("shaft", concat(sh), "steel", 4, "steel", "2")
    add("shaft_nuts", concat(sn), "steel", 8, "steel", "45")
    add("shaft_washers", concat(sw), "steel", 8, "steel", "46")
    add("spring", concat(spr), "steel", 4, "steel", "3")
    add("spring_washer", concat(wa), "steel", 8, "steel", "25")

    lm = [lmk10uu(x, y) for x in (P["guide_x1"], P["guide_x2"])
          for y in (P["guide_y1"], P["guide_y2"])]
    add("lmk", concat(lm), "bearing", 4, "bearing", "8")

    add("drive_shaft", drive_shaft(), "steel", P["drive_shaft_n"],
        "steel", "20")
    add("cam", cam(5.0), "pla", 1, "cam", "10")
    cam_parts = {"cam_3": cam(3.0), "cam_5": cam(5.0), "cam_10": cam(10.0)}

    br = [bearing_6200(P["bearing_x1"] - 4.5, P["bearing_x1"] + 4.5,
                       100, P["drive_z"]),
          bearing_6200(P["bearing_x2"] - 4.5, P["bearing_x2"] + 4.5,
                       100, P["drive_z"])]
    add("shaft_bearings", concat(br), "bearing", 2, "bearing", "9")

    add("cam_washers", concat([
        cam_washer(P["cam_washer_l_x0"], P["cam_washer_l_x1"]),
        cam_washer(P["cam_washer_r_x0"], P["cam_washer_r_x1"])]),
        "steel", 2, "steel", "33")
    add("cam_nuts", concat([
        locknut(P["cam_nut_l_x0"], P["cam_nut_l_x1"]),
        locknut(P["cam_nut_r_x0"], P["cam_nut_r_x1"])]),
        "steel", 2, "steel", "34")
    add("cam_locknuts", concat([
        locknut(P["cam_lock_l_x0"], P["cam_lock_l_x1"]),
        locknut(P["cam_lock_r_x0"], P["cam_lock_r_x1"])]),
        "steel", 2, "steel", "16")

    cones, locks = [], []
    clamps = shaft_clamps()
    for tag in ("b1", "b2"):
        c = clamps[tag]
        cones.append(conical_nut(*c["cone_l"], True))
        cones.append(conical_nut(*c["cone_r"], False))
        locks.append(locknut(*c["lock_l"]))
        locks.append(locknut(*c["lock_r"]))
    add("shaft_conical_nuts", concat(cones), "steel",
        P["shaft_fix_conical"], "steel", "17")
    add("shaft_locknuts", concat(locks), "steel",
        P["shaft_fix_lock"], "steel", "16")

    rp = roller()
    add("roller", rp[0], "bearing", 1, "bearing", "9")
    add("axle", rp[1], "steel", 1, "steel", "7")
    add("roller_nuts", concat(rp[2:]), "steel", 4, "steel", "16/17")
    add("bracket", concat([bracket(-1), bracket(1)]), "steel", 2, "steel", "6")

    # балка 21 — стальная труба с втулками и заглушками
    ret = [retainer_beam(0.0), retainer_beam(P["L_vibro"] - P["tube"])]
    ret.extend(beam_spacers(0.0))
    ret.extend(beam_spacers(P["L_vibro"] - P["tube"]))
    add("retainer", concat(ret), "steel", 2, "retainer", "21")
    rpgs = []
    rpgs.extend(beam_plugs(0.0))
    rpgs.extend(beam_plugs(P["L_vibro"] - P["tube"]))
    add("retainer_plugs", concat(rpgs), "plastic", 4, "plastic", "21.7")

    ab = [angle_bracket(side, rear, face)
          for rear in (False, True)
          for side in (-1, 1)
          for face in (False, True)]
    add("angles", concat(ab), "steel", P["pad_n"], "angles", "14")

    ub = [ubolt(P["ubolt_x1"]), ubolt(P["ubolt_x2"])]
    add("ubolts", concat(ub), "steel", 2, "steel", "12")
    ub_nuts = []
    for xc in (P["ubolt_x1"], P["ubolt_x2"]):
        for y in (47.0, 153.0):
            ub_nuts.append(washer_z(xc, y, P["podstol_z1"], od=12, d=6.5,
                                    t=1.6))
            ub_nuts.append(hex_nut_z(xc, y, P["podstol_z1"] + 1.6,
                                     af=10, h=5.0))
    add("ubolt_nuts", concat(ub_nuts), "steel", 8, "steel", "12/19")

    # подстолье: 4 потайных M6x60; гайки приварены к раме (в frame)
    pod = []
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            pod.append(screw_m6_cs_z(x, y, P["podstol_z1"],
                                     P["podstol_z1"] - P["podstol_bolt_len"]))
    add("podstol_bolts", concat(pod), "steel", 4, "steel", "18")

    # LMK: 16 винтов M4x12 + 16 гаек
    fl = []
    fn = []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            for dx in (-16.0, 16.0):
                for dy in (-16.0, 16.0):
                    xx, yy = x + dx, y + dy
                    fl.append(lmk_screw_z(xx, yy))
                    fn.append(hex_nut_z(xx, yy,
                                        P["table_z1"] - P["lmk_nut_recess_h"],
                                        af=P["lmk_nut_recess_af"], h=5.0,
                                        d=4.4))
    add("lmk_screws", concat(fl), "steel", 16, "steel", "23")
    add("lmk_nuts", concat(fn), "steel", 16, "steel", "15")

    # накладка: 4 потайных M4 + гайки
    st, tn = [], []
    for x in (P["table_x0"] + P["overlay_inset"],
              P["table_x1"] - P["overlay_inset"]):
        for y in (P["table_y0"] + P["overlay_inset"],
                  P["table_y1"] - P["overlay_inset"]):
            st.append(screw_m4_z(x, y, 221.8, P["overlay_z1"],
                                 countersunk=True, head_top=P["overlay_z1"]))
            tn.append(hex_nut_z(x, y, 221.8, af=7, h=3.2, d=4.4))
    add("table_screws", concat(st), "steel", 4, "steel", "13")
    add("table_nuts", concat(tn), "steel", 4, "steel", "15")

    # кронштейны ролика: 2 винта M4x16 + 2 гайки
    bs, bn = [], []
    for x in (P["bracket_slot_x1"], P["bracket_slot_x2"]):
        bs.append(screw_socket_m4_z(x, 100.0, 234.0, 214.0))
        bn.append(hex_nut_z(x, 100.0, 218.0, af=7, h=5.0, d=4.4))
    add("bracket_screws", concat(bs), "steel", 2, "steel", "13/23")
    add("bracket_nuts", concat(bn), "steel", 2, "steel", "15")

    # накладки: 8 винтов M4x35 + 8 гаек nyloc (2 на конец балки)
    bb, bn2 = [], []
    for rear in (False, True):
        for side in (-1, 1):
            b2, n2 = beam_bolt(side, rear)
            bb.extend(b2)
            bn2.extend(n2)
    add("angle_bolts", concat(bb), "steel", P["pad_bolt_n"], "angles", "24")
    add("angle_nuts", concat(bn2), "steel", P["pad_bolt_n"], "angles", "24")

    # шпильки поджима M10: опора снизу и поджим под балкой
    st, sb, sp = [], [], []
    for x0 in (0.0, P["L_vibro"] - P["tube"]):
        for y in (P["clamp_stud_y1"], P["clamp_stud_y2"]):
            x = x0 + P["clamp_stud_x_off"]
            st.append(clamp_stud(x, y))
            sb.extend(clamp_bottom(x, y))
            sp.extend(clamp_press(x, y))
    add("clamp_studs", concat(st), "steel", P["clamp_stud_n"],
        "steel", "41")
    add("clamp_bottom", concat(sb), "steel", 8, "steel", "42/44")
    add("clamp_press", concat(sp), "steel", 8, "steel", "43/44")

    add("shield", concat(shield_parts()), "pc", 1, "shield", "29")
    add("shield_screws", shield_screws(), "steel", P["shield_screw_n"],
        "steel", "30")
    add("rubber_pads", concat(rubber_pads()), "rubber",
        P["rubber_pad_n"], "rubber", "31")
    rr = [rubber_ring(x, y) for x in (P["guide_x1"], P["guide_x2"])
          for y in (P["guide_y1"], P["guide_y2"])]
    add("rubber_rings", concat(rr), "rubber", P["ring_n"], "rubber", "32")

    groups = {}
    for key, info in parts.items():
        groups.setdefault(info["group"], []).append(info["shape"])
    groups["cartridge"] = [parts[k]["shape"] for k in
                           ("drive_shaft", "cam", "shaft_bearings",
                            "cam_washers", "cam_nuts", "cam_locknuts",
                            "shaft_conical_nuts", "shaft_locknuts")]
    return parts, groups, cam_parts


def mass_report(parts):
    rows = []
    total = 0.0
    for name, info in parts.items():
        vol = info["shape"].Volume
        m = vol * DENSITY[info["material"]]
        total += m
        rows.append((name, info["spec_no"], info["material"], vol,
                     info["qty"], m))
    return rows, total
