"""
Stuhlpfosten (Support Post) Beam Class

Vertical support posts that carry the Pfetten in Pfettendach construction.
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET

from .base_beam import BaseBeam
from config import BEAM_TYPES, JOINT_TYPES


class Stuhlpfosten(BaseBeam):
    """
    Stuhlpfosten (support post) - vertical beam supporting Pfetten.
    
    Characteristics:
    - Vertical orientation (connects floor/ceiling beam to Pfette)
    - Has tenon at top that inserts into Pfette mortise
    - May have mortise at bottom for floor beam connection
    - Typically square cross-section
    - May be braced by Streben (diagonal braces)
    """
    
    beam_type = BEAM_TYPES['STUHLPFOSTEN']
    
    def __init__(
        self,
        beam_id: int,
        position: np.ndarray,
        orientation: Rotation,
        length: float,
        cross_section: Tuple[float, float],
        top_connection: Dict,
        bottom_connection: Dict,
        brace_connections: List[Dict] = None,
        wood_species: str = "SPRUCE"
    ):
        """
        Args:
            beam_id: Unique identifier
            position: Base point (bottom) in world coordinates
            orientation: Rotation (typically vertical, minimal rotation)
            length: Height of post in meters
            cross_section: (width, height) in mm - often square e.g., (120, 120)
            top_connection: Dict with:
                - pfette_id: ID of Pfette above
                - joint_type: Usually MORTISE_TENON
                - tenon_height: Height of tenon at top (meters)
            bottom_connection: Dict with:
                - base_type: "floor_beam" or "wall" or "ceiling_joist"
                - joint_type: Connection type
            brace_connections: Optional list of Streben connections
            wood_species: Wood type
        """
        super().__init__(beam_id, position, orientation, length, cross_section, wood_species)
        
        self.top_connection = top_connection
        self.bottom_connection = bottom_connection
        self.brace_connections = brace_connections or []
        
        # Verify approximately square cross-section
        if abs(cross_section[0] - cross_section[1]) > 20:
            print(f"Warning: Stuhlpfosten typically has square cross-section, "
                  f"got {cross_section}")
    
    def get_parameters(self) -> Dict:
        """Return parameters for ML Stage 2"""
        params = self.get_base_parameters()
        
        params.update({
            'post_height': self.length,
            'top_joint_type': self.top_connection['joint_type'],
            'bottom_joint_type': self.bottom_connection['joint_type'],
            'tenon_height': self.top_connection.get('tenon_height', 0.10),
            'num_braces': len(self.brace_connections),
            'is_square_section': abs(self.width - self.height) < 5,  # Within 5mm
        })
        
        return params
    
    def get_mesh(self):
        """Generate mesh with tenon at top and base connection"""
        from core.geometry_utils import (
            create_box_mesh, apply_transform
        )
        
        # Create box mesh NOT centered, so its base is at (0,0,0) local
        mesh = create_box_mesh(
            width=self.width_m,
            height=self.height_m,
            length=self.length,
            center=False # <-- THIS IS THE FIX
        )
        
        mesh = self._create_joint_geometry(mesh)
        # The position arg is the base, so this transform is now correct
        mesh = apply_transform(mesh, self.position, self.orientation)
        
        return mesh
    
    def _create_joint_geometry(self, mesh):
        """
        Apply tenon at top for Pfette connection.
        
        The tenon protrudes from the top of the post and inserts
        into a mortise in the Pfette above.
        
        Args:
            mesh: Base beam mesh
            
        Returns:
            Modified mesh with tenon
        """
        from core.geometry_utils import apply_tenon
        
        # Top tenon
        tenon_height = self.top_connection.get('tenon_height', 0.10)  # Default 100mm
        
        # Tenon dimensions (typically 1/3 of post width)
        tenon_width = self.width_m * 0.33
        tenon_depth = self.height_m * 0.33
        
        # Position at top of post
        # Since center=False, beam runs from z=0 to z=length
        top_position = np.array([0, 0, self.length]) # <--- FIX: Was self.length/2
        
        mesh = apply_tenon(
            mesh=mesh,
            position=top_position,
            width=tenon_width,
            height=tenon_depth,
            length=tenon_height
        )
        
        # Bottom connection (if needed)
        # For now, keep simple - could add mortise or other joint
        
        return mesh

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Stuhlpfosten':
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
        
        # Parse connections (simplified)
        top_connection = {'joint_type': JOINT_TYPES['MORTISE_TENON']}
        bottom_connection = {'base_type': 'floor_beam', 'joint_type': JOINT_TYPES['BEARING']}
        
        return cls(
            beam_id=beam_id,
            position=position,
            orientation=orientation,
            length=length,
            cross_section=(width, height),
            top_connection=top_connection,
            bottom_connection=bottom_connection,
            wood_species=wood_species
        )