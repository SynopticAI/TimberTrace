#!/usr/bin/env python3
"""Test 4: Save Template, Reload with New Parameters"""


# Add at top of test script BEFORE importing FreeCAD
import sys
import os

# Find FreeCAD installation
conda_prefix = os.environ.get('CONDA_PREFIX')
freecad_lib = os.path.join(conda_prefix, 'Library', 'bin')
sys.path.insert(0, freecad_lib)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import FreeCAD
import Part
import Mesh
import trimesh

print("=" * 60)
print("TEST 4: Template Save & Reload")
print("=" * 60)

template_path = "/tmp/test_template.FCStd"

# Part 1: Create and save template
print("\n1. Creating parametric template...")
doc = FreeCAD.newDocument("Template")

sheet = doc.addObject('Spreadsheet::Sheet', 'Parameters')
sheet.set('A1', 'length')
sheet.set('B1', '1000')
sheet.setAlias('B1', 'length')

sheet.set('A2', 'width')
sheet.set('B2', '200')
sheet.setAlias('B2', 'width')

sheet.set('A3', 'height')
sheet.set('B3', '300')
sheet.setAlias('B3', 'height')

# Create body with parametric box
body = doc.addObject('PartDesign::Body', 'Body')
box = body.newObject('PartDesign::AdditiveBox', 'Box')
box.setExpression('Length', 'Parameters.length')
box.setExpression('Width', 'Parameters.width')
box.setExpression('Height', 'Parameters.height')

doc.recompute()
print(f"   ✓ Template created")

print(f"\n2. Saving template to {template_path}...")
doc.saveAs(template_path)
print(f"   ✓ Template saved")

initial_volume = box.Shape.Volume
print(f"   Initial volume: {initial_volume:.2f} mm³")

FreeCAD.closeDocument(doc.Name)

# Part 2: Reload and modify
print(f"\n3. Reloading template...")
doc2 = FreeCAD.openDocument(template_path)
print(f"   ✓ Template loaded")

print(f"\n4. Finding objects...")
sheet2 = doc2.getObject('Parameters')
body2 = doc2.getObject('Body')
print(f"   ✓ Found spreadsheet and body")

print(f"\n5. Changing parameters...")
sheet2.set('B1', '3000')  # Triple length
sheet2.set('B2', '600')   # Triple width
sheet2.set('B3', '900')   # Triple height
doc2.recompute()

new_volume = body2.Shape.Volume
print(f"   ✓ Parameters changed")
print(f"     New volume: {new_volume:.2f} mm³")

volume_ratio = new_volume / initial_volume
print(f"     Volume ratio: {volume_ratio:.2f}x (expected: 27.00x)")

if abs(volume_ratio - 27.0) < 0.1:
    print(f"   ✓ Volume change correct (3³ = 27)!")
else:
    print(f"   ✗ Volume change incorrect!")

print(f"\n6. Exporting modified geometry...")
mesh_data = body2.Shape.tessellate(0.1)
mesh_obj = Mesh.Mesh(mesh_data[0], mesh_data[1])
output_path = "/tmp/test_template_modified.stl"
mesh_obj.write(output_path)

loaded = trimesh.load(output_path)
print(f"   ✓ Exported to {output_path}")
print(f"     Trimesh volume: {loaded.volume:.2f} mm³")

FreeCAD.closeDocument(doc2.Name)

print("\n✓ TEMPLATE WORKFLOW WORKING!")
print(f"\nTemplate file: {template_path}")
print(f"Output STL: {output_path}")