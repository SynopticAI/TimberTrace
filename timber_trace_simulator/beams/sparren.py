"""
Sparren (Rafter) Beam Classes

Contains roof-construction-specific Sparren variants:
- Pfettendach_Sparren: Rafter that rests on Pfetten with notches
- Sparrendach_Sparren: Rafter that meets opposing rafter at ridge
- Kehlbalkendach_Sparren: Rafter with collar beam connection
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET

from .base_beam import BaseBeam
from config import BEAM_TYPES, JOINT_TYPES


class Pfettendach_Sparren(BaseBeam):
    """
    Sparren (rafter) for Pfettendach construction.
    
    Characteristics:
    - Rests on Pfetten (purlins) via notches (Sparrenkerve)
    - Does NOT directly connect to opposing Sparren
    - Has notches at each Pfette intersection point
    """
    
    beam_type = BEAM_TYPES['PFETTENDACH_SPARREN']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        pitch_angle: float,
        pfette_connections: List[Dict],
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Start point (lower end) in world coordinates
            orientation: Rotation defining beam direction
            length: Total beam length in meters
            cross_section: (width, height) in mm
            pitch_angle: Roof pitch in degrees
            pfette_connections: List of dicts with keys:
                - position_normalized: 0-1, position along beam length
                - pfette_id: ID of connected Pfette
                - notch_depth: Depth of notch in meters (typically 0.03-0.04m)
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.pitch_angle = pitch_angle
        self.pfette_connections = pfette_connections
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        # Sparren-specific parameters
        params.update({
            'pitch_angle': self.pitch_angle,
            'num_notches': len(self.pfette_connections),
            'notch_positions': [conn['position_normalized'] 
                               for conn in self.pfette_connections],
            'notch_depths': [conn.get('notch_depth', 0.03) 
                            for conn in self.pfette_connections],
        })
        
        return params
    
    def get_mesh(self):
        """
        Generate mesh with notches at Pfette connection points.
        
        Returns:
            trimesh.Trimesh object
        """
        # Import here to avoid circular dependency
        from core.geometry_utils import (
            create_box_mesh, apply_notch, apply_transform
        )
        
        # Create base rectangular beam
        mesh = create_box_mesh(
            width=self.width_m,
            height=self.height_m,
            length=self.length
        )
        
        # Apply notches at each Pfette connection
        mesh = self._create_joint_geometry(mesh)
        
        # Transform to world coordinates
        mesh = apply_transform(mesh, self.position, self.orientation)
        
        return mesh
    
    def _create_joint_geometry(self, mesh):
        """
        Apply notches (Sparrenkerve) at Pfette connection points.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with notches
        """
        from core.geometry_utils import apply_notch
        
        for connection in self.pfette_connections:
            # Calculate notch position along beam
            pos_norm = connection['position_normalized']
            notch_depth = connection.get('notch_depth', 0.03)  # Default 30mm
            
            # Position along beam length (beam extends along Z-axis in local coords)
            z_position = (pos_norm - 0.5) * self.length
            
            # Apply notch on bottom face (-Y direction)
            mesh = apply_notch(
                mesh=mesh,
                position=np.array([0, -self.height_m/2, z_position]),
                depth=notch_depth,
                width=self.width_m * 0.9,  # Notch slightly narrower than beam
                angle=0  # Perpendicular notch
            )
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Pfettendach_Sparren':
        """Deserialize from XML"""
        beam_id = int(element.get('id'))
        
        # Parse position
        pos_text = element.find('position').text
        position = np.array([float(x) for x in pos_text.split(',')])
        
        # Parse orientation
        orient_text = element.find('orientation').text
        quat = [float(x) for x in orient_text.split(',')]
        orientation = Rotation.from_quat(quat)
        
        # Parse dimensions
        dims = element.find('dimensions')
        length = float(dims.get('length'))
        width = float(dims.get('width'))
        height = float(dims.get('height'))
        
        # Parse material
        wood_species = element.find('material').get('species')
        
        # Parse specific parameters
        params = element.find('parameters')
        pitch_angle = float(params.find("param[@name='pitch_angle']").get('value'))
        
        # Parse pfette connections (simplified - would need more detailed parsing)
        pfette_connections = []  # TODO: Parse from XML
        
        return cls(
            beam_id=beam_id,
            position=position,
            orientation=orientation,
            length=length,
            cross_section=(width, height),
            pitch_angle=pitch_angle,
            pfette_connections=pfette_connections,
            wood_species=wood_species
        )


class Sparrendach_Sparren(BaseBeam):
    """
    Sparren (rafter) for Sparrendach construction.
    
    Characteristics:
    - Directly opposes another Sparren at ridge (Firstüberblattung)
    - Forms triangle with opposing Sparren
    - May have Kehlbalken connection
    - NO Pfetten - self-supporting pair
    """
    
    beam_type = BEAM_TYPES['SPARRENDACH_SPARREN']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        pitch_angle: float,
        ridge_joint_type: str,
        opposing_sparren_id: Optional[int] = None,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Base point (eaves end) in world coordinates
            orientation: Rotation defining beam direction
            length: Total beam length in meters
            cross_section: (width, height) in mm
            pitch_angle: Roof pitch in degrees
            ridge_joint_type: Type of ridge connection (RIDGE_LAP, THROUGH_TENON)
            opposing_sparren_id: ID of the opposing Sparren at ridge
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.pitch_angle = pitch_angle
        self.ridge_joint_type = ridge_joint_type
        self.opposing_sparren_id = opposing_sparren_id
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'pitch_angle': self.pitch_angle,
            'ridge_joint_type': self.ridge_joint_type,
            'has_opposing_sparren': self.opposing_sparren_id is not None,
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with ridge joint"""
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
        Apply ridge joint (lap joint or tenon).
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with ridge joint
        """
        # Ridge joint at top end of beam
        if self.ridge_joint_type == JOINT_TYPES['RIDGE_LAP']:
            # Apply half-lap at top end
            from core.geometry_utils import apply_half_lap
            
            mesh = apply_half_lap(
                mesh=mesh,
                position=np.array([0, 0, self.length/2]),
                depth=self.height_m / 2,
                width=self.width_m
            )
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Sparrendach_Sparren':
        """Deserialize from XML"""
        # Similar to Pfettendach_Sparren.from_xml()
        # Implementation omitted for brevity
        pass


class Kehlbalkendach_Sparren(BaseBeam):
    """
    Sparren (rafter) for Kehlbalkendach construction.
    
    Characteristics:
    - Has Kehlbalken (collar beam) connection at ~1/2 height
    - May also have ridge connection to opposing Sparren
    - Connection point for horizontal Kehlbalken
    """
    
    beam_type = BEAM_TYPES['KEHLBALKENDACH_SPARREN']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        pitch_angle: float,
        kehlbalken_connection: Dict,
        ridge_joint_type: str,
        opposing_sparren_id: Optional[int] = None,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Base point in world coordinates
            orientation: Rotation defining beam direction
            length: Total beam length in meters
            cross_section: (width, height) in mm
            pitch_angle: Roof pitch in degrees
            kehlbalken_connection: Dict with:
                - position_normalized: 0-1, position along beam
                - kehlbalken_id: ID of connected Kehlbalken
                - joint_type: Type of connection (MORTISE_TENON, etc.)
            ridge_joint_type: Type of ridge connection
            opposing_sparren_id: ID of opposing Sparren
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.pitch_angle = pitch_angle
        self.kehlbalken_connection = kehlbalken_connection
        self.ridge_joint_type = ridge_joint_type
        self.opposing_sparren_id = opposing_sparren_id
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'pitch_angle': self.pitch_angle,
            'ridge_joint_type': self.ridge_joint_type,
            'kehlbalken_position': self.kehlbalken_connection['position_normalized'],
            'kehlbalken_joint_type': self.kehlbalken_connection.get('joint_type', 'MORTISE_TENON'),
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with Kehlbalken connection and ridge joint"""
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
        Apply Kehlbalken connection and ridge joint.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with joints
        """
        # TODO: Apply mortise for Kehlbalken connection
        # TODO: Apply ridge lap joint
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Kehlbalkendach_Sparren':
        """Deserialize from XML"""
        pass