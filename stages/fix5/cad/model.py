"""Параметрическая модель вибростола, этап fix4 (FreeCAD Part).

Оси: X — вдоль 360 (виброотсек 0…160, вынос 160…360),
     Y — поперёк 200, Z — вверх 300.
Стол вытянут по X: −20…180, по Y: 25…175.

Ключевые решения fix4 (по замечаниям README этапа):
  * кулачок симметричный — 2 максимума и 2 минимума, r(θ)=r0+e·cos2θ;
    отверстия облегчения — по одному на каждом лепестке (на радиусах
    максимумов и минимумов), 4×Ø12;
  * кожух из поликарбоната 5 мм: 2 боковые панели, 4 внутренних и 2
    наружных бортика вниз до Z=246 (верх стола 241 + 5); вынос не закрыт;
    крепление — саморезы M4 с прижимной шляпкой;
  * фиксация кулачка — буртик вала + контактная шайба Ø70 с насечками +
    гайка + контргайка; фаска отверстия кулачка убрана, на торце —
    8 радиальных насечек 3×30×0,5 мм;
  * в углах верхних балок — 8 резиновых буферов (по 2 на пружину) с
    зазором 5 мм до пружины и 3 мм до верхней точки стола;
  * на направляющих валах под LMK — 4 резиновых кольца с зазором 3 мм
    до нижней границы хода стола;
  * кулачок, вал и 6200 — общий блок (картридж), сменяемый при отжатых
    прижимных балках.

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
    "pc": 1.20e-3,         # поликарбонат
    "rubber": 1.15e-3,     # EPDM/NBR
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


def cyl_axis(r, x, y, z, dx, dy, dz, length):
    """Цилиндр от точки (x,y,z) вдоль единичного вектора (dx,dy,dz)."""
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
    """Объединение списка тел (без падения на пустом списке)."""
    if not shapes:
        return None
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()


def gusset_xy(x0, y0, sx, sy, z0, z1, r):
    """Вогнутая галтель R в плоскости XY у внутреннего угла (x0,y0)."""
    x1, y1 = x0 + sx * r, y0 + sy * r
    return box(x0, y0, z0, x1, y1, z1).cut(cyl_z(r, z0 - 1, z1 + 1, x1, y1))


def gusset_yz(y0, z0, sy, sz, x0, x1, r):
    """Вогнутая галтель R в плоскости YZ у внутреннего угла (y0,z0)."""
    y1, z1 = y0 + sy * r, z0 + sz * r
    return box(x0, y0, z0, x1, y1, z1).cut(
        cyl_x(r, x0 - 1, x1 + 1, y1, z1))


def gusset_xz(x0, z0, sx, sz, y0, y1, r):
    """Вогнутая галтель R в плоскости XZ у внутреннего угла (x0,z0)."""
    x1, z1 = x0 + sx * r, z0 + sz * r
    return box(x0, y0, z0, x1, y1, z1).cut(
        cyl_y(r, y0 - 1, y1 + 1, x1, z1))


def frame_gussets():
    """26 вогнутых галтелей R10 в свободных стыках рамы (fix5 п.7).

    Добавлены:
      * 4 нижних угла нижнего пояса (XY, Z=0…20);
      * 8 стыков средних поперечин со стойками (YZ, Z=140…150 и 170…180);
      * 8 стыков верхних/нижних поперечин со стойками (XZ, Z=270…280 и
        20…30);
      * 6 в балках выноса (верх у X=160, верх/низ у задних стоек).
    Не добавлены в верхних внутренних углах (X=20/140, Y=20/180): там
    стоят бортики кожуха и резиновые буферы; это и есть исключение п. 7.
    """
    r = P["frame_fillet_r"]
    Lv = P["L_vibro"]
    T = P["tube"]
    out = []
    # нижний пояс: 4 внутренних угла
    for x0, sx in ((T, +1), (Lv - T, -1)):
        for y0, sy in ((T, +1), (P["W_frame"] - T, -1)):
            out.append(gusset_xy(x0, y0, sx, sy, 0.0, P["base_h"], r))
    # средние поперечины — стойки: верх/низ балки, обе стороны
    for x0, x1 in ((0.0, T), (Lv - T, Lv)):
        for y0, sy in ((T, +1), (P["W_frame"] - T, -1)):
            out.append(gusset_yz(y0, P["mid_z1"], sy, +1, x0, x1, r))
            out.append(gusset_yz(y0, P["mid_z0"], sy, -1, x0, x1, r))
    # верхние/нижние поперечины — стойки (внутренние грани X)
    for x0, sx in ((T, +1), (Lv - T, -1)):
        for y0, y1 in ((0.0, T), (P["W_frame"] - T, P["W_frame"])):
            out.append(gusset_xz(x0, P["top_z0"], sx, -1, y0, y1, r))
            out.append(gusset_xz(x0, P["base_h"], sx, +1, y0, y1, r))
    # fix5 п. 7: 6 галтелей внутри балок выноса
    L = P["L_frame"]
    ext = [
        # верхние продольные балки — граничная поперечина (X=160…170)
        (Lv, P["ext_top_z0"], +1, -1),
        # верхние продольные балки — задние стойки (X=330…340)
        (L - T, P["ext_top_z0"], -1, -1),
        # нижние продольные балки — задние стойки (X=330…340)
        (L - T, P["base_h"], -1, +1),
    ]
    for x0, z0, sx, sz in ext:
        for y0, y1 in ((0.0, T), (P["W_frame"] - T, P["W_frame"])):
            out.append(gusset_xz(x0, z0, sx, sz, y0, y1, r))
    return out


# ----------------------------------------------------------------------------
# кожух: точки саморезов
# ----------------------------------------------------------------------------
def shield_screw_layout():
    """Список (hx, hy, hz, dx, dy, dz, t) — шляпка самореза на наружной
    поверхности панели, ось (dx,dy,dz) направлена в раму.

    t — толщина панели; шляпка стоит на её наружной поверхности. Точки
    используются одновременно для отверстий в поликарбонате, пилотов в
    PETG и тел саморезов — единый источник истины.
    """
    t = P["shield_t"]
    out = []

    # боковые панели (Y=-5…0 и 200…205): 8 точек на сторону
    for yface, sy in ((-t, +1.0), (P["W_frame"] + t, -1.0)):
        for x in (10.0, 80.0, 150.0):
            out.append((x, yface, 15.0, 0.0, sy, 0.0, t))
            out.append((x, yface, 285.0, 0.0, sy, 0.0, t))
        for z in (80.0, 200.0):
            out.append((10.0, yface, z, 0.0, sy, 0.0, t))

    # наружные бортики: 3 точки на каждый
    for y in (40.0, 100.0, 160.0):
        out.append((-t, y, 285.0, +1.0, 0.0, 0.0, t))
        out.append((P["L_vibro"] + t, y, 285.0, -1.0, 0.0, 0.0, t))
    return out


def _points_for(sel):
    return [p for p in shield_screw_layout() if sel(p)]


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

    # fix4 п.7: вогнутые галтели R10 в свободных стыках (20 шт.)
    solids.extend(frame_gussets())

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
    # fix4: пилоты Ø3,5 под саморезы кожуха; точка — на поверхности рамы,
    # отверстие уходит в PETG на 10 мм
    for (hx, hy, hz, dx, dy, dz, t) in shield_screw_layout():
        fx, fy, fz = hx + dx * t, hy + dy * t, hz + dz * t
        holes.append(cyl_axis(P["shield_pilot_d"] / 2.0,
                              fx - dx * 0.5, fy - dy * 0.5, fz - dz * 0.5,
                              dx, dy, dz, 11.0))

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
def cam_radius(theta, stroke):
    """Радиус симметричного двухлепесткового кулачка.

    r(θ) = r0 + e·cos2(θ−π/2), где r0 = 50 − s/2, e = s/2.
    При θ=90° — максимум (50 мм, контакт с роликом), при 0/180° — минимум
    (50−s). Такая функция даёт r(θ)=r(θ+π): 2 максимума и 2 минимума.
    """
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


def _radial_notch(x_face, r0, r1, width, depth, angle):
    """Радиальная насечка на торце кулачка (глубина — вдоль −X)."""
    b = Part.makeBox(depth, r1 - r0, width,
                     V(x_face - depth, r0, -width / 2.0))
    b.rotate(V(0, 0, 0), V(1, 0, 0), math.degrees(angle))
    b.translate(V(0, P["drive_y"], P["drive_z"]))
    return b


def cam(stroke):
    """Симметричный кулачок fix5: 2 лепестка, буртик Ø40×10, гайка M10.

    Профиль r(θ)=r0+e·cos2θ (r0=50−s/2, e=s/2); верх стола 241 мм для
    дисков 3/5/10, ход вниз. Ложбинка 9,5 мм с коническими бортиками.
    Центральное отверстие — шестигранник 17,1 мм под гайку M10 (п. 1);
    на левом торце — буртик Ø40×10 мм (п. 2), чтобы сварка не мешала
    затяжке. Радиальных насечек нет ни на буртике, ни на другом торце.
    Облегчение — 8×Ø10 на R32: 2 на максимумах (90/270), 2 на минимумах
    (0/180), 4 между (45/135/225/315) — п. 5.
    """
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
    # буртик Ø40×10 на левом торце (X=64…74)
    boss = cyl_x(P["cam_boss_d"] / 2.0, P["cam_boss_x0"],
                 P["cam_boss_x1"], cy, cz)
    s = s.fuse(boss)
    # центральный шестигранник 17,1 AF под гайку M10
    s = s.cut(hex_prism_x(P["cam_hex_af"], P["cam_boss_x0"] - 1,
                          gx1 + 1, cy, cz))
    # 8 отверстий Ø10 на R32: 2 макс, 2 мин, 4 между
    hr = P["cam_hole_d"] / 2.0
    rr = P["cam_hole_r"]
    for i in range(8):
        a = math.radians(45.0 * i)
        s = s.cut(cyl_x(hr, gx0 - 1, gx1 + 1,
                        cy + rr * math.cos(a), cz + rr * math.sin(a)))
    return s.removeSplitter()


def cam_washer(x0, x1):
    """Гладкая стальная шайба кулачка Ø40/Ø10,5 (fix5 п. 4)."""
    s = cyl_x(P["cam_washer_od"] / 2.0, x0, x1, P["drive_y"],
              P["drive_z"])
    return s.cut(cyl_x(P["cam_washer_id"] / 2.0, x0 - 1, x1 + 1,
                       P["drive_y"], P["drive_z"]))


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
    """Шпилька Ø10 с приваренной гайкой M10 под кулачок (fix5 п. 3).

    Вал Ø10, X=−10…215. В месте кулачка (X=74…82) — шестигранник 17 AF,
    изображающий гайку M10, приваренную к шпильке. Кулачок садится на неё
    своим шестигранным отверстием 17,1 AF; гайка передаёт момент. Осевое
    положение задают шайбы и гайки с двух сторон (п. 4).
    """
    s = cyl_x(P["shaft_d"] / 2.0, P["shaft_x0"], P["shaft_x1"],
              100, P["drive_z"])
    nut = hex_prism_x(P["weld_nut_af"], P["weld_nut_x0"],
                      P["weld_nut_x1"], 100, P["drive_z"])
    return s.fuse(nut).removeSplitter()


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
# кожух, резиновые буферы и кольца (fix5 п.2, п.4…п.8)
# ----------------------------------------------------------------------------
def _shield_plate(x0, y0, z0, x1, y1, z1, sel):
    s = box(x0, y0, z0, x1, y1, z1)
    for (hx, hy, hz, dx, dy, dz, t) in _points_for(sel):
        s = s.cut(cyl_axis(2.2, hx - dx * 0.5, hy - dy * 0.5,
                           hz - dz * 0.5, dx, dy, dz, t + 1.0))
    return s


def shield_parts():
    """Поликарбонат 5 мм: 2 боковые панели + 2 наружных бортика.

    Боковые панели Y=−5…0 и 200…205, X=0…160, Z=0…300 — закрывают бока
    виброотсека от нижней балки до верхней. Наружные бортики X=−5…0 и
    160…165 идут вниз до Z=246 и закрывают большую часть пружин.
    Внутренних бортиков нет (fix5 п. 8): от закатывания шарика страхуют
    резиновые ограничители в углах. Вынос X>165 не закрыт.
    Крепление — саморезы с прижимной шляпкой (отверстия Ø4,4).
    """
    t = P["shield_t"]
    Lv = P["L_vibro"]
    W = P["W_frame"]
    zt = P["table_top_max"] + P["shield_skirt_gap"]     # 246
    plates = [
        # боковые панели (большой кожух)
        _shield_plate(0, -t, 0, Lv, 0, P["top_z1"],
                      lambda p: abs(p[1] + t) < 1e-6),
        _shield_plate(0, W, 0, Lv, W + t, P["top_z1"],
                      lambda p: abs(p[1] - (W + t)) < 1e-6),
        # наружные бортики (2 стороны, закрывают пружины)
        _shield_plate(-t, 0, zt, 0, W, P["top_z1"],
                      lambda p: abs(p[0] + t) < 1e-6 and p[3] > 0),
        _shield_plate(Lv, 0, zt, Lv + t, W, P["top_z1"],
                      lambda p: abs(p[0] - (Lv + t)) < 1e-6 and p[3] < 0),
    ]
    return plates


def shield_screws():
    """Саморезы M4×16 с прижимной шляпкой Ø8 (fix5 п.8: 22 шт.)."""
    out = []
    for (hx, hy, hz, dx, dy, dz, t) in shield_screw_layout():
        head = cyl_axis(P["shield_screw_head"] / 2.0,
                        hx - dx * 2.5, hy - dy * 2.5, hz - dz * 2.5,
                        dx, dy, dz, 2.5)
        shank = cyl_axis(P["shield_screw_d"] / 2.0 - 0.3,
                         hx, hy, hz, dx, dy, dz, t + 6.5)
        out.append(head.fuse(shank))
    return concat(out)


def rubber_pads():
    """4 резиновых буфера в углах «поперечина — стойка» (fix5 п. 6).

    Один буфер на угол: 20×19×36, низ Z=244 (3 мм выше стола 241), верх
    280; прижат к нижней грани верхней поперечины (Z=280) и к боковой
    грани стойки (Y=20/180). До пружины Ø12 — 5 мм (Y=44/156).
    """
    out = []
    for x0 in (0.0, P["L_vibro"] - P["tube"]):
        for y0 in (P["tube"], P["W_frame"] - P["tube"] - P["rubber_pad_w"]):
            out.append(box(x0, y0, P["rubber_pad_z0"],
                           x0 + P["rubber_pad_x"], y0 + P["rubber_pad_w"],
                           P["rubber_pad_z1"]))
    return out


def rubber_ring(x, y):
    """Резиновое кольцо на направляющем валу под LMK (fix4 п.5).

    ID 10,5; OD 18; высота 10; Z=172…182. При нижнем ходе стола LMK
    опускается на 5 мм (низ 185), до кольца остаётся 3 мм.
    """
    s = cyl_z(P["ring_od"] / 2.0, P["ring_z0"], P["ring_z1"], x, y)
    return s.cut(cyl_z(P["ring_id"] / 2.0, P["ring_z0"] - 1,
                       P["ring_z1"] + 1, x, y))


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

    # fix5 п. 4: шайбы, гайки и контргайки с двух сторон кулачка
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

    # fix4 п.2: кожух поликарбонатный + саморезы
    add("shield", concat(shield_parts()), "pc", 1, "shield", "29")
    add("shield_screws", shield_screws(), "steel", P["shield_screw_n"],
        "steel", "30")
    # fix4 п.4: резиновые буферы в углах
    add("rubber_pads", concat(rubber_pads()), "rubber",
        P["rubber_pad_n"], "rubber", "31")
    # fix4 п.5: резиновые кольца на направляющих валах
    rr = [rubber_ring(x, y) for x in (P["guide_x1"], P["guide_x2"])
          for y in (P["guide_y1"], P["guide_y2"])]
    add("rubber_rings", concat(rr), "rubber", P["ring_n"], "rubber", "32")

    groups = {}
    for key, info in parts.items():
        groups.setdefault(info["group"], []).append(info["shape"])
    # fix4 п.6: картридж — вал + кулачок + 6200 + шайба + гайки
    groups["cartridge"] = [parts[k]["shape"] for k in
                           ("drive_shaft", "cam", "shaft_bearings",
                            "cam_washers", "cam_nuts", "cam_locknuts",
                            "shaft_conical_nuts", "shaft_locknuts")]

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
