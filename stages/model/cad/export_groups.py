"""Экспорт групп STL для рендеров (FreeCAD).

    freecadcmd export_groups.py

Раскладывает тела по материалам в cad/stl/groups; накладка и кулачок —
отдельно (для рендера механизма без стола).
"""
import os
import sys

import FreeCAD as App
import MeshPart

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "stl", "groups")
os.makedirs(OUT, exist_ok=True)

import model

parts, groups, cams = model.build_assembly()


def stl(shape, name):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.8,
                               AngularDeflection=0.6, Relative=False)
    fn = os.path.join(OUT, "grp_%s.stl" % name)
    m.write(fn)
    print(name, len(m.Facets), os.path.getsize(fn) // 1024, "KB")


for name, shapes in groups.items():
    if name == "printed":
        continue
    from params import P  # noqa: F401
    import Part
    stl(Part.makeCompound(shapes), name)
stl(parts["overlay"]["shape"], "overlay")
stl(cams["cam_5"], "cam")
