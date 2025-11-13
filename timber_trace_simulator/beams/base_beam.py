"""
Base Beam Class for Timber Trace Simulator

Abstract base class that all concrete beam types inherit from.
Defines the common interface and shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, List
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET


class BaseBeam(ABC):
    """
    Abstract base class for all timber beam types.
    
    All concrete beam classes must inherit from this and implement:
    - get_parameters()
    - get_mesh()
    - _create_joint_geometry()
    """
    
    # Class variable to be overridden by subclasses
    beam_type: str = "BaseBeam"
    
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
            position: 3D position [x, y, z] in meters (beam center or start point)
            orientation: Rotation object defining beam orientation
            length: Beam length in meters
            cross_section: (width, height) in millimeters
            wood_species: Wood type (SPRUCE, OAK, FIR, PINE)
        """
        self.beam_id = beam_id
        self.position = np.array(position, dtype=float)
        self.orientation = orientation
        self.length = length
        self.cross_section = cross_section  # (width, height) in mm
        self.wood_species = wood_species
        
        # Derived properties
        self.width_m = cross_section[0] / 1000.0  # Convert mm to meters
        self.height_m = cross_section[1] / 1000.0
        
        # Will be set by generator
        self.connected_beam_ids: List[int] = []
        
    @property
    def width(self) -> float:
        """Width in millimeters"""
        return self.cross_section[0]
    
    @property
    def height(self) -> float:
        """Height in millimeters"""
        return self.cross_section[1]
    
    @abstractmethod
    def get_parameters(self) -> Dict:
        """
        Return parameter dictionary for ML Stage 2.
        
        Each beam type defines its own parameter schema.
        Must include at minimum: length, width, height
        
        Returns:
            Dictionary with all beam-specific parameters
        """
        pass
    
    @abstractmethod
    def get_mesh(self):
        """
        Generate 3D mesh representation of this beam.
        
        Returns:
            trimesh.Trimesh object with beam geometry including joints
        """
        pass
    
    @abstractmethod
    def _create_joint_geometry(self):
        """
        Create joint-specific geometry modifications.
        Called internally by get_mesh().
        
        Each beam type implements its own joint logic.
        """
        pass
    
    def get_base_parameters(self) -> Dict:
        """
        Return parameters common to all beam types.
        Subclasses should call this and extend with specific parameters.
        """
        return {
            'beam_id': self.beam_id,
            'beam_type': self.beam_type,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'position': self.position.tolist(),
            'orientation_quaternion': [
                self.orientation.as_quat()[0],
                self.orientation.as_quat()[1],
                self.orientation.as_quat()[2],
                self.orientation.as_quat()[3]
            ],
            'wood_species': self.wood_species,
        }
    
    def transform_point(self, point: np.ndarray) -> np.ndarray:
        """
        Transform a point from beam local coordinates to world coordinates.
        
        Args:
            point: Point in beam-local coordinates (origin at beam center)
            
        Returns:
            Point in world coordinates
        """
        return self.orientation.apply(point) + self.position
    
    def get_bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate axis-aligned bounding box.
        
        Returns:
            (min_corner, max_corner) in world coordinates
        """
        # Beam corners in local coordinates
        hw, hh, hl = self.width_m/2, self.height_m/2, self.length/2
        corners_local = np.array([
            [-hw, -hh, -hl], [hw, -hh, -hl],
            [-hw, hh, -hl],  [hw, hh, -hl],
            [-hw, -hh, hl],  [hw, -hh, hl],
            [-hw, hh, hl],   [hw, hh, hl],
        ])
        
        # Transform to world coordinates
        corners_world = np.array([self.transform_point(c) for c in corners_local])
        
        min_corner = corners_world.min(axis=0)
        max_corner = corners_world.max(axis=0)
        
        return min_corner, max_corner
    
    def get_endpoints(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get the two endpoints of the beam in world coordinates.
        Assumes beam extends along local Z-axis.
        
        Returns:
            (start_point, end_point) in world coordinates
        """
        half_length = self.length / 2
        start_local = np.array([0, 0, -half_length])
        end_local = np.array([0, 0, half_length])
        
        start_world = self.transform_point(start_local)
        end_world = self.transform_point(end_local)
        
        return start_world, end_world
    
    def to_xml(self) -> ET.Element:
        """
        Serialize beam to XML element.
        
        Returns:
            XML Element representing this beam
        """
        beam_elem = ET.Element('beam')
        beam_elem.set('id', str(self.beam_id))
        beam_elem.set('type', self.beam_type)
        
        # Position
        pos_elem = ET.SubElement(beam_elem, 'position')
        pos_elem.text = ','.join(map(str, self.position))
        
        # Orientation (as quaternion)
        quat = self.orientation.as_quat()
        orient_elem = ET.SubElement(beam_elem, 'orientation')
        orient_elem.set('format', 'quaternion')
        orient_elem.text = ','.join(map(str, quat))
        
        # Dimensions
        dims_elem = ET.SubElement(beam_elem, 'dimensions')
        dims_elem.set('length', str(self.length))
        dims_elem.set('width', str(self.width))
        dims_elem.set('height', str(self.height))
        
        # Material
        material_elem = ET.SubElement(beam_elem, 'material')
        material_elem.set('species', self.wood_species)
        
        # Parameters (beam-type specific)
        params = self.get_parameters()
        params_elem = ET.SubElement(beam_elem, 'parameters')
        for key, value in params.items():
            if key not in ['beam_id', 'beam_type', 'length', 'width', 'height', 
                          'position', 'orientation_quaternion', 'wood_species']:
                param_elem = ET.SubElement(params_elem, 'param')
                param_elem.set('name', key)
                param_elem.set('value', str(value))
        
        return beam_elem
    
    @classmethod
    def from_xml(cls, element: ET.Element) -> 'BaseBeam':
        """
        Deserialize beam from XML element.
        Must be implemented by concrete beam classes to instantiate correct type.
        
        Args:
            element: XML Element containing beam data
            
        Returns:
            Instantiated beam of correct type
        """
        raise NotImplementedError("Subclasses must implement from_xml()")
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (f"{self.beam_type}(id={self.beam_id}, "
                f"length={self.length:.2f}m, "
                f"cross_section={self.width}x{self.height}mm, "
                f"pos={self.position})")
    
    def __str__(self) -> str:
        """Human-readable string"""
        return f"{self.beam_type} #{self.beam_id}"