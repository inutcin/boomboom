"""Экспорт групп STL для рендеров (FreeCAD), этап fix2.

    freecadcmd export_groups.py

Группы: frame, table (стол+подстолье), overlay, retainer, cam, steel,
bearing, crabs (крабы + их крепёж).
"""
import os
import sys

import FreeCAD as App
import MeshPart
import Part

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
    stl(Part.makeCompound(shapes), name)
