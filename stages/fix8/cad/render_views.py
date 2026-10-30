"""Рендеры сборки fix8 (Blender 3.0 headless, EEVEE).

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
    ("frame",   (0.16, 0.22, 0.28), 0.00, 0.52, 1.0),
    ("table",   (0.70, 0.60, 0.42), 0.00, 0.60, 1.0),
    ("overlay", (0.92, 0.35, 0.08), 0.00, 0.50, 1.0),
    ("retainer", (0.22, 0.26, 0.30), 0.00, 0.50, 1.0),
    ("cam",     (0.92, 0.30, 0.05), 0.00, 0.50, 1.0),
    ("steel",   (0.55, 0.57, 0.60), 0.90, 0.32, 1.0),
    ("bearing", (0.05, 0.06, 0.08), 0.70, 0.35, 1.0),
    ("angles",  (0.60, 0.62, 0.65), 0.85, 0.30, 1.0),
    ("shield",  (0.55, 0.75, 0.95), 0.00, 0.12, 0.22),
    ("rubber",  (0.04, 0.04, 0.05), 0.00, 0.85, 1.0),
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
drill.append(cyl("drill_body", 0.050, 0.130, (0.275, 0.100, 0.140),
                 (0, math.pi / 2, 0), mat_drill))
drill.append(cyl("drill_chuck", 0.020, 0.030, (0.215, 0.100, 0.140),
                 (0, math.pi / 2, 0), mat_chuck))
drill.append(cube("drill_handle", (0.345, 0.100, 0.130),
                  (0.030, 0.060, 0.090), mat_drill))
drill.append(cyl("drill_side_handle", 0.008, 0.055, (0.275, 0.178, 0.165),
                 (math.pi / 2, 0, 0), mat_handle))

# ----------------------------------------------------------------------------
# пол, свет, камера
# ----------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.17, 0.10, 0))
floor = bpy.context.object
floor.data.materials.append(mat("floor", (0.45, 0.47, 0.50), 0.0, 0.85))

bpy.ops.object.empty_add(location=(0.17, 0.10, 0.15))
target = bpy.context.object
bpy.ops.object.empty_add(location=(0.01, 0.05, 0.09))
target_clamp = bpy.context.object
bpy.ops.object.empty_add(location=(0.01, 0.08, 0.09))
target_down = bpy.context.object
bpy.ops.object.empty_add(location=(0.01, 0.10, 0.14))
target_pocket = bpy.context.object
bpy.ops.object.empty_add(location=(0.28, 0.10, 0.196))
target_podstol = bpy.context.object
bpy.ops.object.empty_add(location=(0.082, 0.10, 0.145))
target_cam = bpy.context.object
bpy.ops.object.empty_add(location=(0.087, 0.10, 0.140))
target_washer = bpy.context.object
bpy.ops.object.empty_add(location=(0.010, 0.050, 0.176))
target_ring = bpy.context.object
bpy.ops.object.empty_add(location=(0.020, 0.032, 0.255))
target_pad = bpy.context.object
bpy.ops.object.empty_add(location=(0.010, 0.100, 0.140))
target_b1 = bpy.context.object
bpy.ops.object.empty_add(location=(0.150, 0.100, 0.140))
target_b2 = bpy.context.object
bpy.ops.object.empty_add(location=(0.080, 0.100, 0.140))
target_bearing = bpy.context.object


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
    ("render_iso", camera("iso", (-0.46, -0.58, 0.42), 55), "full"),
    ("render_iso_rear", camera("iso_rear", (0.78, -0.52, 0.42), 55), "full"),
    ("render_left", camera("left", (0.17, -0.88, 0.18), 65), "full"),
    ("render_top", camera("top", (0.46, -0.38, 0.80), 60), "full"),
    ("render_front", camera("front", (-0.72, 0.10, 0.20), 60), "full"),
    ("render_shield", camera("shield", (-0.62, -0.60, 0.36), 55), "shield"),
    ("render_mechanism", camera("mech", (-0.02, -0.40, 0.21), 80), "mech"),
    ("render_cam", camera("cam", (0.18, -0.24, 0.19), 85,
                          tgt=target_cam), "cam"),
    ("render_washer", camera("washer", (0.21, -0.18, 0.15), 90,
                             tgt=target_washer), "cam"),
    ("render_ring", camera("ring", (-0.12, -0.20, 0.20), 85,
                           tgt=target_ring), "ring"),
    ("render_pad", camera("pad", (-0.12, -0.26, 0.34), 80,
                          tgt=target_pad), "pad"),
    ("render_retainer_down", camera("down", (-0.20, -0.30, 0.28), 80,
                                    tgt=target_down), "down"),
    ("render_bearing_1", camera("bearing1", (-0.19, -0.20, 0.155), 95,
                                tgt=target_b1), "mech"),
    ("render_bearing_2", camera("bearing2", (0.245, -0.20, 0.155), 95,
                                tgt=target_b2), "mech"),
    ("render_bearing_2_left", camera("bearing2l", (0.040, -0.160, 0.170),
                                     110, tgt=target_b2), "bearing"),
    ("render_bearing_clamp", camera("clamp", (-0.22, -0.30, 0.09), 70,
                                    tgt=target_bearing), "mech"),
    ("render_podstol", camera("podstol", (0.54, -0.34, 0.42), 60,
                              tgt=target_podstol), "podstol"),
]

HIDE = {
    "full": set(),
    "shield": set(),
    "mech": {"frame", "table", "overlay", "shield", "rubber"},
    "bearing": {"frame", "table", "overlay", "shield", "rubber", "cam",
                "angles"},
    "cam": {"frame", "table", "overlay", "shield", "rubber",
            "retainer", "angles"},
    "ring": {"shield"},
    "pad": {"shield"},
    "down": {"shield"},
    "podstol": {"shield"},
}


def render(name, cam, mode):
    for k, ob in objs.items():
        ob.hide_render = k in HIDE.get(mode, set())
    for ob in drill:
        ob.hide_render = mode not in ("full", "shield", "podstol")
    if mode == "shield" and "shield" in objs:
        try:
            m = objs["shield"].data.materials[0]
            m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.65
        except Exception:
            pass
    if mode == "down":
        for k in ("retainer", "angles"):
            if k in objs:
                objs[k].location.z -= 0.015
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name, flush=True)
    if mode == "shield" and "shield" in objs:
        try:
            m = objs["shield"].data.materials[0]
            m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.22
        except Exception:
            pass
    if mode == "down":
        for k in ("retainer", "angles"):
            if k in objs:
                objs[k].location.z += 0.015


if QUICK:
    render("render_test", VIEWS[0][1], "full")
else:
    for name, cam, mode in VIEWS:
        render(name, cam, mode)
