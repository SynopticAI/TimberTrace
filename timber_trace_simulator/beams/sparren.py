"""
Pfettendach_Sparren (Rafter) Beam Class - FreeCAD Version

Rafters for Pfettendach construction that rest on Pfetten via notches.
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial.transform import Rotation

from .base_beam import BaseBeam
from config import BEAM_TYPES


class Pfettendach_Sparren(BaseBeam):
    """
    Sparren (rafter) for Pfettendach construction.
    
    FreeCAD Template Convention:
    - Origin at eaves end (lower end) center
    - Extends toward ridge in +Z direction
    - Notches cut into bottom face
    
    Characteristics:
    - Rests on Pfetten (purlins) via notches (Sparrenkerve)
    - Does NOT directly connect to opposing Sparren
    - Has angled notches at each Pfette intersection point
    """
    
    beam_type = BEAM_TYPES['PFETTENDACH_SPARREN']
    freecad_template = "Pfettendach_Sparren.FCStd"
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        pitch_angle: float,
        notch_positions: List[float],  # Normalized 0-1
        notch_depth: float = 30.0,  # mm
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Start point (eaves end) in world coordinates
            orientation: Rotation defining beam direction
            length: Total beam length in meters
            cross_section: (width, height) in mm
            pitch_angle: Roof pitch in degrees
            notch_positions: List of normalized positions (0-1) where notches occur
            notch_depth: Depth of notch cut in mm
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.pitch_angle = pitch_angle
        self.notch_positions = notch_positions
        self.notch_depth = notch_depth
    
    def get_freecad_parameters(self) -> Dict[str, float]:
        """
        Return parameters for Pfettendach_Sparren.FCStd template.
        
        FreeCAD template supports up to 10 notches.
        Unused notches are disabled via notchN_enabled = 0.
        
        Returns:
            Dict with dimensions, pitch_angle, and notch parameters
        """
        params = self.get_base_freecad_parameters()
        
        params.update({
            'pitch_angle': self.pitch_angle,
        })
        
        # Add notch parameters (up to 10)
        MAX_NOTCHES = 10
        for i in range(MAX_NOTCHES):
            if i < len(self.notch_positions):
                # Enable this notch
                params[f'notch{i+1}_enabled'] = 1.0
                params[f'notch{i+1}_z_normalized'] = self.notch_positions[i]
                params[f'notch{i+1}_depth'] = self.notch_depth
                params[f'notch{i+1}_angle'] = self.pitch_angle
            else:
                # Disable unused notches
                params[f'notch{i+1}_enabled'] = 0.0
                params[f'notch{i+1}_z_normalized'] = 0.0
                params[f'notch{i+1}_depth'] = 0.0
                params[f'notch{i+1}_angle'] = 0.0
        
        return params