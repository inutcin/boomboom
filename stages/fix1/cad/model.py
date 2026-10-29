"""Параметрическая модель вибростола, этап fix1 (FreeCAD Part).

Оси: X — вдоль 400 (виброотсек 0…200, вынос 200…400),
     Y — поперёк 200, Z — вверх 300.
Стол вытянут по X: −20…220, по Y: 25…175.

Ключевые решения fix1:
  * рама — PETG, сплошное сечение 20×20, печать одним куском;
  * убраны средние боковые балки, центральная балка с окном и задняя
    нижняя поперечина;
  * валы в X=10/190 (центры средних поперечин), Y=50/150;
  * 6200 зажаты между средней поперечиной и балкой 21 (поз. 21);
  * стол/накладка/подстолье — печать; накладка крепится 4 угловыми M4;
  * LMK10UU (квадратный фланец 40×40) вместо LMF10UU;
  * ограничители WCS10FR Ø30;
  * шайбы пружин, фаска кулачка, гайки nyloc на столе.
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
def frame():
    """Рама PETG, сплошное 20×20, одним куском.

    Состав:
      * 4 стойки виброотсека, 2 стойки выноса;
      * верхний пояс виброотсека (2 продольные + 2 поперечины);
      * 2 средние поперечины (боковых продольных балок нет);
      * нижний пояс виброотсека + вынос;
      * верхние балки выноса; задняя нижняя поперечина отсутствует.
    """
    T = P["tube"]
    W = P["W_frame"]
    H = P["H_frame"]
    Lv = P["L_vibro"]
    L = P["L_frame"]
    solids = []

    # стойки виброотсека
    for x in (0.0, Lv - T):
        for y in (0.0, W - T):
            solids.append(box(x, y, 0, x + T, y + T, H))

    # верхний пояс виброотсека
    for y in (0.0, W - T):
        solids.append(box(0, y, P["top_z0"], Lv, y + T, P["top_z1"]))
    for x in (0.0, Lv - T):
        solids.append(box(x, 0, P["top_z0"], x + T, W, P["top_z1"]))

    # средние поперечины (только по Y)
    # передняя — 20 мм; граничная продлена до X=220 и служит опорой
    # передней поперечине выноса (общая грань Z=170 — без немногообразного
    # контакта по ребру)
    solids.append(box(0, 0, P["mid_z0"], T, W, P["mid_z1"]))
    solids.append(box(Lv - T, 0, P["mid_z0"], Lv + T, W, P["mid_z1"]))

    # нижний пояс виброотсека
    for y in (0.0, W - T):
        solids.append(box(0, y, 0, Lv, y + T, P["base_h"]))
    for x in (0.0, Lv - T):
        solids.append(box(x, 0, 0, x + T, W, P["base_h"]))

    # нижний пояс выноса
    for y in (0.0, W - T):
        solids.append(box(Lv, y, 0, L, y + T, P["base_h"]))

    # стойки выноса (до верхних балок выноса)
    for y in (0.0, W - T):
        solids.append(box(L - T, y, 0, L, y + T, P["ext_top_z1"]))

    # верхние балки выноса
    for y in (0.0, W - T):
        solids.append(box(Lv, y, P["ext_top_z0"], L, y + T, P["ext_top_z1"]))
    solids.append(box(Lv, 0, P["ext_top_z0"], Lv + T, W, P["ext_top_z1"]))
    for y0, y1 in ((0.0, 50.0), (150.0, W)):
        solids.append(box(L - T, y0, P["ext_top_z0"], L, y1, P["ext_top_z1"]))

    s = concat(solids)

    # ---- отверстия и сёдла ----
    holes = []
    # отверстия направляющих валов в верхних и средних поперечинах
    for gx in (P["guide_x1"], P["guide_x2"]):
        for gy in (P["guide_y1"], P["guide_y2"]):
            holes.append(cyl_z(5.25, P["top_z0"] - 1, P["top_z1"] + 1, gx, gy))
            holes.append(cyl_z(5.25, P["mid_z0"] - 1, P["mid_z1"] + 1, gx, gy))
    # сёдла 6200 в нижней грани средних поперечин
    for x0 in (0.0, Lv - T):
        holes.append(cyl_x(P["bearing_groove_r"], x0 - 1, x0 + T + 1,
                           P["drive_y"], P["drive_z"]))
    # отверстия M4 под крабы (передняя и граничная поперечины)
    for xface in (0.0, Lv - T):
        for y in (10.0, W - 10.0):
            for z in (140.0, 180.0):
                holes.append(cyl_x(2.25, xface - 1, xface + T - 10 + 1, y, z))
    # отверстия M6 под подстолье в верхних поперечинах выноса
    for x in (215.0, 385.0):
        for y in (35.0, W - 35.0):
            holes.append(cyl_z(3.1, 179.0, 191.0, x, y))

    for h in holes:
        s = s.cut(h)
    return s.removeSplitter()


# ----------------------------------------------------------------------------
# стол, накладка
# ----------------------------------------------------------------------------
def table():
    s = box(P["table_x0"], P["table_y0"], P["table_z0"],
            P["table_x1"], P["table_y1"], P["table_z1"])
    # отверстия под валы и крепёж фланцев LMK10UU (сетка 32×32)
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(5.25, P["table_z0"] - 1, P["table_z1"] + 1, x, y))
            for dx in (-16.0, 16.0):
                for dy in (-16.0, 16.0):
                    s = s.cut(cyl_z(2.1, P["table_z0"] - 1, P["table_z1"] + 1,
                                    x + dx, y + dy))
    # пазы под M4 кронштейнов + зенковка
    for x in (65.0, 135.0):
        s = s.cut(box(x - 5, 97.75, P["table_z0"] - 1, x + 5, 102.25,
                      P["table_z1"] + 1))
        s = s.cut(Part.makeCone(4.0, 2.0, 2.5, V(x, 100, P["table_z1"]),
                                V(0, 0, -1)))
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
    # сферическая вогнутость Ø140, глубина 2
    R = 1225.0
    cz = P["overlay_z1"] - P["dish_depth"] + R
    s = s.cut(Part.makeSphere(R, V(100, 100, cz)))
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(5.25, P["overlay_z0"] - 1, P["overlay_z1"] + 1, x, y))
    # 4 угловых потайных M4
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
    zf = z1 - P["lmk_flange_t"]          # низ фланца
    body = cyl_z(P["lmk_body_d"] / 2.0, z0, zf, x, y)
    f = P["lmk_flange"] / 2.0
    flange = box(x - f, y - f, zf, x + f, y + f, z1)
    s = body.fuse(flange)
    s = s.cut(cyl_z(5.05, z0 - 1, z1 + 1, x, y))
    for dx in (-P["lmk_hole_pitch"] / 2.0, P["lmk_hole_pitch"] / 2.0):
        for dy in (-P["lmk_hole_pitch"] / 2.0, P["lmk_hole_pitch"] / 2.0):
            s = s.cut(cyl_z(P["lmk_hole_d"] / 2.0, zf - 1, z1 + 1,
                            x + dx, y + dy))
    return s


def bearing_6200(x0, x1, y, z):
    s = cyl_x(P["b6200_od"] / 2.0, x0, x1, y, z)
    s = s.cut(cyl_x(P["b6200_id"] / 2.0 + 0.05, x0 - 1, x1 + 1, y, z))
    return s


# ----------------------------------------------------------------------------
# валы, ограничители, пружины, шайбы
# ----------------------------------------------------------------------------
def shaft(x, y):
    return cyl_z(P["shaft_d"] / 2.0, P["shaft_z0"], P["shaft_z1"], x, y)


def collar(x, y, z0):
    s = cyl_z(P["collar_d"] / 2.0, z0, z0 + P["collar_t"], x, y)
    s = s.cut(cyl_z(P["shaft_d"] / 2.0 + 0.05, z0 - 1,
                    z0 + P["collar_t"] + 1, x, y))
    return s


def spring(x, y):
    z0 = P["overlay_z1"] + P["spring_washer_t"]
    h = P["spring_inst"]
    turns = int(P["spring_turns"])
    mean_r = (P["spring_od"] - P["spring_wire"]) / 2.0 + 0.1  # ID 10,2
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
def cam(stroke):
    """Эксцентриковый диск; stroke — ход ролика (3/5/10 мм)."""
    ecc = stroke / 2.0
    r_work = 45.0 + ecc
    r_flange = r_work + 2.0
    cy, cz = P["drive_y"], P["drive_z"] + ecc
    gx0, gx1 = P["cam_x0"], P["cam_x1"]
    ft = (gx1 - gx0 - P["cam_groove_w"]) / 2.0
    core = Part.makeCylinder(r_work, P["cam_groove_w"],
                             V(gx0 + ft, cy, cz), V(1, 0, 0))
    left = Part.makeCylinder(r_flange, ft, V(gx0, cy, cz), V(1, 0, 0))
    right = Part.makeCylinder(r_flange, ft, V(gx1 - ft, cy, cz), V(1, 0, 0))
    s = core.fuse(left).fuse(right)
    s = s.cut(cyl_x(5.1, gx0 - 1, gx1 + 1, cy, P["drive_z"]))
    # фаска 1×45° с обоих торцов отверстия
    ch = P["cam_chamfer"]
    s = s.cut(Part.makeCone(5.1 + ch, 5.1, ch,
                            V(gx0, cy, P["drive_z"]), V(1, 0, 0)))
    s = s.cut(Part.makeCone(5.1 + ch, 5.1, ch,
                            V(gx1, cy, P["drive_z"]), V(-1, 0, 0)))
    return s


def conical_nut(x0, x1, small_at_right=True, z=None):
    z = P["drive_z"] if z is None else z
    r_big, r_small = 8.0, 6.0
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


def drive_shaft():
    return cyl_x(P["shaft_d"] / 2.0, P["shaft_x0"], P["shaft_x1"],
                 100, P["drive_z"])


def bracket(side):
    """Уголок 40×40×20×2; side=-1 левый, +1 правый."""
    t = P["bracket_t"]
    w = P["bracket_w"]
    z_bottom = 185.0
    z_top = P["table_z0"]
    if side < 0:
        vx0, vx1 = 88.0, 88.0 + t
        hx0, hx1 = 48.0, 88.0
        xm = 65.0
    else:
        vx0, vx1 = 110.0 - t, 110.0
        hx0, hx1 = 110.0, 150.0
        xm = 135.0
    vert = box(vx0, 90, z_bottom, vx1, 90 + w, z_top)
    hor = box(hx0, 90, z_top - t, hx1, 90 + w, z_top)
    s = vert.fuse(hor)
    s = s.cut(cyl_x(5.05, vx0 - 1, vx1 + 1, 100, P["roller_z"]))
    # паз под M4
    s = s.cut(box(xm - 5, 97.75, z_top - t - 1, xm + 5, 102.25, z_top + 1))
    return s


def roller():
    b = bearing_6200(95.5, 104.5, 100, P["roller_z"])
    axle = cyl_x(P["axle_d"] / 2.0, 78, 122, 100, P["roller_z"])
    parts = [b, axle]
    parts.append(conical_nut(90.0, 95.5, True, z=P["roller_z"]))
    parts.append(conical_nut(104.5, 110.0, False, z=P["roller_z"]))
    parts.append(locknut(80.0, 88.0, z=P["roller_z"]))
    parts.append(locknut(112.0, 120.0, z=P["roller_z"]))
    return parts


# ----------------------------------------------------------------------------
# балки 21 и крабы 14
# ----------------------------------------------------------------------------
def retainer_beam(x0):
    """Балка 21: PETG, сплошная 20×20, седло 6200 в верхней грани."""
    x1 = x0 + P["tube"]
    s = box(x0, P["ret_y0"], P["ret_z0"], x1, P["ret_y1"], P["ret_z1"])
    s = s.cut(cyl_x(P["bearing_groove_r"], x0 - 1, x1 + 1,
                    P["drive_y"], P["drive_z"]))
    # отверстия под винты M4 крабов (по одному с каждого конца)
    for y in (40.0, 160.0):
        s = s.cut(cyl_z(2.25, P["ret_z1"] - 10.0, P["ret_z1"] + 1,
                        x0 + 4.5, y))
    return s


def crab(side, front):
    """Стальной угловой краб 1,2 мм (по примеру), применённый в Т-узле.

    Пластина — на передней грани (x=0) или на грани со стороны виброотсека
    (x=180). Полки: вертикальная — по внутренней грани стойки, горизонтальная —
    на верхнюю грань балки 21. Горизонтальная полка винтом M4 подтягивает балку
    вверх, зажимая 6200.
    """
    t = P["crab_t"]
    x0 = -t if front else 180.0 - t
    x1 = 0.0 if front else 180.0
    fx0 = 0.0 if front else 180.0          # начало полок (внутрь рамы)
    fx1 = fx0 + 9.0
    xs = 4.5 if front else 184.5           # ось винта полки

    if side < 0:
        post = box(x0, 0, 130, x1, 20, 192)
        arm = box(x0, 0, 110, x1, 62, 130)
        hfl = box(fx0, 20, 130, fx1, 55.5, 131.2)
        vfl = box(fx0, 20, 130, fx1, 21.2, 139)
        y_screw, y_fl = 10.0, 40.0
    else:
        post = box(x0, 180, 130, x1, 200, 192)
        arm = box(x0, 138, 110, x1, 200, 130)
        hfl = box(fx0, 144.5, 130, fx1, 180, 131.2)
        vfl = box(fx0, 178.8, 130, fx1, 180, 139)
        y_screw, y_fl = 190.0, 160.0

    s = post.fuse(arm).fuse(hfl).fuse(vfl)
    # отверстия под винты крепления к стойке (2 шт.)
    for z in (140.0, 180.0):
        s = s.cut(cyl_x(2.25, x0 - 1, x1 + 1, y_screw, z))
    # отверстие под винт полки
    s = s.cut(cyl_z(2.25, P["ret_z1"] - 1, P["ret_z1"] + 2, xs, y_fl))
    return s


# ----------------------------------------------------------------------------
# подстолье, хомуты, крепёж
# ----------------------------------------------------------------------------
def podstol():
    s = box(P["podstol_x0"], P["podstol_y0"], P["podstol_z0"],
            P["podstol_x1"], P["podstol_y1"], P["podstol_z1"])
    # рёбра снизу по краям
    for y0 in (P["rib_y1"], P["rib_y3"]):
        s = s.fuse(box(P["rib_x0"], y0, P["podstol_z0"] - P["rib_h"],
                       P["rib_x1"], y0 + P["rib_w"], P["podstol_z0"]))
    for x in (215.0, 385.0):
        for y in (35.0, 165.0):
            s = s.cut(cyl_z(3.1, P["podstol_z0"] - 1, P["podstol_z1"] + 1, x, y))
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
        legs.append(cyl_z(P["ubolt_d"] / 2.0, z,
                          z + P["ubolt_leg"], xc, y))
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


def screw_m4_x(x0, x1, y, z, head_left=True):
    """Винт M4 вдоль X с головкой на конце x0 (head_left) или x1."""
    shank = cyl_x(2.0, min(x0, x1), max(x0, x1), y, z)
    if head_left:
        head = cyl_x(4.0, x0, x0 + 2.2, y, z)
    else:
        head = cyl_x(4.0, x1 - 2.2, x1, y, z)
    return shank.fuse(head)


def screw_m4_flange_z(x, y, z_head=219.0, z_end=None):
    """Винт M4 снизу фланца LMK в стол (головка под фланцем)."""
    z_end = P["table_z1"] if z_end is None else z_end
    shank = cyl_z(2.0, z_head, z_end, x, y)
    head = cyl_z(3.5, z_head - 1.5, z_head, x, y)
    return head.fuse(shank)


# ----------------------------------------------------------------------------
# сборка
# ----------------------------------------------------------------------------
def build_assembly(drill=False, draw=False):
    """Возвращает (parts, groups, cams)."""
    parts = {}

    def add(name, shape, material, qty, group, spec_no):
        parts[name] = dict(shape=shape, material=material, qty=qty,
                           group=group, spec_no=spec_no)

    add("frame", frame(), "petg", 1, "frame", "22")
    add("table", table(), "pla", 1, "table", "5")
    add("overlay", overlay(), "pla", 1, "overlay", "4")
    add("podstol", podstol(), "petg", 1, "table", "11")

    # валы, ограничители, пружины, шайбы
    sh, co, spr, wa = [], [], [], []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            sh.append(shaft(x, y))
            co.append(collar(x, y, P["shaft_z0"]))
            co.append(collar(x, y, P["shaft_z1"] - P["collar_t"]))
            spr.append(spring(x, y))
            wa.append(washer_z(x, y, P["overlay_z1"]))
            wa.append(washer_z(x, y, P["top_z0"] - P["spring_washer_t"]))
    add("shaft", concat(sh), "steel", 4, "steel", "2")
    add("collar", concat(co), "steel", 8, "steel", "1")
    add("spring", concat(spr), "steel", 4, "steel", "3")
    add("spring_washer", concat(wa), "steel", 8, "steel", "25")

    # линейные подшипники LMK10UU
    lm = [lmk10uu(x, y) for x in (P["guide_x1"], P["guide_x2"])
          for y in (P["guide_y1"], P["guide_y2"])]
    add("lmk", concat(lm), "bearing", 4, "bearing", "8")

    # привод
    add("drive_shaft", drive_shaft(), "steel", 1, "steel", "20")
    add("cam", cam(5.0), "pla", 1, "cam", "10")
    cam_parts = {"cam_3": cam(3.0), "cam_5": cam(5.0), "cam_10": cam(10.0)}

    br = [bearing_6200(P["bearing_x1"] - 4.5, P["bearing_x1"] + 4.5,
                       100, P["drive_z"]),
          bearing_6200(P["bearing_x2"] - 4.5, P["bearing_x2"] + 4.5,
                       100, P["drive_z"])]
    add("shaft_bearings", concat(br), "bearing", 2, "bearing", "9")

    # конусные гайки и контргайки на кулачке
    nuts = [conical_nut(84.0, 94.0, True), conical_nut(106.0, 116.0, False)]
    add("conical_nuts", concat(nuts), "steel", 2, "steel", "17")
    lns = [locknut(74.0, 84.0), locknut(116.0, 126.0)]
    add("locknuts", concat(lns), "steel", 2, "steel", "16")

    # ролик, ось, кронштейн
    rp = roller()
    add("roller", rp[0], "bearing", 1, "bearing", "9")
    add("axle", rp[1], "steel", 1, "steel", "7")
    add("roller_nuts", concat(rp[2:]), "steel", 4, "steel", "16/17")
    add("bracket", concat([bracket(-1), bracket(1)]), "steel", 2, "steel", "6")

    # балки 21 и крабы
    add("retainer", concat([retainer_beam(0.0), retainer_beam(180.0)]),
        "petg", 2, "retainer", "21")
    cr = [crab(-1, True), crab(1, True), crab(-1, False), crab(1, False)]
    add("crabs", concat(cr), "steel", 4, "crabs", "14")

    # U-хомуты и их гайки
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

    # крепёж подстолья M6 (в резьбовые вставки)
    pod = []
    for x in (215.0, 385.0):
        for y in (35.0, 165.0):
            pod.append(bolt_m6_z(x, y, P["podstol_z1"], 180.0))
    add("podstol_bolts", concat(pod), "steel", 4, "steel", "18")

    # крепёж фланцев LMK10UU (16 шт. M4)
    fl = []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            for dx in (-16.0, 16.0):
                for dy in (-16.0, 16.0):
                    fl.append(screw_m4_flange_z(x + dx, y + dy))
    add("flange_screws", concat(fl), "steel", 16, "steel", "23")

    # крепёж накладки (4 угла) и кронштейнов (2)
    st, tn = [], []
    for x in (P["table_x0"] + P["overlay_inset"],
              P["table_x1"] - P["overlay_inset"]):
        for y in (P["table_y0"] + P["overlay_inset"],
                  P["table_y1"] - P["overlay_inset"]):
            st.append(screw_m4_z(x, y, 221.8, P["overlay_z1"],
                                 countersunk=True, head_top=P["overlay_z1"]))
            tn.append(hex_nut_z(x, y, 221.8, af=7, h=3.2, d=4.4))
    for x in (65.0, 135.0):
        st.append(screw_m4_z(x, 100, 219.8, P["table_z1"],
                             countersunk=True, head_top=P["table_z1"]))
        tn.append(hex_nut_z(x, 100, 219.8, af=7, h=3.2, d=4.4))
    add("table_screws", concat(st), "steel", 6, "steel", "13")
    add("table_nuts", concat(tn), "steel", 6, "steel", "15")

    # крепёж крабов: 2 винта в стойку + 1 в балку 21 на каждый краб
    cb = []
    for side, front in ((-1, True), (1, True), (-1, False), (1, False)):
        ys = 10.0 if side < 0 else 190.0
        yf = 40.0 if side < 0 else 160.0
        if front:
            for z in (140.0, 180.0):
                cb.append(screw_m4_x(-3.4, 10.0, ys, z, head_left=True))
            cb.append(screw_m4_z(4.5, yf, 133.2, 120.0))
        else:
            for z in (140.0, 180.0):
                cb.append(screw_m4_x(176.6, 190.0, ys, z, head_left=True))
            cb.append(screw_m4_z(184.5, yf, 133.2, 120.0))
    add("crab_screws", concat(cb), "steel", 12, "crabs", "24")

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
