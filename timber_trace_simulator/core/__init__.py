"""
Core Package - Timber Trace Simulator

Geometry utilities, visualization, and I/O functions.
"""

from .geometry_utils import (
    # Basic mesh creation
    create_box_mesh,
    create_cylinder_mesh,
    
    # Joint operations
    apply_notch,
    apply_mortise,
    apply_tenon,
    apply_half_lap,
    apply_angled_cut,
    
    # Transformations
    apply_transform,
    create_rotation_matrix,
    
    # Mesh utilities
    get_mesh_bounds,
    get_mesh_dimensions,
    combine_meshes,
    mesh_to_point_cloud,
    validate_mesh,
    
    # Visualization
    add_color_to_mesh,
    create_coordinate_axes,
    
    # Export
    export_mesh,
    export_scene,
)

__all__ = [
    'create_box_mesh',
    'create_cylinder_mesh',
    'apply_notch',
    'apply_mortise',
    'apply_tenon',
    'apply_half_lap',
    'apply_angled_cut',
    'apply_transform',
    'create_rotation_matrix',
    'get_mesh_bounds',
    'get_mesh_dimensions',
    'combine_meshes',
    'mesh_to_point_cloud',
    'validate_mesh',
    'add_color_to_mesh',
    'create_coordinate_axes',
    'export_mesh',
    'export_scene',
]