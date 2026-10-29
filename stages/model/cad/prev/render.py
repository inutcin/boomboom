#!/usr/bin/env python3
"""Рендеры сборки вибростола (Blender 3.0 headless).

Запуск:
    cd stages/model/cad && blender -b --python render.py

Импортирует STL из stl/asm, назначает материалы по имени детали, ставит
свет/камеру и рендерит 9 ракурсов в ../pic. Затем проверяет, что габариты
видимых объектов лежат внутри кадра (0.05..0.95 по обеим осям).
"""

import math
import os
import sys
import traceback

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# --------------------------------------------------------------------------
# Пути
# --------------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(BASE, "stl", "asm")
OUT_DIR = os.path.normpath(os.path.join(BASE, os.pardir, "pic"))

os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# Материалы: (имя файла содержит) -> (цвет, metallic, roughness)
# Порядок важен - первый совпавший выигрывает.
# --------------------------------------------------------------------------
MAT_RULES = [
    ("Дрель", (0.25, 0.45, 0.75), 0.6, 0.35),
    ("Накладка", (0.85, 0.35, 0.10), 0.0, 0.55),
    ("Кулачковый", (0.85, 0.35, 0.10), 0.0, 0.55),
    ("Стол", (0.80, 0.62, 0.42), 0.0, 0.7),
    ("Подстолье", (0.80, 0.62, 0.42), 0.0, 0.7),
    ("Прокладка", (0.06, 0.06, 0.06), 0.0, 0.9),
    ("Пружина", (0.20, 0.20, 0.22), 0.9, 0.35),
]
MAT_DEFAULT = ("Прочее", (0.55, 0.58, 0.62), 0.8, 0.35)

SMOOTH_TOKENS = ("Подшипник", "Пружина", "Вал", "Кулачковый", "Ось")

# Z-фикс (только для рендера, геометрия STL не меняется).
# В модели верх "Прокладки под дрель" (z=188.0) точно совпадает с верхом
# "Подстолья" (z=188.0) - прокладка целиком лежит в толще подстолья и её
# верхняя грань копланарна столешнице, Eevee даёт z-fighting (чёрное пятно
# 100x80 на виде сверху). Опускаем прокладку на 0.25 мм: её верх уходит под
# столешницу, видимой остаётся фанера подстолья.
NUDGE_Z = {"Прокладка": -0.25}

HIDE_TOKENS = (
    "Рама",
    "Линейный подшипник LMF10UU",
    "Кронштейн",
    "Контрагайка",
    "Краб-система",
    "Балка фиксации",
    "Подстолье",
    "Дрель",
    "Хомут",
    "Прокладка",
    "Болт",
    "Шайба",
    "Ограничитель",
    "Гайка М4",
    "Гайка М6",
)

# --------------------------------------------------------------------------
# Ракурсы: файл, позиция камеры, цель, объектив, разрешение, орто
# --------------------------------------------------------------------------
VIEWS = [
    dict(name="render_iso.png", pos=(825, -855, 589), tgt=(200, 0, 140),
         lens=50, res=(2000, 1500), ortho=None),
    dict(name="render_iso_rear.png", pos=(-467, 827, 565), tgt=(210, 0, 140),
         lens=50, res=(1600, 1200), ortho=None),
    dict(name="render_front.png", pos=(-1250, 0, 215), tgt=(200, 0, 150),
         lens=85, res=(1600, 1200), ortho=None),
    dict(name="render_left.png", pos=(200, -1020, 255), tgt=(205, 0, 150),
         lens=50, res=(1600, 1200), ortho=None),
    dict(name="render_top.png", pos=(212, 0, 900), tgt=(212, 0, 100),
         lens=None, res=(1600, 1200), ortho=620.0),
    # Кадрирование ниже скорректировано: исходные (-430,-330,300)/85 мм и
    # (-320,0,190)/100 мм обрезали раму (габарит 485x200x313 мм), проверка
    # bbox 0.05..0.95 не проходила. Точка съёмки отодвинута по той же линии
    # взгляда, объектив уменьшен до 50 мм; направление ракурса сохранено.
    dict(name="render_cam.png", pos=(-748, -528, 373), tgt=(100, 0, 178),
         lens=50, res=(1600, 1200), ortho=None),
    dict(name="render_cam_axial.png", pos=(-890, 0, 194.5), tgt=(60, 0, 187),
         lens=50, res=(1600, 1200), ortho=None),
    # 520,-520,205 обрезал по верху гайку М10 (v=0.966) - отодвинуто на 12%.
    dict(name="render_mech_iso.png", pos=(570.4, -582.4, 206.8), tgt=(100, 0, 190),
         lens=60, res=(1600, 1200), ortho=None, hide=True),
    dict(name="render_mech_axial.png", pos=(-360, 0, 205), tgt=(20, 0, 200),
         lens=40, res=(1600, 1200), ortho=None, hide=True),
]


def log(msg=""):
    print(msg, flush=True)


# --------------------------------------------------------------------------
# Импорт
# --------------------------------------------------------------------------
def make_material(name, rgb, metallic, roughness):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        for node in nt.nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf = node
                break
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


def material_for(stem):
    """Возвращает (имя материала, rgb, metallic, roughness) по имени файла."""
    for token, rgb, metallic, roughness in MAT_RULES:
        if token in stem:
            return token, rgb, metallic, roughness
    return MAT_DEFAULT


def set_shading(obj, smooth):
    mesh = obj.data
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
        try:
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = math.radians(40.0)
        except AttributeError:
            pass
    else:
        for poly in mesh.polygons:
            poly.use_smooth = False
        try:
            mesh.use_auto_smooth = False
        except AttributeError:
            pass


def import_assembly():
    """Импортирует все STL сборки и возвращает список объектов."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 0.001

    files = sorted(f for f in os.listdir(STL_DIR) if f.lower().endswith(".stl"))
    if not files:
        raise RuntimeError("Нет STL в %s" % STL_DIR)

    objects = []
    for fname in files:
        path = os.path.join(STL_DIR, fname)
        stem = os.path.splitext(fname)[0]
        before = set(bpy.data.objects)
        bpy.ops.import_mesh.stl(filepath=path)
        imported = [o for o in bpy.data.objects if o not in before]
        if not imported:
            imported = list(bpy.context.selected_objects)
        if not imported:
            log("ПРОПУСК (пустой импорт): %s" % fname)
            continue

        obj = imported[0]
        obj.name = stem
        obj.data.name = stem

        # Материал по имени файла
        mat_name, rgb, metallic, roughness = material_for(stem)
        obj.data.materials.clear()
        obj.data.materials.append(
            make_material("M_" + mat_name, rgb, metallic, roughness)
        )

        # Сглаживание только для тел вращения
        set_shading(obj, any(t in stem for t in SMOOTH_TOKENS))

        # Сдвиг копланарных поверхностей (см. NUDGE_Z)
        for token, dz in NUDGE_Z.items():
            if token in stem:
                obj.location.z += dz
                log("Z-ФИКС: %s -> z %+0.2f мм" % (stem, dz))
                break

        objects.append(obj)

    log("ИМПОРТ: %d объектов из %s" % (len(objects), STL_DIR))
    return objects


# --------------------------------------------------------------------------
# Сцена: свет, фон, пол
# --------------------------------------------------------------------------
def add_empty(name, location):
    empty = bpy.data.objects.new(name, None)
    empty.location = location
    empty.empty_display_size = 50
    bpy.context.scene.collection.objects.link(empty)
    return empty


def aim_at(obj, target_location):
    """Ориентирует объект (свет) на точку: -Z смотрит в цель."""
    direction = Vector(target_location) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_world(scene):
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is None:
        bg = world.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)
    bg.inputs[1].default_value = 0.25


def setup_floor():
    bpy.ops.mesh.primitive_plane_add(size=1200.0, location=(0.0, 0.0, -1.0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    mat = make_material("M_Floor", (0.40, 0.40, 0.40), 0.0, 0.9)
    floor.data.materials.append(mat)
    return floor


def setup_lights():
    # Солнце
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 2.8
    sun_data.angle = math.radians(20.0)
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.location = (-500.0, -700.0, 1400.0)
    aim_at(sun, (200.0, 0.0, 100.0))

    # Основной (key) источник
    key_data = bpy.data.lights.new("Key", type="AREA")
    key_data.energy = 190000.0
    key_data.shape = "SQUARE"
    key_data.size = 400.0
    key = bpy.data.objects.new("Key", key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (-400.0, -600.0, 1200.0)
    aim_at(key, (200.0, 0.0, 150.0))

    # Заполняющий (fill)
    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 90000.0
    fill_data.shape = "SQUARE"
    fill_data.size = 400.0
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (800.0, 500.0, 600.0)
    aim_at(fill, (200.0, 0.0, 150.0))


def setup_render(scene):
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError:
        scene.render.engine = "EEVEE"
    eevee = scene.eevee
    eevee.taa_render_samples = 64
    try:
        eevee.use_gtao = True
        eevee.gtao_distance = 50.0
        eevee.gtao_factor = 1.0
    except AttributeError:
        pass

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 100
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.use_persistent_data = True

    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    try:
        scene.view_settings.look = "None"
    except Exception:
        pass
    cm = "?"
    try:
        scene.view_settings.view_transform = "Filmic"
        cm = "Filmic"
    except Exception:
        try:
            scene.view_settings.view_transform = "Standard"
            cm = "Standard"
        except Exception:
            cm = "fallback"
    log("COLOR MANAGEMENT: %s" % cm)
    log("SAMPLES: %d, GTAO: %s" % (eevee.taa_render_samples,
                                   getattr(eevee, "use_gtao", "n/a")))


def setup_camera(scene):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = "PERSP"
    cam_data.lens = 50.0
    cam_data.clip_start = 1.0
    cam_data.clip_end = 100000.0
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    target = add_empty("CamTarget", (200.0, 0.0, 140.0))
    con = cam.constraints.new(type="TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return cam, target


# --------------------------------------------------------------------------
# Проверка кадрирования
# --------------------------------------------------------------------------
def project_bbox(scene, cam, obj):
    """Возвращает (umin, umax, vmin, vmax, behind) для bbox объекта."""
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    us, vs = [], []
    behind = False
    for p in pts:
        co = world_to_camera_view(scene, cam, p)
        us.append(co.x)
        vs.append(co.y)
        if co.z <= 0.0:
            behind = True
    return min(us), max(us), min(vs), max(vs), behind


def check_frame(scene, cam, objects, hide=False, label=""):
    visible = [o for o in objects
               if o.type == "MESH" and not (hide and o.hide_render)]
    if not visible:
        log("ПРОВЕРКА %s: нет видимых объектов" % label)
        return False

    u0 = v0 = 1e9
    u1 = v1 = -1e9
    bad = []
    for obj in visible:
        umin, umax, vmin, vmax, behind = project_bbox(scene, cam, obj)
        u0 = min(u0, umin)
        u1 = max(u1, umax)
        v0 = min(v0, vmin)
        v1 = max(v1, vmax)
        if behind or umin < 0.05 or umax > 0.95 or vmin < 0.05 or vmax > 0.95:
            bad.append((obj.name, umin, umax, vmin, vmax, behind))

    ok = not bad
    log("ПРОВЕРКА %s: %s  u=%.3f..%.3f v=%.3f..%.3f  объектов=%d"
        % (label, "PASS" if ok else "FAIL", u0, u1, v0, v1, len(visible)))
    for name, umin, umax, vmin, vmax, behind in bad[:12]:
        log("    вне кадра: %-45s u=%.3f..%.3f v=%.3f..%.3f%s"
            % (name, umin, umax, vmin, vmax, " BEHIND" if behind else ""))
    if len(bad) > 12:
        log("    ... ещё %d объектов" % (len(bad) - 12))
    return ok


# --------------------------------------------------------------------------
# Рендер
# --------------------------------------------------------------------------
def apply_hide(objects, hide):
    for obj in objects:
        obj.hide_render = bool(hide) and any(t in obj.name for t in HIDE_TOKENS)


def render_view(scene, cam, target, objects, view):
    name = view["name"]
    path = os.path.join(OUT_DIR, name)
    res_x, res_y = view["res"]

    try:
        cam.location = view["pos"]
        target.location = view["tgt"]
        if view["ortho"]:
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = view["ortho"]
        else:
            cam.data.type = "PERSP"
            cam.data.lens = view["lens"]
        cam.data.clip_start = 1.0
        cam.data.clip_end = 100000.0

        scene.render.resolution_x = res_x
        scene.render.resolution_y = res_y
        scene.render.resolution_percentage = 100
        scene.render.filepath = path
        scene.render.image_settings.file_format = "PNG"

        bpy.context.view_layer.update()

        hide = view.get("hide", False)
        apply_hide(objects, hide)
        bpy.context.view_layer.update()

        ok_frame = check_frame(scene, cam, objects, hide=hide, label=name)

        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)

        if os.path.exists(path):
            size = os.path.getsize(path)
            log("RENDER OK %s (%d bytes)" % (path, size))
        else:
            log("RENDER FAIL %s (файл не создан)" % path)
            ok_frame = False
        return ok_frame
    except Exception:
        log("RENDER FAIL %s" % path)
        traceback.print_exc()
        return False
    finally:
        apply_hide(objects, False)
        bpy.context.view_layer.update()


def main():
    objects = import_assembly()
    scene = bpy.context.scene

    setup_world(scene)
    setup_floor()
    setup_lights()
    setup_render(scene)
    cam, target = setup_camera(scene)

    results = []
    for view in VIEWS:
        results.append((view["name"], render_view(scene, cam, target, objects, view)))

    log("")
    log("ИТОГО:")
    for name, ok in results:
        path = os.path.join(OUT_DIR, name)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        log("  %-24s %-10d %s" % (name, size, "FRAME OK" if ok else "FRAME BAD"))
    log("ГОТОВО: %d/%d ракурсов в кадре" % (sum(1 for _, ok in results if ok),
                                             len(results)))


if __name__ == "__main__":
    # Необязательный список файлов после "--" - рендерить только их.
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args:
        VIEWS[:] = [v for v in VIEWS if v["name"] in args]
    main()
