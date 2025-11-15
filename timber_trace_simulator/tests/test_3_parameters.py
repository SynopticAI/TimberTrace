#!/usr/bin/env python3
"""Test 3: Parametric Control via Spreadsheet"""


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

print("=" * 60)
print("TEST 3: Parametric Control via Spreadsheet")
print("=" * 60)

print("\n1. Creating document with spreadsheet...")
doc = FreeCAD.newDocument("ParametricTest")

# Create spreadsheet
sheet = doc.addObject('Spreadsheet::Sheet', 'Parameters')
print(f"   ✓ Spreadsheet created")

print("\n2. Setting up parameters...")
# Set parameter values and aliases
sheet.set('A1', 'length')
sheet.set('B1', '1000')
sheet.setAlias('B1', 'length')

sheet.set('A2', 'width')
sheet.set('B2', '200')
sheet.setAlias('B2', 'width')

sheet.set('A3', 'height')
sheet.set('B3', '300')
sheet.setAlias('B3', 'height')

doc.recompute()
print(f"   ✓ Parameters set")
print(f"     length = {sheet.get('B1')}")
print(f"     width = {sheet.get('B2')}")
print(f"     height = {sheet.get('B3')}")

print("\n3. Creating parametric box...")
box = doc.addObject("Part::Box", "ParametricBox")
box.setExpression('Length', 'Parameters.length')
box.setExpression('Width', 'Parameters.width')
box.setExpression('Height', 'Parameters.height')
doc.recompute()

initial_volume = box.Shape.Volume
print(f"   ✓ Parametric box created")
print(f"     Volume: {initial_volume:.2f} mm³")

print("\n4. Changing parameters programmatically...")
sheet.set('B1', '2000')  # Double length
sheet.set('B2', '400')   # Double width
doc.recompute()

new_volume = box.Shape.Volume
print(f"   ✓ Parameters updated")
print(f"     New length: {sheet.get('B1')}")
print(f"     New width: {sheet.get('B2')}")
print(f"     New volume: {new_volume:.2f} mm³")

volume_ratio = new_volume / initial_volume
print(f"     Volume ratio: {volume_ratio:.2f}x (expected: 4.00x)")

if abs(volume_ratio - 4.0) < 0.1:
    print(f"   ✓ Volume change correct!")
else:
    print(f"   ✗ Volume change incorrect!")
    sys.exit(1)

print("\n5. Closing document...")
FreeCAD.closeDocument(doc.Name)

print("\n✓ PARAMETRIC CONTROL WORKING!")