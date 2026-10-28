# Формирование модели устройства по эскизу от руки

## Редакция 2 (28.10.2026)

Исходник — переделанный эскиз
[`pics/common_idea.jpg`](./pics/common_idea.jpg): компактная схема
200 × 200, рама из трубы 20 × 20 × 1,5, направляющие Ø10 с линейными
подшипниками, кулачок на шпильке М10, ролики 6200.

Нужно было получить:

- эскиз в двух проекциях — **вид сбоку** и **вид слева**;
- **трёхмерное изображение** конструкции.

Дополнительно на листах дан **вид сверху** (он есть в эскизе) и
спецификация на 18 позиций.

## Что выпущено

| Лист | SVG | PNG | Содержание |
|---:|---|---|---|
| 1 | [`figs/side_view.svg`](./figs/side_view.svg) | [`pics/side_view.png`](./pics/side_view.png) | Вид сбоку, разрез А–А; вид сверху 1:4 |
| 2 | [`figs/left_view.svg`](./figs/left_view.svg) | [`pics/left_view.png`](./pics/left_view.png) | Вид слева; узел контакта ролик–кулачок 1:1 |
| 3 | [`figs/isometric.svg`](./figs/isometric.svg) | [`pics/isometric.png`](./pics/isometric.png) | Изометрия с разрезом стола и подстолья |

Листы A3, масштаб 1:2; PNG — 3307 × 2339 px (200 dpi).

## Сборка

```bash
bash stages/model/tools/render.sh
```

Скрипт запускает `node stages/model/tools/generate.js` и растрирует SVG
через `inkscape` (резерв — headless Chromium). Генератор детерминированный,
без внешних зависимостей.

> В среде, где готовилась редакция 2, у агента был отключён `bash`,
> поэтому SVG/PNG пересобираются этой командой. До её запуска в `figs/`
> и `pics/` лежат файлы редакции 1 — см. [`figs/README.md`](./figs/README.md)
> и [`pics/README.md`](./pics/README.md).

## Документы

- [`Report.md`](./Report.md) — отчёт, параметры, расчёты, проверка
  требований, риски и предложения.
- [`Interview.md`](./Interview.md) — трактовка эскиза, допущения,
  открытые вопросы.
- [`archive_v1/`](./archive_v1/README.md) — редакция 1 (27.10.2026).

## Состав

```
stages/model/
  README.md
  Report.md
  Interview.md
  figs/  side_view.svg  left_view.svg  isometric.svg
  pics/  side_view.png  left_view.png  isometric.png  common_idea.jpg
  tools/ generate.js  render.sh
  archive_v1/ README.md  Report.md  Interview.md
```
