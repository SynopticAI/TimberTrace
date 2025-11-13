"""
Five Random Beams Example

Generates 5 different beam types with various positions and joints,
then exports as a single STL file for external viewing.
"""

import sys
import numpy as np
from scipy.spatial.transform import Rotation
import os

# Get the full path to this script's directory (e.g., .../examples)
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))

from beams import (
    Pfettendach_Sparren,
    Firstpfette,
    Mittelpfette,
    Stuhlpfosten,
    Strebe
)
from core.geometry_utils import combine_meshes, export_mesh


def main():
    print("Generating 5 random beams...")
    
    meshes = []
    
    # Beam 1: Pfettendach_Sparren with notches
    print("1. Creating Pfettendach_Sparren with 2 notches...")
    sparren = Pfettendach_Sparren(
        beam_id=0,
        position=np.array([0, 0, 0]),
        orientation=Rotation.from_euler('y', 45, degrees=True),
        length=5.0,
        cross_section=(80, 160),
        pitch_angle=45.0,
        pfette_connections=[
            {'position_normalized': 0.3, 'pfette_id': 1, 'notch_depth': 0.03},
            {'position_normalized': 0.7, 'pfette_id': 2, 'notch_depth': 0.03},
        ]
    )
    meshes.append(sparren.get_mesh())
    
    # Beam 2: Firstpfette with mortises
    print("2. Creating Firstpfette with 2 mortises...")
    pfette = Firstpfette(
        beam_id=1,
        position=np.array([0, 3.0, 0]),
        orientation=Rotation.identity(),
        length=8.0,
        cross_section=(100, 200),
        stuhlpfosten_connections=[
            {'position_normalized': 0.3, 'stuhlpfosten_id': 3, 'joint_type': 'MORTISE_TENON'},
            {'position_normalized': 0.7, 'stuhlpfosten_id': 4, 'joint_type': 'MORTISE_TENON'},
        ],
        sparren_support_spacing=0.8
    )
    meshes.append(pfette.get_mesh())
    
    # Beam 3: Another Sparren at different angle
    print("3. Creating second Sparren at different angle...")
    sparren2 = Pfettendach_Sparren(
        beam_id=2,
        position=np.array([6, 0, 0]),
        orientation=Rotation.from_euler('y', -45, degrees=True),
        length=5.0,
        cross_section=(80, 160),
        pitch_angle=45.0,
        pfette_connections=[
            {'position_normalized': 0.3, 'pfette_id': 1, 'notch_depth': 0.03},
            {'position_normalized': 0.7, 'pfette_id': 2, 'notch_depth': 0.03},
        ]
    )
    meshes.append(sparren2.get_mesh())
    
    # Beam 4: Stuhlpfosten with tenon
    print("4. Creating Stuhlpfosten with tenon...")
    post = Stuhlpfosten(
        beam_id=3,
        position=np.array([-2, 0.5, 0]),
        orientation=Rotation.identity(),
        length=2.5,
        cross_section=(120, 120),
        top_connection={
            'pfette_id': 1,
            'joint_type': 'MORTISE_TENON',
            'tenon_height': 0.10
        },
        bottom_connection={
            'base_type': 'floor_beam',
            'joint_type': 'BEARING'
        }
    )
    meshes.append(post.get_mesh())
    
    # Beam 5: Mittelpfette
    print("5. Creating Mittelpfette...")
    mittelpfette = Mittelpfette(
        beam_id=4,
        position=np.array([0, 1.5, 2]),
        orientation=Rotation.from_euler('z', 0, degrees=True),
        length=7.0,
        cross_section=(100, 200),
        support_connections=[
            {'position_normalized': 0.5, 'support_id': 5, 'support_type': 'stuhlpfosten', 'joint_type': 'MORTISE_TENON'}
        ],
        height_above_base=1.5,
        sparren_support_spacing=0.8
    )
    meshes.append(mittelpfette.get_mesh())
    
    # Combine all meshes
    print("\nCombining meshes...")
    combined = combine_meshes(meshes)
    
    print(f"Combined mesh stats:")
    print(f"  Total vertices: {len(combined.vertices)}")
    print(f"  Total faces: {len(combined.faces)}")
    print(f"  Total volume: {combined.volume:.4f} m³")
    
    # Export to STL
    output_path = "five_random_beams.stl"
    print(f"\nExporting to {output_path}...")
    export_mesh(combined, output_path)
    
    print("\n✓ Done! Open the STL file in your 3D viewer.")
    print(f"  File: {output_path}")


if __name__ == "__main__":
    main()
