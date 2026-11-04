#!/usr/bin/env python3
"""Раскрой 4 труб 20x20x2 длиной 1000 мм на раму fix11.

Лист A4 альбом, масштаб 1:5, рез 5 мм. Выход: SVG, PDF, PNG и cut_plan.csv.

Раскладка (принята в Interview):
  труба 1: T07 360, T08 360, T11 200                 -> 935, остаток 65
  труба 2: T01 260, T02 260, T03 260, T05 150         -> 950, остаток 50
  труба 3: T09 T10 T13 T14 T15 T16 (6x160)           -> 990, остаток 10
  труба 4: T17 160, T18 160, T04 260, T12 200, T06 150
                                                       -> 955, остаток 45

Задние стойки T05/T06 входят в раскрой. Поджимные балки 21
(2x159,6) в раскрой не входят — режутся из другой трубы. Каждый
отрезок отделяется своим резом, поэтому на трубу с k отрезками
приходится k резов по 5 мм. Всего 18 резов: 3740 + 90 = 3830 мм.
"""

import os
import csv
from xml.sax.saxutils import escape

import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "fig")
PIC = os.path.join(HERE, "pic")
PDF = os.path.join(HERE, "pdf")
for d in (FIG, PIC, PDF):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------------------
# исходные данные
# ---------------------------------------------------------------------------
STOCK = 1000.0
KERF = 5.0
SCALE = 0.2             # 1:5
TUBE = 20.0

# (обозначение, длина)
TUBES = [
    {"n": 1, "parts": [("T07", 360), ("T08", 360), ("T11", 200)]},
    {"n": 2, "parts": [("T01", 260), ("T02", 260), ("T03", 260),
                       ("T05", 150)]},
    {"n": 3, "parts": [("T09", 160), ("T10", 160), ("T13", 160),
                       ("T14", 160), ("T15", 160), ("T16", 160)]},
    {"n": 4, "parts": [("T17", 160), ("T18", 160), ("T04", 260),
                       ("T12", 200), ("T06", 150)]},
]

# ---------------------------------------------------------------------------
# svg helpers (единицы — миллиметры бумаги)
# ---------------------------------------------------------------------------
FONT = "DejaVu Sans, Arial, sans-serif"
W, H = 297.0, 210.0


def num(x, nd=2):
    """Число для подписи: десятичная запятая."""
    if nd == 0:
        s = "%.0f" % x
    else:
        s = ("%." + str(nd) + "f") % x
        s = s.rstrip("0").rstrip(".")
    if s in ("", "-0"):
        s = "0"
    return s.replace(".", ",")


def fmt(x, nd=3):
    """Координата/размер в SVG: только точка, без запятой."""
    if nd == 0:
        s = "%.0f" % x
    else:
        s = ("%." + str(nd) + "f") % x
        s = s.rstrip("0").rstrip(".")
    if s in ("", "-0"):
        s = "0"
    return s


def esc(s):
    return escape(str(s))


def line(x1, y1, x2, y2, w=0.18, dash=None, color="#000"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
            'stroke-width="%s" stroke-linecap="round"%s/>'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), color, fmt(w, 3), d))


def rect(x, y, w, h, sw=0.2, fill="none", stroke="#000", dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" '
            'stroke="%s" stroke-width="%s"%s/>'
            % (fmt(x), fmt(y), fmt(w), fmt(h), fill, stroke, fmt(sw, 3), d))


def text(x, y, s, size=2.6, anchor="start", weight="normal", rot=0,
         color="#000"):
    tr = (' transform="rotate(%s %s %s)"' % (fmt(rot), fmt(x), fmt(y))
          if rot else "")
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" '
            'font-weight="%s" text-anchor="%s" fill="%s"%s>%s</text>'
            % (fmt(x), fmt(y), FONT, fmt(size, 2), weight, anchor, color,
               tr, esc(s)))


def txt_bg(x, y, s, size=2.4, anchor="middle"):
    w = max(1.2, len(s) * size * 0.56)
    if anchor == "middle":
        x0 = x - w / 2.0
    elif anchor == "end":
        x0 = x - w
    else:
        x0 = x
    return rect(x0, y - size * 0.92, w, size * 1.18, 0, "#fff", "none")


def arrow(x, y, dx, dy, size=1.25):
    bx, by = x - dx * size, y - dy * size
    px, py = -dy * 0.42, dx * 0.42
    return ('<polygon points="%s,%s %s,%s %s,%s" fill="#000"/>'
            % (fmt(x), fmt(y), fmt(bx + px), fmt(by + py),
               fmt(bx - px), fmt(by - py)))


def dim_piece(x1, x2, y, frm_y, label):
    """Размер готовой длины между кромками; стрелки внутрь."""
    o = [line(x1, frm_y, x1, y + 2.0, 0.12),
         line(x2, frm_y, x2, y + 2.0, 0.12),
         line(x1, y, x2, y, 0.15),
         arrow(x1, y, -1, 0), arrow(x2, y, 1, 0)]
    tx = (x1 + x2) / 2.0
    o.append(txt_bg(tx, y - 0.8, label, 2.2))
    o.append(text(tx, y - 0.8, label, 2.2, "middle"))
    return "".join(o)


# ---------------------------------------------------------------------------
# расчёт
# ---------------------------------------------------------------------------
def calc(tube):
    pos = 0.0
    rows = []
    cuts = []
    for pid, length in tube["parts"]:
        start = pos
        end = start + length
        cut0 = end
        cut1 = cut0 + KERF
        rows.append({"id": pid, "length": length,
                     "start": start, "end": end})
        cuts.append(cut0)
        pos = cut1
    used = pos
    off = STOCK - used
    return rows, cuts, used, off


ALL = []
for t in TUBES:
    rows, cuts, used, off = calc(t)
    t["rows"] = rows
    t["cuts"] = cuts
    t["used"] = used
    t["off"] = off
    ALL.extend(rows)

TOTAL_LEN = sum(r["length"] for r in ALL)
TOTAL_CUTS = len(ALL)
TOTAL_USED = TOTAL_LEN + TOTAL_CUTS * KERF
TOTAL_OFF = STOCK * len(TUBES) - TOTAL_USED

assert len(ALL) == 18, len(ALL)
assert len({r["id"] for r in ALL}) == 18
assert {r["id"] for r in ALL} == {"T%02d" % i for i in range(1, 19)}
assert abs(TOTAL_LEN - 3740.0) < 1e-9
assert abs(TOTAL_USED - 3830.0) < 1e-9
assert abs(TOTAL_OFF - 170.0) < 1e-9
for t in TUBES:
    assert t["used"] <= STOCK + 1e-9, (t["n"], t["used"])
    assert t["off"] >= 0

# ---------------------------------------------------------------------------
# лист
# ---------------------------------------------------------------------------
body = []
body.append('<rect width="297" height="210" fill="#fff"/>')
# рамка
body.append(rect(4, 4, 289, 202, 0.55))
body.append(rect(6, 6, 285, 198, 0.28))

# заголовок
body.append(text(10, 13.2, "РАСКРОЙ ТРУБ РАМЫ 20×20×2 — 4 ТРУБЫ ПО 1000 мм",
                 5.1, weight="bold"))
body.append(text(10, 19.0,
                 "fix11 · сварная рама, 18 отрезков · рез ≤5 мм · масштаб 1:5",
                 2.9))
body.append(line(8, 21.5, 289, 21.5, 0.35))

# ---------------------------------------------------------------------------
# четыре полосы труб
# ---------------------------------------------------------------------------
X0 = 48.0
BAR_LEN = STOCK * SCALE       # 200 мм
BAR_H = TUBE * SCALE          # 4 мм
BAR_Y = [34.0, 66.0, 98.0, 130.0]

# пояснение к размерной линии позиций
body.append(text(10, 23.2, "позиции резов", 1.8, weight="bold"))
body.append(text(10, 25.5, "от левого торца, мм", 1.8))

for t, y in zip(TUBES, BAR_Y):
    # левая надпись
    body.append(text(10, y + 2.4, "ТРУБА %d" % t["n"], 2.9,
                     weight="bold"))
    body.append(text(10, y + 5.7, "1000 мм", 2.1))

    # позиции резов (сверху)
    yd = y - 7.0
    body.append(line(X0, y - 1.0, X0, yd - 1.8, 0.12))
    body.append(line(X0, yd, X0 + BAR_LEN, yd, 0.15))
    body.append(text(X0, yd - 1.7, "0", 1.9, "middle"))
    for c in t["cuts"]:
        x = X0 + c * SCALE
        body.append(line(x, y - 1.0, x, yd - 1.5, 0.12))
        body.append(line(x, yd - 1.4, x, yd + 1.4, 0.28))
        body.append(text(x, yd - 1.7, num(c, 1), 1.9, "middle"))

    # полоса: отрезки, резы, остаток
    for i, r in enumerate(t["rows"]):
        xs = X0 + r["start"] * SCALE
        xe = X0 + r["end"] * SCALE
        fill = "#f4f4f4" if i % 2 == 0 else "#e9e9e9"
        body.append(rect(xs, y, xe - xs, BAR_H, 0.3, fill))
        body.append(text((xs + xe) / 2.0, y + 2.55, r["id"], 2.15,
                         "middle"))
    for c in t["cuts"]:
        body.append(rect(X0 + c * SCALE, y, KERF * SCALE, BAR_H,
                         0, "#d9534f", "none"))

    xo = X0 + t["used"] * SCALE
    wo = max(0.35, t["off"] * SCALE)
    body.append(rect(xo, y, wo, BAR_H, 0.25, "#cfcfcf", "#555",
                     dash="1 0.65"))
    # штриховка остатка
    if t["off"] * SCALE > 4:
        step = 2.2
        xx = xo - BAR_H
        while xx < xo + wo:
            x1 = max(xo, xx)
            x2 = min(xo + wo, xx + BAR_H)
            if x2 > x1:
                body.append(line(x1, y + BAR_H - (x1 - xx),
                                 x2, y + BAR_H - (x2 - xx), 0.18,
                                 color="#777"))
            xx += step

    # размеры готовых длин (снизу)
    yb = y + 10.0
    for r in t["rows"]:
        body.append(dim_piece(X0 + r["start"] * SCALE,
                              X0 + r["end"] * SCALE,
                              yb, y + BAR_H, num(r["length"], 1)))

    # правая надпись остатка
    xr = X0 + BAR_LEN + 4.0
    xc = xo + wo / 2.0
    body.append(line(xr - 1.0, y + 2.0, min(xr - 0.4, xc), y + 2.0,
                     0.12, color="#777"))
    body.append(text(xr, y + 2.35,
                     "ост. %s" % num(t["off"], 1), 2.35, weight="bold"))
    body.append(text(xr, y + 5.35,
                     "занято %s" % num(t["used"], 1), 1.75))

# линия отсечения нижней части
body.append(line(8, 146.0, 289, 146.0, 0.3))

# ---------------------------------------------------------------------------
# примечания
# ---------------------------------------------------------------------------
notes = [
    ("ПРИМЕЧАНИЯ", 2.7, True),
    ("1. Сталь 20×20×2; 4 трубы по 1000 мм. Размеры — готовые длины,", 1.8, False),
    ("   рез 5 мм учтён; при меньшем резе остатки растут.", 1.8, False),
    ("   3740 + 18×5 = 3830; остаток 170 мм.", 1.8, False),
    ("2. Резать по длинам; позиции — для реза 5 мм; резы 90°, заусенцы снять.", 1.8, False),
    ("3. Отверстия/прорези — по листам 22_T01…T18:", 1.8, False),
    ("   T13/T14 — Ø10 верх. стенка; T17/T18 — прорезь R15.", 1.8, False),
    ("4. Поджимные балки 21 (2×159,6) — из отдельной трубы.", 1.8, False),
    ("5. Масштаб 1:5; деталь А — 1:1.", 1.8, False),
]
yy = 151.6
for s, size, bold in notes:
    body.append(text(10, yy, s, size, weight="bold" if bold else "normal"))
    yy += 3.35

# ---------------------------------------------------------------------------
# таблица раскроя
# ---------------------------------------------------------------------------
TX, TY, TW = 104.0, 150.5, 122.0
COLS = [9.0, 38.0, 31.0, 36.0, 8.0]
ROW_H = 5.35
NROWS = 1 + len(TUBES) + 1
TH = ROW_H * NROWS

body.append(rect(TX, TY, TW, TH, 0.32))
# горизонтальные линии
for i in range(1, NROWS):
    body.append(line(TX, TY + i * ROW_H, TX + TW, TY + i * ROW_H, 0.18))
# вертикальные линии
cx = TX
for w in COLS[:-1]:
    cx += w
    body.append(line(cx, TY, cx, TY + TH, 0.18))
# итоговая строка — лёгкая заливка
body.append(rect(TX + 0.01, TY + (NROWS - 1) * ROW_H + 0.01,
                 TW - 0.02, ROW_H - 0.02, 0, "#ececec", "none"))

headers = ["Тр.", "Позиции", "Длины, мм", "Резы от торца, мм", "Ост."]
data = []
for t in TUBES:
    ids = " ".join(r["id"] for r in t["rows"])
    lens = "+".join(num(r["length"], 1) for r in t["rows"])
    cuts = "·".join(num(c, 1) for c in t["cuts"])
    data.append([str(t["n"]), ids, lens, cuts, num(t["off"], 1)])
data.append(["Итого", "18 отрезков", "3740", "рез 90", "170"])

for ri in range(NROWS):
    vals = headers if ri == 0 else data[ri - 1]
    x = TX + 1.2
    for ci, (w, v) in enumerate(zip(COLS, vals)):
        size = 1.75 if ri else 1.8
        weight = "bold" if (ri == 0 or ri == NROWS - 1) else "normal"
        anchor = "middle" if ci in (0, 4) else "start"
        xx = x + (w - 2.4) / 2.0 if anchor == "middle" else x
        body.append(text(xx, TY + ri * ROW_H + 3.55, v, size, anchor,
                         weight))
        x += w

# ---------------------------------------------------------------------------
# деталь А: рез 1:1
# ---------------------------------------------------------------------------
DX, DY, DW, DH = 230.0, 150.0, 60.0, 36.0
body.append(rect(DX, DY, DW, DH, 0.3))
body.append(text(DX + 2, DY + 2.1, "ДЕТАЛЬ А — РЕЗ ≤5 мм (1:1)",
                 2.15, weight="bold"))

# два торца трубы в разрезе вдоль оси
ax0, ay0 = 237.0, 158.0
aw, ah = 15.0, 20.0
gap = 5.0
# левый и правый куски
body.append(rect(ax0, ay0, aw, ah, 0.35, "#e8e8e8"))
body.append(rect(ax0 + aw + gap, ay0, aw, ah, 0.35, "#e8e8e8"))
# внутренние полости (стенка 2 мм)
body.append(rect(ax0 + 2, ay0 + 2, aw - 4, ah - 4, 0.28, "#fff"))
body.append(rect(ax0 + aw + gap + 2, ay0 + 2, aw - 4, ah - 4,
                 0.28, "#fff"))
# зона реза
body.append(rect(ax0 + aw, ay0, gap, ah, 0, "#f2b8b5", "none"))
body.append(line(ax0 + aw + gap / 2, ay0 - 1.5,
                 ax0 + aw + gap / 2, ay0 + ah + 1.5, 0.25,
                 dash="2 0.8", color="#b52b27"))
body.append(text(ax0 + aw + gap / 2, ay0 + ah / 2 + 1.1, "рез", 1.65,
                 "middle", rot=-90, color="#8b1a17"))

# размер 5 мм (стрелки снаружи, т.к. размер мал)
yb = ay0 + ah + 4.0
body.append(line(ax0 + aw, ay0 + ah, ax0 + aw, yb + 1.8, 0.12))
body.append(line(ax0 + aw + gap, ay0 + ah, ax0 + aw + gap, yb + 1.8, 0.12))
body.append(line(ax0 + aw, yb, ax0 + aw + gap, yb, 0.15))
body.append(arrow(ax0 + aw, yb, 1, 0))
body.append(arrow(ax0 + aw + gap, yb, -1, 0))
body.append(txt_bg(ax0 + aw + gap / 2, yb + 2.6, "5", 2.1))
body.append(text(ax0 + aw + gap / 2, yb + 2.6, "5", 2.1, "middle"))

# вертикальный размер 20
xr = ax0 + 2 * aw + gap + 3.5
body.append(line(ax0 + 2 * aw + gap, ay0, xr + 1.8, ay0, 0.12))
body.append(line(ax0 + 2 * aw + gap, ay0 + ah, xr + 1.8, ay0 + ah, 0.12))
body.append(line(xr, ay0, xr, ay0 + ah, 0.15))
body.append(arrow(xr, ay0, 0, -1))
body.append(arrow(xr, ay0 + ah, 0, 1))
body.append(txt_bg(xr + 2.5, ay0 + ah / 2 + 0.8, "20", 2.0))
body.append(text(xr + 2.5, ay0 + ah / 2 + 0.8, "20", 2.0, "middle",
                 rot=-90))

# подпись детали
body.append(text(ax0, DY + DH - 1.0, "стенка 2", 1.65))

# ---------------------------------------------------------------------------
# основная надпись
# ---------------------------------------------------------------------------
BX, BY, BW, BH = 10.0, 188.0, 279.0, 16.0
body.append(rect(BX, BY, BW, BH, 0.4))
for x in (105.0, 140.0, 175.0, 210.0, 250.0):
    body.append(line(x, BY, x, BY + BH, 0.22))

body.append(text(12, BY + 6.2, "fix11 · РАСКРОЙ ТРУБ РАМЫ", 3.0,
                 weight="bold"))
body.append(text(12, BY + 12.2,
                 "сталь 20×20×2 · 4 трубы × 1000 мм · рез ≤5 мм", 1.9))

body.append(text(107, BY + 4.2, "МАСШТАБ", 1.45))
body.append(text(107, BY + 11.2, "1:5", 3.1, weight="bold"))

body.append(text(142, BY + 4.2, "ЛИСТ", 1.45))
body.append(text(142, BY + 11.2, "1/1", 3.1, weight="bold"))

body.append(text(177, BY + 4.2, "РЕЗ", 1.45))
body.append(text(177, BY + 11.0, "≤5 мм", 2.5, weight="bold"))

body.append(text(212, BY + 4.2, "ДАТА", 1.45))
body.append(text(212, BY + 10.8, "04.11.2026", 2.15))

body.append(text(252, BY + 4.2, "РАЗРАБОТАЛ", 1.45))
body.append(text(252, BY + 10.8, "DeepSeek / OpenCode", 1.75))

svg = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" '
       'viewBox="0 0 297 210">\n' + "".join(body) + "\n</svg>\n")

svg_path = os.path.join(FIG, "tube_cut_layout.svg")
pdf_path = os.path.join(PDF, "tube_cut_layout.pdf")
png_path = os.path.join(PIC, "tube_cut_layout.png")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=pdf_path)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=png_path,
                 dpi=160)

# ---------------------------------------------------------------------------
# cut_plan.csv
# ---------------------------------------------------------------------------
csv_path = os.path.join(HERE, "cut_plan.csv")
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Труба", "Поз.", "Длина, мм", "Начало, мм", "Конец, мм",
                "Рез после, мм", "Занято, мм", "Остаток, мм", "Примечание"])
    for t in TUBES:
        for r in t["rows"]:
            note = ""
            if r["id"] in ("T13", "T14"):
                note = "Ø10 только верхняя стенка"
            elif r["id"] in ("T17", "T18"):
                note = "прорезь R15; 2×Ø10,5"
            elif r["id"] in ("T01", "T02"):
                note = "2×Ø4,5"
            elif r["id"] in ("T07", "T08", "T09", "T10"):
                note = "3×Ø4,5"
            elif r["id"] in ("T11", "T12"):
                note = "4×Ø6,6"
            elif r["id"] in ("T15", "T16"):
                note = "2×Ø10,5; 3×Ø4,5"
            w.writerow([t["n"], r["id"], num(r["length"], 1),
                        num(r["start"], 1), num(r["end"], 1),
                        "%s–%s" % (num(r["end"], 1),
                                   num(r["end"] + KERF, 1)),
                        num(t["used"], 1), num(t["off"], 1), note])
    w.writerow([])
    w.writerow(["Итого", "18 отрезков", num(TOTAL_LEN, 1), "", "",
                "18 резов × 5 мм", num(TOTAL_USED, 1), num(TOTAL_OFF, 1),
                "4 трубы × 1000 мм"])
    w.writerow(["B21", "2×159,6", "319,2", "", "", "",
                "не входят", "", "поджимные балки 21 — из отдельной трубы"])

print("SVG :", svg_path)
print("PDF :", pdf_path)
print("PNG :", png_path)
print("CSV :", csv_path)
print("Итого: длина %.1f, резов %d, занято %.1f, остаток %.1f"
      % (TOTAL_LEN, TOTAL_CUTS, TOTAL_USED, TOTAL_OFF))
for t in TUBES:
    print("  труба %d: %s | занято %.1f | остаток %.1f"
          % (t["n"], " ".join(r["id"] for r in t["rows"]),
             t["used"], t["off"]))
