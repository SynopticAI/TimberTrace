"""
Example: Generate a Simple Pfettendach

This script demonstrates how to use the PfettendachRechteckGenerator
to create a full roof structure, get all the beam meshes,
and export them as a single combined STL file.
"""

import sys
import os
import numpy as np

# --- Add project root to path ---
# This is the same path fix from five_random_beams.py
# It allows Python to find the 'generators', 'beams', and 'core' packages
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)
# ------------------------------

from generators import PfettendachRechteckGenerator
from core.geometry_utils import combine_meshes, export_mesh

def main():
    """
    Main function to generate and export the roof.
    """
    print("--- TimberTrace Roof Generation Example ---")

    # 1. Define Roof Parameters
    # These parameters will be fed to the generator.
    print("1. Defining roof parameters...")
    roof_params = {
        'building_length': 10.0,  # 10 meters long
        'building_width': 8.0,    # 8 meters wide
        'roof_pitch_deg': 45.0,   # 45-degree pitch
        'sparren_spacing': 0.8,   # 80cm between rafters
        'pfetten_count': 5,       # 5 purlins (1 First, 2 Mittel, 2 Fuß)
        'support_spacing': 3.0    # 3m between support posts
    }
    print(f"   - Parameters set for {roof_params['building_width']}x{roof_params['building_length']}m roof.")

    # 2. Instantiate Generator
    print("2. Initializing PfettendachRechteckGenerator...")
    try:
        generator = PfettendachRechteckGenerator(roof_params)
    except ValueError as e:
        print(f"\nError initializing generator: {e}")
        return

    # 3. Generate Beams
    print("3. Generating all roof beams...")
    beams = generator.generate()
    print(f"   - Successfully generated {len(beams)} beams.")

    # 4. Get Meshes from Beams
    print("4. Generating 3D mesh for each beam...")
    meshes = []
    for beam in beams:
        try:
            # get_mesh() applies all joints and transformations
            meshes.append(beam.get_mesh())
        except Exception as e:
            print(f"   - Warning: Failed to generate mesh for {beam}: {e}")
    
    if not meshes:
        print("Error: No meshes were generated. Aborting.")
        return
        
    print(f"   - Generated {len(meshes)} meshes.")

    # 5. Combine Meshes
    print("5. Combining all meshes into a single scene...")
    combined_mesh = combine_meshes(meshes)
    print(f"   - Combined mesh stats:")
    print(f"     - Vertices: {len(combined_mesh.vertices)}")
    print(f"     - Faces: {len(combined_mesh.faces)}")

    # 6. Export to STL
    # Save the file in the same directory as this script
    output_filename = "generated_pfettendach.stl"
    output_path = os.path.join(script_dir, output_filename)
    
    print(f"\n6. Exporting combined mesh to STL...")
    try:
        export_mesh(combined_mesh, output_path)
        print(f"\n✓ Success! Roof exported to:")
        print(f"  {output_path}")
        print("You can now open this file in a 3D viewer (like 3D Viewer on Windows, or Blender).")
    except Exception as e:
        print(f"\nError exporting file: {e}")


if __name__ == "__main__":
    main()