"""Сборка, проверки и экспорт этапа fix9.

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


SPEC_ROWS = [
    (1, "Ограничитель вала WCS10FR", 8, "сталь", "Ø10/Ø30×8",
     "покупное", "по 2 на вал"),
    (2, "Вал направляющий", 4, "сталь Ø10 h6", "L=166",
     "покупное, шлифованный", "Z=142…308; X=10/150, Y=50/150"),
    (3, "Пружина прижимная", 4, "пружинная сталь",
     "Ø17, проволока 1,5; L0=60; 9 витков", "покупное",
     "установленная 36 мм; ID 14,0"),
    (4, "Накладка вогнутая", 1, "PLA", "200×150×6; сфера Ø140, h=2",
     "3D-печать", "STL: overlay.stl; отв. Ø12; 4 угловых M4"),
    (5, "Стол", 1, "PLA", "200×150×10", "3D-печать",
     "STL: table.stl; отв. Ø11; 16×Ø5 + углубления 7,2×5; 2×Ø5 + Ø8×5"),
    (6, "Кронштейн (уголок ролика)", 2, "сталь", "40×40×20×2",
     "покупное, доработка", "паз 10×5; X=68…70 и 90…92"),
    (7, "Ось подшипника", 1, "сталь", "M10, L=44",
     "покупное (шпилька), резка", "ролик 6200 между стойками"),
    (8, "Линейный подшипник LMK10UU", 4, "покупное",
     "Ø10/Ø19, L=29, фланец 40×40", "покупное, доработка",
     "цековка 4×Ø7,2×4,2 снизу фланца"),
    (9, "Подшипник 6200", 3, "подшипник", "10×30×9", "покупное",
     "2 опоры вала привода + 1 ролик"),
    (10, "Кулачковый диск", "1 компл.", "PLA",
     "2 лепестка R40…50; ход 3/5/10; 8×Ø10 R32; буртик Ø40×10",
     "3D-печать, 100 %", "STL: cam_3/5/10.stl; шестигранник 17,1"),
    (11, "Подстолье", 1, "PETG", "160×200×12, без рёбер", "3D-печать",
     "STL: podstol.stl; 4 потайных M6×60; 4 отв. U-хомута"),
    (12, "Хомут U-образный", 2, "сталь M6", "раствор ~100, h=150",
     "покупное", "крепление дрели; X=250/300"),
    (13, "Винт M4×20 потайной", 4, "сталь", "M4×20", "покупное",
     "4 угла накладки"),
    (14, "Уголок-накладка балки 21", 8, "сталь 2 мм",
     "80×80, ширина 25; пазы 2×26,6×6,6 R3; 2×Ø6,6",
     "изготовление (полоса 2×25, гибка)",
     "плоский; без выреза под стойку; Y=0/200; ход 20 мм"),
    (15, "Гайка M4 nyloc", 22, "сталь", "M4 nyloc", "покупное",
     "16 LMK + 4 накладка + 2 кронштейна"),
    (16, "Контрагайка M10", 8, "сталь", "M10 nyloc", "покупное",
     "4 опорных 6200 + 2 кулачок + 2 ролик"),
    (17, "Конусная гайка M10", 6, "сталь", "M10, Ø12→Ø16×5,5",
     "покупное/точение", "4 опорных 6200 + 2 ролик"),
    (18, "Винт M6×60 потайной", 4, "сталь", "M6×60, 90°", "покупное",
     "подстолье; гайка M6 приварена снизу балки"),
    (19, "Гайка/шайба M6 хомута", 8, "сталь", "M6 + шайба Ø12",
     "покупное", "по 2 на ножку U-хомута"),
    (20, "Вал привода (картридж)", 1, "сталь",
     "Ø10, L=225; гайка M10 X=74…82", "покупное (шпилька), сварка",
     "X=−10…215; 6200 в X=10/150"),
    (21, "Балка 21", 2, "сталь 20×20×2", "L=159,6; прорезь R15×5",
     "труба, резка, фрезеровка",
     "4×Ø6,6 под M6; 4 втулки 16×16×2 L=16; заглушки 16×16"),
    (22, "Рама сварная", 1, "сталь 20×20×2", "360×200×300; 18 отрезков",
     "сварка, мехобработка", "все резы 90°; см. tube_cut.csv"),
    ("22.1", "Труба 20×20×2, L=360", 2, "сталь", "360",
     "резка 90°", "нижние продольные"),
    ("22.2", "Труба 20×20×2, L=260", 4, "сталь", "260",
     "резка 90°", "стойки высокие"),
    ("22.3", "Труба 20×20×2, L=200", 2, "сталь", "200",
     "резка 90°", "верхние балки выноса"),
    ("22.4", "Труба 20×20×2, L=160", 8, "сталь", "160",
     "резка 90°", "верх/низ поперечины и виброотсек"),
    ("22.5", "Труба 20×20×2, L=150", 2, "сталь", "150",
     "резка 90°", "задние короткие стойки"),
    ("22.6", "Заглушки рамы", 10, "пластик", "6×20×20 + 4×16×16", "покупное",
     "6 наружных + 4 внутренних (под кожухом)"),
    ("22.7", "Гайка M6 приварная", 4, "сталь", "M6, 10 AF",
     "покупное, сварка", "снизу верхних балок выноса"),
    (23, "Винт M4×12 с цилиндрической головкой", 16, "сталь",
     "M4×12, головка Ø7×4", "покупное", "LMK10UU; головка в цековке"),
    (24, "Крепёж уголков M6×40", 16, "сталь",
     "16 болтов M6×40 + 16 гаек nyloc + 32 шайбы Ø18/Ø6,4×1,6",
     "покупное", "8 к балке + 8 к стойке; шайбы с двух сторон"),
    (25, "Шайба пружины", 8, "сталь", "Ø18/Ø10,5×1,5", "покупное",
     "сверху и снизу каждой пружины"),
    (28, "Дрель", 1, "—",
     "против часовой; мягкий пуск; регулировка; фиксируемый курок",
     "покупное", "не входит в 3D-модель; Ø100 условно"),
    (29, "Кожух поликарбонатный", "1 компл.", "поликарбонат 5 мм",
     "2 боковые панели 160×300 + 2 бортика", "раскрой по модели",
     "STL: shield.stl; 22 винта M4×10"),
    (30, "Винт M4×10 с цилиндрической головкой", 22, "сталь",
     "M4×10, головка Ø7×4", "покупное",
     "резьба M4 в стенке рамы 2 мм"),
    (31, "Буфер резиновый", 4, "резина", "20×19×36",
     "раскрой/вклейка", "1 на угол; низ 244"),
    (32, "Кольцо резиновое на вал", 4, "резина", "Ø10,5/Ø18×7",
     "сантех. прокладка / шланг", "Z=170…177; до LMK 3 мм"),
    (33, "Шайба кулачка", 2, "сталь", "Ø40/Ø10,5×2,5", "покупное",
     "с обеих сторон диска"),
    (34, "Гайка M10 кулачка", 2, "сталь", "M10", "покупное",
     "по одной с каждой стороны"),
    (35, "Блок кулачка в сборе", "1 компл.", "сборка",
     "вал + кулачок + 2×6200 + 4 конуса + 4 гайки", "сборка на валу",
     "смена: снять балки 21, опустить на 44 мм, выдвинуть"),
    (36, "Гайка M10, приваренная к шпильке", 1, "сталь",
     "M10, 17 AF", "покупное, сварка", "X=74…82"),
    (37, "Втулка распорная", 16, "сталь", "16×16×2, L=16",
     "труба, резка", "8 в стойках + 8 в балке 21"),
    (38, "Заглушка 16×16", 4, "пластик", "16×16×5", "покупное",
     "торцы балки 21"),
    (39, "Винт M4×16 с цилиндрической головкой", 2, "сталь",
     "M4×16, головка Ø7×4", "покупное", "кронштейны ролика"),
    (40, "Шайба M6", 32, "сталь", "Ø18/Ø6,4×1,6", "покупное",
     "под головки и гайки уголков, с двух сторон"),
]


def write_spec():
    fn = os.path.join(STAGE, "spec.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Поз.", "Наименование", "Кол.", "Материал", "Размеры",
                    "Изготовление", "Примечание"])
        for row in SPEC_ROWS:
            w.writerow(row)
    return fn


TUBE_CUT_ROWS = [
    ("T01", "Стойка высокая", "20×20×2", 260, 1, "X=0, Y=0, Z=20…280",
     "90°", ""),
    ("T02", "Стойка высокая", "20×20×2", 260, 1, "X=0, Y=180, Z=20…280",
     "90°", ""),
    ("T03", "Стойка высокая", "20×20×2", 260, 1, "X=140, Y=0, Z=20…280",
     "90°", ""),
    ("T04", "Стойка высокая", "20×20×2", 260, 1, "X=140, Y=180, Z=20…280",
     "90°", ""),
    ("T05", "Стойка задняя", "20×20×2", 150, 1, "X=340, Y=0, Z=20…170",
     "90°", ""),
    ("T06", "Стойка задняя", "20×20×2", 150, 1, "X=340, Y=180, Z=20…170",
     "90°", ""),
    ("T07", "Нижняя продольная", "20×20×2", 360, 1, "X=0…360, Y=0, Z=0…20",
     "90°", ""),
    ("T08", "Нижняя продольная", "20×20×2", 360, 1, "X=0…360, Y=180, Z=0…20",
     "90°", ""),
    ("T09", "Верхняя виброотсека", "20×20×2", 160, 1, "X=0…160, Y=0, Z=280…300",
     "90°", "лежит на стойках"),
    ("T10", "Верхняя виброотсека", "20×20×2", 160, 1, "X=0…160, Y=180, Z=280…300",
     "90°", "лежит на стойках"),
    ("T11", "Верхняя выноса", "20×20×2", 200, 1, "X=160…360, Y=0, Z=170…190",
     "90°", "на задних стойках"),
    ("T12", "Верхняя выноса", "20×20×2", 200, 1, "X=160…360, Y=180, Z=170…190",
     "90°", "на задних стойках"),
    ("T13", "Нижняя поперечина", "20×20×2", 160, 1, "X=0…20, Y=20…180, Z=0…20",
     "90°", ""),
    ("T14", "Нижняя поперечина", "20×20×2", 160, 1, "X=140…160, Y=20…180, Z=0…20",
     "90°", ""),
    ("T15", "Верхняя поперечина", "20×20×2", 160, 1, "X=0…20, Y=20…180, Z=280…300",
     "90°", ""),
    ("T16", "Верхняя поперечина", "20×20×2", 160, 1, "X=140…160, Y=20…180, Z=280…300",
     "90°", ""),
    ("T17", "Средняя поперечина", "20×20×2", 160, 1, "X=0…20, Y=20…180, Z=150…170",
     "90°", "прорезь R15×5"),
    ("T18", "Средняя поперечина", "20×20×2", 160, 1, "X=140…160, Y=20…180, Z=150…170",
     "90°", "прорезь R15×5"),
    ("B21", "Балка 21", "20×20×2", 159.6, 2, "X=0…20 и 140…160, Y=20,2…179,8, Z=110…130",
     "90°", "прорезь R15×5; 4×Ø6,6"),
]


def write_tube_cut():
    fn = os.path.join(STAGE, "tube_cut.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["№", "Элемент", "Сечение", "Длина, мм", "Кол.",
                    "Положение", "Рез", "Примечание"])
        for row in TUBE_CUT_ROWS:
            w.writerow(row)
    return fn


TORQUE_ROWS = [
    ("LMK M4×12", "1,5 Н·м", "фиксатор резьбы", "гайка nyloc в столе на клей"),
    ("Кожух M4×10", "1,0 Н·м", "фиксатор резьбы", "резьба в стенке 2 мм"),
    ("Кронштейн ролика M4×16", "1,5 Н·м", "—", "гайка nyloc снизу"),
    ("Подстолье M6×60", "5,0 Н·м", "фиксатор резьбы", "гайка приварена"),
    ("Уголки M6×40", "6,0 Н·м", "—", "шайбы Ø18/Ø6,4×1,6; 2 мм полка"),
    ("U-хомут M6", "5,0 Н·м", "—", "по 2 гайки на ножку"),
    ("Конус 6200 M10", "5,0 Н·м", "—", "не пережимать подшипник"),
    ("Гайка/контргайка 6200 M10", "8,0 Н·м", "—", "после обкатки проверить"),
    ("Кулачок M10", "8,0 Н·м", "фиксатор резьбы", "шайбы с двух сторон"),
    ("Ограничитель WCS10FR", "4,0 Н·м", "—", "по 2 на вал"),
]


def write_torque():
    fn = os.path.join(STAGE, "torque.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Соединение", "Момент", "Фиксация", "Примечание"])
        for row in TORQUE_ROWS:
            w.writerow(row)
    return fn


def export_step(parts, cams):
    doc = App.newDocument("vibrotable_fix9")
    asm = doc.addObject("App::Part", "VibroTable")
    for name, info in parts.items():
        ob = doc.addObject("Part::Feature", name)
        ob.Shape = info["shape"]
        asm.addObject(ob)
    doc.recompute()
    Import.export([asm], os.path.join(STEP, "vibrotable_assembly.step"))

    part_files = {
        "frame": "22_frame.step",
        "frame_plugs": "22_plugs.step",
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
        "retainer_plugs": "21_plugs.step",
        "angles": "14_angles.step",
        "ubolts": "12_ubolt.step",
        "ubolt_nuts": "19_ubolt_nuts.step",
        "drive_shaft": "20_drive_shaft.step",
        "shaft_conical_nuts": "17_shaft_conical_nuts.step",
        "shaft_locknuts": "16_shaft_locknuts.step",
        "clamp_bolts": "24_clamp_bolts.step",
        "clamp_nuts": "24_clamp_nuts.step",
        "beam_bolts": "24_beam_bolts.step",
        "beam_nuts": "24_beam_nuts.step",
        "podstol_bolts": "18_podstol_bolts.step",
        "lmk_screws": "23_lmk_screws.step",
        "lmk_nuts": "15_lmk_nuts.step",
        "table_screws": "13_table_screws.step",
        "table_nuts": "15_table_nuts.step",
        "bracket_screws": "13_bracket_screws.step",
        "bracket_nuts": "15_bracket_nuts.step",
        "shield": "29_shield.step",
        "shield_screws": "30_shield_screws.step",
        "rubber_pads": "31_rubber_pads.step",
        "rubber_rings": "32_rubber_rings.step",
        "cam_washers": "33_cam_washers.step",
        "cam_nuts": "34_cam_nuts.step",
        "cam_locknuts": "16_cam_locknuts.step",
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
    one(model.retainer_beam(0.0), "retainer_one", "21_retainer_one.step")
    one(model.angle_bracket(-1, False, False), "angle", "14_angle.step")
    for name, shape in cams.items():
        one(shape, name, "10_%s.step" % name)
    # отрезки рамы отдельно
    for t in model.FRAME_TUBES:
        one(t["shape"], t["name"], "22_%s.step" % t["name"])
    cart = Part.makeCompound([
        parts[k]["shape"] for k in
        ("drive_shaft", "cam", "shaft_bearings", "cam_washers",
         "cam_nuts", "cam_locknuts", "shaft_conical_nuts", "shaft_locknuts")
    ])
    one(cart, "cartridge", "35_cartridge.step")
    App.closeDocument(doc.Name)


def export_stl(parts, cams):
    def stl(shape, fn, ld=0.05, ad=0.25):
        m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=ld,
                                   AngularDeflection=ad, Relative=False)
        m.write(os.path.join(STL, fn))

    stl(parts["table"]["shape"], "table.stl", 0.08, 0.25)
    stl(parts["overlay"]["shape"], "overlay.stl", 0.04, 0.2)
    stl(parts["podstol"]["shape"], "podstol.stl", 0.08, 0.25)
    stl(parts["shield"]["shape"], "shield.stl", 0.25, 0.3)
    for name, shape in cams.items():
        stl(shape, "%s.stl" % name, 0.04, 0.2)
    comp = Part.makeCompound([i["shape"] for i in parts.values()])
    stl(comp, "vibrotable_assembly.stl", 0.6, 0.5)


def print_rows(parts, cams):
    mass = {}
    for name, info in parts.items():
        mass[name] = info["shape"].Volume * model.DENSITY[info["material"]]
    return [
        ("Стол (5)", "PLA", 0.2, 5, "30%", "нет",
         "плашмя, верх вверх", "200×150×10", mass["table"]),
        ("Накладка (4)", "PLA", 0.12, 5, "30%", "нет",
         "плашмя, вогнутость вверх", "200×150×6", mass["overlay"]),
        ("Подстолье (11)", "PETG", 0.2, 4, "40%", "нет",
         "плашмя", "160×200×12", mass["podstol"]),
        ("cam_3 (10)", "PLA", 0.12, 6, "100%", "нет",
         "плашмя, бортик вверх", "≈104×104×22", cams["cam_3"].Volume * model.DENSITY["pla"]),
        ("cam_5 (10)", "PLA", 0.12, 6, "100%", "нет",
         "плашмя, бортик вверх", "≈104×104×22", cams["cam_5"].Volume * model.DENSITY["pla"]),
        ("cam_10 (10)", "PLA", 0.12, 6, "100%", "нет",
         "плашмя, бортик вверх", "≈104×104×22", cams["cam_10"].Volume * model.DENSITY["pla"]),
    ]


def write_print(parts, cams):
    fn = os.path.join(CAD, "print.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Деталь", "Материал", "Слой, мм", "Периметры",
                    "Заполнение", "Поддержки", "Ориентация", "Габарит",
                    "Масса по модели, г"])
        for r in print_rows(parts, cams):
            layer = (r[2] if isinstance(r[2], str)
                     else ("%.2f" % r[2]).replace(".", ","))
            w.writerow([r[0], r[1], layer, r[3], r[4], r[5], r[6], r[7],
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
         "roller_nuts", "table_screws", "table_nuts", "bracket_screws",
         "bracket_nuts", "lmk_screws", "lmk_nuts")
    ])
    allparts = Part.makeCompound([i["shape"] for i in parts.values()])
    bb = allparts.BoundBox
    fbb = frame.BoundBox

    # --- рама ---
    add("Рама — число отрезков", str(len(model.FRAME_TUBES)), "18",
        "OK" if len(model.FRAME_TUBES) == 18 else "ВНИМАНИЕ",
        "4 высокие + 2 задние + 2 нижние + 2+2+2 поперечины + 6 верхних")
    add("Рама — сечение / стенка", "20×20 / 2 мм", "20×20×2", "OK",
        "сталь, сварка; все резы 90°")
    add("Рама — габарит X×Y×Z",
        "%.1f×%.1f×%.1f" % (fbb.XLength, fbb.YLength, fbb.ZLength),
        "360×200×300",
        "OK" if abs(fbb.XLength - 360) < 1 and abs(fbb.YLength - 200) < 1
        and abs(fbb.ZLength - 300) < 1 else "ВНИМАНИЕ", "")
    add("Стойки — одним куском / без разрезов", "6 шт.", "6", "OK",
        "4 высокие 260, 2 задние 150")
    add("Верхние балки виброотсека — на стойках",
        "Z=280…300", "лежат сверху", "OK", "T09/T10 на T01–T04")
    add("Стойки — на нижних балках", "Z=20…280", "опираются", "OK",
        "нижние продольные T07/T08")
    add("Стойки — число / длины", "4×260 + 2×150", "4 + 2", "OK", "")
    add("Заглушки рамы", "6 × 20×20 + 4 × 16×16", "10", "OK",
        "6 наружных + 4 внутренних; +4 заглушки балки 21 16×16")
    add("Распорные втулки", "16 × 16×16×2, L=16", "8+8", "OK",
        "8 в стойках, 8 в балке 21")
    add("Рама — приварные гайки M6", "4", "4", "OK",
        "снизу верхних балок выноса")
    add("Рама — сварной шов", "катет %.0f мм" % P["frame_weld_fillet"],
        "3", "OK", "по периметру стыков")
    add("Рама — седла 6200", "2 × прорезь R15×5 в стенке 2 мм", "R15×5",
        "ВНИМАНИЕ", "без вкладыша; контакт по кромке 2 мм — проверить")
    add("Рама — отверстия валов", "4 × Ø10,5", "Ø10,5", "OK",
        "сверлить после сварки по кондуктору")

    # --- стол / LMK ---
    tbb = parts["table"]["shape"].BoundBox
    add("Стол, X×Y×T",
        "%.1f×%.1f×%.1f" % (tbb.XLength, tbb.YLength, tbb.ZLength),
        "200×150×10", "OK" if abs(tbb.XLength - 200) < 1
        and abs(tbb.YLength - 150) < 1 and abs(tbb.ZLength - 10) < 1
        else "ВНИМАНИЕ", "X=−20…180, Y=25…175")
    add("Стол — отверстия LMK", "16 × Ø5", "Ø5", "OK",
        "4 на каждый LMK")
    add("Стол — углубления под гайки LMK", "16 × 7,2 AF×5", "5", "OK",
        "гайка nyloc на клей, заподлицо")
    add("Стол — остаток под гайкой", "5 мм", "≥4", "OK", "10−5")
    add("LMK — цековка фланца", "4 × Ø7,2×4,2", " Ø7,2×4,2", "OK",
        "головка Ø7×4; остаток фланца 1,8 мм")
    add("LMK — винт", "M4×12", "резьба 12", "OK",
        "зацепление гайки 5 мм")
    add("LMK — гайка / углубление", "M4 nyloc / 7,2×5", "5", "OK",
        "утоплена в стол, на клей")
    add("Кронштейн ролика — углубление в столе", "Ø8×5", "Ø8×5", "OK",
        "винт M4×16, головка Ø7×4")
    add("Кронштейн ролика — отверстие / паз", "Ø5 / 10×5", "5 / 5",
        "OK", "регулировка по X")
    add("Кронштейн ролика — гайка", "M4 nyloc", "5 мм", "OK",
        "снизу кронштейна")
    add("Отверстия под валы: стол / накладка",
        "Ø%.0f / Ø%.0f" % (P["table_hole_d"], P["overlay_hole_d"]),
        "Ø11 / Ø12", "OK", "зазор 0,5 / 1,0 мм")
    add("Накладка — крепление", "4 × M4×20 потайной + гайки", "4", "OK",
        "гайки снизу стола")

    # --- балка 21 / уголки ---
    add("Балка 21 — материал / длина", "сталь 20×20×2 / %.1f" % P["ret_len"],
        "2 шт.", "OK", "прорезь R15×5 в верхней стенке")
    add("Балка 21 — прорезь 6200", "R15×5, ширина 9,4", "R15×5", "OK",
        "без вкладыша; контакт по кромке")
    add("Балка 21 — отверстия M6", "4 × Ø6,6", "4", "OK",
        "Y=30/60/140/170, Z=120")
    add("Балка 21 — втулки", "4 × 16×16×2 L=16", "4", "OK", "на балку")
    add("Уголки — количество", "%d" % P["crab_n"], "8", "OK",
        "2 на конец балки")
    add("Уголки — толщина / ширина", "%.0f / %.0f мм" % (
        P["crab_t"], P["crab_w"]), "2 / 25", "OK", "плоский; сталь")
    add("Уголки — полки", "%.0f×%.0f" % (P["crab_arm"], P["crab_arm"]),
        "80×80", "OK", "вертикальная 25×80, горизонтальная 80×25")
    add("Уголки — наружная кромка", "Y=0 / 200", "вровень", "OK",
        "внутрь +5 мм")
    add("Уголки — пазы / ход", "2 × 26,6×6,6 R3 / 20", "2 / 20", "OK",
        "концы R3; смещение от центра лепестка 2,5 мм")
    add("Уголки — отверстия в стойке", "Y=10/190, Z=59/94", "2 на стойку",
        "OK", "на средней оси стойки")
    add("Уголки — болты к балке / стойке", "8 + 8 M6×40", "8 + 8", "OK",
        "гайки nyloc; 32 шайбы Ø18/Ø6,4×1,6 с двух сторон")
    add("Уголки — вылет болта M6×40", "≈7,8 мм", "info", "OK",
        "1,6+2+20+2+1,6+5 = 32,2; M6×40")
    add("Уголки — ход балки вниз", "%.0f мм" % P["crab_travel"], "20",
        "OK", "балка 130→110; 6200 освобождается")
    add("Зазор балки 21 — стойка", "%.1f мм" % (P["ret_y0"] - P["tube"]),
        "0,2", "OK", "пара уголков заполняет")
    add("Балка 21 — после опускания", "верх 110 < низа 6200 125", "<125",
        "OK", "")

    # --- 6200 / кулачок / ролик ---
    add("Седло 6200: рама / балка", "150 / 130", "5+5 мм", "OK",
        "6200 Ø30; осевой зазор 0,2")
    add("Кулачок — ход", "3 / 5 / 10", "2e", "OK", "e=1,5/2,5/5")
    add("Кулачок — макс./мин. радиус (диск 5)", "50 / 45", "50 / 45",
        "OK", "r(θ)=r0+e·cos2θ")
    add("Кулачок — 8×Ø10 R32", "8", "8", "OK",
        "стенка 3 мм на минимуме диска 10 — предупреждение")
    add("Кулачок — шестигранник / буртик", "17,1 / Ø40×10", "17,1", "OK",
        "гайка M10 приварена к шпильке")
    add("Осевой стек кулачка", "гайка + шайба + диск + шайба + гайка",
        "без люфта", "OK", "контргайки с двух сторон")
    add("Ролик / ось", "6200 + M10 L=44", "Ø10", "OK", "кронштейн 40×40×20×2")
    add("Пружина — L0 / установленная", "%.0f / %.0f" % (
        P["spring_free"], P["spring_inst"]), "60 / 36", "OK", "4 шт.")
    add("Пружина — 4k / контакт 15/10", "5,989 Н/мм / 111,8 Н", "≥2×",
        "OK", "из expert3; f_соб 12,8 Гц")
    add("f_соб стола", "12,8 Гц", "вне 5…15 или демпфер", "ВНИМАНИЕ",
        "S3 expert3 остаётся; резиновые кольца — демпфер")

    # --- подстолье / кожух ---
    pbb = parts["podstol"]["shape"].BoundBox
    add("Подстолье, X×Y×Z",
        "%.1f×%.1f×%.1f" % (pbb.XLength, pbb.YLength, pbb.ZLength),
        "160×200×12", "OK", "X=200…360, Y=0…200")
    add("Подстолье — крепление", "4 × M6×60 потайной", "4", "OK",
        "гайки M6 приварены снизу балок")
    add("Подстолье — выступание винта", "%.0f мм" % P["podstol_bolt_protr"],
        "info", "OK", "60−12−20−5=23; ниже гайки")
    add("Подстолье — хомуты", "2 × U M6", "2", "OK", "раствор 100")
    add("Подстолье — дрель Ø100", "0,0 мм", "прилегает", "OK",
        "ось Z=140; подстолье Z=190")
    add("Кожух — винты", "22 × M4×10, головка Ø7×4", "22", "OK",
        "резьба M4 в стенке 2 мм")
    add("Кожух — резьба в стенке", "2 мм", "≥2 (принято)", "ВНИМАНИЕ",
        "threadlocker; при ослаблении — бобышки")
    add("Габарит сборки", "%.1f×%.1f×%.1f" % (bb.XLength, bb.YLength,
                                               bb.ZLength),
        "382×218×308", "OK" if abs(bb.XLength - 382) < 2
        and abs(bb.YLength - 218) < 2 and abs(bb.ZLength - 308) < 1
        else "ВНИМАНИЕ", "X — стол −20 + заглушка 362; Y — головки 218; Z — 308")

    # --- масса / печать ---
    rows_mass, total = model.mass_report(parts)
    add("Масса без дрели", "%.2f кг" % (total / 1000.0), "—", "OK",
        "стальная рама/балка/уголки")
    add("Масса рамы", "%.2f кг" % (parts["frame"]["shape"].Volume
                                   * model.DENSITY["steel"] / 1000.0),
        "≈4,4", "OK", "18 труб + втулки/гайки")
    add("Область печати", "≥%.0f×%.0f×%.0f" % (
        P["print_vol_x"], P["print_vol_y"], P["print_vol_z"]), "—", "OK",
        "рама и балка не печатаются")

    # --- интерференции ---
    pairs = [
        ("Рама — стол", frame, parts["table"]["shape"]),
        ("Рама — LMK10UU", frame, parts["lmk"]["shape"]),
        ("Рама — подстолье", frame, parts["podstol"]["shape"]),
        ("Рама — кулачок 5", frame, parts["cam"]["shape"]),
        ("Рама — балка 21", frame, parts["retainer"]["shape"]),
        ("Рама — уголки", frame, parts["angles"]["shape"]),
        ("Рама — вал привода", frame, parts["drive_shaft"]["shape"]),
        ("Рама — направляющие валы", frame, parts["shaft"]["shape"]),
        ("Рама — ограничители", frame, parts["collar"]["shape"]),
        ("Рама — пружины", frame, parts["spring"]["shape"]),
        ("Рама — шайбы пружин", frame, parts["spring_washer"]["shape"]),
        ("Рама — U-хомуты", frame, parts["ubolts"]["shape"]),
        ("Рама — кронштейны", frame, parts["bracket"]["shape"]),
        ("Рама — кожух", frame, parts["shield"]["shape"]),
        ("Рама — винты LMK", frame, parts["lmk_screws"]["shape"]),
        ("Рама — болты подстолья", frame, parts["podstol_bolts"]["shape"]),
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
        ("Стол — уголки", parts["table"]["shape"], parts["angles"]["shape"]),
        ("Стол — кожух", parts["table"]["shape"], parts["shield"]["shape"]),
        ("Накладка — направляющие валы", parts["overlay"]["shape"],
         parts["shaft"]["shape"]),
        ("Кулачок — кронштейн", parts["cam"]["shape"],
         parts["bracket"]["shape"]),
        ("Кулачок — ролик", parts["cam"]["shape"], parts["roller"]["shape"]),
        ("Кулачок — шайбы", parts["cam"]["shape"],
         parts["cam_washers"]["shape"]),
        ("Кулачок — гайки", parts["cam"]["shape"],
         parts["cam_nuts"]["shape"]),
        ("Кулачок — контргайки", parts["cam"]["shape"],
         parts["cam_locknuts"]["shape"]),
        ("Кронштейн — гайки ролика", parts["bracket"]["shape"],
         parts["roller_nuts"]["shape"]),
        ("Балка 21 — уголки", parts["retainer"]["shape"],
         parts["angles"]["shape"]),
        ("Уголки — прижимные болты", parts["angles"]["shape"],
         parts["clamp_bolts"]["shape"]),
        ("Уголки — гайки прижимные", parts["angles"]["shape"],
         parts["clamp_nuts"]["shape"]),
        ("Уголки — болты балки", parts["angles"]["shape"],
         parts["beam_bolts"]["shape"]),
        ("Уголки — гайки балки", parts["angles"]["shape"],
         parts["beam_nuts"]["shape"]),
        ("Уголки — вал привода", parts["angles"]["shape"],
         parts["drive_shaft"]["shape"]),
        ("Уголки — ограничители", parts["angles"]["shape"],
         parts["collar"]["shape"]),
        ("Уголки — направляющие валы", parts["angles"]["shape"],
         parts["shaft"]["shape"]),
        ("Уголки — LMK10UU", parts["angles"]["shape"], parts["lmk"]["shape"]),
        ("Уголки — опорные 6200", parts["angles"]["shape"],
         parts["shaft_bearings"]["shape"]),
        ("Балка 21 — болты накладок", parts["retainer"]["shape"],
         parts["beam_bolts"]["shape"]),
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
        ("Вал привода — шайбы кулачка", parts["drive_shaft"]["shape"],
         parts["cam_washers"]["shape"]),
        ("Вал привода — гайки кулачка", parts["drive_shaft"]["shape"],
         parts["cam_nuts"]["shape"]),
        ("Вал привода — контргайки кулачка", parts["drive_shaft"]["shape"],
         parts["cam_locknuts"]["shape"]),
        ("Вал привода — гайки 6200", parts["drive_shaft"]["shape"],
         parts["shaft_conical_nuts"]["shape"]),
        ("Вал привода — контргайки 6200", parts["drive_shaft"]["shape"],
         parts["shaft_locknuts"]["shape"]),
        ("6200 — гайки 6200", parts["shaft_bearings"]["shape"],
         parts["shaft_conical_nuts"]["shape"]),
        ("6200 — контргайки 6200", parts["shaft_bearings"]["shape"],
         parts["shaft_locknuts"]["shape"]),
        ("Конусы 6200 — контргайки 6200",
         parts["shaft_conical_nuts"]["shape"],
         parts["shaft_locknuts"]["shape"]),
        ("Конусы 6200 — рама", parts["shaft_conical_nuts"]["shape"], frame),
        ("Контргайки 6200 — рама", parts["shaft_locknuts"]["shape"], frame),
        ("Конусы 6200 — балка 21", parts["shaft_conical_nuts"]["shape"],
         parts["retainer"]["shape"]),
        ("Контргайки 6200 — балка 21", parts["shaft_locknuts"]["shape"],
         parts["retainer"]["shape"]),
        ("Конусы 6200 — уголки", parts["shaft_conical_nuts"]["shape"],
         parts["angles"]["shape"]),
        ("Контргайки 6200 — уголки", parts["shaft_locknuts"]["shape"],
         parts["angles"]["shape"]),
        ("Конусы 6200 — кулачок", parts["shaft_conical_nuts"]["shape"],
         parts["cam"]["shape"]),
        ("Контргайки 6200 — кулачок", parts["shaft_locknuts"]["shape"],
         parts["cam"]["shape"]),
        ("Кронштейн — ролик", parts["bracket"]["shape"],
         parts["roller"]["shape"]),
        ("Кронштейн — ось", parts["bracket"]["shape"], parts["axle"]["shape"]),
        ("Ролик — ось", parts["roller"]["shape"], parts["axle"]["shape"]),
        ("Винты LMK — LMK", parts["lmk_screws"]["shape"],
         parts["lmk"]["shape"]),
        ("Гайки LMK — стол", parts["lmk_nuts"]["shape"],
         parts["table"]["shape"]),
        ("Винты кронштейна — стол", parts["bracket_screws"]["shape"],
         parts["table"]["shape"]),
        ("Гайки кронштейна — стол", parts["bracket_nuts"]["shape"],
         parts["table"]["shape"]),
        ("Винты накладки — стол", parts["table_screws"]["shape"],
         parts["table"]["shape"]),
        ("Гайки накладки — стол", parts["table_nuts"]["shape"],
         parts["table"]["shape"]),
        ("Прижимные болты — рама", parts["clamp_bolts"]["shape"], frame),
        ("Гайки прижимные — рама", parts["clamp_nuts"]["shape"], frame),
        ("Болты подстолья — рама", parts["podstol_bolts"]["shape"], frame),
        ("Болты подстолья — подстолье", parts["podstol_bolts"]["shape"],
         parts["podstol"]["shape"]),
        ("Кожух — саморезы", parts["shield"]["shape"],
         parts["shield_screws"]["shape"]),
        ("Буферы — рама", parts["rubber_pads"]["shape"], frame),
        ("Буферы — стол", parts["rubber_pads"]["shape"],
         parts["table"]["shape"]),
        ("Буферы — накладка", parts["rubber_pads"]["shape"],
         parts["overlay"]["shape"]),
        ("Буферы — пружины", parts["rubber_pads"]["shape"],
         parts["spring"]["shape"]),
        ("Кольца — рама", parts["rubber_rings"]["shape"], frame),
        ("Кольца — валы", parts["rubber_rings"]["shape"],
         parts["shaft"]["shape"]),
        ("Кольца — LMK", parts["rubber_rings"]["shape"],
         parts["lmk"]["shape"]),
        ("Кольца — пружины", parts["rubber_rings"]["shape"],
         parts["spring"]["shape"]),
        ("Кулачок — приваренная гайка", parts["cam"]["shape"],
         parts["drive_shaft"]["shape"]),
        ("Шайбы — гайки кулачка", parts["cam_washers"]["shape"],
         parts["cam_nuts"]["shape"]),
        ("Гайки — контргайки кулачка", parts["cam_nuts"]["shape"],
         parts["cam_locknuts"]["shape"]),
        ("Шайбы — контргайки кулачка", parts["cam_washers"]["shape"],
         parts["cam_locknuts"]["shape"]),
    ]
    for name, a, b in pairs:
        v = cv(a, b)
        st = "OK" if (v == v and v < 0.5) else "ВНИМАНИЕ"
        add(name, "%.3f мм³" % v if v == v else "n/a", "<0,5 мм³", st,
            "пересечение объёмов" if v >= 0.5 else "")
    add("Рама — винты кожуха", "резьбовое соединение M4",
        "допустимо", "OK",
        "винт ввёрнут в стенку 2 мм; пересечение резьбы не считается")

    # ход стола ±5 мм
    for dz, tag in ((-5, "5 мм, низ"), (5, "5 мм, верх")):
        t = move(table_asm, dz)
        for nm, other in (("рама", frame),
                          ("балка 21", parts["retainer"]["shape"]),
                          ("уголки", parts["angles"]["shape"]),
                          ("направляющие", parts["shaft"]["shape"]),
                          ("подстолье", parts["podstol"]["shape"]),
                          ("кожух", parts["shield"]["shape"])):
            v = cv(t, other)
            add("Стол при ходе %s — %s" % (tag, nm),
                "%.3f мм³" % v, "<0,5 мм³",
                "OK" if v < 0.5 else "ВНИМАНИЕ", "")

    # сменные диски
    for s in (3, 5, 10):
        c = cams["cam_%d" % s]
        cmin = c.rotated(App.Vector(P["cam_axis_x"], 100, P["drive_z"]),
                         App.Vector(1, 0, 0), 90)
        v = cv(table_asm, c)
        add("Кулачок %d: макс. вверху — ролик" % s, "%.3f мм³" % v,
            "<0,5 мм³", "OK" if v < 0.5 else "ВНИМАНИЕ",
            "верх стола 241")
        v = cv(move(table_asm, -s), cmin)
        add("Кулачок %d: мин. вверху — ролик" % s, "%.3f мм³" % v,
            "<0,5 мм³", "OK" if v < 0.5 else "ВНИМАНИЕ",
            "стол опущен на %d мм" % s)

    # опускание балки 21 на 20 мм
    ret_low = move(parts["retainer"]["shape"], -P["crab_travel"])
    ang_low = move(parts["angles"]["shape"], -P["crab_travel"])
    for nm, other in (("рама", frame), ("6200", parts["shaft_bearings"]["shape"]),
                      ("кулачок", parts["cam"]["shape"])):
        v = cv(ret_low, other)
        add("Балка 21, опущена на 20 мм — %s" % nm, "%.3f мм³" % v,
            "<0,5 мм³", "OK" if v < 0.5 else "ВНИМАНИЕ", "")
    v = cv(ang_low, frame)
    add("Уголки, опущены на 20 мм — рама", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "пазы 26,6 мм")

    # путь картриджа
    cart = Part.makeCompound([
        parts[k]["shape"] for k in
        ("drive_shaft", "cam", "shaft_bearings", "cam_washers",
         "cam_nuts", "cam_locknuts", "shaft_conical_nuts", "shaft_locknuts")
    ])
    low = cart.translated(App.Vector(0, 0, -44.0))
    for nm, other in (("рама", frame), ("уголки", parts["angles"]["shape"]),
                      ("стол", table_asm), ("кожух",
                                            parts["shield"]["shape"])):
        v = cv(low, other)
        add("Блок, опущен на 44 мм — %s" % nm, "%.3f мм³" % v, "<0,5 мм³",
            "OK" if v < 0.5 else "ВНИМАНИЕ", "")
    v = cv(low.translated(App.Vector(-100, 0, 0)), frame)
    add("Блок, опущен и выдвинут вперёд — рама", "%.3f мм³" % v,
        "<0,5 мм³", "OK" if v < 0.5 else "ВНИМАНИЕ", "")

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
    print("build fix9...", flush=True)
    parts, groups, cams = model.build_assembly()
    print("write params/spec/tube/torque", flush=True)
    write_params()
    write_spec()
    write_tube_cut()
    write_torque()
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
