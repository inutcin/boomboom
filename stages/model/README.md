# Формирование эскизов устройства по рисунку от руки.

Требуется взять фото эскизов трёх проекций
- [`stages/model/pic/vibrotable_front.png`](../../../stages/model/pic/vibrotable_front.png)
- [`stages/model/pic/vibrotable_left.png`](../../../stages/model/pic/vibrotable_left.png)
- [`stages/model/pic/vibrotable_top.png`](../../../stages/model/pic/vibrotable_top.png)
 
Сделать на его основе

- 3D модель в установленном формате 
- эскиз в 3 проекциях: вид сбоку и вид слева
- трёхмерное изображение конструкции.
- спецификацию деталей

Строго следовать эскизу не придумывать

## Результаты этапа

- Отчёт: [Report.md](./Report.md); предыдущая попытка — [Report_prev.md](./Report_prev.md)
- Вопросы и уточнения: [Interview.md](./Interview.md)
- 3D-модель: [cad/step/vibrotable_assembly.step](./cad/step/vibrotable_assembly.step),
  детали — `cad/step/*.step`; исходники — [cad/](./cad/) (`model.py`, `params.py`,
  `build.py`, `draw_sheet.py`, `render_views.py`, `export_groups.py`)
- Печатные детали: [cad/stl/](./cad/stl/) (`overlay.stl`, `cam_3.stl`,
  `cam_5.stl`, `cam_10.stl`)
- Эскиз в трёх проекциях (A3, HLR): [fig/vibrotable_views.svg](./fig/vibrotable_views.svg);
  изометрия — [fig/iso.svg](./fig/iso.svg)
- Спецификация и параметры: [fig/vibrotable_spec.svg](./fig/vibrotable_spec.svg),
  [spec.csv](./spec.csv), [params.csv](./params.csv),
  [cad/checks.csv](./cad/checks.csv), [cad/mass.csv](./cad/mass.csv)
- Рендеры: [pic/](./pic/) (`render_iso.png`, `render_iso_rear.png`,
  `render_left.png`, `render_top.png`, `render_mechanism.png`);
  превью листов — `views_sheet.png`, `spec_sheet.png`
- Материалы предыдущей попытки (стол 156×156, CadQuery) сохранены в
  `fig/prev/`, `pic/prev/`, `cad/prev/` и [Report_prev.md](./Report_prev.md);
  они не являются результатом текущей сборки.
