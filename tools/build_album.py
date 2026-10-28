#!/usr/bin/env python3
"""Сводный PDF: общий вид и детали узлов по этапам model и correct/1.

Запуск из корня проекта:
    python3 tools/build_album.py
Результат:
    stages/all_stages.pdf
"""
from pathlib import Path
import os

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "stages" / "all_stages.pdf"

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("DejaVu", FONT_REG))
if os.path.exists(FONT_BOLD):
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", FONT_BOLD))
    BOLD = "DejaVu-Bold"
else:
    BOLD = "DejaVu"

LAND = landscape(A3)
PORT = A3

PAGES = [
    {
        "group": "Общий вид",
        "title": "Исходный эскиз",
        "desc": "Фотография эскиза от руки — исходная идея устройства.",
        "file": "stages/model/pics/common_idea.jpg",
        "source": True,
    },
    {
        "group": "Общий вид",
        "title": "Вид сбоку. Разрез А–А",
        "desc": "Общая компоновка, разрез по оси, пружины и привод.",
        "file": "stages/model/pics/side_view.png",
    },
    {
        "group": "Общий вид",
        "title": "Вид слева",
        "desc": "Два ролика, кулачковый диск и пружинная подвеска.",
        "file": "stages/model/pics/left_view.png",
    },
    {
        "group": "Общий вид",
        "title": "Изометрия",
        "desc": "Пространственная схема устройства и расположение узлов.",
        "file": "stages/model/pics/isometric.png",
    },
    {
        "group": "Детали узлов",
        "title": "Столешница",
        "desc": "Облегчение, лунка Ø360 × 3, бортик и шарик Ø20.",
        "file": "stages/correct/1/pics/table.png",
    },
    {
        "group": "Детали узлов",
        "title": "Подстолье",
        "desc": "Окно Ø250, отверстия шпилек M12 и U-болтов M8.",
        "file": "stages/correct/1/pics/subtable.png",
    },
    {
        "group": "Детали узлов",
        "title": "Крепление ролика",
        "desc": "Вид снизу, разрез Д–Д, шестигранный крепёж M8.",
        "file": "stages/correct/1/pics/roller_unit.png",
    },
    {
        "group": "Детали узлов",
        "title": "Ось ролика и подшипник",
        "desc": "Разрез А–А, 6202-2RS, втулка 15/12, болт M12×45.",
        "file": "stages/correct/1/pics/roller_axle.png",
    },
    {
        "group": "Детали узлов",
        "title": "Крепление дрели",
        "desc": "Два U-болта M8, резиновые подкладки и окно.",
        "file": "stages/correct/1/pics/drill_mount.png",
    },
    {
        "group": "Детали узлов",
        "title": "Крепление кулачкового диска",
        "desc": "Оправка Ø10/Ø40, шайба Ø60, винт M8, профиль диска.",
        "file": "stages/correct/1/pics/cam_mount.png",
    },
    {
        "group": "Экспертиза",
        "title": "Кинематика кулачок–ролики",
        "desc": "Фактическая амплитуда, угол контакта, боковые силы.",
        "file": "stages/expert/pics/kinematics.png",
    },
    {
        "group": "Экспертиза",
        "title": "Динамика подвески и контакт",
        "desc": "Сила инерции, требуемый поджим пружин, резонанс.",
        "file": "stages/expert/pics/dynamics.png",
    },
    {
        "group": "Экспертиза",
        "title": "Карта рисков и защита",
        "desc": "Критичные зоны, рекомендуемый привод, сводка замечаний.",
        "file": "stages/expert/pics/safety.png",
    },
]


def line(c, x1, y1, x2, y2, width=0.6):
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def draw_cover(c):
    W, H = LAND
    c.setPageSize(LAND)
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColorRGB(0.09, 0.09, 0.09)
    c.setLineWidth(1.2)
    c.rect(36, 36, W - 72, H - 72, stroke=1, fill=0)
    line(c, 48, 48, W - 48, 48)
    line(c, 48, H - 48, W - 48, H - 48)

    c.setFillColorRGB(0.09, 0.09, 0.09)
    c.setFont(BOLD, 42)
    c.drawString(70, H - 100, "ВИБРОСТОЛ")
    c.setFont("DejaVu", 20)
    c.drawString(70, H - 138, "Сводный альбом: общий вид, детали узлов и экспертиза")
    line(c, 70, H - 160, W - 70, H - 160, 0.8)

    left_x, right_x = 70, 620
    top_y = H - 205
    c.setFont(BOLD, 15)
    c.drawString(left_x, top_y, "ОБЩИЙ ВИД")
    c.drawString(right_x, top_y, "ДЕТАЛИ УЗЛОВ")

    y = top_y - 32
    prev_group = "Общий вид"
    for idx, page in enumerate(PAGES, start=2):
        x = left_x if page["group"] == "Общий вид" else right_x
        if idx == 6:
            y = top_y - 32
            prev_group = page["group"]
        if page["group"] != prev_group:
            prev_group = page["group"]
            y -= 6
            c.setFont(BOLD, 15)
            c.drawString(right_x, y, "ЭКСПЕРТИЗА")
            y -= 28
        c.setFont(BOLD, 11.5)
        c.drawString(x, y, f"{idx}.  {page['title']}")
        c.setFont("DejaVu", 8.8)
        c.setFillColorRGB(0.36, 0.36, 0.36)
        c.drawString(x + 18, y - 12, page["desc"])
        c.setFillColorRGB(0.09, 0.09, 0.09)
        y -= 38

    c.setFont(BOLD, 11)
    c.drawString(70, 218, "Редакции")
    c.setFont("DejaVu", 9.5)
    c.drawString(70, 202, "Страницы 2–5 — общий вид этапа model; страницы 6–11 — детали узлов этапа correct/1.")
    c.drawString(70, 188, "Страницы 12–14 — листы инженерной экспертизы; полный перечень замечаний — stages/expert/Report.md.")
    c.drawString(70, 174, "Более поздние редакции узлов — листы correct/1. При противоречии использовать их.")
    c.drawString(70, 160, "Общие виды model сохранены как исходная редакция, так как позднее не перевыпускались.")

    c.setFont("DejaVu", 9)
    c.drawString(70, 105, "28.10.2026  ·  DeepSeek / OpenCode  ·  A3, 200 dpi  ·  14 страниц")
    c.drawString(70, 90, "Источники: stages/model/pics/*, stages/correct/1/pics/*, stages/expert/pics/*")

    c.bookmarkPage("cover")
    c.addOutlineEntry("Обложка и содержание", "cover", level=0)
    c.showPage()


def draw_source(c, page):
    W, H = PORT
    c.setPageSize(PORT)
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColorRGB(0.09, 0.09, 0.09)
    c.setLineWidth(0.8)
    c.rect(36, 36, W - 72, H - 72, stroke=1, fill=0)

    c.setFont(BOLD, 22)
    c.setFillColorRGB(0.09, 0.09, 0.09)
    c.drawString(60, H - 78, "Исходный эскиз")
    c.setFont("DejaVu", 10)
    c.drawString(60, H - 98, "model · stages/model/pics/common_idea.jpg")

    img = ImageReader(str(ROOT / page["file"]))
    iw, ih = img.getSize()
    box_x, box_y = 60, 100
    box_w, box_h = W - 120, H - 220
    scale = min(box_w / iw, box_h / ih)
    dw, dh = iw * scale, ih * scale
    dx = box_x + (box_w - dw) / 2
    dy = box_y + (box_h - dh) / 2
    c.drawImage(img, dx, dy, width=dw, height=dh, preserveAspectRatio=True, anchor="c")

    c.setFont("DejaVu", 9)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawString(60, 72, "Фотография эскиза от руки; исходный материал этапа model.")


def draw_drawing(c, page):
    W, H = LAND
    c.setPageSize(LAND)
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    img = ImageReader(str(ROOT / page["file"]))
    c.drawImage(img, 0, 0, width=W, height=H, preserveAspectRatio=True, anchor="c")


def main():
    for page in PAGES:
        path = ROOT / page["file"]
        if not path.exists():
            raise SystemExit(f"Нет файла: {path}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=LAND)
    c.setTitle("Вибростол — общий вид, детали узлов и экспертиза")
    c.setAuthor("DeepSeek / OpenCode")
    c.setSubject("Сводный альбом: общий вид и детали узлов этапов model и correct/1, инженерная экспертиза этапа expert")
    c.setCreator("reportlab / tools/build_album.py")

    draw_cover(c)
    for idx, page in enumerate(PAGES, start=2):
        if page.get("source"):
            draw_source(c, page)
        else:
            draw_drawing(c, page)
        key = f"p{idx}"
        c.bookmarkPage(key)
        c.addOutlineEntry(f"{idx}. {page['group']} — {page['title']}", key, level=1)
        c.showPage()
    c.save()
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
