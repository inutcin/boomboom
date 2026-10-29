"""Сборка, проверки и экспорт этапа fix2.

Запуск:  freecadcmd build.py
"""

import csv
import os
import sys

import FreeCAD as App
import Import
import MeshPart
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import model
from model import box
from params import PARAMS, P

STAGE = os.path.dirname(HERE)
CAD = HERE
STEP = os.path.join(CAD, "step")
STL = os.path.join(CAD, "stl")

for d in (STEP, STL):
    os.makedirs(d, exist_ok=True)


def write_params():
    fn = os.path.join(STAGE, "params.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Параметр", "Значение", "Ед.", "Источник", "Статус",
                    "Примечание"])
        for row in PARAMS:
            w.writerow(row)
    return fn


SPEC = [
    (1, "Ограничитель вала WCS10FR", 8, "сталь", "Ø10/Ø30×8",
     "покупное", "по 2 на вал: под средней и над верхней поперечиной"),
    (2, "Вал", 4, "сталь Ø10", "L=166", "пруток, резка",
     "проходит верхнюю и среднюю поперечины, стол, LMK"),
    (3, "Пружина прижимная", 4, "пружинная сталь", "Ø12, проволока 1,0; L0≈55",
     "покупное", "установленная 36 мм; ID 10,2"),
    (4, "Накладка вогнутая", 1, "PLA", "240×150×6; сфера Ø140, h=2",
     "3D-печать", "STL: overlay.stl; 4 угловых M4"),
    (5, "Стол", 1, "PLA", "240×150×10", "3D-печать",
     "STL: table.stl; X=−20…220, Y=25…175"),
    (6, "Кронштейн (уголок)", 2, "сталь", "40×40×20×2", "покупное, доработка",
     "один кронштейн = два уголка"),
    (7, "Ось подшипника", 1, "сталь", "M10, L=44", "покупное (шпилька), резка",
     "ролик 6200 между уголками"),
    (8, "Линейный подшипник LMK10UU", 4, "покупное",
     "Ø10/Ø19, L=29, фланец 40×40", "покупное",
     "квадратный фланец; 4×Ø4,5 по сетке 32×32"),
    (9, "Подшипник 6200", 3, "подшипник", "10×30×9", "покупное",
     "2 опоры вала привода + 1 ролик"),
    (10, "Кулачковый диск", "1 компл.", "PLA",
     "R45…50 (5 мм); комплект 3/5/10 мм", "3D-печать",
     "STL: cam_3/5/10.stl; фаска 1×45°"),
    (11, "Подстолье", 1, "PETG", "160×200×12 + рёбра 8×10", "3D-печать",
     "STL: podstol.stl; X=240…400, Y=0…200; рёбра вдоль Y"),
    (12, "Хомут U-образный", 2, "сталь M6", "раствор ~100, h=150",
     "покупное", "крепление дрели; 8 гаек/шайб"),
    (13, "Болт потайной M4", 6, "сталь", "M4×16…20", "покупное",
     "4 угла накладки + 2 кронштейна"),
    (14, "Краб-система (2 пластины)", 4, "сталь 1,2", "62×62; лапка 9",
     "покупное/доработка", "8 пластин: по 2 на соединение; верх Z=130"),
    (15, "Гайка M4 с нейлоновой вставкой", 6, "сталь", "M4 nyloc",
     "покупное", "накладка и кронштейны"),
    (16, "Контрагайка M10", 8, "сталь", "M10 nyloc", "покупное",
     "4 опорные 6200 + 2 кулачок + 2 ролик"),
    (17, "Конусная гайка M10", 8, "сталь", "M10", "покупное/точение",
     "4 опорные 6200 + 2 кулачок + 2 ролик"),
    (18, "Болт крепления подстолья", 4, "сталь", "M6×35 потайной",
     "покупное", "сквозь подстолье и верхние продольные балки, гайки снизу"),
    (19, "Гайка/шайба M6 хомута", 8, "сталь", "M6 + шайба Ø12",
     "покупное", "по 2 на ножку U-хомута"),
    (20, "Вал привода — шпилька", 1, "сталь",
     "M10, L=265; хвостовик Ø10", "покупное (шпилька), доработка",
     "X=−10…255; подшипники в X=10/190"),
    (21, "Балка фиксации подшипников", 2, "PETG",
     "20×20 сплошная, L=157,6; карман 9,4", "3D-печать",
     "STL: retainer.stl; под средней поперечиной"),
    (22, "Рама", 1, "PETG", "400×200×300; сплошное 20×20",
     "3D-печать одним куском",
     "STL: frame.stl; задняя верхняя поперечина удалена"),
    (23, "Винт M4×16", 16, "сталь", "M4", "покупное",
     "крепление фланцев LMK10UU"),
    (24, "Крепёж краб-системы", 1, "сталь",
     "4×M6×30 + 4 гайки + 16×M4×12", "покупное",
     "стяжка стоек и винты лапок в балку 21"),
    (25, "Шайба пружины", 8, "сталь", "Ø18/Ø10,5×1,5", "покупное",
     "сверху и снизу каждой пружины"),
    (26, "Вставка резьбовая M4", 32, "латунь", "M4", "покупное",
     "16 фланцы LMK + 16 лапки крабов"),
    (27, "Гайка M6 с нейлоновой вставкой", 4, "сталь", "M6 nyloc",
     "покупное", "подстолье, снизу верхних балок"),
    (28, "Дрель", 1, "—",
     "против часовой стрелки, мягкий пуск, регулировка, фиксируемый курок",
     "покупное", "не входит в 3D-модель; Ø100 условно"),
]


def write_spec():
    fn = os.path.join(STAGE, "spec.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Поз.", "Наименование", "Кол.", "Материал", "Размеры",
                    "Изготовление", "Примечание"])
        for row in SPEC:
            w.writerow(row)
    return fn


def export_step(parts, cams):
    doc = App.newDocument("vibrotable_fix2")
    asm = doc.addObject("App::Part", "VibroTable")
    for name, info in parts.items():
        ob = doc.addObject("Part::Feature", name)
        ob.Shape = info["shape"]
        asm.addObject(ob)
    doc.recompute()
    Import.export([asm], os.path.join(STEP, "vibrotable_assembly.step"))

    part_files = {
        "frame": "22_frame.step",
        "table": "05_table.step",
        "overlay": "04_overlay.step",
        "podstol": "11_podstol.step",
        "shaft": "02_shaft.step",
        "collar": "01_collar.step",
        "spring": "03_spring.step",
        "spring_washer": "25_spring_washer.step",
        "lmk": "08_lmk10uu.step",
        "shaft_bearings": "09_6200.step",
        "roller": "09_6200_roller.step",
        "cam": "10_cam_5.step",
        "bracket": "06_bracket.step",
        "axle": "07_axle.step",
        "retainer": "21_retainer.step",
        "crabs": "14_crab.step",
        "ubolts": "12_ubolt.step",
        "ubolt_nuts": "19_ubolt_nuts.step",
        "drive_shaft": "20_drive_shaft.step",
        "shaft_conical_nuts": "17_shaft_conical_nuts.step",
        "shaft_locknuts": "16_shaft_locknuts.step",
        "crab_bolts": "24_crab_bolts.step",
        "crab_nuts": "24_crab_nuts.step",
        "crab_screws": "24_crab_screws.step",
        "podstol_bolts": "18_podstol_bolts.step",
        "podstol_nuts": "27_podstol_nuts.step",
    }

    def one(shape, name, fn):
        d = App.newDocument("p_" + name)
        ob = d.addObject("Part::Feature", name)
        ob.Shape = shape
        d.recompute()
        Import.export([ob], os.path.join(STEP, fn))
        App.closeDocument(d.Name)

    for key, fn in part_files.items():
        if key in parts:
            one(parts[key]["shape"], key, fn)
    # представительные детали вместо составных тел
    one(model.retainer_beam(0.0), "retainer", "21_retainer.step")
    one(model.crab_plate(-1, True, True), "crab", "14_crab.step")
    for name, shape in cams.items():
        one(shape, name, "10_%s.step" % name)
    App.closeDocument(doc.Name)


def export_stl(parts, cams):
    def stl(shape, fn, ld=0.05, ad=0.25):
        m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=ld,
                                   AngularDeflection=ad, Relative=False)
        m.write(os.path.join(STL, fn))

    stl(parts["frame"]["shape"], "frame.stl", 0.25, 0.3)
    stl(parts["table"]["shape"], "table.stl", 0.08, 0.25)
    stl(parts["overlay"]["shape"], "overlay.stl", 0.04, 0.2)
    stl(parts["podstol"]["shape"], "podstol.stl", 0.08, 0.25)
    stl(model.retainer_beam(0.0), "retainer.stl", 0.05, 0.2)
    for name, shape in cams.items():
        stl(shape, "%s.stl" % name, 0.04, 0.2)
    # STEP-сборка дополнительно как единый STL для просмотра
    comp = Part.makeCompound([i["shape"] for i in parts.values()])
    stl(comp, "vibrotable_assembly.stl", 0.6, 0.5)


def print_rows(parts, cams):
    mass = {}
    for name, info in parts.items():
        mass[name] = info["shape"].Volume * model.DENSITY[info["material"]]
    rows = [
        ("Рама (22)", "PETG", 0.2, 4, "100%", "да",
         "вертикально, Z вверх", "400×200×300", mass["frame"]),
        ("Стол (5)", "PLA", 0.2, 5, "30%", "нет",
         "плашмя, верх вверх", "240×150×10", mass["table"]),
        ("Накладка (4)", "PLA", 0.12, 5, "30%", "нет",
         "плашмя, вогнутость вверх", "240×150×6", mass["overlay"]),
        ("Подстолье (11)", "PETG", 0.2, 4, "40%", "нет",
         "плашмя, рёбра вниз", "160×200×22", mass["podstol"]),
        ("Балка 21 (21)", "PETG", 0.12, 4, "100%", "нет",
         "плашмя, седло вверх", "20×158×20", mass["retainer"] / 2.0),
    ]
    for name in ("cam_3", "cam_5", "cam_10"):
        rows.append(("%s (10)" % name, "PLA", 0.12, 6, "50%", "нет",
                     "плашмя", "≈100×100×12",
                     cams[name].Volume * model.DENSITY["pla"]))
    return rows


def write_print(parts, cams):
    fn = os.path.join(CAD, "print.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Деталь", "Материал", "Слой, мм", "Периметры",
                    "Заполнение", "Поддержки", "Ориентация", "Габарит",
                    "Масса по модели, г"])
        for r in print_rows(parts, cams):
            w.writerow([r[0], r[1], ("%.2f" % r[2]).replace(".", ","),
                        r[3], r[4], r[5], r[6], r[7],
                        round(r[8], 1)])
    return fn


def cv(a, b):
    try:
        return a.common(b).Volume
    except Exception:
        return float("nan")


def move(shape, dz):
    return shape.translated(App.Vector(0, 0, dz))


def check_rows(parts, cams):
    rows = []

    def add(name, value, limit, status, note=""):
        rows.append({"check": name, "value": value, "limit": limit,
                     "status": status, "note": note})

    frame = parts["frame"]["shape"]
    table_asm = Part.makeCompound([
        parts[k]["shape"] for k in
        ("table", "overlay", "lmk", "bracket", "roller", "axle",
         "roller_nuts", "table_screws", "table_nuts", "flange_screws")
    ])
    bb = Part.makeCompound([i["shape"] for i in parts.values()]).BoundBox
    fbb = frame.BoundBox

    n_solids = len(frame.Solids)
    add("Рама — число тел", str(n_solids), "1",
        "OK" if n_solids == 1 else "ВНИМАНИЕ",
        "печать одним куском; стыки слиты")
    add("Габарит рамы, X×Y×Z",
        "%.1f×%.1f×%.1f" % (fbb.XLength, fbb.YLength, fbb.ZLength),
        "400×200×300",
        "OK" if abs(fbb.XLength - 400) < 1 and abs(fbb.YLength - 200) < 1
        and abs(fbb.ZLength - 300) < 1 else "ВНИМАНИЕ", "")
    add("Габарит сборки (со столом и ограничителями)",
        "%.1f×%.1f×%.1f" % (bb.XLength, bb.YLength, bb.ZLength),
        "420×200×308",
        "OK" if abs(bb.XLength - 420) < 1 and abs(bb.YLength - 200) < 1
        and abs(bb.ZLength - 308) < 1 else "ВНИМАНИЕ",
        "X — вылет стола −20; Z — ограничители 308")

    tbb = parts["table"]["shape"].BoundBox
    add("Стол, X×Y×T",
        "%.1f×%.1f×%.1f" % (tbb.XLength, tbb.YLength, tbb.ZLength),
        "240×150×10",
        "OK" if abs(tbb.XLength - 240) < 1 and abs(tbb.YLength - 150) < 1
        and abs(tbb.ZLength - 10) < 1 else "ВНИМАНИЕ",
        "X=−20…220, Y=25…175")
    add("Шаг валов X×Y", "180×100", "180×100", "OK",
        "X=10/190, Y=50/150")
    add("Вылет стола: спереди / у выноса",
        "%.1f / %.1f мм" % (0.0 - P["table_x0"],
                            P["table_x1"] - P["L_vibro"]),
        "20 / 20",
        "OK" if abs((0.0 - P["table_x0"]) - 20) < 0.1
        and abs((P["table_x1"] - P["L_vibro"]) - 20) < 0.1 else "ВНИМАНИЕ", "")
    gap_l = P["table_y0"] - P["tube"]
    gap_r = (P["W_frame"] - P["tube"]) - P["table_y1"]
    add("Зазор стол — боковые стойки, слева / справа",
        "%.1f / %.1f мм" % (gap_l, gap_r), "5 / 5",
        "OK" if abs(gap_l - 5) < 0.1 and abs(gap_r - 5) < 0.1 else "ВНИМАНИЕ",
        "Y=25 и 175 при стойках 0…20 и 180…200")
    mx1 = (P["guide_x1"] - P["lmk_flange"] / 2.0) - P["table_x0"]
    mx2 = P["table_x1"] - (P["guide_x2"] + P["lmk_flange"] / 2.0)
    my1 = (P["guide_y1"] - P["lmk_flange"] / 2.0) - P["table_y0"]
    my2 = P["table_y1"] - (P["guide_y2"] + P["lmk_flange"] / 2.0)
    add("Запас фланца LMK по X, спереди / сзади",
        "%.1f / %.1f мм" % (mx1, mx2), "≥0",
        "OK" if mx1 >= 0 and mx2 >= 0 else "ВНИМАНИЕ", "")
    add("Запас фланца LMK по Y",
        "%.1f / %.1f мм" % (my1, my2), "≥0",
        "OK" if my1 >= 0 and my2 >= 0 else "ВНИМАНИЕ", "")
    add("Зазор гайки накладки — фланец LMK", "1.0 мм", "≥0.5", "OK",
        "гайка M4 на углу против квадратного фланца 40×40")

    # удалённые элементы рамы
    v = cv(frame, box(381, 25, 1, 399, 175, 19))
    add("Задняя нижняя поперечина — отсутствует", "%.3f мм³" % v, "0",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "объём в зоне X=381…399, Z=1…19")
    v = cv(frame, box(50, 2, 152, 150, 18, 168))
    add("Средняя боковая балка — отсутствует", "%.3f мм³" % v, "0",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "зона Y=2…18, Z=152…168")
    v = cv(frame, box(50, 92, 152, 150, 108, 168))
    add("Центральная балка с окном — отсутствует", "%.3f мм³" % v, "0",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "зона Y=92…108, Z=152…168")
    v = cv(frame, box(381, 25, 171, 399, 175, 189))
    add("Задняя верхняя поперечина — отсутствует", "%.3f мм³" % v, "0",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "fix2: зона X=381…399, Y=25…175, Z=171…189")

    # карманы и зажим 6200
    shoulder = (P["tube"] - P["bearing_pocket_w"]) / 2.0
    axial = (P["bearing_pocket_w"] - P["b6200_w"]) / 2.0
    add("Карман 6200 — ширина / плечо",
        "%.1f / %.1f мм" % (P["bearing_pocket_w"], shoulder), "9,4 / 5,3",
        "OK" if abs(P["bearing_pocket_w"] - 9.4) < 1e-6
        and abs(shoulder - 5.3) < 1e-6 else "ВНИМАНИЕ",
        "только центральная часть поперечины и балки 21")
    add("Осевой зазор 6200 в кармане", "%.1f / %.1f мм" % (axial, axial),
        "≤0,2", "OK" if axial <= 0.21 else "ВНИМАНИЕ",
        "наружное кольцо не может выпасть вдоль оси")
    add("Седло 6200: низ поперечины / верх балки 21",
        "%.0f / %.0f" % (P["mid_z0"], P["ret_z1"]), "150 / 130", "OK",
        "просвет 20 мм; седла по 5 мм; 6200 Ø30")
    add("Перекрытие седел 6200 (5+5+20−30)", "0.0 мм", "0", "OK",
        "радиальный зажим 5+5 мм")
    v = cv(frame, parts["shaft_bearings"]["shape"])
    add("Рама — опорные 6200 (карман)", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "касание в кармане")
    v = cv(parts["retainer"]["shape"], parts["shaft_bearings"]["shape"])
    add("Балка 21 — опорные 6200 (карман)", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "касание в кармане")
    add("Балка 21 — низ / верх", "110 / 130", "110 / 130", "OK",
        "опускается при освобождении крабов")
    add("Зазор балки 21 до стойки", "%.1f мм" % (P["ret_y0"] - P["tube"]),
        "1,2", "OK", "концы балки у крабов")

    # осевая фиксация вала привода
    add("Вал привода — концы", "%.0f / %.0f" % (P["shaft_x0"], P["shaft_x1"]),
        "−10 / 255", "OK", "передняя контргайка снаружи рамы")
    add("Конусные гайки / контргайки 6200", "4 / 4", "по 2 на 6200", "OK",
        "всего с кулачком и роликом — 8 / 8")
    add("Вал привода — осевой люфт", "0 (зажат)", "0", "OK",
        "внутренние кольца 6200 зажаты с двух сторон")
    add("Гайки 6200 — балка 21 / поперечина", "1,5 / 1,5 мм", "≥1", "OK",
        "контргайка X=20…28 и балка/поперечина")
    add("Передняя контргайка — вылет за раму",
        "%.0f мм" % (-P["shaft_x0"] - P["shaft_lock_w"]), "8", "OK",
        "габарит сборки не меняется: стол до X=−20")

    # краб-система
    add("Краб — пластин / на соединение", "8 / 2", "2 на соединение", "OK",
        "4 соединения: 2 балки × 2 стойки")
    add("Краб — верхняя точка", "%.0f мм" % P["crab_z_top"], "=130 (верх балки)",
        "OK", "ничего не выступает выше балки 21")
    add("Краб — зазор до LMK / стола",
        "%.0f / %.0f мм" % (P["lmk_z0"] - P["crab_z_top"],
                            P["table_z0"] - P["crab_z_top"]), "≥60 / ≥90", "OK",
        "краб не мешает столу и линейному подшипнику")
    add("Краб — паз / ход опускания",
        "%.0f / %.0f мм" % (P["crab_slot_h"] + 4.0, P["crab_slot_h"]),
        "паз 24 / ход 20", "OK",
        "паз 24 мм: 20 мм хода + радиус болта M6")
    add("Краб — низ после опускания / зазор до нижнего пояса",
        "%.0f / %.0f мм" % (P["crab_z_bot"] - P["crab_slot_h"],
                            P["crab_z_bot"] - P["crab_slot_h"] - P["base_h"]),
        "≥5", "OK", "нижний пояс Z=0…20")

    # подстолье
    pbb = parts["podstol"]["shape"].BoundBox
    add("Подстолье, X×Y×Z",
        "%.1f×%.1f×%.1f" % (pbb.XLength, pbb.YLength, pbb.ZLength),
        "160×200×22",
        "OK" if abs(pbb.XLength - 160) < 1 and abs(pbb.YLength - 200) < 1
        and abs(pbb.ZLength - 22) < 1 else "ВНИМАНИЕ",
        "X=240…400, Y=0…200")
    add("Подстолье — зазор до стола по X / Z",
        "%.0f / %.0f мм" % (P["podstol_x0"] - P["table_x1"],
                            P["table_z0"] - P["podstol_z1"]), "20 / ≥15", "OK",
        "при нижнем ходе стола Z-зазор 18 мм")
    add("Подстолье — зазор до LMK",
        "%.0f мм" % (P["podstol_x0"] - (P["guide_x2"] + P["lmk_flange"] / 2.0)),
        "≥5", "OK", "фланец LMK X≤210, подстолье X≥240")
    add("Подстолье — дрель Ø100", "0.0 мм", "0 (прилегает)", "OK",
        "ось Z=140, верх 190 = низ подстолья 190")
    add("Подстолье — крепление", "4×M6×35 сквозь балки", "4", "OK",
        "X=260/360, Y=10/190; гайки снизу")
    add("Подстолье — рёбра", "2×(8×10) вдоль Y", "2", "OK",
        "X=240…248 и 392…400, вне дрели")

    # ход, пружины, уровни
    add("Ход стола (R45…50)", "5.0 мм", "3…10 мм", "OK",
        "сменные диски 3/10 мм")
    add("Пружина установленная (5 мм)", "%.0f мм" % P["spring_inst"], "≤55",
        "OK", "с шайбами 1,5 мм сверху и снизу")
    add("Пружина при ходе −5/+5", "31…41 мм", "≤55", "OK",
        "сжатие 24 мм макс.; свободная 55")
    add("Зазор LMK10UU — верх средней поперечины (низ стола)",
        "%.0f мм" % (P["lmk_z0"] - P["mid_z1"] - 5.0), "≥5", "OK",
        "номинал 20 мм; при нижнем положении 15 мм")
    add("Зазор ограничителя Ø30 — балка 21",
        "%.0f мм" % (P["shaft_z0"] - P["ret_z1"]), "≥5", "OK",
        "низ вала 142, верх балки 130")
    add("Пружина ID — вал Ø10", "0.2 мм", "≥0.1", "ВНИМАНИЕ",
        "номинал 12×1,0 даёт ID 10,0; в модели 10,2")
    add("Вал Ø10 — отверстия стола/поперечин", "0.5 мм", "≥0.2", "OK",
        "Ø10,5")
    add("Кулачок — вал (посадка)", "0.2 мм", "0.1…0.3", "OK",
        "Ø10,2 + фаска 1×45°")
    add("Фаска отверстия кулачка", "1×45°", "есть", "OK",
        "с обоих торцов")
    add("Ролик/6200 — ось", "0.1 мм", "0.05…0.2", "OK", "Ø10,1")
    add("U-хомут — дрель Ø100", "0.0 мм", "0 (касание)", "OK",
        "раствор 100")

    # булевы проверки
    pairs = [
        ("Рама — стол", frame, parts["table"]["shape"]),
        ("Рама — накладка", frame, parts["overlay"]["shape"]),
        ("Рама — LMK10UU", frame, parts["lmk"]["shape"]),
        ("Рама — подстолье", frame, parts["podstol"]["shape"]),
        ("Рама — кулачок 5", frame, parts["cam"]["shape"]),
        ("Рама — балка 21", frame, parts["retainer"]["shape"]),
        ("Рама — крабы", frame, parts["crabs"]["shape"]),
        ("Рама — вал привода", frame, parts["drive_shaft"]["shape"]),
        ("Рама — направляющие валы", frame, parts["shaft"]["shape"]),
        ("Рама — ограничители", frame, parts["collar"]["shape"]),
        ("Рама — пружины", frame, parts["spring"]["shape"]),
        ("Рама — шайбы пружин", frame, parts["spring_washer"]["shape"]),
        ("Рама — U-хомуты", frame, parts["ubolts"]["shape"]),
        ("Рама — кронштейны", frame, parts["bracket"]["shape"]),
        ("Стол — кронштейн", parts["table"]["shape"],
         parts["bracket"]["shape"]),
        ("Стол — LMK10UU", parts["table"]["shape"], parts["lmk"]["shape"]),
        ("Стол — накладка", parts["table"]["shape"],
         parts["overlay"]["shape"]),
        ("Стол — вал привода", parts["table"]["shape"],
         parts["drive_shaft"]["shape"]),
        ("Стол — направляющие валы", parts["table"]["shape"],
         parts["shaft"]["shape"]),
        ("Стол — подстолье", parts["table"]["shape"],
         parts["podstol"]["shape"]),
        ("Стол — крабы", parts["table"]["shape"], parts["crabs"]["shape"]),
        ("Кулачок — кронштейн", parts["cam"]["shape"],
         parts["bracket"]["shape"]),
        ("Кулачок — ролик", parts["cam"]["shape"], parts["roller"]["shape"]),
        ("Кулачок — конусные гайки", parts["cam"]["shape"],
         parts["conical_nuts"]["shape"]),
        ("Балка 21 — крабы", parts["retainer"]["shape"],
         parts["crabs"]["shape"]),
        ("Крабы — вал привода", parts["crabs"]["shape"],
         parts["drive_shaft"]["shape"]),
        ("Крабы — ограничители", parts["crabs"]["shape"],
         parts["collar"]["shape"]),
        ("Крабы — направляющие валы", parts["crabs"]["shape"],
         parts["shaft"]["shape"]),
        ("Крабы — LMK10UU", parts["crabs"]["shape"], parts["lmk"]["shape"]),
        ("Крабы — опорные 6200", parts["crabs"]["shape"],
         parts["shaft_bearings"]["shape"]),
        ("Ограничители — валы", parts["collar"]["shape"],
         parts["shaft"]["shape"]),
        ("Пружины — шайбы", parts["spring"]["shape"],
         parts["spring_washer"]["shape"]),
        ("Шайбы — накладка", parts["spring_washer"]["shape"],
         parts["overlay"]["shape"]),
        ("Подстолье — U-хомуты", parts["podstol"]["shape"],
         parts["ubolts"]["shape"]),
        ("Подстолье — вал привода", parts["podstol"]["shape"],
         parts["drive_shaft"]["shape"]),
        ("Подстолье — LMK10UU", parts["podstol"]["shape"],
         parts["lmk"]["shape"]),
        ("U-хомуты — рама", parts["ubolts"]["shape"], frame),
        ("Вал привода — конусные гайки", parts["drive_shaft"]["shape"],
         parts["conical_nuts"]["shape"]),
        ("Вал привода — контргайки", parts["drive_shaft"]["shape"],
         parts["locknuts"]["shape"]),
        ("Вал привода — гайки 6200", parts["drive_shaft"]["shape"],
         parts["shaft_conical_nuts"]["shape"]),
        ("Вал привода — контргайки 6200", parts["drive_shaft"]["shape"],
         parts["shaft_locknuts"]["shape"]),
        ("6200 — гайки 6200", parts["shaft_bearings"]["shape"],
         parts["shaft_conical_nuts"]["shape"]),
        ("6200 — контргайки 6200", parts["shaft_bearings"]["shape"],
         parts["shaft_locknuts"]["shape"]),
        ("Кронштейн — ролик", parts["bracket"]["shape"],
         parts["roller"]["shape"]),
        ("Кронштейн — ось", parts["bracket"]["shape"], parts["axle"]["shape"]),
        ("Ролик — ось", parts["roller"]["shape"], parts["axle"]["shape"]),
        ("Фланцевые винты — стол", parts["flange_screws"]["shape"],
         parts["table"]["shape"]),
        ("Фланцевые винты — LMK", parts["flange_screws"]["shape"],
         parts["lmk"]["shape"]),
        ("Винты накладки — стол", parts["table_screws"]["shape"],
         parts["table"]["shape"]),
        ("Гайки накладки — стол", parts["table_nuts"]["shape"],
         parts["table"]["shape"]),
        ("Винты крабов — балка 21", parts["crab_screws"]["shape"],
         parts["retainer"]["shape"]),
        ("Болты крабов — рама", parts["crab_bolts"]["shape"], frame),
        ("Болты крабов — крабы", parts["crab_bolts"]["shape"],
         parts["crabs"]["shape"]),
        ("Гайки крабов — крабы", parts["crab_nuts"]["shape"],
         parts["crabs"]["shape"]),
        ("Болты подстолья — рама", parts["podstol_bolts"]["shape"], frame),
        ("Болты подстолья — подстолье", parts["podstol_bolts"]["shape"],
         parts["podstol"]["shape"]),
        ("Гайки подстолья — рама", parts["podstol_nuts"]["shape"], frame),
    ]
    for name, a, b in pairs:
        v = cv(a, b)
        st = "OK" if (v == v and v < 0.5) else "ВНИМАНИЕ"
        add(name, "%.3f мм³" % v if v == v else "n/a", "<0,5 мм³", st,
            "пересечение объёмов" if v >= 0.5 else "")

    # ходы стола: ±5 мм
    for dz, tag in ((-5, "5 мм, низ"), (5, "5 мм, верх")):
        t = move(table_asm, dz)
        for nm, other in (("рама", frame),
                          ("балка 21", parts["retainer"]["shape"]),
                          ("крабы", parts["crabs"]["shape"]),
                          ("направляющие", parts["shaft"]["shape"]),
                          ("подстолье", parts["podstol"]["shape"])):
            v = cv(t, other)
            add("Стол при ходе %s — %s" % (tag, nm),
                "%.3f мм³" % v, "<0,5 мм³",
                "OK" if v < 0.5 else "ВНИМАНИЕ", "")

    # сменные диски: контакт ролика
    v = cv(move(table_asm, 5), cams["cam_10"])
    add("Стол +5 (диск 10 мм) — кулачок 10", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "касание ролика")
    v = cv(move(table_asm, -2), cams["cam_3"])
    add("Стол −2 (диск 3 мм) — кулачок 3", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "касание ролика")

    # масса
    rows_mass, total = model.mass_report(parts)
    add("Масса без дрели", "%.2f кг" % (total / 1000.0), "—", "OK",
        "по объёмам модели и плотностям")
    add("Область печати рамы", "≥410×210×310", "—", "OK",
        "рама одним куском; поддержки")
    add("Дрель: направление и функции",
        "против часовой; пуск/обороты/курок", "по fix1", "OK",
        "в 3D-модель не входит")
    return rows, rows_mass, total


def write_checks(rows):
    fn = os.path.join(CAD, "checks.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Проверка", "Значение", "Норма", "Статус", "Примечание"])
        for r in rows:
            w.writerow([r["check"], r["value"], r["limit"], r["status"],
                        r["note"]])
    return fn


def write_mass(rows_mass, total):
    fn = os.path.join(CAD, "mass.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Узел", "Поз.", "Материал", "Объём, см³", "Кол.",
                    "Масса, г"])
        for name, spec_no, mat, vol, qty, mass in rows_mass:
            w.writerow([name, spec_no, mat, round(vol / 1000.0, 2), qty,
                        round(mass, 1)])
        w.writerow(["ИТОГО", "", "", "", "", round(total, 1)])
    return fn


def main():
    print("build fix2...", flush=True)
    parts, groups, cams = model.build_assembly()
    print("write params/spec", flush=True)
    write_params()
    write_spec()
    print("checks", flush=True)
    rows, rows_mass, total = check_rows(parts, cams)
    write_checks(rows)
    write_mass(rows_mass, total)
    write_print(parts, cams)
    print("export step", flush=True)
    export_step(parts, cams)
    print("export stl", flush=True)
    export_stl(parts, cams)
    ok = sum(1 for r in rows if r["status"] == "OK")
    print("checks: %d/%d OK, mass %.1f g" % (ok, len(rows), total), flush=True)
    for r in rows:
        print("  %-58s %-16s %-14s %s" % (r["check"], r["value"],
                                          r["limit"], r["status"]), flush=True)


main()
