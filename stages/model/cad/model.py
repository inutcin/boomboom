"""Параметрическая модель вибростола (FreeCAD Part).

Оси: X — вдоль 400, Y — поперёк 200 (стол выходит до ±20…220), Z — вверх.
Все размеры берутся из params.py.
"""

import math
import FreeCAD as App
import Part

from params import P

V = App.Vector

DENSITY = {
    "steel": 7.85e-3,      # г/мм3
    "plywood": 0.70e-3,
    "pla": 1.24e-3,
    "bearing": 7.85e-3,    # оценка по стали (реальные массы ниже)
}


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


def tube_x(x0, x1, y0, z0, size=20.0, wall=1.5):
    outer = box(x0, y0, z0, x1, y0 + size, z0 + size)
    inner = box(min(x0, x1) - 1, y0 + wall, z0 + wall,
                max(x0, x1) + 1, y0 + size - wall, z0 + size - wall)
    return outer.cut(inner)


def tube_y(y0, y1, x0, z0, size=20.0, wall=1.5):
    outer = box(x0, y0, z0, x0 + size, y1, z0 + size)
    inner = box(x0 + wall, min(y0, y1) - 1, z0 + wall,
                x0 + size - wall, max(y0, y1) + 1, z0 + size - wall)
    return outer.cut(inner)


def tube_z(z0, z1, x0, y0, size=20.0, wall=1.5):
    outer = box(x0, y0, z0, x0 + size, y0 + size, z1)
    inner = box(x0 + wall, y0 + wall, min(z0, z1) - 1,
                x0 + size - wall, y0 + size - wall, max(z0, z1) + 1)
    return outer.cut(inner)


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
    """Объединение списка тел (без падения на пустом списке)."""
    if not shapes:
        return None
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()


# ----------------------------------------------------------------------------
# рама (поз. 22)
# ----------------------------------------------------------------------------
def frame(draw=False):
    """Рама поз. 22: набор труб 20x20x1,5 + сплошная центральная балка.

    draw='front' — условно не показывать переднюю (X=0) раму,
    draw='side'  — условно не показывать ближнюю (Y=0…25) раму.
    """
    front = (draw == "front")
    side = (draw == "side")
    T = P["tube"]
    solids = []

    # стойки виброотсека
    for x in (0.0, P["L_vibro"] - T):
        if front and x == 0.0:
            continue
        for y in (0.0, P["W_frame"] - T):
            solids.append(tube_z(0, P["H_frame"], x, y))

    # верхний пояс: продольные балки с отверстиями под валы
    for y, gy in ((5.0, P["guide_y1"]), (175.0, P["guide_y2"])):
        if side and y == 5.0:
            continue
        b = tube_x(0, P["L_vibro"], y, P["top_z0"])
        for gx in (P["guide_x1"], P["guide_x2"]):
            b = b.cut(cyl_z(5.25, P["top_z0"] - 1, P["top_z1"] + 1, gx, gy))
        solids.append(b)
    if not front:
        solids.append(tube_y(T, P["W_frame"] - T, 0, P["top_z0"]))
    solids.append(tube_y(T, P["W_frame"] - T, P["L_vibro"] - T, P["top_z0"]))

    # средний пояс: продольные балки с отверстиями под валы
    for y, gy in ((5.0, P["guide_y1"]), (175.0, P["guide_y2"])):
        if side and y == 5.0:
            continue
        b = tube_x(0, P["L_vibro"], y, P["mid_z0"])
        for gx in (P["guide_x1"], P["guide_x2"]):
            b = b.cut(cyl_z(5.25, P["mid_z0"] - 1, P["mid_z1"] + 1, gx, gy))
        solids.append(b)
    if not front:
        solids.append(tube_y(T, P["W_frame"] - T, 0, P["mid_z0"]))
    solids.append(tube_y(T, P["W_frame"] - T, P["L_vibro"] - T, P["mid_z0"]))

    # центральная балка среднего пояса — сплошной брус с окном и сёдлами 6200
    central = box(T, 90, P["mid_z0"], P["L_vibro"] - T, 110, P["mid_z1"])
    central = central.cut(box(92, 88, P["mid_z0"] - 2, 108, 112, P["mid_z1"] + 2))
    for x in (P["bearing_x1"], P["bearing_x2"]):
        central = central.cut(cyl_x(15.05, x - 7, x + 7, 100, P["drive_z"]))
    solids.append(central)

    # нижний пояс виброотсека
    if not side:
        solids.append(tube_x(0, P["L_vibro"], 0, 0))
    solids.append(tube_x(0, P["L_vibro"], 180, 0))
    if not front:
        solids.append(tube_y(0, P["W_frame"], 0, 0))
    solids.append(tube_y(0, P["W_frame"], P["L_vibro"] - T, 0))

    # вынос: нижний пояс
    if not side:
        solids.append(tube_x(P["L_vibro"], P["L_frame"], 0, 0))
    solids.append(tube_x(P["L_vibro"], P["L_frame"], 180, 0))
    solids.append(tube_y(0, P["W_frame"], P["L_frame"] - T, 0))

    # вынос: стойки
    for y in (0.0, P["W_frame"] - T):
        solids.append(tube_z(0, P["ext_top_z1"], P["L_frame"] - T, y))

    # вынос: верхние балки
    if not side:
        solids.append(tube_x(P["L_vibro"], P["L_frame"], 0, P["ext_top_z0"]))
    solids.append(tube_x(P["L_vibro"], P["L_frame"], 180, P["ext_top_z0"]))
    for y0, y1 in ((0.0, P["W_frame"]), (0.0, 50.0), (150.0, P["W_frame"])):
        x0 = P["L_vibro"] if y0 == 0.0 and y1 == P["W_frame"] else P["L_frame"] - T
        if y1 - y0 == P["W_frame"]:
            b = tube_y(y0, y1, P["L_vibro"], P["ext_top_z0"])
        else:
            b = tube_y(y0, y1, P["L_frame"] - T, P["ext_top_z0"])
        # отверстия M6 под подстолье
        for yy in (35.0, 165.0):
            if y0 < yy < y1:
                xx = P["L_vibro"] + 15.0 if y1 - y0 == P["W_frame"] else P["L_frame"] - 15.0
                b = b.cut(cyl_z(3.2, P["ext_top_z0"] - 1, P["ext_top_z1"] + 1, xx, yy))
        solids.append(b)

    return Part.makeCompound(solids)


# ----------------------------------------------------------------------------
# стол, накладка
# ----------------------------------------------------------------------------
def table():
    s = box(P["table_x0"], P["table_y0"], P["table_z0"],
            P["table_x1"], P["table_y1"], P["table_z1"])
    # отверстия под валы
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(5.25, P["table_z0"] - 1, P["table_z1"] + 1, x, y))
    # центральный M4
    s = s.cut(cyl_z(2.25, P["table_z0"] - 1, P["table_z1"] + 1, 100, 100))
    # глухие отверстия под винты фланцев LMF10UU
    for gx in (P["guide_x1"], P["guide_x2"]):
        for gy in (P["guide_y1"], P["guide_y2"]):
            for i in range(4):
                a = math.radians(45 + 90 * i)
                s = s.cut(cyl_z(2.1, P["table_z0"], P["table_z1"],
                                gx + 14.5 * math.cos(a), gy + 14.5 * math.sin(a)))
    # пазы под M4 кронштейнов + зенковка
    for x in (65.0, 135.0):
        s = s.cut(box(x - 5, 97.75, P["table_z0"] - 1, x + 5, 102.25, P["table_z1"] + 1))
        s = s.cut(Part.makeCone(4.0, 2.0, 2.5, V(x, 100, P["table_z1"] - 2.5), V(0, 0, -1)))
    return s


def overlay():
    s = box(P["table_x0"], P["table_y0"], P["overlay_z0"],
            P["table_x1"], P["table_y1"], P["overlay_z1"])
    # сферическая вогнутость Ø140, глубина 2
    R = 1225.0
    cz = P["overlay_z1"] - P["dish_depth"] + R
    dish = Part.makeSphere(R, V(100, 100, cz))
    s = s.cut(dish)
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(5.25, P["overlay_z0"] - 1, P["overlay_z1"] + 1, x, y))
    # центральный потайной M4
    s = s.cut(cyl_z(2.25, P["overlay_z0"] - 1, P["overlay_z1"] + 1, 100, 100))
    s = s.cut(Part.makeCone(4.0, 2.0, 2.5, V(100, 100, P["overlay_z1"] - 2.5),
                            V(0, 0, -1)))
    return s


# ----------------------------------------------------------------------------
# линейный подшипник LMF10UU и 6200
# ----------------------------------------------------------------------------
def lmf10uu(x, y):
    z0, z1 = P["lmf_z0"], P["lmf_z1"]
    body = cyl_z(9.5, z0, z1 - P["lmf_flange_t"], x, y)
    flange = cyl_z(20.0, z1 - P["lmf_flange_t"], z1, x, y)
    s = body.fuse(flange)
    s = s.cut(cyl_z(5.05, z0 - 1, z1 + 1, x, y))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        s = s.cut(cyl_z(2.25, z1 - P["lmf_flange_t"] - 1, z1 + 1,
                        x + 14.5 * math.cos(a), y + 14.5 * math.sin(a)))
    return s


def bearing_6200(x0, x1, y, z):
    s = cyl_x(15.0, x0, x1, y, z)
    s = s.cut(cyl_x(5.05, x0 - 1, x1 + 1, y, z))
    return s


# ----------------------------------------------------------------------------
# валы, ограничители, пружины
# ----------------------------------------------------------------------------
def shaft(x, y):
    return cyl_z(5.0, P["shaft_z0"], P["shaft_z1"], x, y)


def collar(x, y, z0):
    s = cyl_z(P["collar_d"] / 2.0, z0, z0 + P["collar_t"], x, y)
    s = s.cut(cyl_z(5.05, z0 - 1, z0 + P["collar_t"] + 1, x, y))
    return s


def spring(x, y):
    z0 = P["overlay_z1"] + 0.5
    h = P["spring_inst"] - 1.0
    turns = int(P["spring_turns"])
    mean_r = (P["spring_od"] - P["spring_wire"]) / 2.0 + 0.1  # фактический ID 10,2
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


# ----------------------------------------------------------------------------
# привод: вал, гайки, кулачок, ролик
# ----------------------------------------------------------------------------
def cam(stroke):
    """Эксцентриковый диск; stroke — ход ролика (3/5/10 мм)."""
    ecc = stroke / 2.0
    r_work = 45.0 + ecc
    r_flange = r_work + 2.0
    cy, cz = 100.0, P["drive_z"] + ecc
    gx0, gx1 = P["cam_x0"], P["cam_x1"]
    ft = (gx1 - gx0 - P["cam_groove_w"]) / 2.0
    core = Part.makeCylinder(r_work, P["cam_groove_w"],
                             V(gx0 + ft, cy, cz), V(1, 0, 0))
    left = Part.makeCylinder(r_flange, ft, V(gx0, cy, cz), V(1, 0, 0))
    right = Part.makeCylinder(r_flange, ft, V(gx1 - ft, cy, cz), V(1, 0, 0))
    s = core.fuse(left).fuse(right)
    s = s.cut(cyl_x(5.1, gx0 - 1, gx1 + 1, 100, P["drive_z"]))
    return s


def conical_nut(x0, x1, small_at_right=True, z=None):
    z = P["drive_z"] if z is None else z
    r_big, r_small = 8.0, 6.0
    if small_at_right:
        cone = Part.makeCone(r_big, r_small, abs(x1 - x0), V(x0, 100, z), V(1, 0, 0))
    else:
        cone = Part.makeCone(r_small, r_big, abs(x1 - x0), V(x0, 100, z), V(1, 0, 0))
    return cone.cut(cyl_x(5.1, min(x0, x1) - 1, max(x0, x1) + 1, 100, z))


def locknut(x0, x1, z=None):
    z = P["drive_z"] if z is None else z
    s = hex_prism_x(17.0, x0, x1, 100, z)
    return s.cut(cyl_x(5.1, min(x0, x1) - 1, max(x0, x1) + 1, 100, z))


def drive_shaft():
    return cyl_x(5.0, P["shaft_x0"], P["shaft_x1"], 100, P["drive_z"])


def bracket(side):
    """Уголок 40x40x20x2; side=-1 левый, +1 правый."""
    t = P["bracket_t"]
    w = P["bracket_w"]
    z_bottom = 185.0
    z_top = P["table_z0"]
    if side < 0:
        vx0, vx1 = 88.0, 88.0 + t
        hx0, hx1 = 48.0, 88.0
    else:
        vx0, vx1 = 110.0 - t, 110.0
        hx0, hx1 = 110.0, 150.0
    vert = box(vx0, 90, z_bottom, vx1, 90 + w, z_top)
    hor = box(hx0, 90, z_top - t, hx1, 90 + w, z_top)
    s = vert.fuse(hor)
    s = s.cut(cyl_x(5.05, vx0 - 1, vx1 + 1, 100, 205))
    # паз под M4
    xm = 65.0 if side < 0 else 135.0
    s = s.cut(box(xm - 5, 97.75, z_top - t - 1, xm + 5, 102.25, z_top + 1))
    return s


def roller():
    b = bearing_6200(95.5, 104.5, 100, 205)
    axle = cyl_x(5.0, 78, 122, 100, 205)
    parts = [b, axle]
    parts.append(conical_nut(90.0, 95.5, True, z=205))
    parts.append(conical_nut(104.5, 110.0, False, z=205))
    parts.append(locknut(80.0, 88.0, z=205))
    parts.append(locknut(112.0, 120.0, z=205))
    return parts


# ----------------------------------------------------------------------------
# балки 21 и крабы 14
# ----------------------------------------------------------------------------
def retainer_beam(x0, x1):
    """Балка 21: стальной брус 20x20 с седлом под 6200."""
    s = box(x0, P["ret_y0"], P["ret_z0"], x1, P["ret_y1"], P["ret_z1"])
    xc = 60.0 if x0 < 100 else 140.0
    s = s.cut(cyl_x(15.05, xc - 7, xc + 7, 100, P["drive_z"]))
    # глухие отверстия под потайные M6 крабов
    xx = 30.0 if x0 < 100 else 170.0
    for yy in (95.0, 105.0):
        s = s.cut(cyl_z(3.1, 110.0, P["ret_z1"], xx, yy))
    return s


def crab(side, front):
    """Т-краб: пластина на стойке, вынос по Y, полка над балкой 21."""
    t = P["crab_t"]
    x0, x1 = (0.0, 20.0) if side < 0 else (180.0, 200.0)
    tab_x0, tab_x1 = (0.0, 40.0) if side < 0 else (160.0, 200.0)
    if front:
        plate_y0, plate_y1 = 20.0, 25.0
        arm_y0, arm_y1 = 25.0, 90.0
        tab_y0, tab_y1 = 85.0, 100.0
        screw_y = 95.0
    else:
        plate_y0, plate_y1 = 175.0, 180.0
        arm_y0, arm_y1 = 110.0, 175.0
        tab_y0, tab_y1 = 100.0, 115.0
        screw_y = 105.0
    z0 = P["ret_z1"]
    plate = box(x0, plate_y0, z0, x1, plate_y1, z0 + 20.0)
    arm = box(x0, arm_y0, z0, x1, arm_y1, z0 + t)
    tab = box(tab_x0, tab_y0, z0, tab_x1, tab_y1, z0 + t)
    s = plate.fuse(arm).fuse(tab)
    # два M6 через пластину в стойку (вдоль Y)
    for xx in (x0 + 5.0, x0 + 15.0):
        yy = plate_y0 - 1.0 if front else plate_y1 + 1.0
        s = s.cut(cyl_y(3.2, plate_y0 - 1, plate_y1 + 1, xx, z0 + 10.0))
    # потайной M6 сверху в балку 21
    xx = 30.0 if side < 0 else 170.0
    s = s.cut(cyl_z(3.2, z0 - 1, z0 + t + 1, xx, screw_y))
    s = s.cut(Part.makeCone(6.0, 3.2, 3.0, V(xx, screw_y, z0 + t), V(0, 0, -1)))
    return s


# ----------------------------------------------------------------------------
# вынос: подстолье, хомуты, крепёж
# ----------------------------------------------------------------------------
def podstol():
    s = box(P["podstol_x0"], P["podstol_y0"], P["podstol_z0"],
            P["podstol_x1"], P["podstol_y1"], P["podstol_z1"])
    for x in (P["podstol_x0"] + 15, P["L_frame"] - 15):
        for y in (35.0, 165.0):
            s = s.cut(cyl_z(3.2, P["podstol_z0"] - 1, P["podstol_z1"] + 1, x, y))
    for x in (P["ubolt_x1"], P["ubolt_x2"]):
        for y in (47.0, 153.0):
            s = s.cut(cyl_z(3.3, P["podstol_z0"] - 1, P["podstol_z1"] + 1, x, y))
    return s


def ubolt(xc):
    z = P["drive_z"]
    R = P["ubolt_inner"] / 2.0 + P["ubolt_d"] / 2.0
    tor = Part.makeTorus(R, P["ubolt_d"] / 2.0, V(xc, 100, z), V(1, 0, 0))
    tor = tor.cut(box(xc - 20, 0, z, xc + 20, 200, z + 100))
    legs = []
    for y in (100 - R, 100 + R):
        legs.append(cyl_z(P["ubolt_d"] / 2.0, z, z + 100.0, xc, y))
    s = tor
    for leg in legs:
        s = s.fuse(leg)
    return s


def hex_nut_z(x, y, z0, af=10.0, h=5.0, d=6.2):
    s = hex_prism_z(af, z0, z0 + h, x, y)
    return s.cut(cyl_z(d / 2.0, z0 - 1, z0 + h + 1, x, y))


def washer_z(x, y, z0, od=12.0, d=6.5, t=1.6):
    s = cyl_z(od / 2.0, z0, z0 + t, x, y)
    return s.cut(cyl_z(d / 2.0, z0 - 1, z0 + t + 1, x, y))


def bolt_m6_z(x, y, z_head, z_end):
    head = hex_prism_z(10.0, z_head, z_head + 4.0, x, y)
    shank = cyl_z(3.0, z_head, z_end, x, y)
    return head.fuse(shank)


def screw_m6_z(x, y, z_end, head_top):
    """Потайной M6: стержень снизу вверх, головка заподлицо с head_top."""
    shank = cyl_z(3.0, z_end, head_top, x, y)
    head = Part.makeCone(6.0, 3.0, 3.5, V(x, y, head_top), V(0, 0, -1))
    return shank.fuse(head)


def screw_m4_z(x, y, z_head, z_end, countersunk=False, head_top=None):
    shank = cyl_z(2.0, min(z_head, z_end), max(z_head, z_end), x, y)
    if countersunk:
        top = head_top if head_top is not None else z_head + 2.5
        head = Part.makeCone(4.0, 2.0, 2.5, V(x, y, top), V(0, 0, -1))
        return shank.fuse(head)
    head = cyl_z(3.5, z_head - 1.8, z_head, x, y)
    return shank.fuse(head)


# ----------------------------------------------------------------------------
# сборка
# ----------------------------------------------------------------------------
def build_assembly(drill=False, draw=False):
    """Возвращает (parts, groups, cams)."""
    parts = {}

    def add(name, shape, material, qty, group, spec_no):
        parts[name] = dict(shape=shape, material=material, qty=qty,
                           group=group, spec_no=spec_no)

    add("frame", frame(draw=draw), "steel", 1, "frame", "22")
    add("table", table(), "plywood", 1, "wood", "5")
    add("overlay", overlay(), "pla", 1, "printed", "4")
    add("podstol", podstol(), "plywood", 1, "wood", "11")

    # валы и ограничители
    sh = []
    co = []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            sh.append(shaft(x, y))
            co.append(collar(x, y, P["shaft_z0"]))
            co.append(collar(x, y, P["shaft_z1"] - P["collar_t"]))
    add("shaft", concat(sh), "steel", 4, "steel", "2")
    add("collar", concat(co), "steel", 8, "steel", "1")
    add("spring", concat([spring(P["guide_x1"], P["guide_y1"]),
                          spring(P["guide_x2"], P["guide_y1"]),
                          spring(P["guide_x1"], P["guide_y2"]),
                          spring(P["guide_x2"], P["guide_y2"])]),
        "steel", 4, "steel", "3")

    # линейные подшипники
    lm = [lmf10uu(x, y) for x in (P["guide_x1"], P["guide_x2"])
          for y in (P["guide_y1"], P["guide_y2"])]
    add("lmf", concat(lm), "bearing", 4, "bearing", "8")

    # привод
    add("drive_shaft", drive_shaft(), "steel", 1, "steel", "20")
    add("cam", cam(5.0), "pla", 1, "printed", "10")
    cam_parts = {"cam_3": cam(3.0), "cam_5": cam(5.0), "cam_10": cam(10.0)}

    br = [bearing_6200(55.5, 64.5, 100, P["drive_z"]),
          bearing_6200(135.5, 144.5, 100, P["drive_z"])]
    add("shaft_bearings", concat(br), "bearing", 2, "bearing", "9")

    nuts = []
    cones = [
        (48.0, 55.5, True), (64.5, 74.0, False),
        (126.0, 135.5, True), (144.5, 154.0, False),
        (84.0, 94.0, True), (106.0, 116.0, False),
    ]
    for x0, x1, sr in cones:
        nuts.append(conical_nut(x0, x1, sr))
    add("conical_nuts", concat(nuts), "steel", 6, "steel", "17")

    lns = [locknut(40.0, 48.0), locknut(74.0, 82.0),
           locknut(116.0, 124.0), locknut(154.0, 162.0)]
    add("locknuts", concat(lns), "steel", 4, "steel", "16")

    # ролик, ось, кронштейн
    rp = roller()
    add("roller", rp[0], "bearing", 1, "bearing", "9")
    add("axle", rp[1], "steel", 1, "steel", "7")
    add("roller_nuts", concat(rp[2:]), "steel", 4, "steel", "16/17")
    add("bracket", concat([bracket(-1), bracket(1)]), "steel", 2, "steel", "6")

    # балки 21 и крабы
    add("retainer", concat([retainer_beam(20, 90), retainer_beam(110, 180)]),
        "steel", 2, "steel", "21")
    cr = [crab(-1, True), crab(-1, False), crab(1, True), crab(1, False)]
    add("crabs", concat(cr), "steel", 4, "steel", "14")

    # U-хомуты и их гайки
    ub = [ubolt(P["ubolt_x1"]), ubolt(P["ubolt_x2"])]
    add("ubolts", concat(ub), "steel", 2, "steel", "12")
    ub_nuts = []
    for xc in (P["ubolt_x1"], P["ubolt_x2"]):
        for y in (47.0, 153.0):
            ub_nuts.append(washer_z(xc, y, P["podstol_z1"], od=12, d=6.5))
            ub_nuts.append(hex_nut_z(xc, y, P["podstol_z1"] + 1.6, af=10, h=5.0))
    add("ubolt_nuts", concat(ub_nuts), "steel", 8, "steel", "12/19")

    # крепёж подстолья M6
    pod = []
    for x in (P["podstol_x0"] + 15, P["L_frame"] - 15):
        for y in (35.0, 165.0):
            pod.append(bolt_m6_z(x, y, P["podstol_z1"], 164.0))
            pod.append(hex_nut_z(x, y, 164.0, af=10, h=5.0))
    add("podstol_bolts", concat(pod), "steel", "4+4", "steel", "18/19")

    # крепёж фланцев LMF10UU (16 шт. M4x12)
    fl = []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            for i in range(4):
                a = math.radians(45 + 90 * i)
                xx = x + 14.5 * math.cos(a)
                yy = y + 14.5 * math.sin(a)
                fl.append(screw_m4_z(xx, yy, 213.0, 235.0))
    add("flange_screws", concat(fl), "steel", 16, "steel", "23")

    # крепёж стола: 2 кронштейна + накладка
    st = [screw_m4_z(65, 100, 219.0, 232.5, countersunk=True, head_top=235.0),
          screw_m4_z(135, 100, 219.0, 232.5, countersunk=True, head_top=235.0),
          screw_m4_z(100, 100, 221.0, 236.5, countersunk=True, head_top=239.0)]
    add("table_screws", concat(st), "steel", 3, "steel", "13")
    tn = [hex_nut_z(65, 100, 219.0, af=7, h=3.2, d=4.4),
          hex_nut_z(135, 100, 219.0, af=7, h=3.2, d=4.4),
          hex_nut_z(100, 100, 221.0, af=7, h=3.2, d=4.4)]
    add("table_nuts", concat(tn), "steel", 3, "steel", "15")

    # крабы: болты M6 (поз. 24)
    cb = []
    for side in (-1, 1):
        for front in (True, False):
            xx = 30.0 if side < 0 else 170.0
            yy = 95.0 if front else 105.0
            cb.append(screw_m6_z(xx, yy, 114.0, 131.0))
    add("crab_screws", concat(cb), "steel", 4, "steel", "24")

    groups = {}
    for key, info in parts.items():
        groups.setdefault(info["group"], []).append(info["shape"])

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
