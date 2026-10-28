# Растровые копии эскизов

В этом каталоге должны лежать PNG-копии векторных листов из `../fig/` с теми же
именами. Конвертацию выполняет заказчик (в среде агента нет командной оболочки).

```bash
cd stages/model
rsvg-convert -f png -d 300 -p 300 -b white -o pic/views_side_left.png fig/views_side_left.svg
rsvg-convert -f png -d 300 -p 300 -b white -o pic/view_top.png        fig/view_top.svg
rsvg-convert -f png -d 300 -p 300 -b white -o pic/assembly_3d.png     fig/assembly_3d.svg
```

Ожидаемый результат — три файла:

| Файл | Лист |
|---|---|
| `views_side_left.png` | лист 1: виды сбоку и слева |
| `view_top.png` | лист 2: вид сверху, узел I, спецификация |
| `assembly_3d.png` | лист 3: изометрия |

Каталог `../pics/` содержит исходное фото эскиза `common_idea.jpg` и не изменяется.
