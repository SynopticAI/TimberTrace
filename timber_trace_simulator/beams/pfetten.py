"""
Pfetten (Purlin) Beam Classes

Contains the three types of purlins used in Pfettendach construction:
- Firstpfette: Ridge purlin at the peak
- Mittelpfette: Middle purlins (intermediate support)
- Fußpfette: Foot/eaves purlin at the bottom
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET

from .base_beam import BaseBeam
from config import BEAM_TYPES, JOINT_TYPES


class Firstpfette(BaseBeam):
    """
    Firstpfette (ridge purlin) - horizontal beam at the roof peak.
    
    Characteristics:
    - Runs along the ridge (First) of the roof
    - Supported by Stuhlpfosten (posts) via mortise-tenon joints
    - Receives Sparren on both sides (via notches in the Sparren)
    - Typically the highest horizontal beam
    """
    
    beam_type = BEAM_TYPES['FIRSTPFETTE']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        stuhlpfosten_connections: List[Dict],
        sparren_support_spacing: float,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Center point of beam in world coordinates
            orientation: Rotation (typically just around vertical axis for horizontal beam)
            length: Total beam length in meters
            cross_section: (width, height) in mm
            stuhlpfosten_connections: List of dicts with:
                - position_normalized: 0-1, position along beam
                - stuhlpfosten_id: ID of supporting post
                - joint_type: Usually MORTISE_TENON
            sparren_support_spacing: Distance between supported Sparren (meters)
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.stuhlpfosten_connections = stuhlpfosten_connections
        self.sparren_support_spacing = sparren_support_spacing
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'num_support_posts': len(self.stuhlpfosten_connections),
            'support_positions': [conn['position_normalized'] 
                                 for conn in self.stuhlpfosten_connections],
            'sparren_spacing': self.sparren_support_spacing,
            'num_sparren_supported': int(self.length / self.sparren_support_spacing) * 2,  # Both sides
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with mortises for Stuhlpfosten"""
        from core.geometry_utils import (
            create_box_mesh, apply_transform
        )
        
        mesh = create_box_mesh(
            width=self.width_m,
            height=self.height_m,
            length=self.length
        )
        
        mesh = self._create_joint_geometry(mesh)
        mesh = apply_transform(mesh, self.position, self.orientation)
        
        return mesh
    
    def _create_joint_geometry(self, mesh):
        """
        Apply mortises for Stuhlpfosten connections.
        
        The Stuhlpfosten have tenons that insert into mortises in the Pfette.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with mortises
        """
        from core.geometry_utils import apply_mortise
        
        for connection in self.stuhlpfosten_connections:
            pos_norm = connection['position_normalized']
            
            # Position along beam (beam extends along Z-axis)
            z_position = (pos_norm - 0.5) * self.length
            
            # Mortise dimensions (typical: 1/3 width of post, 2/3 depth)
            mortise_width = 0.08  # ~80mm typical
            mortise_height = 0.08
            mortise_depth = self.height_m * 0.67
            
            # Apply mortise on bottom face (-Y direction)
            mesh = apply_mortise(
                mesh=mesh,
                position=np.array([0, -self.height_m/2, z_position]),
                width=mortise_width,
                height=mortise_height,
                depth=mortise_depth
            )
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Firstpfette':
        """Deserialize from XML"""
        # Similar structure to Sparren.from_xml()
        pass


class Mittelpfette(BaseBeam):
    """
    Mittelpfette (middle purlin) - intermediate horizontal support beam.
    
    Characteristics:
    - Runs parallel to ridge, positioned between First and Fuß
    - Supported by Stuhlpfosten or Streben
    - Receives Sparren from both sides (via notches in Sparren)
    - Multiple Mittelpfetten may exist at different heights
    """
    
    beam_type = BEAM_TYPES['MITTELPFETTE']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        support_connections: List[Dict],
        height_above_base: float,
        sparren_support_spacing: float,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Center point in world coordinates
            orientation: Rotation
            length: Total beam length in meters
            cross_section: (width, height) in mm
            support_connections: List of dicts with:
                - position_normalized: 0-1
                - support_id: ID of Stuhlpfosten or Strebe
                - support_type: "stuhlpfosten" or "strebe"
                - joint_type: Connection type
            height_above_base: Vertical height from base (meters)
            sparren_support_spacing: Distance between Sparren
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.support_connections = support_connections
        self.height_above_base = height_above_base
        self.sparren_support_spacing = sparren_support_spacing
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'height_above_base': self.height_above_base,
            'num_supports': len(self.support_connections),
            'support_positions': [conn['position_normalized'] 
                                 for conn in self.support_connections],
            'sparren_spacing': self.sparren_support_spacing,
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with connection points for supports"""
        from core.geometry_utils import (
            create_box_mesh, apply_transform
        )
        
        mesh = create_box_mesh(
            width=self.width_m,
            height=self.height_m,
            length=self.length
        )
        
        mesh = self._create_joint_geometry(mesh)
        mesh = apply_transform(mesh, self.position, self.orientation)
        
        return mesh
    
    def _create_joint_geometry(self, mesh):
        """
        Apply mortises/notches for Stuhlpfosten or Streben connections.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh
        """
        from core.geometry_utils import apply_mortise
        
        for connection in self.support_connections:
            pos_norm = connection['position_normalized']
            z_position = (pos_norm - 0.5) * self.length
            
            if connection['support_type'] == 'stuhlpfosten':
                # Mortise for post tenon
                mesh = apply_mortise(
                    mesh=mesh,
                    position=np.array([0, -self.height_m/2, z_position]),
                    width=0.08,
                    height=0.08,
                    depth=self.height_m * 0.67
                )
            # elif connection['support_type'] == 'strebe':
            #     # Different joint for brace connection
            #     pass
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Mittelpfette':
        """Deserialize from XML"""
        pass


class Fußpfette(BaseBeam):
    """
    Fußpfette (foot/eaves purlin) - horizontal beam at the eaves.
    
    Characteristics:
    - Runs along the lower edge of the roof (eaves/traufe)
    - Typically rests on the wall plate or beam
    - Receives the lower ends of Sparren
    - May be supported by wall or by extended Stuhlpfosten
    """
    
    beam_type = BEAM_TYPES['FUSSPFETTE']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        wall_support: bool,
        sparren_support_spacing: float,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Center point in world coordinates
            orientation: Rotation
            length: Total beam length in meters
            cross_section: (width, height) in mm
            wall_support: True if resting on wall, False if on posts
            sparren_support_spacing: Distance between Sparren
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.wall_support = wall_support
        self.sparren_support_spacing = sparren_support_spacing
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'wall_support': self.wall_support,
            'sparren_spacing': self.sparren_support_spacing,
            'num_sparren_supported': int(self.length / self.sparren_support_spacing) * 2,
        })
        
        return params
    
    def get_mesh(self):
        """
        Generate mesh for Fußpfette.
        
        Simpler than other pfetten - typically no mortises needed
        as it usually rests on wall or has simple bearing connections.
        """
        from core.geometry_utils import (
            create_box_mesh, apply_transform
        )
        
        mesh = create_box_mesh(
            width=self.width_m,
            height=self.height_m,
            length=self.length
        )
        
        mesh = self._create_joint_geometry(mesh)
        mesh = apply_transform(mesh, self.position, self.orientation)
        
        return mesh
    
    def _create_joint_geometry(self, mesh):
        """
        Fußpfette typically has simple bearing connections.
        May add wall plate notch or simple bearing surface preparation.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh (minimal modifications for Fußpfette)
        """
        # For now, return mesh unchanged
        # Can add wall bearing notch if needed
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Fußpfette':
        """Deserialize from XML"""
        pass