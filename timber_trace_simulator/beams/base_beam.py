"""
Base Beam Class for Timber Trace Simulator - FreeCAD Version

Abstract base class that all concrete beam types inherit from.
Simplified for FreeCAD template-based geometry generation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation


class BaseBeam(ABC):
    """
    Abstract base class for all timber beam types.
    
    All concrete beam classes must implement:
    - get_freecad_parameters() - Returns dict for FreeCAD spreadsheet
    - freecad_template - Class variable with template filename
    """
    
    # Must be overridden by subclasses
    beam_type: str = "BaseBeam"
    freecad_template: str = "base.FCStd"
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        wood_species: str = "SPRUCE"
    ):
        """
        Initialize a beam.
        
        Args:
            beam_id: Unique identifier for this beam instance
            position: 3D position [x, y, z] in meters (beam START point)
            orientation: Rotation object defining beam orientation
            length: Beam length in meters
            cross_section: (width, height) in millimeters
            wood_species: Wood type (SPRUCE, OAK, FIR, PINE)
        """
        self.beam_id = beam_id
        self.position = np.array(position, dtype=float)
        self.orientation = orientation
        self.length = length  # meters
        self.cross_section = cross_section  # (width, height) in mm
        self.wood_species = wood_species
    
    @property
    def width(self) -> float:
        """Width in millimeters"""
        return self.cross_section[0]
    
    @property
    def height(self) -> float:
        """Height in millimeters"""
        return self.cross_section[1]
    
    @property
    def length_mm(self) -> float:
        """Length in millimeters (for FreeCAD)"""
        return self.length * 1000.0
    
    @abstractmethod
    def get_freecad_parameters(self) -> Dict[str, float]:
        """
        Return parameter dictionary for FreeCAD spreadsheet.
        
        Each beam type defines its own parameter schema.
        Values should be in millimeters and degrees (FreeCAD standard units).
        
        Returns:
            Dictionary with all beam-specific parameters for FreeCAD template
        """
        pass
    
    def get_base_freecad_parameters(self) -> Dict[str, float]:
        """
        Return parameters common to all beam types.
        Subclasses should call this and extend with specific parameters.
        
        Returns:
            Dict with length, width, height in mm
        """
        return {
            'length': self.length_mm,
            'width': self.width,
            'height': self.height,
        }
    
    def get_mesh(self):
        """
        Generate 3D mesh from FreeCAD template.
        
        Returns:
            trimesh.Trimesh object in world coordinates
        """
        from core.freecad_utils import generate_mesh_from_template
        from core.geometry_utils import apply_transform
        
        # Get mesh in local coordinates from FreeCAD template
        local_mesh = generate_mesh_from_template(
            template_path=self.freecad_template,
            parameters=self.get_freecad_parameters()
        )
        
        # Transform to world coordinates
        world_mesh = apply_transform(local_mesh, self.position, self.orientation)
        
        return world_mesh
    
    def get_parameters(self) -> Dict:
        """
        Return parameters for ML Stage 2 (legacy compatibility).
        
        Returns:
            Dictionary with all beam parameters
        """
        params = {
            'beam_id': self.beam_id,
            'beam_type': self.beam_type,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'position': self.position.tolist(),
            'orientation_quaternion': self.orientation.as_quat().tolist(),
            'wood_species': self.wood_species,
        }
        
        # Add FreeCAD parameters
        params.update(self.get_freecad_parameters())
        
        return params
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (f"{self.beam_type}(id={self.beam_id}, "
                f"length={self.length:.2f}m, "
                f"cross_section={self.width}x{self.height}mm)")
    
    def __str__(self) -> str:
        """Human-readable string"""
        return f"{self.beam_type} #{self.beam_id}"