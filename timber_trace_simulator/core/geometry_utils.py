"""
Geometry Utilities for Timber Trace Simulator

Mesh generation and manipulation functions using Trimesh.
Implements simplified joints using boolean operations.

Joint Detail Level: SIMPLIFIED
- Notch: Rectangular cut
- Mortise: Rectangular hole
- Tenon: Rectangular protrusion
- No peg holes, chamfers, or wedges initially
"""

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from typing import Tuple, Optional
#from config import GEOMETRIC_PRECISION


# ============================================================================
# Basic Mesh Creation
# ============================================================================

def create_box_mesh(
    width: float,
    height: float,
    length: float,
    center: bool = True
) -> trimesh.Trimesh:
    """
    Create a rectangular box mesh representing a timber beam.
    
    Coordinate system:
    - X-axis: width direction
    - Y-axis: height direction  
    - Z-axis: length direction (beam extends along Z)
    
    Args:
        width: Width in meters (X direction)
        height: Height in meters (Y direction)
        length: Length in meters (Z direction)
        center: If True, center the box at origin. If False, start at origin.
        
    Returns:
        trimesh.Trimesh object
    """
    # Create box with specified dimensions
    extents = np.array([width, height, length])
    box = trimesh.creation.box(extents=extents)
    
    if not center:
        # Move box so it starts at origin and extends in +Z direction
        box.apply_translation([0, 0, length / 2])
    
    return box


def create_cylinder_mesh(
    radius: float,
    length: float,
    center: bool = True,
    sections: int = 32
) -> trimesh.Trimesh:
    """
    Create a cylindrical mesh (for future use with round beams or pegs).
    
    Args:
        radius: Cylinder radius in meters
        length: Cylinder length in meters
        center: If True, center at origin
        sections: Number of radial sections (resolution)
        
    Returns:
        trimesh.Trimesh object
    """
    cylinder = trimesh.creation.cylinder(
        radius=radius,
        height=length,
        sections=sections
    )
    
    if not center:
        cylinder.apply_translation([0, 0, length / 2])
    
    return cylinder


# ============================================================================
# Joint Application Functions
# ============================================================================

def apply_notch(
    mesh: trimesh.Trimesh,
    position: np.ndarray,
    depth: float,
    width: float,
    angle: float = 0
) -> trimesh.Trimesh:
    """
    Apply a rectangular notch (cut) to a beam mesh.
    
    A notch is a rectangular cut into the beam surface, typically used
    for Sparren resting on Pfetten (Sparrenkerve).
    
    Args:
        mesh: Beam mesh to modify
        position: 3D position [x, y, z] of notch center in beam local coords
        depth: How deep the notch cuts into the beam (meters)
        width: Width of the notch in X direction (meters)
        angle: Rotation angle of notch in degrees (0 = perpendicular to beam)
               For a sparrenkerve, this should be the roof pitch angle.
        
    Returns:
        Modified mesh with notch applied
    """
    # Create a cutting box for the notch
    # The notch cuts downward from the position
    notch_length = width * 1.2  # Make slightly longer to ensure clean cut
    notch_height = depth * 1.5  # Make slightly deeper for clean cut
    notch_width = width
    
    # Create the cutting box
    cutting_box = create_box_mesh(
        width=notch_width,
        height=notch_height,
        length=notch_length,
        center=True
    )
    
    # Rotate if needed
    if angle != 0:
        # Rotate around X-axis to create angled "seat" for bird's mouth
        rotation = Rotation.from_euler('x', angle, degrees=True) # <--- FIX: Was 'z'
        cutting_box.apply_transform(rotation.as_matrix())
    
    # Position the cutting box
    # Position is the center of the notch opening
    # We move it slightly "into" the beam to ensure a clean cut
    pos_offset = position.copy()
    if pos_offset[1] < 0: # Bottom face
        pos_offset[1] += depth * 0.1
    else: # Top face
        pos_offset[1] -= depth * 0.1
        
    cutting_box.apply_translation(pos_offset)
    
    # Perform boolean difference (subtract notch from beam)
    try:
        result = mesh.difference(cutting_box, engine='blender')
        if result.is_empty:
            print("Warning: Notch boolean operation resulted in empty mesh. Returning original.")
            return mesh
        return result
    except Exception as e:
        print(f"Warning: Notch boolean operation failed: {e}. Returning original mesh.")
        return mesh

def apply_mortise(
    mesh: trimesh.Trimesh,
    position: np.ndarray,
    width: float,
    height: float,
    depth: float
) -> trimesh.Trimesh:
    """
    Apply a rectangular mortise (hole) to a beam mesh.
    
    A mortise is a rectangular hole cut into the beam to receive a tenon.
    Typically used in Pfetten to receive Stuhlpfosten tenons.
    
    Args:
        mesh: Beam mesh to modify
        position: 3D position [x, y, z] of mortise opening in beam local coords
        width: Width of mortise in X direction (meters)
        height: Height/Length of mortise in Z direction (along beam) (meters)
        depth: Depth of mortise penetration into beam in Y direction (meters)
        
    Returns:
        Modified mesh with mortise applied
    """
    # Create a cutting box for the mortise
    # Make penetration (height) and length slightly larger
    # to avoid co-planar boolean failures.
    cutting_box = create_box_mesh(
        width=width,              # X-direction
        height=depth * 1.1,       # Y-direction (penetration) <--- FIX: Was 'height'
        length=height * 1.1,      # Z-direction (along beam) <--- FIX: Was 'depth'
        center=True
    )
    
    # Position the cutting box
    # For a mortise on the bottom face, position is at the surface
    # and we need to move it UP by depth/2 to cut inward.
    mortise_position = position.copy()
    mortise_position[1] += depth / 2  # Move into the beam
    
    cutting_box.apply_translation(mortise_position)
    
    # Perform boolean difference
    try:
        result = mesh.difference(cutting_box, engine='blender')
        if result.is_empty:
            print("Warning: Mortise boolean operation resulted in empty mesh. Returning original.")
            return mesh
        return result
    except Exception as e:
        print(f"Warning: Mortise boolean operation failed: {e}. Returning original mesh.")
        return mesh


def apply_tenon(
    mesh: trimesh.Trimesh,
    position: np.ndarray,
    width: float,
    height: float,
    length: float
) -> trimesh.Trimesh:
    """
    Apply a rectangular tenon (protrusion) to a beam mesh.
    
    A tenon is a rectangular protrusion that extends from the beam
    to insert into a mortise. Typically used on Stuhlpfosten tops.
    
    Args:
        mesh: Beam mesh to modify
        position: 3D position [x, y, z] where tenon starts in beam local coords
        width: Width of tenon in X direction (meters)
        height: Height of tenon in Y direction (meters)
        length: Length of tenon protrusion (meters)
        
    Returns:
        Modified mesh with tenon added
    """
    # Create a box for the tenon protrusion
    tenon_box = create_box_mesh(
        width=width,
        height=height,
        length=length,
        center=True
    )
    
    # Position the tenon
    # It should protrude outward from the position
    tenon_position = position.copy()
    tenon_position[2] += length / 2  # Extend outward along Z
    
    tenon_box.apply_translation(tenon_position)
    
    # Perform boolean union (add tenon to beam)
    try:
        result = mesh.union(tenon_box, engine='blender')
        if result.is_empty:
            print("Warning: Tenon boolean operation resulted in empty mesh. Returning original.")
            return mesh
        return result
    except Exception as e:
        print(f"Warning: Tenon boolean operation failed: {e}. Returning original mesh.")
        return mesh


def apply_half_lap(
    mesh: trimesh.Trimesh,
    position: np.ndarray,
    depth: float,
    width: float
) -> trimesh.Trimesh:
    """
    Apply a half-lap joint cut to a beam mesh.
    
    A half-lap removes half the beam height, typically used at
    ridge connections (Firstüberblattung).
    
    Args:
        mesh: Beam mesh to modify
        position: 3D position [x, y, z] of lap center in beam local coords
        depth: Depth of cut (typically half beam height)
        width: Width of the lap (full beam width typically)
        
    Returns:
        Modified mesh with lap cut applied
    """
    # Create a cutting box for the lap
    lap_length = width * 1.2  # Slightly longer for clean cut
    
    cutting_box = create_box_mesh(
        width=width,
        height=depth,
        length=lap_length,
        center=True
    )
    
    cutting_box.apply_translation(position)
    
    # Perform boolean difference
    try:
        result = mesh.difference(cutting_box, engine='blender')
        if result.is_empty:
            print("Warning: Half-lap boolean operation resulted in empty mesh. Returning original.")
            return mesh
        return result
    except Exception as e:
        print(f"Warning: Half-lap boolean operation failed: {e}. Returning original mesh.")
        return mesh


def apply_angled_cut(
    mesh: trimesh.Trimesh,
    position: np.ndarray,
    angle: float,
    direction: np.ndarray = np.array([0, 0, 1])
) -> trimesh.Trimesh:
    """
    Apply an angled cut to a beam end (for Streben or angled connections).
    
    Args:
        mesh: Beam mesh to modify
        position: 3D position [x, y, z] where cut plane intersects
        angle: Angle of cut in degrees
        direction: Normal direction of the cut plane
        
    Returns:
        Modified mesh with angled cut
    """
    # TODO: Implement angled cutting plane
    # For now, return original mesh
    return mesh


# ============================================================================
# Transformation Functions
# ============================================================================

def apply_transform(
    mesh: trimesh.Trimesh,
    position: np.ndarray,
    orientation: Rotation
) -> trimesh.Trimesh:
    """
    Transform mesh from local coordinates to world coordinates.
    
    Args:
        mesh: Mesh in local coordinates
        position: Target position [x, y, z] in world coordinates
        orientation: Target orientation as scipy Rotation object
        
    Returns:
        Transformed mesh
    """
    # Create 4x4 transformation matrix
    transform_matrix = np.eye(4)
    
    # Set rotation (upper-left 3x3)
    transform_matrix[:3, :3] = orientation.as_matrix()
    
    # Set translation (upper-right 3x1)
    transform_matrix[:3, 3] = position
    
    # Apply transformation
    mesh_transformed = mesh.copy()
    mesh_transformed.apply_transform(transform_matrix)
    
    return mesh_transformed


def create_rotation_matrix(
    pitch: float = 0,
    yaw: float = 0,
    roll: float = 0
) -> np.ndarray:
    """
    Create rotation matrix from Euler angles.
    
    Args:
        pitch: Rotation around X-axis in degrees
        yaw: Rotation around Y-axis in degrees
        roll: Rotation around Z-axis in degrees
        
    Returns:
        3x3 rotation matrix
    """
    rotation = Rotation.from_euler('xyz', [pitch, yaw, roll], degrees=True)
    return rotation.as_matrix()


# ============================================================================
# Mesh Analysis and Utilities
# ============================================================================

def get_mesh_bounds(mesh: trimesh.Trimesh) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get axis-aligned bounding box of mesh.
    
    Args:
        mesh: Input mesh
        
    Returns:
        (min_corner, max_corner) as numpy arrays [x, y, z]
    """
    return mesh.bounds[0], mesh.bounds[1]


def get_mesh_dimensions(mesh: trimesh.Trimesh) -> np.ndarray:
    """
    Get dimensions (width, height, length) of mesh bounding box.
    
    Args:
        mesh: Input mesh
        
    Returns:
        Array [width, height, length] in meters
    """
    return mesh.extents


def combine_meshes(meshes: list) -> trimesh.Trimesh:
    """
    Combine multiple meshes into a single mesh.
    
    Args:
        meshes: List of trimesh.Trimesh objects
        
    Returns:
        Combined mesh
    """
    if not meshes:
        raise ValueError("Cannot combine empty list of meshes")
    
    if len(meshes) == 1:
        return meshes[0]
    
    # Concatenate all meshes
    combined = trimesh.util.concatenate(meshes)
    return combined


def mesh_to_point_cloud(
    mesh: trimesh.Trimesh,
    num_points: int = 10000
) -> np.ndarray:
    """
    Sample points uniformly from mesh surface.
    
    Useful for creating point clouds from mesh models.
    
    Args:
        mesh: Input mesh
        num_points: Number of points to sample
        
    Returns:
        Array of shape (num_points, 3) with XYZ coordinates
    """
    points, _ = trimesh.sample.sample_surface(mesh, num_points)
    return points


def validate_mesh(mesh: trimesh.Trimesh) -> bool:
    """
    Check if mesh is valid and watertight.
    
    Args:
        mesh: Mesh to validate
        
    Returns:
        True if valid, False otherwise
    """
    if mesh.is_empty:
        return False
    
    if not mesh.is_watertight:
        print("Warning: Mesh is not watertight")
        return False
    
    if not mesh.is_winding_consistent:
        print("Warning: Mesh has inconsistent winding")
        # Try to fix
        mesh.fix_normals()
    
    return True


# ============================================================================
# Visualization Helpers
# ============================================================================

def add_color_to_mesh(
    mesh: trimesh.Trimesh,
    color: np.ndarray
) -> trimesh.Trimesh:
    """
    Add uniform color to mesh vertices.
    
    Args:
        mesh: Input mesh
        color: RGB color as array [r, g, b] with values 0-1
        
    Returns:
        Mesh with color assigned
    """
    mesh_colored = mesh.copy()
    
    # Convert to 0-255 range
    color_255 = (np.array(color) * 255).astype(np.uint8)
    
    # Create color array for all vertices
    colors = np.tile(color_255, (len(mesh_colored.vertices), 1))
    
    # Add alpha channel (fully opaque)
    colors = np.column_stack([colors, np.full(len(mesh_colored.vertices), 255)])
    
    mesh_colored.visual.vertex_colors = colors
    
    return mesh_colored


def create_coordinate_axes(
    length: float = 1.0,
    radius: float = 0.01
) -> trimesh.Trimesh:
    """
    Create coordinate axes for visualization (RGB = XYZ).
    
    Args:
        length: Length of each axis
        radius: Radius of axis cylinders
        
    Returns:
        Combined mesh with three colored axes
    """
    # X-axis (red)
    x_axis = trimesh.creation.cylinder(radius=radius, height=length)
    x_axis.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0])
    )
    x_axis.apply_translation([length/2, 0, 0])
    x_axis.visual.vertex_colors = [255, 0, 0, 255]
    
    # Y-axis (green)
    y_axis = trimesh.creation.cylinder(radius=radius, height=length)
    y_axis.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
    )
    y_axis.apply_translation([0, length/2, 0])
    y_axis.visual.vertex_colors = [0, 255, 0, 255]
    
    # Z-axis (blue)
    z_axis = trimesh.creation.cylinder(radius=radius, height=length)
    z_axis.apply_translation([0, 0, length/2])
    z_axis.visual.vertex_colors = [0, 0, 255, 255]
    
    # Combine
    axes = trimesh.util.concatenate([x_axis, y_axis, z_axis])
    return axes


# ============================================================================
# Export Functions
# ============================================================================

def export_mesh(
    mesh: trimesh.Trimesh,
    filepath: str,
    file_format: Optional[str] = None
):
    """
    Export mesh to file.
    
    Supported formats: STL, OBJ, PLY, OFF, GLTF, GLB
    
    Args:
        mesh: Mesh to export
        filepath: Output file path
        file_format: File format (auto-detected from extension if None)
    """
    mesh.export(filepath, file_type=file_format)
    print(f"Exported mesh to {filepath}")


def export_scene(
    meshes: list,
    filepath: str
):
    """
    Export multiple meshes as a scene.
    
    Args:
        meshes: List of trimesh.Trimesh objects
        filepath: Output file path (typically .glb or .gltf)
    """
    scene = trimesh.Scene(meshes)
    scene.export(filepath)
    print(f"Exported scene to {filepath}")


# ============================================================================
# Testing and Debugging
# ============================================================================

def test_basic_beam():
    """Test basic beam creation"""
    print("Testing basic beam creation...")
    beam = create_box_mesh(0.08, 0.16, 5.0)
    print(f"  Created beam with {len(beam.vertices)} vertices")
    print(f"  Bounds: {beam.bounds}")
    print(f"  Volume: {beam.volume:.4f} m³")
    assert validate_mesh(beam), "Beam mesh is invalid"
    print("  ✓ Basic beam test passed")
    return beam


def test_notch():
    """Test notch application"""
    print("Testing notch application...")
    beam = create_box_mesh(0.08, 0.16, 5.0)
    
    # Apply notch at center, on bottom face
    notched_beam = apply_notch(
        mesh=beam,
        position=np.array([0, -0.08, 0]),  # Bottom face center
        depth=0.03,  # 30mm deep
        width=0.07   # 70mm wide
    )
    
    print(f"  Original volume: {beam.volume:.6f} m³")
    print(f"  Notched volume: {notched_beam.volume:.6f} m³")
    print(f"  Volume removed: {(beam.volume - notched_beam.volume):.6f} m³")
    assert notched_beam.volume < beam.volume, "Notch did not remove volume"
    print("  ✓ Notch test passed")
    return notched_beam


def test_mortise():
    """Test mortise application"""
    print("Testing mortise application...")
    beam = create_box_mesh(0.10, 0.20, 5.0)
    
    # Apply mortise on bottom face
    mortised_beam = apply_mortise(
        mesh=beam,
        position=np.array([0, -0.10, 0]),  # Bottom face
        width=0.08,
        height=0.08,
        depth=0.13  # 130mm deep
    )
    
    print(f"  Original volume: {beam.volume:.6f} m³")
    print(f"  Mortised volume: {mortised_beam.volume:.6f} m³")
    print(f"  Volume removed: {(beam.volume - mortised_beam.volume):.6f} m³")
    assert mortised_beam.volume < beam.volume, "Mortise did not remove volume"
    print("  ✓ Mortise test passed")
    return mortised_beam


def test_tenon():
    """Test tenon application"""
    print("Testing tenon application...")
    beam = create_box_mesh(0.12, 0.12, 2.0)
    
    # Apply tenon at top
    tenoned_beam = apply_tenon(
        mesh=beam,
        position=np.array([0, 0, 1.0]),  # Top end
        width=0.04,
        height=0.04,
        length=0.10  # 100mm protrusion
    )
    
    print(f"  Original volume: {beam.volume:.6f} m³")
    print(f"  Tenoned volume: {tenoned_beam.volume:.6f} m³")
    print(f"  Volume added: {(tenoned_beam.volume - beam.volume):.6f} m³")
    assert tenoned_beam.volume > beam.volume, "Tenon did not add volume"
    print("  ✓ Tenon test passed")
    return tenoned_beam


if __name__ == "__main__":
    """Run tests if executed directly"""
    print("=" * 60)
    print("Running Geometry Utils Tests")
    print("=" * 60)
    
    test_basic_beam()
    print()
    test_notch()
    print()
    test_mortise()
    print()
    test_tenon()
    
    print()
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)