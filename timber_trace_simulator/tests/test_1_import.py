#!/usr/bin/env python3
"""Test 1: Basic FreeCAD Import"""

# Add at top of test script BEFORE importing FreeCAD
import sys
import os

# Find FreeCAD installation
conda_prefix = os.environ.get('CONDA_PREFIX')
freecad_lib = os.path.join(conda_prefix, 'Library', 'bin')
sys.path.insert(0, freecad_lib)

print("=" * 60)
print("TEST 1: Basic FreeCAD Import")
print("=" * 60)

print("\nPython info:")
print(f"  Version: {sys.version}")
print(f"  Executable: {sys.executable}")

print("\nImporting FreeCAD modules...")
try:
    import FreeCAD
    print("  ✓ FreeCAD")
    print(f"    Version: {'.'.join(FreeCAD.Version())}")
    
    import Part
    print("  ✓ Part")
    
    import Mesh
    print("  ✓ Mesh")
    
    import Sketcher
    print("  ✓ Sketcher")
    
    import PartDesign
    print("  ✓ PartDesign")
    
    # Check if spreadsheet module exists
    try:
        import Spreadsheet
        print("  ✓ Spreadsheet")
    except:
        print("  ⚠ Spreadsheet (may need to create object to access)")
    
    print("\n✓ ALL IMPORTS SUCCESSFUL")
    sys.exit(0)
    
except ImportError as e:
    print(f"\n✗ IMPORT FAILED: {e}")
    print("\nTroubleshooting:")
    print("  1. Is conda environment activated?")
    print("     conda activate timbertrace")
    print("  2. Is FreeCAD installed?")
    print("     conda list | grep freecad")
    print("  3. Try reinstalling:")
    print("     conda install -c conda-forge freecad --force-reinstall")
    sys.exit(1)