"""Параметрическая модель вибростола, этап fix3 (FreeCAD Part).

Оси: X — вдоль 360 (виброотсек 0…160, вынос 160…360),
     Y — поперёк 200, Z — вверх 300.
Стол вытянут по X: −20…180, по Y: 25…175.

Ключевые решения fix1:
  * рама — PETG, сплошное сечение 20×20, печать одним куском;
  * убраны средние боковые балки, центральная балка с окном и задняя
    нижняя поперечина;
  * 6200 зажаты между средней поперечиной и балкой 21 (поз. 21);
  * стол/накладка/подстолье — печать; накладка крепится 4 угловыми M4;
  * LMK10UU (квадратный фланец 40×40) вместо LMF10UU;
  * ограничители WCS10FR Ø30.

Ключевые решения fix2:
  * карманы 6200 шириной 9,4 мм только в центральной части поперечин и
    балок 21 — осевая фиксация наружного кольца;
  * конусные гайки и контргайки с обеих сторон каждого 6200 на валу;
  * подстолье развёрнуто на 90°, крепление M6 через верхние балки.

Ключевые решения fix3:
  * виброотсек 160 мм (было 200): рама 360×200×300, валы X=10/150,
    стол 200×150, вал привода X=−10…215, кулачок по центру X=74…86;
  * в выносе нет поперечин: только 2 верхние продольные балки 140…360,
    жёсткость даёт подстолье;
  * балка 21 крепится 8 плоскими Γ-образными накладками 2 мм: горизон­
    тальная полка 60×20 ложится на боковую грань балки и стягивается с ней
    2 болтами M4 насквозь, вертикальная полка идёт вниз по стойке и имеет
    2 паза 20 мм под прижимные болты M4, стягивающие пару накладок;
  * подстолье без рёбер, болты M6×45 с обычной головкой сверху;
  * кулачок: конический бортик ложбинки (самоцентровка ролика), фаска
    1×45° на отверстии, 8 отверстий Ø10 на R32 для облегчения;
  * отверстия под валы: стол Ø11, накладка Ø12.
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
      * 4 стойки виброотсека (0…160), 2 стойки выноса;
      * верхний пояс виброотсека (2 продольные + 2 поперечины);
      * 2 средние поперечины (боковых продольных балок нет);
      * нижний пояс виброотсека + вынос;
      * верхние продольные балки выноса 140…360 (fix3: поперечин в выносе
        нет, жёсткость даёт подстолье; балки опираются на граничную
        поперечину 140…160 по плоскости Z=170 и входят в стойки).
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

    # средние поперечины (только по Y): передняя 0…20 и граничная 140…160
    solids.append(box(0, 0, P["mid_z0"], T, W, P["mid_z1"]))
    solids.append(box(Lv - T, 0, P["mid_z0"], Lv, W, P["mid_z1"]))

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

    # fix3: верхние продольные балки выноса без поперечин; начинаются от
    # граничной поперечины (Lv−T) и проходят через стойки выноса
    for y in (0.0, W - T):
        solids.append(box(Lv - T, y, P["ext_top_z0"], L, y + T,
                          P["ext_top_z1"]))

    s = concat(solids)

    # ---- отверстия и сёдла ----
    holes = []
    # отверстия направляющих валов в верхних и средних поперечинах
    for gx in (P["guide_x1"], P["guide_x2"]):
        for gy in (P["guide_y1"], P["guide_y2"]):
            holes.append(cyl_z(P["guide_hole_d"] / 2.0, P["top_z0"] - 1,
                               P["top_z1"] + 1, gx, gy))
            holes.append(cyl_z(P["guide_hole_d"] / 2.0, P["mid_z0"] - 1,
                               P["mid_z1"] + 1, gx, gy))
    # карманы 6200 в нижней грани средних поперечин: только центральная
    # часть шириной 9,4 мм, плечи 5,3 мм — осевая фиксация наружного кольца
    pw = P["bearing_pocket_w"]
    for x0, bx in ((0.0, P["bearing_x1"]), (Lv - T, P["bearing_x2"])):
        holes.append(cyl_x(P["bearing_groove_r"], bx - pw / 2.0,
                           bx + pw / 2.0, P["drive_y"], P["drive_z"]))
    # fix3: отверстия M4 под прижимные болты накладок балки 21 — по два на
    # каждую пару (Z=61 и 87); в накладках под них вертикальные пазы 20 мм
    for xface in (0.0, Lv - T):
        for y in (10.0, W - 10.0):
            for z in (P["crab_clamp_z1"], P["crab_clamp_z2"]):
                holes.append(cyl_x(2.25, xface - 1, xface + T + 1, y, z))
    # отверстия M6 под болты подстолья в верхних продольных балках выноса
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            holes.append(cyl_z(3.1, P["ext_top_z0"] - 1, P["ext_top_z1"] + 1,
                               x, y))

    for h in holes:
        s = s.cut(h)
    return s.removeSplitter()


# ----------------------------------------------------------------------------
# стол, накладка
# ----------------------------------------------------------------------------
def table():
    s = box(P["table_x0"], P["table_y0"], P["table_z0"],
            P["table_x1"], P["table_y1"], P["table_z1"])
    # fix3: отверстия под валы Ø11 (вал Ø10 + 1) и крепёж фланцев LMK
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(P["table_hole_d"] / 2.0, P["table_z0"] - 1,
                            P["table_z1"] + 1, x, y))
            for dx in (-16.0, 16.0):
                for dy in (-16.0, 16.0):
                    s = s.cut(cyl_z(2.1, P["table_z0"] - 1, P["table_z1"] + 1,
                                    x + dx, y + dy))
    # пазы под M4 кронштейнов ролика + зенковка
    for x in (P["bracket_slot_x1"], P["bracket_slot_x2"]):
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
    cx = (P["table_x0"] + P["table_x1"]) / 2.0
    cz = P["overlay_z1"] - P["dish_depth"] + R
    s = s.cut(Part.makeSphere(R, V(cx, 100, cz)))
    # fix3: отверстия под валы Ø12 (вал Ø10 + 2)
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            s = s.cut(cyl_z(P["overlay_hole_d"] / 2.0, P["overlay_z0"] - 1,
                            P["overlay_z1"] + 1, x, y))
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
    """Эксцентриковый диск; stroke — ход ролика (3/5/10 мм).

    fix3: бортик ложбинки — конус от r_work (у ложбинки) до r_flange (на
    торце) вместо прямого: ролик самоцентрируется, деталь печатается без
    поддержек. В отверстии — фаска 1×45° с обоих торцов под конусную гайку.
    Для облегчения — 8 отверстий Ø10 на R32.
    """
    ecc = stroke / 2.0
    r_work = 45.0 + ecc
    r_flange = r_work + 2.0
    cy, cz = P["drive_y"], P["drive_z"] + ecc
    gx0, gx1 = P["cam_x0"], P["cam_x1"]
    gw = P["cam_groove_w"]
    ft = (gx1 - gx0 - gw) / 2.0
    core = Part.makeCylinder(r_work, gw, V(gx0 + ft, cy, cz), V(1, 0, 0))
    # скошенные бортики: r_work у ложбинки -> r_flange на торце
    left = Part.makeCone(r_work, r_flange, ft, V(gx0 + ft, cy, cz),
                         V(-1, 0, 0))
    right = Part.makeCone(r_work, r_flange, ft, V(gx1 - ft, cy, cz),
                          V(1, 0, 0))
    s = core.fuse(left).fuse(right)
    s = s.cut(cyl_x(5.1, gx0 - 1, gx1 + 1, cy, P["drive_z"]))
    # фаска 1×45° с обоих торцов отверстия
    ch = P["cam_chamfer"]
    s = s.cut(Part.makeCone(5.1 + ch, 5.1, ch,
                            V(gx0, cy, P["drive_z"]), V(1, 0, 0)))
    s = s.cut(Part.makeCone(5.1 + ch, 5.1, ch,
                            V(gx1, cy, P["drive_z"]), V(-1, 0, 0)))
    # 8 отверстий облегчения по радиусу R32
    n = int(P["cam_hole_n"])
    hr = P["cam_hole_d"] / 2.0
    rr = P["cam_hole_r"]
    for i in range(n):
        a = 2.0 * math.pi * i / n
        s = s.cut(cyl_x(hr, gx0 - 1, gx1 + 1,
                        cy + rr * math.cos(a), cz + rr * math.sin(a)))
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
    """Кронштейн ролика — уголок 40×40×20×2; side=-1 левый, +1 правый.

    fix3: кулачок переехал в X=74…86, поэтому стойки кронштейна стоят
    в X=68…70 и 90…92, полки — 28…68 и 92…130.
    """
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
    # паз под M4
    s = s.cut(box(xm - 5, 97.75, z_top - t - 1, xm + 5, 102.25, z_top + 1))
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
# балка 21 и уголки 14
# ----------------------------------------------------------------------------
def retainer_beam(x0):
    """Балка 21: PETG, сплошная 20×20, карман 6200 в верхней грани.

    Карман только в центральной части (ширина 9,4 мм) — наружное кольцо
    6200 фиксируется и в осевом направлении. fix3: балка в распор между
    стойками (Y=20,2…179,8), без винтов снизу — её держат уголки.
    """
    x1 = x0 + P["tube"]
    bx = P["bearing_x1"] if abs(x0) < 1e-6 else P["bearing_x2"]
    s = box(x0, P["ret_y0"], P["ret_z0"], x1, P["ret_y1"], P["ret_z1"])
    pw = P["bearing_pocket_w"]
    s = s.cut(cyl_x(P["bearing_groove_r"], bx - pw / 2.0, bx + pw / 2.0,
                    P["drive_y"], P["drive_z"]))
    # fix3: сквозные отверстия M4 под болты накладок (крепление сбоку)
    for y in (P["crab_beam_bolt_y1"], P["crab_beam_bolt_y2"],
              P["W_frame"] - P["crab_beam_bolt_y1"],
              P["W_frame"] - P["crab_beam_bolt_y2"]):
        s = s.cut(cyl_x(2.25, x0 - 1, x1 + 1, y, P["crab_beam_bolt_z"]))
    return s


def angle_bracket(side, rear_beam, xb_face):
    """Плоская Γ-образная накладка (уголок) крепления балки 21 (fix3).

    side      — -1: стойка Y=0…20, +1: стойка Y=180…200;
    rear_beam — False: балка X=0…20, True: балка X=140…160;
    xb_face   — False: накладка на передней (по X) грани, True: на задней.

    Накладка — сталь 2 мм, полки шириной 20 мм, длина 60 мм:
      * горизонтальная полка 60×20 лежит на боковой грани балки 21
        (Z=110…130, не выходит за её габарит) и стягивается с балкой
        2 болтами M4 насквозь — жёсткое крепление;
      * вертикальная полка 20×80 идёт вниз по стойке (Z=50…130) и имеет
        два вертикальных паза 20 мм под прижимные болты M4, которыми пара
        накладок (передняя + задняя) обжимает стойку с двух сторон.
    Нижней полки под балкой нет. При ослаблении болтов накладки вместе с
    балкой опускаются на 15 мм, освобождая кольцо 6200.
    """
    t = P["crab_t"]
    arm = P["crab_arm"]
    w = P["crab_w"]
    zt = P["crab_z_top"]
    zb = P["crab_z_beam"]
    zbot = P["crab_z_bot"]

    T = P["tube"]
    xa = 0.0 if not rear_beam else P["L_vibro"] - T
    xb = xa + T

    if not xb_face:
        lx0, lx1 = xa - t, xa
    else:
        lx0, lx1 = xb, xb + t

    if side < 0:
        vert_y0, vert_y1 = 0.0, w
        hor_y0, hor_y1 = w, w + arm
        ys = 10.0
        by = (P["crab_beam_bolt_y1"], P["crab_beam_bolt_y2"])
    else:
        vert_y0, vert_y1 = P["W_frame"] - w, P["W_frame"]
        hor_y0, hor_y1 = P["W_frame"] - w - arm, P["W_frame"] - w
        ys = P["W_frame"] - 10.0
        by = (P["W_frame"] - P["crab_beam_bolt_y1"],
              P["W_frame"] - P["crab_beam_bolt_y2"])

    # вертикальная полка по стойке вниз + горизонтальная полка по балке
    vert = box(lx0, vert_y0, zbot, lx1, vert_y1, zt)
    hor = box(lx0, hor_y0, zb, lx1, hor_y1, zt)
    s = vert.fuse(hor)

    # два паза 20 мм под прижимные болты M4 (стяжка пары через стойку)
    for z0 in (P["crab_slot_z1"], P["crab_slot_z2"]):
        s = s.cut(box(lx0 - 1, ys - 2.5, z0, lx1 + 1, ys + 2.5,
                      z0 + P["crab_slot_h"]))
    # два отверстия Ø4,5 под болты крепления к балке
    for y in by:
        s = s.cut(cyl_x(2.25, lx0 - 1, lx1 + 1, y, P["crab_beam_bolt_z"]))
    return s


# ----------------------------------------------------------------------------
# подстолье, хомуты, крепёж
# ----------------------------------------------------------------------------
def podstol():
    """Подстолье PETG 160×200×12 (fix3: без рёбер)."""
    s = box(P["podstol_x0"], P["podstol_y0"], P["podstol_z0"],
            P["podstol_x1"], P["podstol_y1"], P["podstol_z1"])
    # fix3: обычные болты M6 с головкой сверху — без зенковки
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            s = s.cut(cyl_z(3.1, P["podstol_z0"] - 1,
                            P["podstol_z1"] + 1, x, y))
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


def screw_m4_z(x, y, z_head, z_end, countersunk=False, head_top=None):
    shank = cyl_z(2.0, min(z_head, z_end), max(z_head, z_end), x, y)
    if countersunk:
        top = head_top if head_top is not None else z_head + 2.5
        head = Part.makeCone(4.0, 2.0, 2.5, V(x, y, top), V(0, 0, -1))
        return shank.fuse(head)
    head = cyl_z(3.5, z_head - 1.8, z_head, x, y)
    return shank.fuse(head)


def screw_m4_flange_z(x, y, z_head=219.0, z_end=None):
    """Винт M4 снизу фланца LMK в стол (головка под фланцем)."""
    z_end = P["table_z1"] if z_end is None else z_end
    shank = cyl_z(2.0, z_head, z_end, x, y)
    head = cyl_z(3.5, z_head - 1.5, z_head, x, y)
    return head.fuse(shank)


def angle_bolt(side, rear_beam):
    """Прижимные болты M4 стяжки пары накладок через стойку (вдоль X).

    Возвращает (болты, гайки).
    """
    T = P["tube"]
    t = P["crab_t"]
    xa = 0.0 if not rear_beam else P["L_vibro"] - T
    xb = xa + T
    x_out = xa - t
    x_in = xb + t
    y = 10.0 if side < 0 else P["W_frame"] - 10.0
    bolts, nuts = [], []
    for z in (P["crab_clamp_z1"], P["crab_clamp_z2"]):
        shank = cyl_x(2.0, x_out - 2.5, x_in + 4.2, y, z)
        head = cyl_x(3.8, x_out - 2.5, x_out, y, z)
        nut = hex_prism_x(7.0, x_in, x_in + 3.2, y, z)
        nut = nut.cut(cyl_x(2.1, x_in - 1, x_in + 4, y, z))
        bolts.append(shank.fuse(head))
        nuts.append(nut)
    return bolts, nuts


def beam_bolt(side, rear_beam):
    """Болты M4 крепления накладок к балке 21 насквозь (вдоль X).

    Возвращает (болты, гайки).
    """
    T = P["tube"]
    t = P["crab_t"]
    xa = 0.0 if not rear_beam else P["L_vibro"] - T
    xb = xa + T
    x_out = xa - t
    x_in = xb + t
    z = P["crab_beam_bolt_z"]
    if side < 0:
        ys = (P["crab_beam_bolt_y1"], P["crab_beam_bolt_y2"])
    else:
        ys = (P["W_frame"] - P["crab_beam_bolt_y1"],
              P["W_frame"] - P["crab_beam_bolt_y2"])
    bolts, nuts = [], []
    for y in ys:
        shank = cyl_x(2.0, x_out - 2.5, x_in + 4.2, y, z)
        head = cyl_x(3.8, x_out - 2.5, x_out, y, z)
        nut = hex_prism_x(7.0, x_in, x_in + 3.2, y, z)
        nut = nut.cut(cyl_x(2.1, x_in - 1, x_in + 4, y, z))
        bolts.append(shank.fuse(head))
        nuts.append(nut)
    return bolts, nuts


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

    # конусные гайки и контргайки на кулачке (X=74…86)
    cx = P["cam_axis_x"]
    nuts = [conical_nut(cx - 14.0, cx - 6.0, True),
            conical_nut(cx + 6.0, cx + 14.0, False)]
    add("conical_nuts", concat(nuts), "steel", 2, "steel", "17")
    lns = [locknut(cx - 22.0, cx - 14.0), locknut(cx + 14.0, cx + 22.0)]
    add("locknuts", concat(lns), "steel", 2, "steel", "16")

    # осевая фиксация вала в опорных 6200 — по 2 конусные гайки
    # и по 2 контргайки на каждый подшипник
    nl = P["shaft_fix_nut_len"]
    b1, b2 = P["bearing_x1"], P["bearing_x2"]
    sh_con = [
        conical_nut(b1 - 10.0, b1 - 4.5, True),                   # 6200 №1, слева
        conical_nut(b1 + 4.5, b1 + 4.5 + nl, False),              # 6200 №1, справа
        conical_nut(b2 - 10.0, b2 - 4.5, True),                   # 6200 №2, слева
        conical_nut(b2 + 4.5, b2 + 4.5 + nl, False),              # 6200 №2, справа
    ]
    add("shaft_conical_nuts", concat(sh_con), "steel", 4, "steel", "17")
    sh_ln = [
        locknut(b1 - 4.5 - nl - P["shaft_lock_w"], b1 - 4.5 - nl),
        locknut(b1 + 4.5 + nl, b1 + 4.5 + nl + P["shaft_lock_w"]),
        locknut(b2 - 4.5 - P["shaft_lock_w"], b2 - 4.5),
        locknut(b2 + 4.5 + nl, b2 + 4.5 + nl + P["shaft_lock_w"]),
    ]
    add("shaft_locknuts", concat(sh_ln), "steel", 4, "steel", "16")

    # ролик, ось, кронштейн
    rp = roller()
    add("roller", rp[0], "bearing", 1, "bearing", "9")
    add("axle", rp[1], "steel", 1, "steel", "7")
    add("roller_nuts", concat(rp[2:]), "steel", 4, "steel", "16/17")
    add("bracket", concat([bracket(-1), bracket(1)]), "steel", 2, "steel", "6")

    # балки 21 и уголки
    add("retainer", concat([retainer_beam(0.0),
                            retainer_beam(P["L_vibro"] - P["tube"])]),
        "petg", 2, "retainer", "21")
    ab = [angle_bracket(side, rear, face)
          for rear in (False, True)
          for side in (-1, 1)
          for face in (False, True)]
    add("angles", concat(ab), "steel", 8, "angles", "14")

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

    # fix3: болты подстолья M6×45 с обычной головкой сверху, гайка и
    # шайба снизу верхней продольной балки
    pod, pod_nuts = [], []
    z_end = P["ext_top_z0"] - 6.6          # 163,4 — под шайбу и гайку
    for x in (P["podstol_bolt_x1"], P["podstol_bolt_x2"]):
        for y in (P["podstol_bolt_y1"], P["podstol_bolt_y2"]):
            pod.append(bolt_m6_z(x, y, P["podstol_z1"], z_end))
            pod_nuts.append(washers_and_nut(x, y, z_end))
    add("podstol_bolts", concat(pod), "steel", 4, "steel", "18")
    add("podstol_nuts", concat(pod_nuts), "steel", 4, "steel", "27")

    # крепёж фланцев LMK10UU (16 шт. M4)
    fl = []
    for x in (P["guide_x1"], P["guide_x2"]):
        for y in (P["guide_y1"], P["guide_y2"]):
            for dx in (-16.0, 16.0):
                for dy in (-16.0, 16.0):
                    fl.append(screw_m4_flange_z(x + dx, y + dy))
    add("flange_screws", concat(fl), "steel", 16, "steel", "23")

    # крепёж накладки (4 угла) и кронштейнов ролика (2)
    st, tn = [], []
    for x in (P["table_x0"] + P["overlay_inset"],
              P["table_x1"] - P["overlay_inset"]):
        for y in (P["table_y0"] + P["overlay_inset"],
                  P["table_y1"] - P["overlay_inset"]):
            st.append(screw_m4_z(x, y, 221.8, P["overlay_z1"],
                                 countersunk=True, head_top=P["overlay_z1"]))
            tn.append(hex_nut_z(x, y, 221.8, af=7, h=3.2, d=4.4))
    for x in (P["bracket_slot_x1"], P["bracket_slot_x2"]):
        st.append(screw_m4_z(x, 100, 219.8, P["table_z1"],
                             countersunk=True, head_top=P["table_z1"]))
        tn.append(hex_nut_z(x, 100, 219.8, af=7, h=3.2, d=4.4))
    add("table_screws", concat(st), "steel", 6, "steel", "13")
    add("table_nuts", concat(tn), "steel", 6, "steel", "15")

    # крепёж накладок: прижимные болты M4 стяжки стоек (по 2 на пару) и
    # болты M4 крепления накладок к балке (по 2 на конец)
    cb, cn, bb, bn = [], [], [], []
    for rear in (False, True):
        for side in (-1, 1):
            b1, n1 = angle_bolt(side, rear)
            cb.extend(b1)
            cn.extend(n1)
            b2, n2 = beam_bolt(side, rear)
            bb.extend(b2)
            bn.extend(n2)
    add("clamp_bolts", concat(cb), "steel", 8, "angles", "24")
    add("clamp_nuts", concat(cn), "steel", 8, "angles", "24")
    add("beam_bolts", concat(bb), "steel", 8, "angles", "24")
    add("beam_nuts", concat(bn), "steel", 8, "angles", "24")

    groups = {}
    for key, info in parts.items():
        groups.setdefault(info["group"], []).append(info["shape"])

    return parts, groups, cam_parts


def washers_and_nut(x, y, z0):
    w = washer_z(x, y, z0, od=12.0, d=6.5, t=1.6)
    n = hex_nut_z(x, y, z0 + 1.6, af=10, h=P["podstol_nut_h"])
    return w.fuse(n)


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
