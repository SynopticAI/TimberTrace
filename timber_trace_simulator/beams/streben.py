"""
Streben (Diagonal Brace) Beam Class

Diagonal bracing elements that provide lateral stability to the roof structure.
"""

from typing import Dict, Tuple
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET

from .base_beam import BaseBeam
from config import BEAM_TYPES, JOINT_TYPES


class Strebe(BaseBeam):
    """
    Strebe (diagonal brace) - angled beam for structural bracing.
    
    Characteristics:
    - Connects at an angle (typically 30-60 degrees)
    - Provides lateral stability against wind and other lateral loads
    - Usually connects Stuhlpfosten to Pfette or floor beam
    - May use mortise-tenon or notched connections at both ends
    """
    
    beam_type = BEAM_TYPES['STREBE']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        angle: float,
        start_connection: Dict,
        end_connection: Dict,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Start point in world coordinates
            orientation: Rotation defining beam direction
            length: Total beam length in meters
            cross_section: (width, height) in mm
            angle: Angle from horizontal in degrees (typically 30-60°)
            start_connection: Dict with:
                - connected_beam_id: ID of beam at start
                - joint_type: Connection type
            end_connection: Dict with:
                - connected_beam_id: ID of beam at end
                - joint_type: Connection type
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.angle = angle
        self.start_connection = start_connection
        self.end_connection = end_connection
        
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'brace_angle': self.angle,
            'start_joint_type': self.start_connection['joint_type'],
            'end_joint_type': self.end_connection['joint_type'],
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with angled end cuts"""
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
        Apply angled cuts or joints at both ends.
        
        Streben typically have angled cuts at the ends to fit
        against the connected beams (Stuhlpfosten, Pfetten, etc.)
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with end joints
        """
        # For now, return base mesh
        # Could add angled cuts at ends based on connection angles
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Strebe':
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
        angle = float(params.find("param[@name='brace_angle']").get('value'))
        
        # Simplified connections
        start_connection = {'joint_type': JOINT_TYPES['MORTISE_TENON']}
        end_connection = {'joint_type': JOINT_TYPES['MORTISE_TENON']}
        
        return cls(
            beam_id=beam_id,
            position=position,
            orientation=orientation,
            length=length,
            cross_section=(width, height),
            angle=angle,
            start_connection=start_connection,
            end_connection=end_connection,
            wood_species=wood_species
        )