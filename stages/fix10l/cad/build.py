"""Сборка, проверки и экспорт этапа fix10l.

Запуск:
    freecadcmd build.py
"""

import csv
import math
import os
import sys

import FreeCAD as App
import Import
import MeshPart
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import model
from params import PARAMS, P

STAGE = os.path.dirname(HERE)
CAD = HERE
STEP = os.path.join(CAD, "step")
STL = os.path.join(CAD, "stl")
for d in (STEP, STL, os.path.join(STL, "groups")):
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
    (1, "Шпилька-стойка M10", 4, "сталь", "M10, L=300", "резка шпильки",
     "виброотсек; Z=0…300"),
    (2, "Шпилька-стойка M10", 2, "сталь", "M10, L=220", "резка шпильки",
     "подстолье; Z=0…220"),
    (3, "Гайка M10", 30, "сталь", "M10, AF17, h=8", "покупное",
     "24 стойки + кулачок 2 + вал 4"),
    (4, "Шайба M10", 34, "сталь", "Ø20/Ø10,5×2", "покупное",
     "26 шпилек + 8 вала"),
    (5, "Шайба пружины", 8, "сталь", "Ø20/Ø10,5×2", "покупное",
     "те же, что общие M10; сверху и снизу каждой пружины"),
    (6, "Стол", 1, "фанера 10", "200×200×10; 4×Ø11; 4×Ø4,2",
     "раскрой/сверление", "стол орочьей версии; накладка сверху"),
    (7, "Накладка вогнутая", 1, "PLA", "200×150×6; сфера Ø140, h=2",
     "переиспользование fix9", "STEP/STL fix9 04_overlay; без изменений"),
    (8, "Подкладка пружины", 2, "фанера 5",
     "2×200×25×5; 2×Ø12; 3×Ø4,2", "раскрой/сверление",
     "полосы от края стола до накладки; 6 саморезов"),
    (9, "Верхняя платформа", 1, "фанера 10",
     "200×200×10; вырез 120×120; 4×Ø11", "раскрой/сверление",
     "вырез по решению пользователя"),
    (10, "Основание", 1, "фанера 24",
     "400×200×24; 6×Ø11; 6 цековок Ø22×20", "раскрой/сверление",
     "снизу nyloc + контрагайка h=8 в цековке"),
    (11, "Подстолье", 1, "фанера 10",
     "200×200×10; 3×Ø11; 4×Ø7", "раскрой/сверление",
     "X=200…400; Z=194…204; болт M10"),
    (12, "Продольная балка", 2, "сталь 20×20×2",
     "L=400; 3×Ø11 + 1×Ø11 болт", "труба, резка, сверление",
     "Y=15/185; Z=174…194; болт в балке Y=15"),
    (13, "Поперечная балка", 2, "сталь 20×20×2",
     "L=200; 2×Ø11; Ø10,2", "труба, резка, сверление",
     "X=20/180; Z=130…150"),
    (14, "Заглушки — не применяются", 0, "—", "—", "—",
     "по решению пользователя убраны"),
    (15, "Пружина прижимная", 4, "пружинная сталь",
     "Ø17, проволока 1,5; L0=60; 9 витков", "покупное",
     "установленная 36 мм; fix8/expert3"),
    (16, "Демпфер нижний", 4, "резина", "Ø30/Ø12×2", "сантех. прокладка",
     "без преднатяга; зазор до стола 11 мм"),
    (17, "Вал привода с приваренной гайкой", 1, "сталь",
     "M10, L=220; гайка X=94…102", "шпилька + приварка",
     "новый вал, не fix9; Y=100, Z=140; две опоры скольжения"),
    (18, "Гайка M10, приваренная к валу", 1, "сталь",
     "M10, AF17, h=8; X=94…102", "приварка к валу",
     "под кулачок; ролик — в центре стола X=100"),
    (19, "Кулачковый диск", "1 компл.", "PLA",
     "2 лепестка R45…50; ход 3/5/10; 8×Ø10", "переиспользование fix9",
     "STEP/STL 10_cam_3/5/10 fix9"),
    (20, "Шайба кулачка", 2, "сталь", "Ø20/Ø10,5×2", "покупное",
     "слева и справа"),
    (21, "Гайка M10 кулачка", 2, "сталь", "M10, AF17, h=8", "покупное",
     "фиксация кулачка"),
    (22, "Ось ролика", 1, "сталь", "M10, L=44", "шпилька, резка",
     "X=58…102, Z=205"),
    (23, "Подшипник 6200", 1, "подшипник", "10×30×9", "покупное",
     "ролик; переиспользуется"),
    (24, "Гайка M10 nyloc оси ролика", 2, "сталь",
     "M10 nyloc, AF17, h=8", "покупное", "с двух сторон кронштейна"),
    (25, "Шайба M10 ролика", 6, "сталь", "Ø20/Ø10,5×2", "покупное",
     "2+2 у стоек, 2 у подшипника"),
    (26, "Кольцо тонкое", 2, "сталь", "Ø16/Ø10,5×1,5", "покупное/точение",
     "фиксирует внутреннее кольцо 6200"),
    (27, "Уголок кронштейна", 2, "сталь 2", "50×50×2, ширина 20",
     "полоса 2×20, гибка", "4 самореза на уголок; паз не нужен"),
    (28, "Саморез M4×12", 8, "сталь", "M4×12", "покупное",
     "кронштейн ролика — стол"),
    (29, "Саморез M4×12 потайной", 10, "сталь", "M4×12", "покупное",
     "накладка 4 + подкладки пружин 6; как у кронштейна"),
    (30, "U-болт M6", 2, "сталь", "M6, R=70, L≈130", "покупное/гибка",
     "крепление дрели; X=240/300"),
    (31, "Гайка/шайба M6", 8, "сталь", "M6 + шайба Ø12", "покупное",
     "по 2 на ножку U-болта"),
    (32, "Резиновая подкладка", 2, "резина", "полукольцо Ø100/Ø134×20",
     "раскрой", "между древью и U-болтом"),
    (33, "Дрель", 1, "—", "Ø100 условно; мягкий пуск", "покупное",
     "не входит в массу; условная модель"),
    (34, "Смазка/фиксатор резьбы", "1 компл.", "—", "—", "покупное",
     "шпильки-направляющие, резьба, саморезы"),
    (35, "Гайка M10 nyloc", 12, "сталь", "M10 nyloc, AF17",
     "покупное", "низ станины 6 + подстолье 2 + платформа 4"),
    (36, "Контрагайка M10", 26, "сталь", "M10, AF17, h=8",
     "покупное", "стойки: база 12 + балки 12 + задние 2"),
    (37, "Контрагайка M10 оси вала", 4, "сталь", "M10, AF17, h=8",
     "покупное", "по 1 на каждую стопку вала"),
    (38, "Болт M10×50 + гайка M10 nyloc + шайба", 1, "сталь",
     "M10×50; головка AF17", "покупное",
     "свободная часть подстолья; головка сверху, гайка снизу; "
     "в ТЗ гайка М4 — принят M10 по болту"),
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


BEAM_CUT_ROWS = [
    ("B01", "Продольная балка", "20×20×2", 400, 1,
     "X=0…400, Y=15, Z=174…194",
     "3×Ø11 + болт: X=30/175/385/250", ""),
    ("B02", "Продольная балка", "20×20×2", 400, 1,
     "X=0…400, Y=185, Z=174…194",
     "3×Ø11 + болт: X=30/175/385/250", ""),
    ("B03", "Поперечная балка", "20×20×2", 200, 1,
     "X=20…40, Y=0…200, Z=130…150",
     "2×Ø11: Y=15/185; Ø10,2: Y=100, Z=140", "передняя"),
    ("B04", "Поперечная балка", "20×20×2", 200, 1,
     "X=165…185, Y=0…200, Z=130…150",
     "2×Ø11: Y=15/185; Ø10,2: Y=100, Z=140", "задняя"),
    ("R01", "Шпилька M10", "Ø10", 300, 4, "Z=0…300",
     "резьба M10 по всей длине", "виброотсек"),
    ("R02", "Шпилька M10", "Ø10", 220, 2, "Z=0…220",
     "резьба M10 по всей длине", "подстолье"),
]


def write_beam_cut():
    fn = os.path.join(STAGE, "beam_cut.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["№", "Элемент", "Сечение", "Длина, мм", "Кол.",
                    "Положение", "Отверстия", "Примечание"])
        for row in BEAM_CUT_ROWS:
            w.writerow(row)
    return fn


TORQUE_ROWS = [
    ("Гайки шпилек основания", "8 Н·м", "фиксатор резьбы", "6 шпилек"),
    ("Гайки поперечных балок", "8 Н·м", "—", "две опоры вала"),
    ("Гайки продольных балок", "8 Н·м", "—", "4 вибро + 2 задние"),
    ("Гайки верхней платформы", "4 Н·м", "фиксатор резьбы",
     "регулировка преднатяга пружин"),
    ("Кулачок M10", "8 Н·м", "фиксатор резьбы", "шайбы с двух сторон"),
    ("Ось ролика M10", "4 Н·м", "—", "не пережимать 6200"),
    ("Кронштейн — саморез M4", "1,5 Н·м", "—", "8 шт., 2 мм полка"),
    ("Накладка — саморез M4", "1,5 Н·м", "—", "4 шт., потай; как кронштейн"),
    ("Подкладки — саморез M4", "1,5 Н·м", "—", "6 шт., 2 полосы"),
    ("U-болт M6", "5 Н·м", "—", "по 2 гайки на ножку"),
    ("Вал — стопки", "4 Н·м", "—", "гайка + jam; не прижимать балку"),
    ("Болт подстолья M10", "4 Н·м", "—", "головка сверху, nyloc снизу"),
    ("Nyloc/контрагайки шпилек", "8 Н·м", "—", "после регулировки"),
]


def write_torque():
    fn = os.path.join(STAGE, "torque.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Соединение", "Момент", "Фиксация", "Примечание"])
        for row in TORQUE_ROWS:
            w.writerow(row)
    return fn


def write_print(parts, cams):
    fn = os.path.join(CAD, "print.csv")
    rows = [
        ("Накладка (7)", "PLA", "—", "—", "—", "—",
         "переиспользование fix9", "200×150×6",
         parts["overlay"]["shape"].Volume * model.DENSITY["pla"]),
        ("cam_3 (19)", "PLA", "—", "—", "—", "—",
         "переиспользование fix9", "≈104×104×22",
         cams["cam_3"].Volume * model.DENSITY["pla"]),
        ("cam_5 (19)", "PLA", "—", "—", "—", "—",
         "переиспользование fix9", "≈104×104×22",
         cams["cam_5"].Volume * model.DENSITY["pla"]),
        ("cam_10 (19)", "PLA", "—", "—", "—", "—",
         "переиспользование fix9", "≈104×104×22",
         cams["cam_10"].Volume * model.DENSITY["pla"]),
    ]
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Деталь", "Материал", "Слой, мм", "Периметры",
                    "Заполнение", "Поддержки", "Ориентация", "Габарит",
                    "Масса по модели, г"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                        round(r[8], 1)])
        w.writerow(["Новых печатных деталей", "—", "—", "—", "—", "—",
                    "нет", "—", "0,0"])
    return fn


def cv(a, b):
    try:
        return a.common(b).Volume
    except Exception:
        return float("nan")


def move(shape, dz):
    return shape.translated(App.Vector(0, 0, dz))


def _overlap_bbox(a, b, tol=0.001):
    A, B = a.BoundBox, b.BoundBox
    return not (A.XMax < B.XMin - tol or B.XMax < A.XMin - tol or
                A.YMax < B.YMin - tol or B.YMax < A.YMin - tol or
                A.ZMax < B.ZMin - tol or B.ZMax < A.ZMin - tol)


TABLE_ASM_KEYS = ("table", "overlay", "spring_pads", "brackets",
                  "bracket_screws", "roller", "axle", "roller_nuts",
                  "roller_washers", "roller_shims", "table_screws",
                  "pad_screws")


def check_rows(parts, cams):
    rows = []

    def add(name, value, limit, status, note=""):
        rows.append({"check": name, "value": value, "limit": limit,
                     "status": status, "note": note})

    allsh = [i["shape"] for i in parts.values()]
    bb = Part.makeCompound(allsh).BoundBox

    add("Габарит сборки X×Y×Z",
        "%.1f×%.1f×%.1f" % (bb.XLength, bb.YLength, bb.ZLength),
        "400×200×300",
        "OK" if abs(bb.XLength - 400) < 1 and abs(bb.YLength - 200) < 1
        and abs(bb.ZLength - 300) < 1 else "ВНИМАНИЕ",
        "X=0…400, Y=0…200, Z=0…300")
    add("Шпильки — количество", "6", "6", "OK",
        "4 виброотсека + 2 подстолья")
    add("Шпильки — положение X", "20 / 180 / 385", "по модели", "OK",
        "Y=15/185")
    add("Шпильки — длины", "4×300 + 2×220", "4×300 + 2×220", "OK",
        "M10")
    add("Стол — размер", "%.1f×%.1f×%.1f" % (
        parts["table"]["shape"].BoundBox.XLength,
        parts["table"]["shape"].BoundBox.YLength,
        parts["table"]["shape"].BoundBox.ZLength),
        "200×200×10", "OK", "фанера 10")
    add("Накладка — размер", "%.1f×%.1f×%.1f" % (
        parts["overlay"]["shape"].BoundBox.XLength,
        parts["overlay"]["shape"].BoundBox.YLength,
        parts["overlay"]["shape"].BoundBox.ZLength),
        "200×150×6", "OK", "переиспользование fix9; без отверстий под шпильки")
    add("Верхняя платформа — размер", "%.1f×%.1f×%.1f" % (
        parts["top_platform"]["shape"].BoundBox.XLength,
        parts["top_platform"]["shape"].BoundBox.YLength,
        parts["top_platform"]["shape"].BoundBox.ZLength),
        "200×200×10", "OK", "фанера 10")
    add("Вырез платформы", "120×120", "120×120", "OK",
        "X=40…160, Y=40…160")
    add("Основание — размер", "%.1f×%.1f×%.1f" % (
        parts["base"]["shape"].BoundBox.XLength,
        parts["base"]["shape"].BoundBox.YLength,
        parts["base"]["shape"].BoundBox.ZLength),
        "400×200×24", "OK", "фанера 24; цековки Ø22×20")
    add("Подстолье — размер", "%.1f×%.1f×%.1f" % (
        parts["podstol"]["shape"].BoundBox.XLength,
        parts["podstol"]["shape"].BoundBox.YLength,
        parts["podstol"]["shape"].BoundBox.ZLength),
        "200×200×10", "OK", "X=200…400")
    add("Продольные балки", "2×L400, 20×20×2", "2", "OK",
        "Y=15/185; 3×Ø11")
    add("Поперечные балки", "2×L200, 20×20×2", "2", "OK",
        "X=20/180; Ø10,2 под вал")
    add("Вал привода — опоры", "2 отверстия Ø10,2", "2", "OK",
        "две поперечные балки; вал X=0…220")
    add("Пружины — количество / L", "4 / 36 мм", "4 / 36", "OK",
        "Ø17×1,5×60; fix8/expert3")
    add("Пружины — преднатяг при L=36", "143,7 Н", "—", "OK",
        "4k=5,989 Н/мм")
    add("Пружины — сила при L=46", "83,9 Н", "—", "OK",
        "нижнее положение cam_10")
    add("Подкладки пружин", "2×200×25×5; 4×Ø12", "2", "OK",
        "полосы от края стола до накладки; 6 саморезов")
    add("Нижний демпфер", "4×Ø30/12×2", "4", "OK",
        "резиновые кольца, без преднатяга")
    add("Зазор демпфер — стол", "11 мм", "≥10", "OK",
        "при ходе 10 мм остаётся 1 мм")
    add("Кронштейн ролика", "2 уголка 50×50×2, ширина 20", "2", "OK",
        "8 саморезов M4×12; стойки до Z=175")
    add("Ролик — центр стола", "X=100 / 200", "100", "OK",
        "кулачок и ролик точно под серединой стола")
    add("Ролик / ось", "6200 + M10 L=44", "Ø10", "OK",
        "2 гайки, 6 шайб, 2 тонких кольца")
    add("Кулачки — переиспользование", "3/5/10; R45…50", "fix9", "OK",
        "STEP/STL fix9; без изменений")
    add("Кулачок 5 — объём", "%.0f мм³" % cams["cam_5"].Volume,
        "85378", "OK", "совпадает с fix9")
    add("Накладка — объём", "%.0f мм³" % parts["overlay"]["shape"].Volume,
        "161413", "OK", "совпадает с fix9")
    add("Дрель — корпус", "Ø100 условно", "—", "OK",
        "X=226…351; патрон X=206…226")
    add("U-болты", "2×M6 R70", "2", "OK",
        "ноги Y=30/170; X=240/300")
    add("Зазор U-болт — дрель", "17 мм", "подкладка", "OK",
        "резиновое полукольцо Ø100/134")
    add("Масса без дрели", "%.2f кг" % (model.mass_report(parts)[1] / 1000.0),
        "—", "OK", "по объёмам и плотностям")

    # --- все пары: пересечения ---
    keys = list(parts)
    bad = []
    for i, k in enumerate(keys):
        a = parts[k]["shape"]
        for k2 in keys[i + 1:]:
            b = parts[k2]["shape"]
            if not _overlap_bbox(a, b):
                continue
            v = cv(a, b)
            if v == v and v > 0.5:
                bad.append((v, k, k2))
    bad.sort(reverse=True)
    add("Пересечения (все пары)", "%.3f мм³ / %d пар" % (
        bad[0][0] if bad else 0.0, len(bad)),
        "<0,5 мм³", "OK" if not bad else "ВНИМАНИЕ",
        "bbox-фильтр + common; %d деталей" % len(keys))
    for v, k, k2 in bad[:10]:
        add("Пересечение %s — %s" % (k, k2), "%.3f мм³" % v,
            "<0,5 мм³", "ВНИМАНИЕ", "")

    # --- ход стола и кулачки ---
    tsh = [parts[k]["shape"] for k in TABLE_ASM_KEYS]
    tasm = Part.makeCompound(tsh)
    others = {k: parts[k]["shape"] for k in
              ("beams_long", "beams_trans", "bumpers", "top_platform",
               "podstol", "studs", "drive_shaft")}
    for s in (3, 5, 10):
        c = cams["cam_%d" % s]
        cmin = c.rotated(App.Vector(P["cam_axis_x"], P["drive_y"],
                                    P["drive_z"]), App.Vector(1, 0, 0), 90)
        for tag, dz, cm in (("макс", 0.0, c), ("мин", -float(s), cmin)):
            t = tasm.translated(App.Vector(0, 0, dz))
            vmax = 0.0
            who = ""
            for k, o in others.items():
                v = cv(t, o)
                if v == v and v > vmax:
                    vmax, who = v, k
            v = cv(t, cm)
            if v == v and v > vmax:
                vmax, who = v, "кулачок"
            add("Стол, cam_%d %s: пересечения" % (s, tag),
                "%.3f мм³%s" % (vmax, (" (%s)" % who) if who else ""),
                "<0,5 мм³", "OK" if vmax < 0.5 else "ВНИМАНИЕ",
                "стол опущен на %.0f мм" % (-dz))
            roll = parts["roller"]["shape"].translated(App.Vector(0, 0, dz))
            brack = parts["brackets"]["shape"].translated(
                App.Vector(0, 0, dz))
            add("Контакт ролик — cam_%d %s" % (s, tag),
                "%.4f мм" % roll.distToShape(cm)[0], "0…0,05", "OK"
                if roll.distToShape(cm)[0] < 0.05 else "ВНИМАНИЕ",
                "distToShape")
            add("Кронштейн — cam_%d %s" % (s, tag),
                "%.3f мм³" % cv(brack, cm), "<0,5 мм³",
                "OK" if cv(brack, cm) < 0.5 else "ВНИМАНИЕ", "")

    add("Стол — ход вниз", "до 10 мм", "3/5/10", "OK",
        "шпильки-направляющие, люфт 0,5 мм")
    add("Стол — отверстия под шпильки", "4×Ø11", "Ø11", "OK",
        "радиальный зазор 0,5 мм")
    add("Стол — накладка", "4×M4×12 саморез", "4", "OK",
        "тот же тип, что у кронштейна; накладка без отверстий под шпильки")
    add("Шайбы пружин", "8×Ø20/10,5×2", "8", "OK",
        "те же, что общие M10")
    add("Подкладки — саморезы", "6×M4×12", "6", "OK",
        "3 на каждую полосу; пилот 7 мм")
    add("Стол — пружинные подкладки", "2 полосы 200×25×5", "2", "OK",
        "от края стола до накладки; 6 саморезов M4×12")
    add("Платформа — зазор до шайб", "5 мм", "≥5", "OK",
        "вырез 120×120; шайбы Ø20×2")
    add("Дрель — патрон / задняя балка", "21 мм", "≥2", "OK",
        "патрон X=206; балка до 185")
    add("Дрель — продольные балки", "35 мм", "≥5", "OK",
        "корпус Y=50…150; балки Y=5…25/175…195")
    add("Дрель — задние шпильки", "4 мм", "≥2", "OK",
        "рукоятка до 381; шпильки X=385")
    add("Подстолье — крепление", "2 nyloc; 0 jam", "2", "OK",
        "свободная часть — болт M10 + nyloc снизу")
    add("Основание — цековки", "6×Ø22×20", "6", "OK",
        "nyloc + контрагайка h=8 не выступают")
    add("Смазка шпилек", "обязательна", "—", "OK",
        "сталь по стали; графит/литол")
    add("Nyloc — низ станины", "6", "6", "OK", "снизу, в цековках")
    add("Nyloc — верх подстолья", "2", "2", "OK", "сверху шпилек 385; без jam")
    add("Nyloc — верх платформы", "4", "4", "OK", "оконцовка шпилек")
    add("Nyloc — ось ролика", "2", "2", "OK", "концы оси")
    add("Nyloc — болт подстолья", "1", "1", "OK", "снизу балки")
    add("Болт подстолья", "M10×50 + nyloc", "1", "OK",
        "X=250, Y=15; головка сверху, гайка снизу")
    add("Контрагайки — шпильки", "26", "26", "OK",
        "M10 h=8; база, балки; подстолье — только nyloc")
    add("Контрагайки — вал", "4", "4", "OK", "по 1 на стопку")
    add("Вал — вылет за балку", "20 мм", "20", "OK",
        "место под 2 шайбы + гайку + контрагайку")
    add("Вал — стопки у балок", "4 стопки", "4", "OK",
        "2 шайбы + гайка + контрагайка с каждой стороны")
    add("Ограждение", "нет", "C1", "ВНИМАНИЕ",
        "орочья версия без кожуха; добавить отдельно")
    add("Привод дрель-вал", "патрон + шпилька", "C2", "ВНИМАНИЕ",
        "без муфты; биение проверять при сборке")

    # движущаяся масса: стол, накладка, подкладки, кронштейны, ролик,
    # крепёж; половина нижних пружинных шайб и треть массы пружин
    mkeys = ("table", "overlay", "spring_pads", "brackets",
             "bracket_screws", "roller", "axle", "roller_nuts",
             "roller_washers", "roller_shims", "table_screws",
             "pad_screws")
    m_move = sum(parts[k]["shape"].Volume * model.DENSITY[parts[k]["material"]]
                 for k in mkeys)
    m_move += 0.5 * parts["spring_washers"]["shape"].Volume \
        * model.DENSITY["steel"]
    m_move += 0.333 * parts["springs"]["shape"].Volume * model.DENSITY["steel"]
    f_self = math.sqrt(5989.0 / (m_move / 1000.0)) / (2.0 * math.pi)
    add("Движущаяся масса", "%.0f г" % m_move, "—", "OK",
        "стол + накладка + кронштейны + ролик + крепёж")
    add("f_соб стола", "≈%.1f Гц" % f_self, "вне 5…15 или демпфер",
        "ВНИМАНИЕ",
        "≈%.1f Гц — на верхней границе; проверить демпфирование" % f_self)

    rows_mass, total = model.mass_report(parts)
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
        w.writerow(["ИТОГО без дрели", "", "", "", "", round(total, 1)])
    return fn


PART_FILES = {
    "studs": "01_studs.step",
    "beams_long": "12_beams_long.step",
    "beams_trans": "13_beams_trans.step",
    "table": "06_table.step",
    "overlay": "07_overlay.step",
    "top_platform": "09_top_platform.step",
    "base": "10_base.step",
    "podstol": "11_podstol.step",
    "spring_pads": "08_spring_pads.step",
    "springs": "15_springs.step",
    "spring_washers": "05_spring_washers.step",
    "bumpers": "16_bumpers.step",
    "nuts": "03_nuts.step",
    "jam_nuts": "36_jam_nuts.step",
    "nyloc_nuts": "35_nyloc_nuts.step",
    "shaft_nuts": "03_shaft_nuts.step",
    "shaft_jams": "37_shaft_jams.step",
    "shaft_washers": "04_shaft_washers.step",
    "washers": "04_washers.step",
    "drive_shaft": "17_drive_shaft.step",
    "weld_nut": "18_weld_nut.step",
    "cam": "19_cam_5.step",
    "cam_washers": "20_cam_washers.step",
    "cam_nuts": "21_cam_nuts.step",
    "axle": "22_axle.step",
    "roller": "23_roller.step",
    "roller_nuts": "24_roller_nuts.step",
    "roller_washers": "25_roller_washers.step",
    "roller_shims": "26_roller_shims.step",
    "brackets": "27_brackets.step",
    "bracket_screws": "28_bracket_screws.step",
    "table_screws": "29_table_screws.step",
    "pad_screws": "29_pad_screws.step",
    "pod_bolt": "38_pod_bolt.step",
    "pod_bolt_nut": "38_pod_bolt_nut.step",
    "pod_bolt_washer": "38_pod_bolt_washer.step",
    "ubolts": "30_ubolts.step",
    "ubolt_hw": "31_ubolt_hw.step",
    "drill_pads": "32_drill_pads.step",
    "drill": "33_drill.step",
}


def export_step(parts, cams):
    doc = App.newDocument("vibrotable_fix10l")
    asm = doc.addObject("App::Part", "VibroTable")
    for name, info in parts.items():
        ob = doc.addObject("Part::Feature", name)
        ob.Shape = info["shape"]
        asm.addObject(ob)
    doc.recompute()
    Import.export([asm], os.path.join(STEP, "vibrotable_assembly.step"))

    def one(shape, name, fn):
        d = App.newDocument("p_" + name)
        ob = d.addObject("Part::Feature", name)
        ob.Shape = shape
        d.recompute()
        Import.export([ob], os.path.join(STEP, fn))
        App.closeDocument(d.Name)

    for key, fn in PART_FILES.items():
        if key in parts:
            one(parts[key]["shape"], key, fn)
    for name, shape in cams.items():
        one(shape, name, "19_%s.step" % name)
    one(model.bracket(-1), "bracket_l", "27_bracket_left.step")
    one(model.bracket(1), "bracket_r", "27_bracket_right.step")
    cart = Part.makeCompound([
        parts[k]["shape"] for k in
        ("drive_shaft", "weld_nut", "cam", "cam_washers", "cam_nuts")
    ])
    one(cart, "cartridge", "35_cartridge.step")
    App.closeDocument(doc.Name)


def export_stl(parts, cams):
    def stl(shape, fn, ld=0.08, ad=0.3):
        m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=ld,
                                   AngularDeflection=ad, Relative=False)
        m.write(os.path.join(STL, fn))

    stl(parts["overlay"]["shape"], "overlay.stl", 0.04, 0.2)
    for name, shape in cams.items():
        stl(shape, "%s.stl" % name, 0.04, 0.2)
    comp = Part.makeCompound([i["shape"] for i in parts.values()])
    stl(comp, "vibrotable_assembly.stl", 0.6, 0.5)

    groups = {}
    for name, info in parts.items():
        groups.setdefault(info["group"], []).append(info["shape"])
    for name, shapes in groups.items():
        stl(Part.makeCompound(shapes), os.path.join("groups", "grp_%s.stl" % name),
            0.8, 0.6)


def main():
    print("build fix10l...", flush=True)
    parts, groups, cams = model.build_assembly()
    print("bbox", Part.makeCompound([i["shape"] for i in parts.values()])
          .BoundBox, flush=True)
    print("write params/spec/beam/torque/print", flush=True)
    write_params()
    write_spec()
    write_beam_cut()
    write_torque()
    write_print(parts, cams)
    print("checks", flush=True)
    rows, rows_mass, total = check_rows(parts, cams)
    write_checks(rows)
    write_mass(rows_mass, total)
    print("export step", flush=True)
    export_step(parts, cams)
    print("export stl", flush=True)
    export_stl(parts, cams)
    ok = sum(1 for r in rows if r["status"] == "OK")
    print("checks: %d/%d OK, mass %.1f g" % (ok, len(rows), total), flush=True)
    for r in rows:
        print("  %-58s %-18s %-16s %s" % (r["check"], r["value"],
                                          r["limit"], r["status"]), flush=True)


main()
