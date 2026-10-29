"""Рендеры сборки fix2 (Blender 3.0 headless, EEVEE).

Запуск:
    blender -b --python render_views.py [-- --quick]

Импортирует группы STL из cad/stl/groups, назначает материалы, ставит свет,
камеру и рендерит ракурсы в ../pic. Дрель — условная модель-заглушка.
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

# ----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 32 if QUICK else 64
sc.eevee.use_gtao = True
sc.eevee.use_soft_shadows = True
sc.render.resolution_x = 900 if QUICK else 1200
sc.render.resolution_y = 675 if QUICK else 900
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"

# ----------------------------------------------------------------------------
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.80, 0.84, 0.90, 1.0)
bg.inputs[1].default_value = 0.45


def mat(name, color, metal=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    return m


GROUPS = [
    ("frame",   (0.16, 0.22, 0.28), 0.00, 0.52),
    ("table",   (0.70, 0.60, 0.42), 0.00, 0.60),
    ("overlay", (0.92, 0.35, 0.08), 0.00, 0.50),
    ("retainer", (0.22, 0.26, 0.30), 0.00, 0.50),
    ("cam",     (0.92, 0.30, 0.05), 0.00, 0.50),
    ("steel",   (0.55, 0.57, 0.60), 0.90, 0.32),
    ("bearing", (0.05, 0.06, 0.08), 0.70, 0.35),
    ("crabs",   (0.60, 0.62, 0.65), 0.85, 0.30),
]
objs = {}
for name, c, me, ro in GROUPS:
    fn = os.path.join(STL_DIR, "grp_%s.stl" % name)
    if not os.path.exists(fn):
        print("MISSING", fn)
        continue
    bpy.ops.import_mesh.stl(filepath=fn)
    ob = bpy.context.selected_objects[0]
    ob.name = name
    ob.scale = (0.001, 0.001, 0.001)
    ob.data.materials.append(mat(name, c, me, ro))
    for poly in ob.data.polygons:
        poly.use_smooth = False
    objs[name] = ob
bpy.context.view_layer.update()

# ----------------------------------------------------------------------------
# дрель — условная модель под подстольем
# ----------------------------------------------------------------------------
def cyl(name, r, depth, loc, rot=(0, 0, 0), material=None, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    if material:
        ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def cube(name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(material)
    return ob


mat_drill = mat("drill", (0.16, 0.30, 0.52), 0.55, 0.38)
mat_chuck = mat("chuck", (0.35, 0.36, 0.38), 0.85, 0.28)
mat_handle = mat("handle", (0.06, 0.06, 0.07), 0.0, 0.6)

drill = []
drill.append(cyl("drill_body", 0.050, 0.110, (0.325, 0.100, 0.140),
                 (0, math.pi / 2, 0), mat_drill))
drill.append(cyl("drill_chuck", 0.020, 0.030, (0.255, 0.100, 0.140),
                 (0, math.pi / 2, 0), mat_chuck))
drill.append(cube("drill_handle", (0.395, 0.100, 0.130),
                  (0.030, 0.060, 0.090), mat_drill))
drill.append(cyl("drill_side_handle", 0.008, 0.055, (0.315, 0.178, 0.165),
                 (math.pi / 2, 0, 0), mat_handle))

# ----------------------------------------------------------------------------
# пол, свет, камера
# ----------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.19, 0.10, 0))
floor = bpy.context.object
floor.data.materials.append(mat("floor", (0.45, 0.47, 0.50), 0.0, 0.85))

bpy.ops.object.empty_add(location=(0.19, 0.10, 0.15))
target = bpy.context.object
bpy.ops.object.empty_add(location=(0.01, 0.05, 0.09))
target_clamp = bpy.context.object
bpy.ops.object.empty_add(location=(0.01, 0.08, 0.09))
target_down = bpy.context.object
bpy.ops.object.empty_add(location=(0.01, 0.10, 0.14))
target_pocket = bpy.context.object
bpy.ops.object.empty_add(location=(0.32, 0.10, 0.196))
target_podstol = bpy.context.object


def sun(name, rot, power, angle=6.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = power
    d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.rotation_euler = rot
    return o


sun("key", (math.radians(55), 0, math.radians(35)), 2.4)
sun("fill", (math.radians(65), 0, math.radians(-120)), 0.7)


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


area("rim", (0.0, 0.80, 0.55), 14, 0.5, (1.0, 0.96, 0.9))


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
    ("render_iso", camera("iso", (-0.50, -0.58, 0.42), 55), "full"),
    ("render_iso_rear", camera("iso_rear", (0.82, -0.52, 0.42), 55), "full"),
    ("render_left", camera("left", (0.19, -0.88, 0.18), 65), "full"),
    ("render_top", camera("top", (0.50, -0.38, 0.80), 60), "full"),
    ("render_front", camera("front", (-0.80, 0.10, 0.20), 60), "full"),
    ("render_mechanism", camera("mech", (-0.02, -0.40, 0.21), 80), "mech"),
    ("render_clamp", camera("clamp", (-0.18, -0.14, 0.22), 80,
                            tgt=target_clamp), "clamp"),
    ("render_retainer_down", camera("down", (-0.20, -0.30, 0.28), 80,
                                    tgt=target_down), "down"),
    ("render_bearing_pocket", camera("pocket", (-0.10, -0.12, 0.20), 85,
                                     tgt=target_pocket), "pocket"),
    ("render_crab", camera("crab", (-0.30, -0.28, 0.21), 65,
                           tgt=target_clamp), "crab"),
    ("render_podstol", camera("podstol", (0.58, -0.34, 0.42), 60,
                              tgt=target_podstol), "podstol"),
    ("render_shaft_nuts", camera("shaft", (-0.12, 0.01, 0.18), 85,
                                 tgt=target_pocket), "pocket"),
]


def render(name, cam, mode):
    full = mode == "full"
    show = {"frame": full, "table": full, "overlay": full}
    if mode in ("pocket", "crab"):
        show["frame"] = True
    if mode == "podstol":
        show["frame"] = True
        show["table"] = True
    for k in ("frame", "table", "overlay"):
        if k in objs:
            objs[k].hide_render = not show[k]
    for k in ("retainer", "cam", "steel", "bearing", "crabs"):
        if k in objs:
            objs[k].hide_render = False
    for ob in drill:
        ob.hide_render = not (full or mode == "podstol")
    if mode == "down":
        for k in ("retainer", "crabs"):
            if k in objs:
                objs[k].location.z -= 0.020
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name, flush=True)
    if mode == "down":
        for k in ("retainer", "crabs"):
            if k in objs:
                objs[k].location.z += 0.020


if QUICK:
    render("render_test", VIEWS[0][1], "full")
else:
    for name, cam, mode in VIEWS:
        render(name, cam, mode)
