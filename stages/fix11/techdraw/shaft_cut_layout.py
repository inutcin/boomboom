#!/usr/bin/env python3
"""Раскрой направляющих валов fix11: 2 прутка Ø10 x 500 мм -> 4 вала.

Лист A4 альбом, масштаб 1:2,5, рез 5 мм. Выход: SVG, PDF, PNG и
shaft_cut_plan.csv.

Принято:
  - заготовка: 2 сплошных прутка Ø10 h6, L=500 мм;
  - готовые валы: 4 шт. V01…V04, длина резки 176 мм (166 + 10 запас);
  - рез 5 мм, каждый отрезок отделяется своим резом;
  - каждый пруток: Vxx 176, рез 176–181, Vyy 176, рез 357–362,
    остаток 138 мм.

Итого: 4x176 = 704 мм; 4 реза x 5 = 20 мм; занято 724 мм;
остаток 276 мм (2x138).
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
STOCK = 500.0
KERF = 5.0
PART = 176.0            # 166 номинал + 10 мм запас
NOMINAL = 166.0
SCALE = 0.4             # 1:2,5
ROD_D = 10.0

RODS = [
    {"n": 1, "parts": [("V01", PART), ("V02", PART)]},
    {"n": 2, "parts": [("V03", PART), ("V04", PART)]},
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


def circle(cx, cy, r, sw=0.3, fill="none", stroke="#000", dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" '
            'stroke-width="%s"%s/>'
            % (fmt(cx), fmt(cy), fmt(r), fill, stroke, fmt(sw, 3), d))


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


def dim_piece(x1, x2, y, frm_y, label, size=2.0):
    """Размер готовой длины между кромками; стрелки внутрь."""
    o = [line(x1, frm_y, x1, y + 2.0, 0.12),
         line(x2, frm_y, x2, y + 2.0, 0.12),
         line(x1, y, x2, y, 0.15),
         arrow(x1, y, -1, 0), arrow(x2, y, 1, 0)]
    tx = (x1 + x2) / 2.0
    o.append(txt_bg(tx, y - 0.8, label, size))
    o.append(text(tx, y - 0.8, label, size, "middle"))
    return "".join(o)


# ---------------------------------------------------------------------------
# расчёт
# ---------------------------------------------------------------------------
def calc(rod):
    pos = 0.0
    rows = []
    cuts = []
    for pid, length in rod["parts"]:
        start = pos
        end = start + length
        rows.append({"id": pid, "length": length, "start": start,
                     "end": end})
        cuts.append(end)
        pos = end + KERF
    used = pos
    off = STOCK - used
    return rows, cuts, used, off


ALL = []
for rod in RODS:
    rows, cuts, used, off = calc(rod)
    rod["rows"] = rows
    rod["cuts"] = cuts
    rod["used"] = used
    rod["off"] = off
    ALL.extend(rows)

TOTAL_LEN = sum(r["length"] for r in ALL)
TOTAL_CUTS = len(ALL)
TOTAL_USED = TOTAL_LEN + TOTAL_CUTS * KERF
TOTAL_OFF = STOCK * len(RODS) - TOTAL_USED

assert len(ALL) == 4, len(ALL)
assert len({r["id"] for r in ALL}) == 4
assert {r["id"] for r in ALL} == {"V%02d" % i for i in range(1, 5)}
assert abs(TOTAL_LEN - 704.0) < 1e-9
assert abs(TOTAL_USED - 724.0) < 1e-9
assert abs(TOTAL_OFF - 276.0) < 1e-9
for rod in RODS:
    assert rod["cuts"] == [176.0, 357.0], rod["cuts"]
    assert abs(rod["used"] - 362.0) < 1e-9
    assert abs(rod["off"] - 138.0) < 1e-9
    assert rod["used"] <= STOCK + 1e-9

# ---------------------------------------------------------------------------
# лист
# ---------------------------------------------------------------------------
body = []
body.append('<rect width="297" height="210" fill="#fff"/>')
body.append(rect(4, 4, 289, 202, 0.55))
body.append(rect(6, 6, 285, 198, 0.28))

# заголовок
body.append(text(10, 13.2,
                 "РАСКРОЙ НАПРАВЛЯЮЩИХ ВАЛОВ Ø10 — 2 ПРУТКА ПО 500 мм",
                 4.7, weight="bold"))
body.append(text(10, 19.0,
                 "fix11 · 4 вала поз. 2 · L=176 (166 + 10 запас) · "
                 "рез ≤5 мм · масштаб 1:2,5",
                 2.75))
body.append(line(8, 21.5, 289, 21.5, 0.35))

# ---------------------------------------------------------------------------
# две полосы прутков
# ---------------------------------------------------------------------------
X0 = 48.0
BAR_LEN = STOCK * SCALE       # 200 мм
BAR_H = ROD_D * SCALE         # 4 мм
BAR_Y = [38.0, 74.0]

body.append(text(10, 23.2, "позиции резов", 1.8, weight="bold"))
body.append(text(10, 25.5, "от левого торца, мм", 1.8))

for rod, y in zip(RODS, BAR_Y):
    body.append(text(10, y + 2.4, "ПРУТОК %d" % rod["n"], 2.9,
                     weight="bold"))
    body.append(text(10, y + 5.7, "Ø10 × 500", 2.1))

    # позиции резов сверху
    yd = y - 7.0
    body.append(line(X0, y - 1.0, X0, yd - 1.8, 0.12))
    body.append(line(X0, yd, X0 + BAR_LEN, yd, 0.15))
    body.append(text(X0, yd - 1.7, "0", 1.9, "middle"))
    for c in rod["cuts"]:
        x = X0 + c * SCALE
        body.append(line(x, y - 1.0, x, yd - 1.5, 0.12))
        body.append(line(x, yd - 1.4, x, yd + 1.4, 0.28))
        body.append(text(x, yd - 1.7, num(c, 1), 1.9, "middle"))

    # полоса: отрезки, резы, остаток
    for i, r in enumerate(rod["rows"]):
        xs = X0 + r["start"] * SCALE
        xe = X0 + r["end"] * SCALE
        fill = "#f4f4f4" if i % 2 == 0 else "#e9e9e9"
        body.append(rect(xs, y, xe - xs, BAR_H, 0.3, fill))
        body.append(text((xs + xe) / 2.0, y + 2.55, r["id"], 2.15,
                         "middle"))
    for c in rod["cuts"]:
        body.append(rect(X0 + c * SCALE, y, KERF * SCALE, BAR_H,
                         0, "#d9534f", "none"))

    xo = X0 + rod["used"] * SCALE
    wo = max(0.35, rod["off"] * SCALE)
    body.append(rect(xo, y, wo, BAR_H, 0.25, "#cfcfcf", "#555",
                     dash="1 0.65"))
    if rod["off"] * SCALE > 4:
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

    # размеры готовых длин снизу
    yb = y + 10.0
    for r in rod["rows"]:
        body.append(dim_piece(X0 + r["start"] * SCALE,
                              X0 + r["end"] * SCALE,
                              yb, y + BAR_H, num(r["length"], 1)))
    body.append(dim_piece(xo, xo + wo, yb, y + BAR_H,
                          "ост. " + num(rod["off"], 1), 1.8))

    # правая надпись
    xr = X0 + BAR_LEN + 4.0
    body.append(text(xr, y + 2.35,
                     "ост. %s" % num(rod["off"], 1), 2.35,
                     weight="bold"))
    body.append(text(xr, y + 5.35,
                     "занято %s" % num(rod["used"], 1), 1.75))

# линия отсечения нижней части
body.append(line(8, 94.0, 289, 94.0, 0.3))

# ---------------------------------------------------------------------------
# примечания
# ---------------------------------------------------------------------------
notes = [
    ("ПРИМЕЧАНИЯ", 2.7, True),
    ("1. Сталь Ø10 h6, шлифованная; 2 сплошных прутка по 500 мм.", 1.8,
     False),
    ("2. Валы V01…V04: длина резки 176 мм (166 + 10 мм запас).", 1.8,
     False),
    ("   4×176 + 4×5 = 724 мм; остаток 276 мм (2×138).", 1.8, False),
    ("3. Резы 90°, ширина 5 мм; заусенцы снять, фаска 0,5×45°.", 1.8,
     False),
    ("4. Поверхность h6 не повреждать; применять мягкие губки.", 1.8,
     False),
    ("5. 10 мм — запас; при сборке при необходимости подрезать до 166 мм.",
     1.8, False),
    ("6. Валы взаимозаменяемы; маркировать V01…V04.", 1.8, False),
    ("7. Масштаб 1:2,5; деталь А — 2:1.", 1.8, False),
]
yy = 100.0
for s, size, bold in notes:
    body.append(text(10, yy, s, size, weight="bold" if bold else "normal"))
    yy += 3.35

# ---------------------------------------------------------------------------
# таблица раскроя
# ---------------------------------------------------------------------------
TX, TY, TW = 10.0, 136.0, 133.0
COLS = [14.0, 25.0, 25.0, 38.0, 16.0, 15.0]
ROW_H = 5.5
NROWS = 1 + len(RODS) + 1
TH = ROW_H * NROWS

body.append(rect(TX, TY, TW, TH, 0.32))
for i in range(1, NROWS):
    body.append(line(TX, TY + i * ROW_H, TX + TW, TY + i * ROW_H, 0.18))
cx = TX
for w in COLS[:-1]:
    cx += w
    body.append(line(cx, TY, cx, TY + TH, 0.18))
body.append(rect(TX + 0.01, TY + (NROWS - 1) * ROW_H + 0.01,
                 TW - 0.02, ROW_H - 0.02, 0, "#ececec", "none"))

headers = ["Прут.", "Отрезки", "Длины, мм", "Резы от торца, мм",
           "Занято", "Ост."]
data = []
for rod in RODS:
    ids = " ".join(r["id"] for r in rod["rows"])
    lens = "+".join(num(r["length"], 1) for r in rod["rows"])
    cuts = "·".join(num(c, 1) for c in rod["cuts"])
    data.append([str(rod["n"]), ids, lens, cuts, num(rod["used"], 1),
                 num(rod["off"], 1)])
data.append(["Итого", "4 вала", "704", "4×5", "724", "276"])

for ri in range(NROWS):
    vals = headers if ri == 0 else data[ri - 1]
    x = TX + 1.2
    for ci, (w, v) in enumerate(zip(COLS, vals)):
        size = 1.75 if ri else 1.8
        weight = "bold" if (ri == 0 or ri == NROWS - 1) else "normal"
        anchor = "middle" if ci in (0, 4, 5) else "start"
        xx = x + (w - 2.4) / 2.0 if anchor == "middle" else x
        body.append(text(xx, TY + ri * ROW_H + 3.6, v, size, anchor,
                         weight))
        x += w

# ---------------------------------------------------------------------------
# деталь А: торец и рез 2:1
# ---------------------------------------------------------------------------
DX, DY, DW, DH = 155.0, 98.0, 132.0, 54.0
body.append(rect(DX, DY, DW, DH, 0.3))
body.append(text(DX + 2, DY + 2.1,
                 "ДЕТАЛЬ А — ТОРЕЦ И РЕЗ 5 мм (2:1)", 2.15,
                 weight="bold"))

# два торца прутка в продольном виде, 2:1
ax0, ay0, aw, ah = 167.0, 110.0, 18.0, 20.0
gap = 10.0
body.append(rect(ax0, ay0, aw, ah, 0.35, "#e8e8e8"))
body.append(rect(ax0 + aw + gap, ay0, aw, ah, 0.35, "#e8e8e8"))
body.append(line(ax0 - 3, ay0 + ah / 2, ax0 + 2 * aw + gap + 3,
                 ay0 + ah / 2, 0.12, dash="3 0.8 0.8 0.8"))
body.append(rect(ax0 + aw, ay0, gap, ah, 0, "#f2b8b5", "none"))
body.append(line(ax0 + aw + gap / 2, ay0 - 1.5,
                 ax0 + aw + gap / 2, ay0 + ah + 1.5, 0.25,
                 dash="2 0.8", color="#b52b27"))
body.append(text(ax0 + aw + gap / 2, ay0 + ah / 2 + 1.1, "рез", 1.65,
                 "middle", rot=-90, color="#8b1a17"))

# размер 5 мм (2:1 -> 10 мм)
yb = ay0 + ah + 4.0
body.append(line(ax0 + aw, ay0 + ah, ax0 + aw, yb + 1.8, 0.12))
body.append(line(ax0 + aw + gap, ay0 + ah, ax0 + aw + gap, yb + 1.8,
                 0.12))
body.append(line(ax0 + aw, yb, ax0 + aw + gap, yb, 0.15))
body.append(arrow(ax0 + aw, yb, 1, 0))
body.append(arrow(ax0 + aw + gap, yb, -1, 0))
body.append(txt_bg(ax0 + aw + gap / 2, yb + 2.6, "5", 2.1))
body.append(text(ax0 + aw + gap / 2, yb + 2.6, "5", 2.1, "middle"))

# вертикальный размер Ø10 (2:1 -> 20 мм)
xr = ax0 + 2 * aw + gap + 3.5
body.append(line(ax0 + 2 * aw + gap, ay0, xr + 1.8, ay0, 0.12))
body.append(line(ax0 + 2 * aw + gap, ay0 + ah, xr + 1.8, ay0 + ah,
                 0.12))
body.append(line(xr, ay0, xr, ay0 + ah, 0.15))
body.append(arrow(xr, ay0, 0, -1))
body.append(arrow(xr, ay0 + ah, 0, 1))
body.append(txt_bg(xr + 2.6, ay0 + ah / 2 + 0.8, "Ø10", 2.0))
body.append(text(xr + 2.6, ay0 + ah / 2 + 0.8, "Ø10", 2.0, "middle",
                 rot=-90))

# вид с торца: сплошное круглое сечение
ecx, ecy, er = 267.0, 120.0, 10.0
body.append(circle(ecx, ecy, er, 0.32, "#e8e8e8"))
body.append(line(ecx - er - 2, ecy, ecx + er + 2, ecy, 0.12,
                 dash="3 0.8 0.8 0.8"))
body.append(line(ecx, ecy - er - 2, ecx, ecy + er + 2, 0.12,
                 dash="3 0.8 0.8 0.8"))
body.append(text(ecx, ecy + er + 3.6, "Ø10 h6", 2.0, "middle"))
body.append(text(ecx, ecy + er + 6.6, "сплошное", 1.6, "middle"))

# подпись детали
body.append(text(ax0, DY + DH - 1.5,
                 "торец 90°, фаска 0,5×45°, заусенцы снять", 1.65))

# ---------------------------------------------------------------------------
# основная надпись
# ---------------------------------------------------------------------------
BX, BY, BW, BH = 10.0, 188.0, 279.0, 16.0
body.append(rect(BX, BY, BW, BH, 0.4))
for x in (105.0, 140.0, 175.0, 210.0, 250.0):
    body.append(line(x, BY, x, BY + BH, 0.22))

body.append(text(12, BY + 6.2, "fix11 · РАСКРОЙ НАПРАВЛЯЮЩИХ ВАЛОВ",
                 3.0, weight="bold"))
body.append(text(12, BY + 12.2,
                 "сталь Ø10 h6 · 2 прутка × 500 мм · рез 5 мм", 1.9))

body.append(text(107, BY + 4.2, "МАСШТАБ", 1.45))
body.append(text(107, BY + 11.2, "1:2,5", 3.1, weight="bold"))

body.append(text(142, BY + 4.2, "ЛИСТ", 1.45))
body.append(text(142, BY + 11.2, "1/1", 3.1, weight="bold"))

body.append(text(177, BY + 4.2, "РЕЗ", 1.45))
body.append(text(177, BY + 11.0, "≤5 мм", 2.5, weight="bold"))

body.append(text(212, BY + 4.2, "ДАТА", 1.45))
body.append(text(212, BY + 10.8, "05.11.2026", 2.15))

body.append(text(252, BY + 4.2, "РАЗРАБОТАЛ", 1.45))
body.append(text(252, BY + 10.8, "DeepSeek / OpenCode", 1.75))

svg = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" '
       'viewBox="0 0 297 210">\n' + "".join(body) + "\n</svg>\n")

svg_path = os.path.join(FIG, "shaft_cut_layout.svg")
pdf_path = os.path.join(PDF, "shaft_cut_layout.pdf")
png_path = os.path.join(PIC, "shaft_cut_layout.png")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=pdf_path)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=png_path,
                 dpi=160)

# ---------------------------------------------------------------------------
# shaft_cut_plan.csv
# ---------------------------------------------------------------------------
csv_path = os.path.join(HERE, "shaft_cut_plan.csv")
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Пруток", "Поз.", "Длина, мм", "Начало, мм", "Конец, мм",
                "Рез после, мм", "Занято, мм", "Остаток, мм",
                "Примечание"])
    for rod in RODS:
        for r in rod["rows"]:
            w.writerow([rod["n"], r["id"], num(r["length"], 1),
                        num(r["start"], 1), num(r["end"], 1),
                        "%s–%s" % (num(r["end"], 1),
                                   num(r["end"] + KERF, 1)),
                        num(rod["used"], 1), num(rod["off"], 1),
                        "Ø10 h6; L=176 = 166 + 10 запас"])
    w.writerow([])
    w.writerow(["Итого", "4 вала", num(TOTAL_LEN, 1), "", "",
                "4 реза × 5 мм", num(TOTAL_USED, 1), num(TOTAL_OFF, 1),
                "2 прутка × 500 мм"])

print("SVG :", svg_path)
print("PDF :", pdf_path)
print("PNG :", png_path)
print("CSV :", csv_path)
print("Итого: длина %.1f, резов %d, занято %.1f, остаток %.1f"
      % (TOTAL_LEN, TOTAL_CUTS, TOTAL_USED, TOTAL_OFF))
for rod in RODS:
    print("  пруток %d: %s | занято %.1f | остаток %.1f"
          % (rod["n"], " ".join(r["id"] for r in rod["rows"]),
             rod["used"], rod["off"]))
