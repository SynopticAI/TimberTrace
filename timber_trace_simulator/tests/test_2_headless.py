#!/usr/bin/env python3
"""Test 2: FreeCAD Headless Document Creation"""

# Add at top of test script BEFORE importing FreeCAD
import sys
import os

# Find FreeCAD installation
conda_prefix = os.environ.get('CONDA_PREFIX')
freecad_lib = os.path.join(conda_prefix, 'Library', 'bin')
sys.path.insert(0, freecad_lib)

print("=" * 60)
print("TEST 2: Headless Document Creation")
print("=" * 60)

# Set headless mode (important!)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import FreeCAD
import Part
import Mesh

print("\n1. Creating new document...")
doc = FreeCAD.newDocument("TestDoc")
print(f"   ✓ Document created: {doc.Name}")

print("\n2. Creating box object...")
box = doc.addObject("Part::Box", "TestBox")
box.Length = 1000  # mm
box.Width = 200
box.Height = 300
print(f"   ✓ Box created")

print("\n3. Computing geometry...")
doc.recompute()
print(f"   ✓ Recompute successful")
print(f"   Volume: {box.Shape.Volume:.2f} mm³")

print("\n4. Exporting to STL...")
output_path = "/tmp/test_box.stl"
mesh_data = box.Shape.tessellate(0.1)  # Tolerance in mm
mesh_obj = Mesh.Mesh(mesh_data[0], mesh_data[1])
mesh_obj.write(output_path)
print(f"   ✓ Exported to {output_path}")

print("\n5. Loading with trimesh...")
import trimesh
loaded = trimesh.load(output_path)
print(f"   ✓ Loaded successfully")
print(f"   Trimesh volume: {loaded.volume:.2f} mm³")
print(f"   Vertices: {len(loaded.vertices)}")
print(f"   Faces: {len(loaded.faces)}")

print("\n6. Closing document...")
FreeCAD.closeDocument(doc.Name)
print(f"   ✓ Document closed")

print("\n✓ ALL TESTS PASSED")
print(f"\nGenerated file available at: {output_path}")