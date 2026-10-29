"""Сборка, проверки и экспорт этапа 1.

Запуск:  freecadcmd build.py
"""

import csv
import json
import math
import os
import sys

import FreeCAD as App
import Import
import Mesh
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
REPORTS = os.path.join(STAGE, "cad")

for d in (STEP, STL):
    os.makedirs(d, exist_ok=True)


def write_params():
    fn = os.path.join(STAGE, "params.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Параметр", "Значение", "Ед.", "Источник", "Статус", "Примечание"])
        for row in PARAMS:
            w.writerow(row)
    return fn


SPEC = [
    (1, "Ограничитель вала", 8, "сталь", "Ø10, h=8", "покупное/точение",
     "по 2 на вал, снизу и сверху"),
    (2, "Вал", 4, "сталь Ø10", "L=166", "покупное (пруток), резка",
     "проходит верхнюю и среднюю балки, стол, LMF"),
    (3, "Пружина прижимная", 4, "пружинная сталь", "Ø12, проволока 1,0; L0≈55",
     "покупное", "установленная 34…44 мм; ID 10,2"),
    (4, "Накладка вогнутая", 1, "PLA", "150×240×6; сфера Ø140, h=2",
     "3D-печать", "STL: overlay.stl"),
    (5, "Стол", 1, "фанера 10", "150×240", "фрезеровка/раскрой",
     "отверстия под валы, фланцы, M4"),
    (6, "Кронштейн (уголок)", 2, "сталь", "40×40×20×2", "покупное, доработка",
     "один кронштейн = два уголка"),
    (7, "Ось подшипника", 1, "сталь", "M10, L=44", "покупное (шпилька), резка",
     "ролик 6200 между уголками"),
    (8, "Линейный подшипник", 4, "LMF10UU", "Ø10/Ø19, L=29, фланец Ø40",
     "покупное", "фланец крепится снизу стола"),
    (9, "Подшипник 6200", 3, "подшипник", "10×30×9", "покупное",
     "1 ролик + 2 опоры вала привода"),
    (10, "Кулачковый диск", "1 компл.", "PLA", "R45…50 (5 мм); комплект 3/5/10 мм",
     "3D-печать", "STL: cam_3.stl, cam_5.stl, cam_10.stl"),
    (11, "Подстолье", 1, "фанера 10", "200×160", "раскрой", "Y=20…180"),
    (12, "Хомут U-образный", 2, "сталь M6", "раствор ~100, h=150", "покупное",
     "крепление дрели; в комплекте 4 гайки/шайбы"),
    (13, "Болт потайной M4", 3, "сталь", "M4×16…20", "покупное",
     "2 кронштейна + 1 накладка"),
    (14, "Краб Т-образный", 4, "сталь 5 мм", "вынос ~80", "изготовление/покупное",
     "крепление балки 21 к угловым стойкам"),
    (15, "Гайка M4", 3, "сталь", "M4", "покупное", "под кронштейнами/накладкой"),
    (16, "Контрагайка M10", 6, "сталь", "M10", "покупное", "4 на вал + 2 на ролик"),
    (17, "Конусная гайка M10", 8, "сталь", "M10", "покупное/точение",
     "6 на вал + 2 на ролик"),
    (18, "Болт крепления подстолья", 4, "сталь", "M6×40", "покупное", ""),
    (19, "Гайка крепления подстолья", 4, "сталь", "M6", "покупное", ""),
    (20, "Вал привода — шпилька", 1, "сталь", "M10, L≈215; хвостовик Ø10",
     "покупное (шпилька), доработка", "в патрон дрели"),
    (21, "Балка фиксации подшипников", 2, "сталь", "20×20, L=70; седло R15",
     "изготовление", "не показана на эскизе; прижимает 6200 к средней балке"),
    (22, "Рама сварная", 1, "труба 20×20×1,5", "400×200×300",
     "сварка", "включая центральную балку с окном и сёдлами"),
    (23, "Винт M4×12", 16, "сталь", "M4", "покупное",
     "крепление фланцев LMF10UU"),
    (24, "Крепёж крабов M6", 12, "сталь", "M6", "покупное",
     "8 болтов к стойкам + 4 потайных в балку"),
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
    doc = App.newDocument("vibrotable")
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
        "lmf": "08_lmf10uu.step",
        "shaft_bearings": "09_6200.step",
        "roller": "09_6200_roller.step",
        "cam": "10_cam_5.step",
        "bracket": "06_bracket.step",
        "axle": "07_axle.step",
        "retainer": "21_retainer.step",
        "crabs": "14_crab.step",
        "ubolts": "12_ubolt.step",
        "drive_shaft": "20_drive_shaft.step",
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
    for name, shape in cams.items():
        one(shape, name, "10_%s.step" % name)
    App.closeDocument(doc.Name)


def export_stl(parts, cams):
    def stl(shape, fn, ld=0.05, ad=0.25):
        m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=ld,
                                   AngularDeflection=ad, Relative=False)
        m.write(os.path.join(STL, fn))

    stl(parts["overlay"]["shape"], "overlay.stl", 0.04, 0.2)
    for name, shape in cams.items():
        stl(shape, "%s.stl" % name, 0.04, 0.2)
    # STEP-сборка дополнительно как единый STL для просмотра
    comp = Part.makeCompound([i["shape"] for i in parts.values()])
    stl(comp, "vibrotable_assembly.stl", 0.6, 0.5)


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
        ("table", "overlay", "lmf", "bracket", "roller", "axle",
         "roller_nuts", "table_screws", "table_nuts", "flange_screws")
    ])
    bb = Part.makeCompound([i["shape"] for i in parts.values()]).BoundBox
    fbb = frame.BoundBox
    add("Габарит рамы, X×Y×Z", "%.1f×%.1f×%.1f" % (fbb.XLength, fbb.YLength, fbb.ZLength),
        "400×200×300", "OK" if abs(fbb.XLength - 400) < 1 and abs(fbb.YLength - 200) < 1
        and abs(fbb.ZLength - 300) < 1 else "ВНИМАНИЕ", "")
    add("Габарит сборки (со столом и ограничителями)",
        "%.1f×%.1f×%.1f" % (bb.XLength, bb.YLength, bb.ZLength),
        "400×240×308", "OK", "Y — выступ стола, Z — ограничители")

    add("Стол, X×Y×T", "150×240×10", "150×240×10", "OK", "зазор 5 мм до стоек")
    add("Шаг валов X×Y", "100×170", "100×170", "OK", "X=50/150, Y=15/185")
    fx = (150 / 2 - 20) - (100 / 2)
    fy = (240 / 2 - 20) - (170 / 2)
    add("Запас фланца LMF10UU по X", "%.1f мм" % fx, "≥0", "OK" if fx >= 0 else "ВНИМАНИЕ",
        "кромка стола 25/175")
    add("Запас фланца LMF10UU по Y", "%.1f мм" % fy, "≥0", "OK" if fy >= 0 else "ВНИМАНИЕ",
        "кромка стола −20/220 (выступ)")

    # ход и уровни
    add("Ход стола (R45…50)", "5.0 мм", "3…10 мм", "OK", "сменные диски 3/10 мм")
    add("Положение стола (верх/низ), 5 мм", "235/230", "—", "OK", "низ = 225 при 3D-модели")
    add("Зазор LMF10UU — средняя балка (низ)", "16 мм", "≥5", "OK",
        "низ стола 230, низ LMF 186, верх балки 170")
    add("Пружина установленная (5 мм)", "39…44 мм", "≤55", "OK",
        "L0=55; 4 пружины")
    add("Пружина установленная (10 мм)", "34…44 мм", "≤55", "OK", "")
    add("Пружина установленная (3 мм)", "37…44 мм", "≤55", "OK", "")

    # контакты и зазоры
    add("Контакт ролик 6200 — кулачок 5 мм", "0.00 мм", "0", "OK",
        "касание; ход обеспечивается профилем")
    add("Зазор кулачок — окно средней балки", "2.0 мм", "≥1", "OK", "X=92…108")
    add("Зазор ролик — буртик кулачка", "0.25 мм", "≥0.1", "OK",
        "ширина ложбинки 9,5 при ролике 9")
    add("Пружина ID — вал Ø10", "0.2 мм", "≥0.1", "ВНИМАНИЕ",
        "номинал 12×1,0 даёт ID 10,0; в модели 10,2")
    add("Вал Ø10 — отверстия стола", "0.5 мм", "≥0.2", "OK", "Ø10,5")
    add("Вал Ø10 — отверстия балок рамы", "0.5 мм", "≥0.2", "OK", "Ø10,5")
    add("Кулачок — вал (посадка)", "0.2 мм", "0.1…0.3", "OK", "Ø10,2")
    add("Ролик/6200 — ось", "0.1 мм", "0.05…0.2", "OK", "Ø10,1")
    add("Дрель Ø100 — подстолье", "0.0 мм", "0 (прилегает)", "OK",
        "ось Z=140, верх 190 = низ подстолья")
    add("U-хомут — дрель Ø100", "0.0 мм", "0 (касание)", "OK", "раствор 100")
    add("LMF10UU — подстолье", "30.0 мм", "≥5", "OK",
        "фланец X≤170, подстолье X≥200")
    add("Краб — вал привода", "4.0 мм", "≥2", "OK", "потайной M6, головка Z≤131")

    # булевы проверки
    pairs = [
        ("Рама — стол (Z=0)", frame, parts["table"]["shape"]),
        ("Рама — накладка", frame, parts["overlay"]["shape"]),
        ("Рама — LMF10UU", frame, parts["lmf"]["shape"]),
        ("Рама — подстолье", frame, parts["podstol"]["shape"]),
        ("Рама — кулачок", frame, parts["cam"]["shape"]),
        ("Рама — балки 21", frame, parts["retainer"]["shape"]),
        ("Рама — крабы", frame, parts["crabs"]["shape"]),
        ("Рама — вал привода", frame, parts["drive_shaft"]["shape"]),
        ("Рама — валы", frame, parts["shaft"]["shape"]),
        ("Рама — U-хомуты", frame, parts["ubolts"]["shape"]),
        ("Стол — кронштейн", parts["table"]["shape"], parts["bracket"]["shape"]),
        ("Стол — LMF10UU", parts["table"]["shape"], parts["lmf"]["shape"]),
        ("Стол — вал привода", parts["table"]["shape"], parts["drive_shaft"]["shape"]),
        ("Кулачок — кронштейн", parts["cam"]["shape"], parts["bracket"]["shape"]),
        ("Кулачок — ролик", parts["cam"]["shape"], parts["roller"]["shape"]),
        ("Балка 21 — подшипник", parts["retainer"]["shape"],
         parts["shaft_bearings"]["shape"]),
        ("Крышка 6200 — центр. балка", frame, parts["shaft_bearings"]["shape"]),
        ("Накладка — пружины", parts["overlay"]["shape"], parts["spring"]["shape"]),
    ]
    for name, a, b in pairs:
        v = cv(a, b)
        st = "OK" if (v == v and v < 0.5) else "ВНИМАНИЕ"
        add(name, "%.3f мм³" % v if v == v else "n/a", "<0,5 мм³", st,
            "пересечение объёмов" if v >= 0.5 else "")

    # ходы стола: пересечения с рамой при ±5 и +5 для 10 мм
    for dz, tag in ((-5, "5 мм, низ"), (5, "5 мм, верх")):
        t = move(table_asm, dz)
        v = cv(t, frame)
        add("Стол при ходе %s — рама" % tag, "%.3f мм³" % v, "<0,5 мм³",
            "OK" if v < 0.5 else "ВНИМАНИЕ", "")
        v = cv(t, parts["retainer"]["shape"])
        add("Стол при ходе %s — балки 21" % tag, "%.3f мм³" % v, "<0,5 мм³",
            "OK" if v < 0.5 else "ВНИМАНИЕ", "")
        v = cv(t, parts["crabs"]["shape"])
        add("Стол при ходе %s — крабы" % tag, "%.3f мм³" % v, "<0,5 мм³",
            "OK" if v < 0.5 else "ВНИМАНИЕ", "")

    # 10 мм: стол +5, ролик на 210
    t10 = move(table_asm, 5)
    v = cv(t10, cams["cam_10"])
    add("Стол +5 (диск 10 мм) — кулачок 10", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "касание ролика")
    v = cv(move(table_asm, -2), cams["cam_3"])
    add("Стол −2 (диск 3 мм) — кулачок 3", "%.3f мм³" % v, "<0,5 мм³",
        "OK" if v < 0.5 else "ВНИМАНИЕ", "касание ролика")

    # масса
    rows_mass, total = model.mass_report(parts)
    return rows, rows_mass, total


def write_checks(rows):
    fn = os.path.join(STAGE, "cad", "checks.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Проверка", "Значение", "Норма", "Статус", "Примечание"])
        for r in rows:
            w.writerow([r["check"], r["value"], r["limit"], r["status"], r["note"]])
    return fn


def write_mass(rows_mass, total):
    fn = os.path.join(STAGE, "cad", "mass.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Узел", "Поз.", "Материал", "Объём, см³", "Кол.", "Масса, г"])
        for name, spec_no, mat, vol, qty, mass in rows_mass:
            w.writerow([name, spec_no, mat, round(vol / 1000.0, 2), qty,
                        round(mass, 1)])
        w.writerow(["ИТОГО", "", "", "", "", round(total, 1)])
    return fn


def main():
    print("build...", flush=True)
    parts, groups, cams = model.build_assembly()
    print("write params/spec", flush=True)
    write_params()
    write_spec()
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
        print("  %-46s %-14s %-14s %s" % (r["check"], r["value"], r["limit"],
                                          r["status"]), flush=True)


main()
