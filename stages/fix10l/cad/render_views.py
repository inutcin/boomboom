"""Рендеры сборки fix10l (Blender, EEVEE).

Запуск:
    blender -b --python render_views.py [-- --quick]

Импортирует группы STL из cad/stl/groups, назначает материалы, ставит свет,
камеры и рендерит ракурсы в ../pic. Дрель — условная модель-заглушка.
"""

import math
import os
import sys

import bpy

BASE = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(BASE, "stl", "groups")
OUT_DIR = os.path.normpath(os.path.join(BASE, os.pardir, "pic"))
QUICK = "--quick" in sys.argv
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 24 if QUICK else 64
sc.eevee.use_gtao = True
sc.eevee.use_soft_shadows = True
sc.render.resolution_x = 900 if QUICK else 1200
sc.render.resolution_y = 675 if QUICK else 900
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.80, 0.84, 0.90, 1.0)
bg.inputs[1].default_value = 0.45


def mat(name, color, metal=0.0, rough=0.5, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    try:
        p.inputs["Alpha"].default_value = alpha
    except Exception:
        pass
    if alpha < 1.0:
        m.blend_method = "BLEND"
        m.show_transparent_back = False
        try:
            m.shadow_method = "NONE"
        except Exception:
            pass
    return m


GROUPS = [
    ("wood", (0.62, 0.44, 0.26), 0.0, 0.62, 1.0),
    ("overlay", (0.92, 0.35, 0.08), 0.0, 0.50, 1.0),
    ("steel", (0.55, 0.57, 0.60), 0.90, 0.32, 1.0),
    ("spring", (0.72, 0.73, 0.75), 0.90, 0.28, 1.0),
    ("bearing", (0.05, 0.06, 0.08), 0.70, 0.35, 1.0),
    ("cam", (0.92, 0.30, 0.05), 0.0, 0.48, 1.0),
    ("rubber", (0.04, 0.04, 0.05), 0.0, 0.85, 1.0),
    ("plastic", (0.86, 0.86, 0.82), 0.0, 0.60, 1.0),
    ("drill", (0.16, 0.30, 0.52), 0.55, 0.38, 1.0),
]
objs = {}
for name, c, me, ro, al in GROUPS:
    fn = os.path.join(STL_DIR, "grp_%s.stl" % name)
    if not os.path.exists(fn):
        print("MISSING", fn)
        continue
    bpy.ops.import_mesh.stl(filepath=fn)
    ob = bpy.context.selected_objects[0]
    ob.name = name
    ob.scale = (0.001, 0.001, 0.001)
    ob.data.materials.append(mat(name, c, me, ro, al))
    for poly in ob.data.polygons:
        poly.use_smooth = False
    objs[name] = ob

# ----------------------------------------------------------------------------
# пол, свет, камеры
# ----------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.20, 0.10, 0))
floor = bpy.context.object
floor.data.materials.append(mat("floor", (0.45, 0.47, 0.50), 0.0, 0.85))

bpy.ops.object.empty_add(location=(0.20, 0.10, 0.13))
target = bpy.context.object
bpy.ops.object.empty_add(location=(0.10, 0.10, 0.25))
target_table = bpy.context.object
bpy.ops.object.empty_add(location=(0.10, 0.10, 0.14))
target_cam = bpy.context.object


def sun(name, rot, power, angle=6.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = power
    d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.rotation_euler = rot
    return o


sun("key", (math.radians(55), 0, math.radians(35)), 2.6)
sun("fill", (math.radians(65), 0, math.radians(-120)), 0.8)


def area(name, loc, power, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = power
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.location = loc
    c = o.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return o


area("rim", (0.0, 0.85, 0.55), 18, 0.6, (1.0, 0.96, 0.9))


def camera(name, loc, lens=55, tgt=None):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.clip_start = 0.001
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.location = loc
    c = o.constraints.new("TRACK_TO")
    c.target = tgt if tgt is not None else target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return o


VIEWS = [
    ("render_iso", camera("iso", (-0.24, -0.52, 0.42), 55), "full",
     target),
    ("render_iso_rear", camera("iso_rear", (0.66, -0.46, 0.40), 55), "full",
     target),
    ("render_front", camera("front", (-0.66, 0.10, 0.17), 62), "full",
     target),
    ("render_left", camera("left", (0.20, -0.82, 0.17), 62), "full",
     target),
    ("render_rear", camera("rear", (0.95, 0.10, 0.17), 55), "full",
     target),
    ("render_top", camera("top", (0.20, 0.10, 1.00), 55), "full",
     target),
    ("render_table_top", camera("table_top", (0.10, -0.30, 0.62), 55), "table",
     target_table),
    ("render_mechanism", camera("mech", (-0.10, -0.42, 0.34), 60), "mech",
     target),
    ("render_cam", camera("cam", (-0.22, -0.50, 0.32), 65), "mech",
     target_cam),
]

HIDE = {
    "full": set(),
    "table": set(),
    "mech": {"wood", "overlay", "plastic", "drill", "rubber"},
}
DRILL_VISIBLE = {"full", "table"}


def render(name, cam, mode, tgt):
    for k, ob in objs.items():
        ob.hide_render = k in HIDE.get(mode, set())
    if "drill" in objs:
        objs["drill"].hide_render = mode not in DRILL_VISIBLE
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name, flush=True)


if QUICK:
    render(VIEWS[0][0], VIEWS[0][1], VIEWS[0][2], VIEWS[0][3])
else:
    for name, cam, mode, tgt in VIEWS:
        render(name, cam, mode, tgt)
