"""
Kehlbalken (Collar Beam) Beam Class

Horizontal beams connecting opposing Sparren in Kehlbalkendach construction.
"""

from typing import Dict, Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET

from .base_beam import BaseBeam
from config import BEAM_TYPES, JOINT_TYPES


class Kehlbalken(BaseBeam):
    """
    Kehlbalken (collar beam) - horizontal tie connecting opposing rafters.
    
    Characteristics:
    - Runs horizontally between two opposing Sparren
    - Positioned at approximately 1/2 to 2/3 height up the Sparren
    - Prevents Sparren from spreading apart
    - Connected via mortise-tenon or lap joints to Sparren
    - Creates usable attic space below
    """
    
    beam_type = BEAM_TYPES['KEHLBALKEN']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        height_ratio: float,
        left_sparren_connection: Dict,
        right_sparren_connection: Dict,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Center point in world coordinates
            orientation: Rotation (typically horizontal)
            length: Total beam length in meters (span between Sparren)
            cross_section: (width, height) in mm
            height_ratio: Position ratio up the Sparren (0.0-1.0, typically 0.4-0.6)
            left_sparren_connection: Dict with:
                - sparren_id: ID of left Sparren
                - joint_type: Connection type (MORTISE_TENON typical)
            right_sparren_connection: Dict with:
                - sparren_id: ID of right Sparren
                - joint_type: Connection type
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.height_ratio = height_ratio
        self.left_sparren_connection = left_sparren_connection
        self.right_sparren_connection = right_sparren_connection
        
        # Validate height ratio
        if not 0.3 <= height_ratio <= 0.7:
            print(f"Warning: Kehlbalken height_ratio {height_ratio} outside typical range (0.3-0.7)")
    
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'height_ratio': self.height_ratio,
            'span': self.length,
            'left_joint_type': self.left_sparren_connection['joint_type'],
            'right_joint_type': self.right_sparren_connection['joint_type'],
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with end connections for Sparren"""
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
        Apply joints at both ends for Sparren connections.
        
        Typically tenons at each end that insert into mortises in the Sparren,
        or lap joints.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with end joints
        """
        from core.geometry_utils import apply_tenon
        
        # Left end tenon
        if self.left_sparren_connection['joint_type'] == JOINT_TYPES['MORTISE_TENON']:
            left_position = np.array([0, 0, -self.length/2])
            
            mesh = apply_tenon(
                mesh=mesh,
                position=left_position,
                width=self.width_m * 0.33,
                height=self.height_m * 0.33,
                length=0.08  # 80mm tenon length
            )
        
        # Right end tenon
        if self.right_sparren_connection['joint_type'] == JOINT_TYPES['MORTISE_TENON']:
            right_position = np.array([0, 0, self.length/2])
            
            mesh = apply_tenon(
                mesh=mesh,
                position=right_position,
                width=self.width_m * 0.33,
                height=self.height_m * 0.33,
                length=0.08
            )
        
        return mesh
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Kehlbalken':
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
        height_ratio = float(params.find("param[@name='height_ratio']").get('value'))
        
        # Simplified connections
        left_connection = {'joint_type': JOINT_TYPES['MORTISE_TENON']}
        right_connection = {'joint_type': JOINT_TYPES['MORTISE_TENON']}
        
        return cls(
            beam_id=beam_id,
            position=position,
            orientation=orientation,
            length=length,
            cross_section=(width, height),
            height_ratio=height_ratio,
            left_sparren_connection=left_connection,
            right_sparren_connection=right_connection,
            wood_species=wood_species
        )