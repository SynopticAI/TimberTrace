"""
Pfetten (Purlin) Beam Classes - FreeCAD Version

Contains the three types of purlins used in Pfettendach construction:
- Firstpfette: Ridge purlin at the peak
- Mittelpfette: Middle purlins (intermediate support)
- Fußpfette: Foot/eaves purlin at the bottom
"""

from typing import Dict, Tuple
import numpy as np
from scipy.spatial.transform import Rotation

from .base_beam import BaseBeam
from config import BEAM_TYPES


class Firstpfette(BaseBeam):
    """
    Firstpfette (ridge purlin) - horizontal beam at the roof peak.
    
    FreeCAD Template Convention:
    - Origin at centerline, one end
    - Extends longitudinally in +Z direction
    - Mortises on bottom face for Stuhlpfosten tenons
    
    Characteristics:
    - Runs along the ridge (First) of the roof
    - Supported by Stuhlpfosten via mortise-tenon joints
    - Uses linear pattern for mortises
    """
    
    beam_type = BEAM_TYPES['FIRSTPFETTE']
    freecad_template = "Firstpfette.FCStd"
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        mortise_count: int,
        mortise_spacing: float,  # meters
        mortise_width: float = 80.0,  # mm
        mortise_depth: float = 80.0,  # mm
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Start point (one end at centerline) in world coordinates
            orientation: Rotation (typically just rotation around Z for horizontal beam)
            length: Total beam length in meters
            cross_section: (width, height) in mm
            mortise_count: Number of mortises (= number of Stuhlpfosten)
            mortise_spacing: Distance between mortises in meters
            mortise_width: Width of mortise in mm
            mortise_depth: Depth of mortise penetration in mm
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.mortise_count = mortise_count
        self.mortise_spacing = mortise_spacing
        self.mortise_width = mortise_width
        self.mortise_depth = mortise_depth
    
    def get_freecad_parameters(self) -> Dict[str, float]:
        """
        Return parameters for Firstpfette.FCStd template.
        
        Uses linear pattern for mortises:
        - mortise_count: how many mortises
        - mortise_spacing: distance between them (mm)
        
        FreeCAD template creates mortise pattern automatically.
        
        Returns:
            Dict with dimensions and mortise pattern parameters
        """
        params = self.get_base_freecad_parameters()
        
        params.update({
            'mortise_count': float(self.mortise_count),
            'mortise_spacing': self.mortise_spacing * 1000.0,  # Convert to mm
            'mortise_width': self.mortise_width,
            'mortise_depth': self.mortise_depth,
        })
        
        return params


class Mittelpfette(BaseBeam):
    """
    Mittelpfette (middle purlin) - intermediate horizontal support beam.
    
    FreeCAD Template Convention:
    - Same as Firstpfette
    - Origin at centerline, one end
    - Extends longitudinally in +Z direction
    
    Characteristics:
    - Runs parallel to ridge, between First and Fuß
    - Supported by Stuhlpfosten
    - Uses linear pattern for mortises
    """
    
    beam_type = BEAM_TYPES['MITTELPFETTE']
    freecad_template = "Mittelpfette.FCStd"
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        mortise_count: int,
        mortise_spacing: float,  # meters
        mortise_width: float = 80.0,  # mm
        mortise_depth: float = 80.0,  # mm
        wood_species: str = "SPRUCE"
    ):
        """
        Args: Same as Firstpfette
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.mortise_count = mortise_count
        self.mortise_spacing = mortise_spacing
        self.mortise_width = mortise_width
        self.mortise_depth = mortise_depth
    
    def get_freecad_parameters(self) -> Dict[str, float]:
        """Return parameters for Mittelpfette.FCStd template."""
        params = self.get_base_freecad_parameters()
        
        params.update({
            'mortise_count': float(self.mortise_count),
            'mortise_spacing': self.mortise_spacing * 1000.0,  # Convert to mm
            'mortise_width': self.mortise_width,
            'mortise_depth': self.mortise_depth,
        })
        
        return params


class Fußpfette(BaseBeam):
    """
    Fußpfette (foot/eaves purlin) - horizontal beam at the eaves.
    
    FreeCAD Template Convention:
    - Origin at centerline, one end
    - Extends longitudinally in +Z direction
    - No mortises (rests on wall)
    
    Characteristics:
    - Runs along the lower edge of the roof (eaves)
    - Typically rests on wall (no mortises needed)
    - Simplest Pfette type
    """
    
    beam_type = BEAM_TYPES['FUSSPFETTE']
    freecad_template = "Fusspfette.FCStd"
    
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
        Args:
            beam_id: Unique identifier
            position: Start point in world coordinates
            orientation: Rotation
            length: Total beam length in meters
            cross_section: (width, height) in mm
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
    
    def get_freecad_parameters(self) -> Dict[str, float]:
        """
        Return parameters for Fusspfette.FCStd template.
        
        Fußpfette is simple - just a box, no joints.
        
        Returns:
            Dict with just basic dimensions
        """
        return self.get_base_freecad_parameters()