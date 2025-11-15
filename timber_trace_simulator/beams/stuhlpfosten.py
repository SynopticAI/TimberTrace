"""
Stuhlpfosten (Support Post) Beam Class - FreeCAD Version

Vertical support posts that carry the Pfetten in Pfettendach construction.
"""

from typing import Dict, Tuple
import numpy as np
from scipy.spatial.transform import Rotation

from .base_beam import BaseBeam
from config import BEAM_TYPES


class Stuhlpfosten(BaseBeam):
    """
    Stuhlpfosten (support post) - vertical beam supporting Pfetten.
    
    FreeCAD Template Convention:
    - Origin at bottom center of post
    - Extends upward in +Z direction
    - Tenon protrudes from top
    
    Characteristics:
    - Vertical orientation
    - Has tenon at top that inserts into Pfette mortise
    - Typically square cross-section
    - Simple geometry
    """
    
    beam_type = BEAM_TYPES['STUHLPFOSTEN']
    freecad_template = "Stuhlpfosten.FCStd"
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        tenon_length: float = 100.0,  # mm
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Base point (bottom center) in world coordinates
            orientation: Rotation (typically identity for vertical posts)
            length: Height of post in meters
            cross_section: (width, height) in mm - typically square
            tenon_length: Length of tenon protrusion at top in mm
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.tenon_length = tenon_length
        
        # Verify approximately square cross-section
        if abs(cross_section[0] - cross_section[1]) > 20:
            print(f"Warning: Stuhlpfosten typically has square cross-section, "
                  f"got {cross_section}")
    
    def get_freecad_parameters(self) -> Dict[str, float]:
        """
        Return parameters for Stuhlpfosten.FCStd template.
        
        FreeCAD template calculates:
        - tenon_width = width * 0.33
        - tenon_depth = height * 0.33
        
        Returns:
            Dict with length, width, height, tenon_length (all in mm)
        """
        params = self.get_base_freecad_parameters()
        
        params.update({
            'tenon_length': self.tenon_length,
        })
        
        return params