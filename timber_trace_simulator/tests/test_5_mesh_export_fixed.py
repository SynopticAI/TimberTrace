#!/usr/bin/env python3
"""Test: Verify Corrected FreeCAD Mesh Export"""

import sys
import os

# Add project to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Find FreeCAD installation
conda_prefix = os.environ.get('CONDA_PREFIX')
if conda_prefix:
    freecad_lib = os.path.join(conda_prefix, 'Library', 'bin')
    sys.path.insert(0, freecad_lib)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

print("=" * 60)
print("TEST: Corrected Mesh Export")
print("=" * 60)

from core.freecad_utils import test_freecad_utils

# Run the test
test_freecad_utils()
