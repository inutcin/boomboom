#!/usr/bin/env python3
"""Третья инженерная экспертиза модели fix7: только пружины и контакт ролика.

Скрипт не меняет fix7. Читает params.csv, mass.csv и checks.csv, считает:
  * жёсткость, преднатяг, силы, напряжения и геометрию пружины;
  * фактический контакт ролика с кулачком (идеальная синусоида и 2-лепестковый
    профиль);
  * cad/calc.csv, cad/map.csv, ../findings.csv, ../fig/*.svg, ../pic/*.png.

Запуск:  python3 stages/expert3/cad/analysis.py
"""

from __future__ import annotations

import base64
import csv
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None

try:
    import cairosvg
except Exception:  # pragma: no cover
    cairosvg = None

ROOT = Path(__file__).resolve().parents[2]
FIX7 = ROOT / "fix7"
OUT = Path(__file__).resolve().parent
FIG = OUT.parent / "fig"
PIC = OUT.parent / "pic"
EXPERT3 = OUT.parent


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(value: str, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return default


PARAMS = {row["Параметр"]: row for row in read_csv(FIX7 / "params.csv")}
MASS = {row["Узел"]: num(row["Масса, г"])
        for row in read_csv(FIX7 / "cad" / "mass.csv")}
P = {key: num(row["Значение"]) for key, row in PARAMS.items()}

# ---------------------------------------------------------------------------
# исходные данные и допущения
# ---------------------------------------------------------------------------
GRAVITY = 9.80665
G_STEEL = 79300.0          # МПа, модуль сдвига пружинной стали
E_STEEL = 200000.0
E_PLA = 3500.0
NU_PLA = 0.35
RHO_STEEL = 7.85e-3        # г/мм³

SPRING_COUNT = 4
SPRING_OD = P["spring_od"]          # 12
SPRING_WIRE = P["spring_wire"]      # 1.0
SPRING_MEAN = SPRING_OD - SPRING_WIRE
SPRING_N = P["spring_turns"]        # 11
SPRING_FREE = P["spring_free"]      # 70
SPRING_INST = P["spring_inst"]      # 36
SPRING_BOTTOM = SPRING_INST + 10.0  # при диске 10 мм
SPRING_K = (G_STEEL * SPRING_WIRE ** 4 /
            (8 * SPRING_MEAN ** 3 * SPRING_N))
SPRING_KT = SPRING_COUNT * SPRING_K
SPRING_PRELOAD = SPRING_KT * (SPRING_FREE - SPRING_INST)
SPRING_BOTTOM_FORCE = SPRING_KT * (SPRING_FREE - SPRING_BOTTOM)
SPRING_COMPRESSION = SPRING_FREE - SPRING_INST
SPRING_SOLID = (SPRING_N + 2) * SPRING_WIRE
SPRING_SOLID_FORCE = SPRING_K * (SPRING_FREE - SPRING_SOLID)
SPRING_INDEX = SPRING_MEAN / SPRING_WIRE
WAHL = ((4 * SPRING_INDEX - 1) / (4 * SPRING_INDEX - 4) +
        0.615 / SPRING_INDEX)
SPRING_MASS = (math.pi * (SPRING_WIRE / 2) ** 2 *
               math.sqrt((math.pi * SPRING_MEAN) ** 2 +
                         (SPRING_FREE / SPRING_N) ** 2) * SPRING_N *
               RHO_STEEL)

M_TABLE = MASS["table"]
M_OVERLAY = MASS["overlay"]
M_BRACKET = MASS["bracket"]
M_AXLE = MASS["axle"]
M_ROLL_NUTS = MASS["roller_nuts"]
M_TABLE_SCREWS = MASS["table_screws"] + MASS["table_nuts"]
M_SPRING_WASHERS_LOWER = MASS["spring_washer"] / 2.0
M_BALL = 33.0
M_MOVING_REAL = (M_TABLE + M_OVERLAY + 4 * 45.0 + M_BRACKET + 15.0 +
                 M_AXLE + M_ROLL_NUTS + M_TABLE_SCREWS +
                 M_SPRING_WASHERS_LOWER + M_BALL) / 1000.0
M_SPRING_EFF = 4 * 2.4 / 3.0 / 1000.0
M_DYN = M_MOVING_REAL + M_SPRING_EFF
F_NAT = math.sqrt(SPRING_KT * 1000.0 / M_DYN) / (2 * math.pi)

CAM_STROKES = (3.0, 5.0, 10.0)
CAM_RMAX = P["cam_rmax"]
ROLLER_R = P["b6200_od"] / 2.0
CAM_CONTACT_RHO = 35.714        # радиус кривизны 10 мм в максимуме
CAM_CONTACT_L = P["b6200_w"]    # 9 мм


# ---------------------------------------------------------------------------
# расчёты
# ---------------------------------------------------------------------------
def spring_stress(force_per_spring: float, mean_d: float = SPRING_MEAN,
                  wire_d: float = SPRING_WIRE) -> float:
    c = mean_d / wire_d
    kw = ((4 * c - 1) / (4 * c - 4) + 0.615 / c)
    return kw * 8 * force_per_spring * mean_d / (math.pi * wire_d ** 3)


TAU_TOP = spring_stress(SPRING_PRELOAD / SPRING_COUNT)
TAU_BOTTOM = spring_stress(SPRING_BOTTOM_FORCE / SPRING_COUNT)
TAU_SOLID = spring_stress(SPRING_SOLID_FORCE)
TAU_MEAN = (TAU_TOP + TAU_BOTTOM) / 2.0
TAU_ALT = (TAU_TOP - TAU_BOTTOM) / 2.0


def contact_ideal(stroke: float, freq: float,
                  k_total: float = SPRING_KT,
                  preload: float = SPRING_PRELOAD,
                  bottom_force: float | None = None) -> dict:
    amp = stroke / 2.0 / 1000.0
    omega = 2 * math.pi * freq
    inertia = M_DYN * amp * omega ** 2
    if bottom_force is None:
        bottom_force = k_total * (SPRING_FREE - (SPRING_INST + stroke))
    return {
        "inertia": inertia,
        "top": preload + M_DYN * GRAVITY - inertia,
        "bottom": bottom_force + M_DYN * GRAVITY + inertia,
        "ratio_top": (preload + M_DYN * GRAVITY - inertia) / inertia,
        "ratio_bottom": (bottom_force + M_DYN * GRAVITY + inertia) / inertia,
    }


@lru_cache(maxsize=None)
def support_function(stroke: float) -> dict:
    """Опорная функция h(φ) и коэффициенты ускорения для 2-лепестков."""
    e = stroke / 2.0
    phi = np.linspace(0.0, 2.0 * math.pi, 1441)
    theta = np.linspace(0.0, 2.0 * math.pi, 3601)
    r = CAM_RMAX - e - e * np.cos(2.0 * theta)
    h = np.max(r[None, :] * np.cos(theta[None, :] - phi[:, None]), axis=1)
    d2 = np.gradient(np.gradient(h, phi), phi)
    it = int(np.argmin(np.abs(phi - math.pi / 2.0)))
    db = np.mean(np.r_[d2[-3:], d2[0:3]])
    dt = np.mean(d2[it - 2:it + 3])
    return {
        "coeff_top": abs(dt) / 4.0,
        "coeff_bottom": abs(db) / 4.0,
        "max_abs_d2": float(np.max(np.abs(d2))),
    }


def contact_actual(stroke: float, freq: float,
                   preload: float = SPRING_PRELOAD,
                   bottom_force: float | None = None) -> dict:
    sf = support_function(stroke)
    omega = 2 * math.pi * freq
    inertia_top = M_DYN * sf["coeff_top"] / 1000.0 * omega ** 2
    inertia_bottom = M_DYN * sf["coeff_bottom"] / 1000.0 * omega ** 2
    if bottom_force is None:
        bottom_force = SPRING_KT * (SPRING_FREE - (SPRING_INST + stroke))
    return {
        "top": preload + M_DYN * GRAVITY - inertia_top,
        "bottom": bottom_force + M_DYN * GRAVITY + inertia_bottom,
        "ratio_top": (preload + M_DYN * GRAVITY - inertia_top) / inertia_top,
        "ratio_bottom": (bottom_force + M_DYN * GRAVITY + inertia_bottom) /
                        inertia_bottom,
        "inertia_top": inertia_top,
        "inertia_bottom": inertia_bottom,
    }


def contact_hertz(force: float, rho_cam: float = CAM_CONTACT_RHO) -> tuple[float, float]:
    r_equiv = rho_cam * ROLLER_R / (rho_cam + ROLLER_R)
    inv_e = ((1 - NU_PLA ** 2) / E_PLA + (1 - 0.30 ** 2) / E_STEEL)
    e_star = 1.0 / inv_e
    b = math.sqrt(4 * force * r_equiv /
                  (math.pi * CAM_CONTACT_L * e_star))
    p0 = 2 * force / (math.pi * b * CAM_CONTACT_L)
    return b, p0


# вариант 8×Ø12×0,9 L0=70 (для сравнения)
K8 = G_STEEL * 0.9 ** 4 / (8 * (12 - 0.9) ** 3 * SPRING_N)
KT8 = 8 * K8
PRE8 = KT8 * (SPRING_FREE - SPRING_INST)
CONTACT8 = contact_ideal(10.0, 15.0, KT8, PRE8, KT8 * (SPRING_FREE - 46.0))
TAU8 = spring_stress(PRE8 / 8, 12 - 0.9, 0.9)
F_NAT8 = math.sqrt(KT8 * 1000.0 / M_DYN) / (2 * math.pi)
L0_MIN = SPRING_INST + (3 * contact_ideal(10.0, 15.0)["inertia"] -
                        M_DYN * GRAVITY) / SPRING_KT
K_MIN = ((3 * contact_ideal(10.0, 15.0)["inertia"] - M_DYN * GRAVITY) /
         (SPRING_FREE - SPRING_INST) / SPRING_COUNT)


# ---------------------------------------------------------------------------
# реестр замечаний
# ---------------------------------------------------------------------------
def build_findings() -> list[tuple[str, str, str, str, str, str, str]]:
    c10 = contact_ideal(10.0, 15.0)
    a10 = contact_actual(10.0, 15.0)
    _, p0_actual = contact_hertz(a10["bottom"])
    return [
        ("S1", "критичное", "Пружина 4×Ø12×1,0 L0=70 перегружена по напряжению",
         f"Преднатяг {SPRING_PRELOAD:.1f} Н, на пружину {SPRING_PRELOAD/4:.1f} Н; "
         f"τ верх {TAU_TOP:.0f} МПа, низ {TAU_BOTTOM:.0f} МПа, размах "
         f"{TAU_ALT*2:.0f} МПа; при сжатии до твёрдого {TAU_SOLID:.0f} МПа. "
         "Для пружинной проволоки Ø1,0 при C=11 это выше усталостного "
         "допустимого (ориентировочно 500…700 МПа).",
         "Перейти на 8…16 пружин с меньшим d (например, 8×Ø12×0,9 L0=70: "
         "k≈0,43, τ≈636 МПа) или на пружину с проверенным материалом/"
         "термообработкой; задать допускаемое τ и ресурс; испытать 10^6 циклов.",
         "τ_max ≤ допускаемого для материала; остаточная деформация ≤0,5 %; "
         "сила ±5 % после 10^6 циклов; протокол.",
         "S1"),
        ("S2", "критичное", "Контакт 1,48× по гармонической синусоиде — ниже цели 2×",
         f"На 15 Гц/10 мм: инерционная {c10['inertia']:.1f} Н, контакт "
         f"{c10['top']:.1f} Н, запас {c10['ratio_top']:.2f}; цель ≥2× "
         f"(≥{2*c10['inertia']:.1f} Н). По фактическому 2-лепестковому профилю "
         f"контакт {a10['top']:.1f} Н ({a10['ratio_top']:.2f}), но он не "
         f"гармонический (C8 expert2). Нужно L0≥{L0_MIN:.1f} мм или "
         f"k≥{K_MIN:.3f} Н/мм на пружину.",
         "Увеличить число/жёсткость пружин или L0; проверить оба закона "
         "движения — гармонический и фактический; не принимать запас только "
         "по негармоническому профилю.",
         "Контакт ≥2× инерционной на 15 Гц/10 мм и на всём диапазоне; "
         "для обоих профилей; протокол.",
         "S2"),
        ("S3", "важное", "Собственная частота 8,64 Гц остаётся внутри 5…15 Гц",
         f"L0 не входит в k, поэтому f_соб={F_NAT:.2f} Гц не изменилась; "
         "демпфирования нет. На 8,64 Гц/10 мм контакт положительный "
         f"({contact_ideal(10.0, F_NAT)['top']:.1f} Н), но силы и шум "
         "резонансные.",
         "Демпфер/полиуретановые втулки; либо изменить k/m так, чтобы f_соб "
         "была вне 5…15 Гц; проверить амплитуду на 8,64 Гц.",
         "f_соб вне 5…15 Гц или коэффициент демпфирования ≥0,1; амплитуда "
         "±0,2 мм на резонансе.",
         "S3"),
        ("S4", "важное", "Пружина ID 10,0 на валу Ø10; сжатие 34 мм",
         "Номинальная 12×1,0 даёт ID 10,0 при вале Ø10 (в модели 10,2); "
         "сжатие L0−36=34 мм (было 19). При сжатии витки могут уменьшать ID "
         "и тереться о вал; сила/износ/заклинивание.",
         "ID≥10,5: например, Ø12,5×1,0 (ID 10,5) или направляющая втулка "
         "Ø9,6; Ø12×0,9 даёт только 10,2. Проверить свободное скольжение.",
         "Зазор ID—вал ≥0,3 мм; пружина не касается вала; страгивание "
         "≤5 Н; износ вала ≤0,02 мм за 10 ч.",
         "S4"),
        ("S5", "важное", "Фактический 2-лепестковый профиль маскирует недостаток пружины",
         f"На 15 Гц/10 мм фактический контакт {a10['top']:.1f} Н сверху и "
         f"{a10['bottom']:.1f} Н снизу; p0≈{p0_actual:.1f} МПа на PLA-кулачке. "
         "Если C8 исправить на гармонический закон, контакт падает до "
         f"{c10['top']:.1f} Н (1,48). Нельзя принимать пружину по "
         "негармоническому профилю.",
         "Согласовать пружину и профиль кулачка; при гармоническом профиле "
         "увеличить пружинный пакет; при необходимости — стальная вставка/"
         "накладка в зоне контакта.",
         "Контакт ≥2× для гармонического и фактического профиля; "
         "p0 ≤ допускаемого для PLA/вставки; 10^6 циклов.",
         "S5"),
        ("S6", "пожелание", "Нет регулировки преднатяга и паспорта пружины",
         "L0=70 задана жёстко; допуск L0/k, материал, концы и ресурс не "
         "заданы; при отклонении L0 на ±1 мм контакт меняется на ±2,7 Н "
         "(≈4,5 %).",
         "Регулировочные шайбы/винт преднатяга; паспорт пружины (k, L0, "
         "материал, концы, допуск, ресурс); контроль силы при сборке.",
         "Преднатяг регулируется; сила ±5 %; паспорт в spec.csv.",
         "S6"),
    ]


def write_findings() -> None:
    rows = build_findings()
    with (EXPERT3 / "findings.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID", "Категория", "Замечание", "Доказательство",
                    "Корректировка", "Критерий приёмки", "Пункт"])
        w.writerows(rows)
    print("findings:", len(rows), Counter(r[1] for r in rows))


# ---------------------------------------------------------------------------
# числовые проверки
# ---------------------------------------------------------------------------
def calc_rows() -> list[list[str]]:
    c10 = contact_ideal(10.0, 15.0)
    a10 = contact_actual(10.0, 15.0)
    c55 = contact_ideal(10.0, 15.0, SPRING_KT,
                        SPRING_KT * (55.0 - SPRING_INST),
                        SPRING_KT * (55.0 - 46.0))
    _, p0a = contact_hertz(a10["bottom"])
    _, p0i = contact_hertz(c10["top"])
    return [
        ["Пружина: L0 / OD / проволока", f"{SPRING_FREE:g} / {SPRING_OD:g} / "
         f"{SPRING_WIRE:g} мм", "70 / 12 / 1,0", "OK", "fix7 п.1"],
        ["Пружина: k", f"{SPRING_K:.3f} Н/мм", "—", "INFO",
         "12×1,0; D=11; n=11"],
        ["Пружина: 4k", f"{SPRING_KT:.3f} Н/мм", "—", "INFO", "4 шт."],
        ["Пружина: установленная / сжатие", f"{SPRING_INST:g} / "
         f"{SPRING_COMPRESSION:g} мм", "L0=70", "OK", "36 мм при верхнем; 46 при нижнем"],
        ["Пружина: преднатяг", f"{SPRING_PRELOAD:.1f} Н", "—", "INFO",
         "4k·(70−36)"],
        ["Пружина: сила внизу", f"{SPRING_BOTTOM_FORCE:.1f} Н", "—", "INFO",
         "4k·(70−46)"],
        ["Пружина: f_соб", f"{F_NAT:.2f} Гц", "вне 5…15 Гц", "FAIL",
         "L0 не меняет k; демпфера нет"],
        ["Пружина: индекс C / Wahl", f"{SPRING_INDEX:.2f} / {WAHL:.3f}", "—", "INFO",
         "C=11; Kw=1,131"],
        ["Пружина: τ верх", f"{TAU_TOP:.0f} МПа", "≤500…700 (усталость)", "FAIL",
         f"на пружину {SPRING_PRELOAD/4:.1f} Н"],
        ["Пружина: τ низ", f"{TAU_BOTTOM:.0f} МПа", "≤500…700", "WARN",
         f"на пружину {SPRING_BOTTOM_FORCE/4:.1f} Н"],
        ["Пружина: размах τ", f"{TAU_ALT*2:.0f} МПа", "—", "WARN",
         f"среднее {TAU_MEAN:.0f} МПа"],
        ["Пружина: τ при сжатии до твёрдого", f"{TAU_SOLID:.0f} МПа", "≤предела", "FAIL",
         f"L_solid={SPRING_SOLID:g} мм; F={SPRING_SOLID_FORCE:.1f} Н/пружину"],
        ["Пружина: твёрдая длина / запас", f"{SPRING_SOLID:g} / "
         f"{SPRING_INST-SPRING_SOLID:g} мм", "—", "OK", "13 мм; запас 23 мм"],
        ["Пружина: сила до твёрдого", f"{SPRING_SOLID_FORCE:.1f} Н/пружину", "—", "INFO",
         f"{4*SPRING_SOLID_FORCE:.1f} Н на 4"],
        ["Пружина: ID номинал / вал", f"{SPRING_OD-2*SPRING_WIRE:.1f} / 10,0 мм",
         "зазор ≥0,3", "FAIL", "в модели 10,2; номинал 10,0"],
        ["Пружина: ID модели / зазор", f"10,2 / 0,2 мм", "≥0,3", "WARN",
         "оптимистично; при сжатии 34 мм"],
        ["Пружина: гибкость L0/D", f"{SPRING_FREE/SPRING_OD:.2f}", "—", "OK",
         "направляется валом; риск трения (S4)"],
        ["Пружина: масса", f"{SPRING_MASS:.2f} г/шт.", "—", "INFO",
         f"{4*SPRING_MASS:.2f} г на 4"],
        ["Контакт 15 Гц/10 мм: идеал", f"{c10['top']:.1f} Н", "≥2× (81,6 Н)",
         "FAIL", f"инерционная {c10['inertia']:.1f} Н; запас {c10['ratio_top']:.2f}"],
        ["Контакт 15 Гц/10 мм: идеал, запас", f"{c10['ratio_top']:.2f}", "≥2", "FAIL",
         "L0=70 недостаточно"],
        ["Контакт 15 Гц/10 мм: факт сверху", f"{a10['top']:.1f} Н", "≥2× (58,2 Н)",
         "OK", f"запас {a10['ratio_top']:.2f}; негармонический профиль"],
        ["Контакт 15 Гц/10 мм: факт снизу", f"{a10['bottom']:.1f} Н", "≥2× (122,2 Н)",
         "OK", f"запас {a10['ratio_bottom']:.2f}; высокая нагрузка"],
        ["Контакт 15 Гц/5 мм: идеал", f"{contact_ideal(5.0,15.0)['top']:.1f} Н",
         "≥2× (40,8 Н)", "OK", f"запас {contact_ideal(5.0,15.0)['ratio_top']:.2f}"],
        ["Контакт 15 Гц/3 мм: идеал", f"{contact_ideal(3.0,15.0)['top']:.1f} Н",
         "≥2× (24,5 Н)", "OK", f"запас {contact_ideal(3.0,15.0)['ratio_top']:.2f}"],
        ["Контакт 5 Гц/10 мм: идеал", f"{contact_ideal(10.0,5.0)['top']:.1f} Н",
         "≥2× (9,1 Н)", "OK", f"запас {contact_ideal(10.0,5.0)['ratio_top']:.2f}"],
        ["Контакт 8,64 Гц/10 мм: идеал", f"{contact_ideal(10.0,F_NAT)['top']:.1f} Н",
         "≥2× (27,1 Н)", "OK", f"запас {contact_ideal(10.0,F_NAT)['ratio_top']:.2f}"],
        ["L0 для 2× на 15/10", f"{L0_MIN:.1f} мм", "≤70", "FAIL",
         "нужно +7,9 мм; напряжение ещё выше"],
        ["k для 2× при L0=70", f"{K_MIN:.3f} Н/мм", "≤0,677", "FAIL",
         "нужно +23 %; напряжение ещё выше"],
        ["Сравнение L0=55/70: контакт 15/10", f"{c55['top']:.1f} / {c10['top']:.1f} Н",
         "—", "INFO", f"запас {c55['ratio_top']:.2f} → {c10['ratio_top']:.2f}"],
        ["Сравнение L0=55/70: τ верх", f"{spring_stress(SPRING_KT*(55-36)/4):.0f} / "
         f"{TAU_TOP:.0f} МПа", "—", "INFO", "рост напряжения"],
        ["Кулачок–ролик: p0 при 135 Н", f"{p0a:.1f} МПа", "PLA/вставка", "WARN",
         "p0 при 60 Н — %.1f МПа" % p0i],
        ["Ролик 6200: нагрузка 135 Н", "L10 ≈ 8·10⁶ ч при 450 об/мин", "—", "OK",
         "C≈8,1 кН; запас большой"],
        ["Вариант 8×Ø12×0,9 L0=70", f"k={K8:.3f}; контакт {CONTACT8['top']:.1f} Н "
         f"({CONTACT8['ratio_top']:.2f}); τ={TAU8:.0f} МПа", "τ≤700; ≥2×", "WARN",
         f"f_соб {F_NAT8:.2f} Гц; 8 мест"],
        ["Допуск L0 / k", "не задан", "±1 мм / ±5 %", "FAIL",
         "при ±1 мм контакт ±2,7 Н"],
        ["Материал / концы / ресурс", "не заданы", "паспорт", "FAIL",
         "пружинная сталь; закрытые шлифованные; 10^6"],
        ["Регулировка преднатяга", "нет", "есть", "WARN", "S6"],
    ]


def write_calc() -> None:
    rows = calc_rows()
    with (OUT / "calc.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Проверка", "Значение", "Норма", "Статус", "Примечание"])
        w.writerows(rows)
    print("calc:", len(rows), Counter(r[3] for r in rows))


def write_map() -> None:
    rows = []
    for stroke in CAM_STROKES:
        for freq in range(5, 16):
            c = contact_ideal(stroke, freq)
            a = contact_actual(stroke, freq)
            rows.append([
                f"{stroke:g}", f"{freq}", f"{30*freq}",
                f"{c['inertia']:.2f}", f"{c['top']:.1f}", f"{c['ratio_top']:.2f}",
                f"{a['top']:.1f}", f"{a['ratio_top']:.2f}",
                f"{a['bottom']:.1f}", f"{a['ratio_bottom']:.2f}",
                "да" if c['ratio_top'] >= 2.0 else "нет",
            ])
    with (OUT / "map.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Ход (размах), мм", "Частота стола, Гц", "Обороты вала, об/мин",
                    "Инерционная сила, Н", "Контакт идеал сверху, Н",
                    "Запас идеал", "Контакт факт сверху, Н", "Запас факт сверху",
                    "Контакт факт снизу, Н", "Запас факт снизу",
                    "Идеал ≥2×"])
        w.writerows(rows)
    print("map:", len(rows))


# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------
class SVG:
    def __init__(self, w: int, h: int, width: str | None = None,
                 height: str | None = None) -> None:
        self.w, self.h = w, h
        self.width = width or f"{w}px"
        self.height = height or f"{h}px"
        self.els: list[str] = []

    def add(self, s: str) -> None:
        self.els.append(s)

    def line(self, x1, y1, x2, y2, stroke="#333", width=1, dash=None) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, fill="none", stroke="#333", width=1, rx=0) -> None:
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def circle(self, x, y, r, fill="none", stroke="#333", width=1) -> None:
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{width}"/>')

    def text(self, x, y, s, size=18, fill="#111", anchor="start",
             weight="normal", family="DejaVu Sans", rotate=None) -> None:
        s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        tr = (f' transform="rotate({rotate} {x:.1f} {y:.1f})"'
              if rotate is not None else "")
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
                 f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                 f'font-weight="{weight}"{tr}>{s}</text>')

    def polyline(self, pts, stroke="#333", width=2, fill="none", dash=None) -> None:
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{width}"{d}/>')

    def polygon(self, pts, fill="#333", stroke="none", width=1) -> None:
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{width}"/>')

    def save(self, path: Path) -> None:
        head = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{self.width}" height="{self.height}" '
                f'viewBox="0 0 {self.w} {self.h}">\n'
                f'<rect width="{self.w}" height="{self.h}" fill="#ffffff"/>\n')
        path.write_text(head + "\n".join(self.els) + "\n</svg>\n", encoding="utf-8")


def plot_axes(svg: SVG, x0, y0, w, h, xmin, xmax, ymin, ymax,
              xlabel, ylabel, xticks, yticks):
    svg.rect(x0, y0, w, h, fill="#fbfbfb", stroke="#999")
    for xv in xticks:
        x = x0 + (xv - xmin) / (xmax - xmin) * w
        svg.line(x, y0, x, y0 + h, "#ddd", 1)
        svg.text(x, y0 + h + 24, f"{xv:g}", 16, "#333", "middle")
    for yv in yticks:
        y = y0 + h - (yv - ymin) / (ymax - ymin) * h
        svg.line(x0, y, x0 + w, y, "#ddd", 1)
        svg.text(x0 - 10, y + 5, f"{yv:g}", 16, "#333", "end")
    svg.text(x0 + w / 2, y0 + h + 52, xlabel, 19, "#111", "middle", "bold")
    svg.text(x0 - 58, y0 + h / 2, ylabel, 19, "#111", "middle", "bold", rotate=-90)

    def xy(xv, yv):
        return (x0 + (xv - xmin) / (xmax - xmin) * w,
                y0 + h - (yv - ymin) / (ymax - ymin) * h)

    return xy


def svg_spring_contact(path: Path) -> None:
    s = SVG(1400, 900, "297mm", "191mm")
    s.text(700, 44, "Пружины L0=70 и контакт ролика после fix7", 28,
           "#111", "middle", "bold")
    s.text(700, 74, "k=0,677 Н/мм; 4 пружины; установленная 36 мм; "
           "f_соб=8,64 Гц", 17, "#444", "middle")
    # left: force vs compression
    x0, y0, w, h = 80, 140, 600, 560
    xy = plot_axes(s, x0, y0, w, h, 0, 40, 0, 180,
                   "Сжатие пружины (70−L), мм", "Сила 4 пружин, Н",
                   [0, 5, 10, 15, 20, 25, 30, 35, 40],
                   [0, 25, 50, 75, 100, 125, 150, 175])
    for l0, color, label in [(55.0, "#2471a3", "L0=55 (fix6)"),
                             (70.0, "#6c3483", "L0=70 (fix7)")]:
        xs = min(l0 - 13, 40.0)
        pts = [xy(0, 0), xy(xs, 4 * SPRING_K * xs)]
        s.polyline(pts, color, 3)
        # installed 36 and bottom 46
        s.circle(*xy(l0 - 36, 4 * SPRING_K * (l0 - 36)), 7, fill=color,
                 stroke="#111", width=2)
        s.circle(*xy(l0 - 46, 4 * SPRING_K * (l0 - 46)), 5, fill="#fff",
                 stroke=color, width=2)
        s.text(*xy(l0 - 36 + 0.5, 4 * SPRING_K * (l0 - 36) + 7), label,
               15, color, "start", "bold")
    s.line(*xy(0, contact_ideal(10, 15)["inertia"]),
           *xy(40, contact_ideal(10, 15)["inertia"]), "#c0392b", 2, "8 6")
    s.text(*xy(1, contact_ideal(10, 15)["inertia"] + 6),
           "инерционная 40,8 Н", 14, "#c0392b")
    s.line(*xy(0, 2 * contact_ideal(10, 15)["inertia"]),
           *xy(40, 2 * contact_ideal(10, 15)["inertia"]), "#1e7a3c", 2, "8 6")
    s.text(*xy(23, 2 * contact_ideal(10, 15)["inertia"] + 6),
           "цель 2× = 81,6 Н", 14, "#1e7a3c")
    s.text(x0 + 10, y0 - 15, "Сила пружин от сжатия", 18, "#111",
           "start", "bold")
    s.text(x0, y0 + h + 92,
           "L0=70: преднатяг 92,1 Н; внизу 65,0 Н; сжатие 34/24 мм.",
           15, "#444")
    s.text(x0, y0 + h + 116,
           "Красная линия — инерционная 15 Гц/10 мм; зелёная — цель 2×.",
           15, "#444")

    # right: contact at 15 Hz vs stroke
    bx0, by0, bw, bh = 760, 140, 560, 560
    s.rect(bx0, by0, bw, bh, fill="#fbfbfb", stroke="#999")
    s.text(bx0 + bw / 2, by0 - 15, "Контакт при 15 Гц, Н", 18, "#111",
           "middle", "bold")
    s.text(bx0 + bw / 2, by0 + bh + 44, "Ход (размах), мм", 16, "#111",
           "middle", "bold")
    maxv = 140
    bar_w = 30
    groups = [(3, "3"), (5, "5"), (10, "10")]
    for j, (stroke, label) in enumerate(groups):
        c = contact_ideal(stroke, 15)
        a = contact_actual(stroke, 15)
        x = bx0 + 60 + j * 165
        for k, (val, color, name) in enumerate([
                (c["top"], "#2471a3", "идеал"),
                (a["top"], "#b9770e", "факт сверху"),
                (a["bottom"], "#6c3483", "факт снизу")]):
            H = max(0, val) / maxv * (bh - 70)
            s.rect(x + k * 40, by0 + bh - 30 - H, bar_w, H, fill=color,
                   stroke=color, width=0)
            s.text(x + k * 40 + bar_w / 2, by0 + bh - 36 - H, f"{val:.0f}",
                   11, "#111", "middle")
        s.text(x + 55, by0 + bh - 10, label, 14, "#111", "middle")
    s.line(bx0 + 30, by0 + bh - 30 - contact_ideal(10, 15)["inertia"] / maxv *
           (bh - 70), bx0 + bw - 20, by0 + bh - 30 -
           contact_ideal(10, 15)["inertia"] / maxv * (bh - 70),
           "#c0392b", 2, "8 6")
    s.line(bx0 + 30, by0 + bh - 30 - 81.6 / maxv * (bh - 70),
           bx0 + bw - 20, by0 + bh - 30 - 81.6 / maxv * (bh - 70),
           "#1e7a3c", 2, "8 6")
    s.text(bx0 + 35, by0 + 28, "синий — идеал; оранжевый — факт сверху; "
           "фиолетовый — факт снизу", 13, "#444")
    s.text(bx0 + 35, by0 + 50, "красная — инерционная; зелёная — цель 2×",
           13, "#c0392b")
    s.text(bx0 + 35, by0 + 72, "15 Гц/10 мм: идеал 60,3 (1,48); факт 72,0 "
           "(2,48) / 135,1 (2,21)", 13, "#1e7a3c")
    s.text(bx0 + 35, by0 + bh + 82,
           "Вывод: по гармонической синусоиде L0=70 не даёт 2×;", 15,
           "#c0392b")
    s.text(bx0 + 35, by0 + bh + 106,
           "фактический 2-лепестковый профиль маскирует недостаток.",
           15, "#c0392b")
    s.save(path)


def svg_contact_map(path: Path) -> None:
    s = SVG(1400, 900, "297mm", "191mm")
    s.text(700, 44, "Карта контакта: запас 2× для пружин L0=70", 28,
           "#111", "middle", "bold")
    s.text(700, 74, "запас = сила контакта / инерционная; идеальная синусоида; "
           "2 лепестка → 150…450 об/мин", 17, "#444", "middle")
    x0, y0, w, h = 120, 130, 1080, 560
    xy = plot_axes(s, x0, y0, w, h, 5, 15, 3, 11,
                   "Частота стола, Гц", "Размах (ход), мм",
                   list(range(5, 16)), list(range(3, 12)))
    # red zone ratio<2
    red = [(x0, y0 + h)]
    for i in range(0, 201):
        f = 5 + 10 * i / 200
        # ratio=2: pre+mg-m*(s/2e-3)w² = 2*m*(s/2e-3)w²
        s_req = 2 * (SPRING_PRELOAD + M_DYN * GRAVITY) / (
            3 * M_DYN * (2 * math.pi * f) ** 2) * 1000.0
        red.append(xy(f, min(s_req, 11.0)))
    red.append((x0 + w, y0 + h))
    red.append((x0, y0 + h))
    s.polygon(red, fill="#fdecea", stroke="none")
    curve = []
    for i in range(0, 101):
        f = 5 + 10 * i / 100
        s_req = 2 * (SPRING_PRELOAD + M_DYN * GRAVITY) / (
            3 * M_DYN * (2 * math.pi * f) ** 2) * 1000.0
        if 3 <= s_req <= 11:
            curve.append(xy(f, s_req))
    s.polyline(curve, "#c0392b", 3)
    s.text(*xy(5.2, 3.4), "запас < 2×", 18, "#c0392b", "start", "bold")
    s.text(*xy(13.7, 10.75), "запас ≥ 2×", 17, "#1e7a3c", "start", "bold")
    colors = {3: "#2471a3", 5: "#b9770e", 10: "#6c3483"}
    for stroke, color in colors.items():
        y = xy(5, stroke)[1]
        s.line(x0, y, x0 + w, y, color, 3, "8 6")
        s.text(x0 + w - 10, y - 8, f"размах {stroke} мм", 16, color, "end", "bold")
        # actual top at 15 Hz marker
        a = contact_actual(stroke, 15)
        s.circle(*xy(15, stroke), 8, fill=color, stroke="#111", width=2)
        fy = y - 22 if stroke == 3 else y + 20
        s.text(xy(15, stroke)[0] - 10, fy, f"факт {a['ratio_top']:.1f}×",
               13, "#111", "end")
    xr = xy(F_NAT, 3)[0]
    s.line(xr, y0, xr, y0 + h, "#7d3c98", 2, "2 4")
    s.text(xr + 8, y0 + 25, f"f_соб {F_NAT:.2f} Гц", 15, "#7d3c98",
           "start", "bold")
    s.text(x0, y0 + h + 92,
           "Красная область — идеальный запас <2×; граница: "
           "a_max=3g (контакт = 2× инерционной).", 16, "#c0392b")
    s.text(x0, y0 + h + 118,
           "При 15 Гц/10 мм идеал 1,48; факт 2,48 сверху и 2,21 снизу — "
           "негармонический профиль (C8) маскирует недостаток.", 16, "#444")
    s.save(path)


def svg_spring_stress(path: Path) -> None:
    s = SVG(1400, 800, "297mm", "169mm")
    s.text(700, 40, "Напряжение в пружине: L0=70 перегружает Ø1,0", 28,
           "#111", "middle", "bold")
    s.text(700, 70, "τ = Kw·8FD/(πd³); C=11; Kw=1,131; "
           "допустимое для усталости ориентировочно 500…700 МПа", 16,
           "#444", "middle")
    # bars: L0 55/70/77.9 top/bottom, 8x0.9
    x0, y0, w, h = 100, 130, 700, 520
    s.rect(x0, y0, w, h, fill="#fbfbfb", stroke="#999")
    maxv = 1400
    bars = [
        ("L0=55\nверх", spring_stress(SPRING_KT * (55 - 36) / 4), "#2471a3"),
        ("L0=55\nниз", spring_stress(SPRING_KT * (55 - 46) / 4), "#2471a3"),
        ("L0=70\nверх", TAU_TOP, "#6c3483"),
        ("L0=70\nниз", TAU_BOTTOM, "#6c3483"),
        ("L0=78\nверх", spring_stress(SPRING_KT * (L0_MIN - 36) / 4), "#c0392b"),
        ("8×0,9\nверх", TAU8, "#b9770e"),
        ("твёрдое\nL0=70", TAU_SOLID, "#7f8c8d"),
    ]
    for i, (label, val, color) in enumerate(bars):
        x = x0 + 40 + i * 90
        H = val / maxv * (h - 60)
        s.rect(x, y0 + h - 40 - H, 52, H, fill=color, stroke=color, width=0)
        s.text(x + 26, y0 + h - 46 - H, f"{val:.0f}", 13, "#111", "middle")
        for li, part in enumerate(label.split("\n")):
            s.text(x + 26, y0 + h - 10 + li * 15, part, 12, "#333", "middle")
    for yv, color, label in [(500, "#1e7a3c", "500 МПа"),
                             (700, "#b9770e", "700 МПа")]:
        yy = y0 + h - 40 - yv / maxv * (h - 60)
        s.line(x0 + 20, yy, x0 + w - 20, yy, color, 2, "8 6")
        s.text(x0 + w - 25, yy - 6, label, 13, color, "end", "bold")
    s.text(x0 + 10, y0 - 15, "Напряжение кручения, МПа", 18, "#111",
           "start", "bold")
    # geometry panel
    px, py = 850, 130
    s.rect(px, py, 480, 520, fill="#fbfbfb", stroke="#999")
    s.text(px + 240, py - 15, "Геометрия и сборка", 18, "#111", "middle", "bold")
    lines = [
        f"L0 = {SPRING_FREE:g} мм; L_уст = {SPRING_INST:g} мм",
        f"Сжатие = {SPRING_COMPRESSION:g} мм (было 19)",
        f"Твёрдая длина = {SPRING_SOLID:g} мм; запас {SPRING_INST-SPRING_SOLID:g} мм",
        f"ID = {SPRING_OD-2*SPRING_WIRE:.1f} мм; вал Ø10; зазор 0",
        f"В модели ID = 10,2; зазор 0,2",
        f"Индекс C = {SPRING_INDEX:.1f}; Wahl = {WAHL:.3f}",
        f"Масса = {SPRING_MASS:.2f} г/шт.; 4 = {4*SPRING_MASS:.2f} г",
        f"f_соб = {F_NAT:.2f} Гц; внутри 5…15",
        f"Преднатяг = {SPRING_PRELOAD:.1f} Н; внизу {SPRING_BOTTOM_FORCE:.1f} Н",
        f"Сила до твёрдого = {SPRING_SOLID_FORCE:.1f} Н/пружину",
        "",
        "Вариант 8×Ø12×0,9 L0=70:",
        f"k = {K8:.3f} Н/мм; 8k = {KT8:.2f} Н/мм",
        f"контакт 15/10 = {CONTACT8['top']:.1f} Н ({CONTACT8['ratio_top']:.2f}×)",
        f"τ = {TAU8:.0f} МПа (высокое; в верхней части 500…700)",
        f"f_соб = {F_NAT8:.2f} Гц",
    ]
    yy = py + 30
    for ln in lines:
        s.text(px + 20, yy, ln, 14, "#222" if ln else "#fff")
        yy += 28
    s.text(40, 780, "Вывод: L0=70 повышает контакт, но τ≈729 МПа и f_соб "
           "8,64 Гц не позволяют принять 4×Ø12×1,0 без проверки/переделки.",
           15, "#c0392b")
    s.save(path)


def svg_sheet(path: Path, image_path: Path) -> None:
    s = SVG(1587, 1123, "420mm", "297mm")
    s.text(40, 50, "Третья инженерная экспертиза: пружины и контакт ролика",
           31, "#111", "start", "bold")
    s.text(40, 80, "Объект — fix7 (L0=70, Ø12, проволока 1,0); только пружины "
           "и контакт; остальные части не проверялись", 16, "#444")
    if image_path.exists():
        data = base64.b64encode(image_path.read_bytes()).decode("ascii")
        s.add(f'<image x="40" y="105" width="650" height="488" '
              f'xlink:href="data:image/png;base64,{data}"/>')
    s.rect(40, 105, 650, 488, "none", "#999", 1)
    tx, ty, tw = 720, 105, 827
    s.text(tx, ty - 8, "Реестр замечаний (findings.csv)", 18, "#111",
           "start", "bold")
    y = ty + 18
    for cat, color in [("критичное", "#c0392b"), ("важное", "#b9770e"),
                       ("пожелание", "#2471a3")]:
        s.rect(tx, y, tw, 24, color, color, 0)
        s.text(tx + 8, y + 18, cat.upper(), 15, "#fff", "start", "bold")
        y += 28
        for r in build_findings():
            if r[1] != cat:
                continue
            s.text(tx + 8, y + 13, r[0], 12, color, "start", "bold")
            title = r[2]
            if len(title) > 82:
                title = title[:79] + "…"
            s.text(tx + 42, y + 13, title, 12, "#111")
            y += 18
        y += 8
    kx, ky = 40, 630
    s.text(kx, ky, "Ключевые числа", 22, "#111", "start", "bold")
    lines = [
        f"Пружина: k={SPRING_K:.3f} Н/мм; 4k={SPRING_KT:.3f}; "
        f"преднатяг {SPRING_PRELOAD:.1f} Н; внизу {SPRING_BOTTOM_FORCE:.1f} Н.",
        f"Сжатие {SPRING_COMPRESSION:g} мм; твёрдая {SPRING_SOLID:g} мм; "
        f"ID {SPRING_OD-2*SPRING_WIRE:.1f} при вале 10.",
        f"τ верх/низ = {TAU_TOP:.0f}/{TAU_BOTTOM:.0f} МПа; τ твёрдого "
        f"{TAU_SOLID:.0f}; цель ≤500…700.",
        f"f_соб={F_NAT:.2f} Гц — внутри 5…15; L0 не меняет частоту.",
        f"Контакт 15/10: идеал {contact_ideal(10,15)['top']:.1f} Н "
        f"({contact_ideal(10,15)['ratio_top']:.2f}×); факт "
        f"{contact_actual(10,15)['top']:.1f} Н "
        f"({contact_actual(10,15)['ratio_top']:.2f}×).",
        f"Цель 2×: L0≥{L0_MIN:.1f} мм или k≥{K_MIN:.3f} Н/мм; "
        "L0=70 недостаточно.",
        f"Факт снизу {contact_actual(10,15)['bottom']:.1f} Н; "
        f"p0≈{contact_hertz(contact_actual(10,15)['bottom'])[1]:.1f} МПа.",
        "Вывод: 4×Ø12×1,0 L0=70 улучшает контакт, но перегружена и не даёт 2× "
        "по гармонической синусоиде.",
    ]
    for ln in lines:
        s.text(kx, ky + 26, "• " + ln, 14, "#222")
        ky += 26
    s.text(40, 1085, "Источник: stages/fix7; расчёты — stages/expert3/cad/"
           "analysis.py; схема — не рабочий чертёж.", 13, "#777")
    s.save(path)


# ---------------------------------------------------------------------------
# размеченные рендеры
# ---------------------------------------------------------------------------
def annotate(src: Path, dst: Path, title: str,
             calls: list[tuple[int, int, str, str]]) -> None:
    if Image is None or not src.exists():
        return
    im = Image.open(src).convert("RGBA")
    draw = ImageDraw.Draw(im, "RGBA")
    try:
        small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        small = title_font = ImageFont.load_default()
    draw.rectangle((0, 0, im.width, 44), fill=(20, 20, 20, 215))
    draw.text((16, 9), title, fill=(255, 255, 255, 255), font=title_font)
    colors = ["#c0392b", "#b9770e", "#2471a3", "#1e7a3c", "#6c3483"]
    for i, (x, y, fid, text) in enumerate(calls):
        color = colors[i % len(colors)]
        draw.ellipse((x - 15, y - 15, x + 15, y + 15), outline=color, width=4,
                     fill=(255, 255, 255, 70))
        draw.text((x - 10, y - 10), fid[:2], fill=color, font=small)
        tw = max(190, len(text) * 9 + 28)
        tx = x + 26
        if tx + tw > im.width - 10:
            tx = x - tw - 26
        ty = max(52, y - 20)
        if ty + 38 > im.height:
            ty = im.height - 50
        draw.rounded_rectangle((tx, ty, tx + tw, ty + 34), radius=7,
                               fill=(255, 255, 255, 228), outline=color, width=3)
        draw.text((tx + 7, ty + 7), f"{fid}: {text}", fill=(20, 20, 20, 255),
                  font=small)
    im.convert("RGB").save(dst)


def make_pics() -> None:
    annotate(FIX7 / "pic" / "render_front.png", PIC / "review_spring.png",
             "fix7 — пружины: L0=70, Ø12, проволока 1,0",
             [(450, 160, "S1", "пружина L0=70"),
              (450, 420, "S4", "ID 10/вал 10"),
              (600, 300, "S3", "f_соб 8,64"),
              (500, 600, "S2", "контакт")])
    annotate(FIX7 / "pic" / "render_mechanism.png", PIC / "review_roller.png",
             "fix7 — ролик и кулачок: контакт",
             [(150, 400, "S5", "2 лепестка"),
              (150, 140, "S2", "контакт 72/135 Н"),
              (450, 300, "S5", "p0 42 МПа"),
              (500, 600, "S1", "пружина")])


def make_previews() -> None:
    if cairosvg is None:
        print("cairosvg not available; previews skipped")
        return
    for svg in sorted(FIG.glob("*.svg")):
        png = PIC / f"{svg.stem}_preview.png"
        try:
            cairosvg.svg2png(url=str(svg), write_to=str(png), dpi=110)
        except Exception as exc:  # pragma: no cover
            print("preview failed:", svg.name, exc)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    PIC.mkdir(parents=True, exist_ok=True)
    write_findings()
    write_calc()
    write_map()
    svg_spring_contact(FIG / "spring_contact.svg")
    svg_contact_map(FIG / "contact_map.svg")
    svg_spring_stress(FIG / "spring_stress.svg")
    make_pics()
    svg_sheet(FIG / "expert_sheet.svg", PIC / "review_spring.png")
    make_previews()
    print("expert3 written to", EXPERT3)
    print("k/kt/preload:", round(SPRING_K, 3), round(SPRING_KT, 3),
          round(SPRING_PRELOAD, 1))
    print("tau top/bottom/solid:", round(TAU_TOP), round(TAU_BOTTOM),
          round(TAU_SOLID))
    print("contact ideal/actual 15/10:", round(contact_ideal(10, 15)["top"], 1),
          round(contact_actual(10, 15)["top"], 1))
    print("f_nat:", round(F_NAT, 2), "L0_min:", round(L0_MIN, 1),
          "k_min:", round(K_MIN, 3))


if __name__ == "__main__":
    main()
