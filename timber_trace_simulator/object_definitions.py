# object_definitions.py
"""
Beam type definitions with constraint-based interfaces.
SI UNITS ONLY (Meters).

DUAL-MODE GEOMETRY: All geometry methods work with both:
  1. Numerical values (float) -> for build123d CAD generation
  2. CVXPY variables -> for constraint solver

This ensures SINGLE SOURCE OF TRUTH for geometry.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass

try:
    from build123d import Box, Part, Location, Rotation, Align
    BUILD123D_AVAILABLE = True
except ImportError:
    BUILD123D_AVAILABLE = False
    print("⚠️  build123d not available - get_model() will fail")


@dataclass
class ConstraintEquation:
    """
    Represents a 3D constraint as three linear expressions.
    Formulated in LOCAL coordinates (Meters), transformed to global during solving.
    
    Expressions are STRING templates that will be evaluated with either:
      - Numerical values (self.x, self.height, etc.)
      - CVXPY variables (cvxpy_vars['x'], cvxpy_vars['height'], etc.)
    """
    x_expr: str  # e.g., "slack_1" or "0" or "self.width/2"
    y_expr: str  
    z_expr: str
    slack_count: int  # 0=point, 1=line, 2=plane


class BeamBase:
    """Base class enforcing interface from Object_Centered_Framework_spec.md"""
    
    def __init__(self):
        # Index 0: Rotation (constant during solving)
        self.theta_z = 0.0  # radians
        
        # Indices 1-3: Position (variables during solving) - METERS
        self.x = 0.0  # m
        self.y = 0.0  # m
        self.z = 0.0  # m
        
        # Indices 4+: Morphology (variables) - METERS
        # Defined by subclasses
    
    def _rotation_matrix(self, theta_z_val: float) -> np.ndarray:
        """
        Returns 3D rotation matrix for Z-axis rotation.
        ALWAYS takes numerical value (not CVXPY variable).
        """
        c = np.cos(theta_z_val)
        s = np.sin(theta_z_val)
        return np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])
    
    def get_constraints(self, direction: int, index: Optional[int] = None) -> Union[List[ConstraintEquation], ConstraintEquation]:
        """
        Returns constraint equations for specified face.
        
        Args:
            direction: Face direction
                       0 = Right, 1 = Left
                       2 = Front, 3 = Back  
                       4 = Top,   5 = Bottom
            index: If None, return all constraints for this face.
                   If int, return only constraint at that index.
        """
        raise NotImplementedError
    
    def get_parameters(self) -> Dict:
        """Returns current parameters + metadata"""
        raise NotImplementedError
    
    def set_parameters(self, params: Dict[str, float]):
        """Update beam parameters"""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Returns min/max bounds for each parameter"""
        raise NotImplementedError
    
    def get_model(self) -> 'Part':
        """Generate 3D solid model from current parameters"""
        raise NotImplementedError


class Pfosten(BeamBase):
    """
    Vertical post (Mittelpfosten/Seitenpfosten).
    Default: 0.1m x 0.1m x 2.2m
    
    SIMPLIFIED: Only top face constraint implemented (center point).
    """
    
    def __init__(self, width: float = 0.1, depth: float = 0.1, height: float = 2.2):
        super().__init__()
        self.width = width    # m (X-direction in local coords)
        self.depth = depth    # m (Y-direction in local coords)
        self.height = height  # m (Z-direction)
    
    def _top_center_point(self, x=None, y=None, z=None, height=None):
        """
        DUAL-MODE: Returns top center point in GLOBAL coordinates.
        
        Works with both numerical values and CVXPY variables.
        This is the SINGLE SOURCE OF TRUTH for top face geometry.
        
        Args:
            x, y, z, height: Can be float OR cvxpy.Variable OR None (use self.*)
        
        Returns:
            np.ndarray or cvxpy expression: [x_global, y_global, z_global]
        """
        # Use current values if not provided
        x_val = x if x is not None else self.x
        y_val = y if y is not None else self.y
        z_val = z if z is not None else self.z
        height_val = height if height is not None else self.height
        
        # Local coordinates: center of top face
        p_local = np.array([0.0, 0.0, height_val])
        
        # Rotate using CURRENT theta_z (always numerical, not optimized)
        R = self._rotation_matrix(self.theta_z)
        
        # Matrix-vector multiply works with both numbers and CVXPY vars
        p_rotated = R @ p_local
        
        # Translate to global position
        p_global = np.array([x_val, y_val, z_val]) + p_rotated
        
        return p_global
    
    def get_constraints(self, direction: int, index: Optional[int] = None) -> Union[List[ConstraintEquation], ConstraintEquation]:
        """
        SIMPLIFIED: Only top face (direction=4) implemented.
        Returns single constraint equation (center point, no slacks).
        """
        if direction == 4:  # Top face
            # Single constraint: center point of top face
            constraints = [ConstraintEquation("0", "0", "self.height", slack_count=0)]
            return constraints[0] if index == 0 else constraints
        else:
            # Other faces not implemented for now
            raise NotImplementedError(f"Pfosten: Only top face (direction=4) implemented, got {direction}")
    
    def get_parameters(self) -> Dict:
        return {
            'values': {
                'theta_z': self.theta_z,
                'x': self.x, 'y': self.y, 'z': self.z,
                'width': self.width, 'depth': self.depth, 'height': self.height,
            },
            'metadata': {
                'theta_z': {'default': 0.0, 'ai_scale': 1.0},
                'x': {'default': 0.0, 'ai_scale': 1.0},
                'y': {'default': 0.0, 'ai_scale': 1.0},
                'z': {'default': 0.0, 'ai_scale': 1.0},
                'width': {'default': 0.1, 'ai_scale': 1.0},
                'depth': {'default': 0.1, 'ai_scale': 1.0},
                'height': {'default': 2.2, 'ai_scale': 1.0},
            },
            'morphology_keys': ['width', 'depth', 'height'],
            'pose_keys': ['theta_z', 'x', 'y', 'z']
        }
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'x': (-50.0, 50.0),      # m
            'y': (-50.0, 50.0),      # m
            'z': (0.0, 20.0),        # m
            'theta_z': (0, 2*np.pi),
            'width': (0.05, 0.3),    # 5cm to 30cm
            'depth': (0.05, 0.3),
            'height': (1.0, 5.0),    # 1m to 5m
        }
    
    def get_model(self) -> 'Part':
        """Generate build123d model using SAME geometry logic"""
        if not BUILD123D_AVAILABLE: 
            raise ImportError("build123d required")
        
        # Create box centered at origin
        box = Box(self.width, self.depth, self.height, 
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # Apply rotation and translation - SAME as constraint equations
        loc = Location((self.x, self.y, self.z)) * Rotation(0, 0, np.degrees(self.theta_z))
        
        return box.move(loc)


class Pfette(BeamBase):
    """
    Horizontal purlin. Default: 6.0m x 0.12m x 0.16m
    
    SIMPLIFIED: Only bottom face constraint implemented (line along length).
    """
    
    def __init__(self, length: float = 6.0, width: float = 0.12, height: float = 0.16):
        super().__init__()
        self.length = length  # m (X-direction in local coords when theta_z=0)
        self.width = width    # m (Y-direction)
        self.height = height  # m (Z-direction)
    
    def _bottom_line(self, x=None, y=None, z=None, slack_u=None):
        """
        DUAL-MODE: Returns bottom centerline in GLOBAL coordinates.
        
        Line runs along the beam's length (local X), centered in width (Y=0).
        Uses one slack variable to span the line.
        
        Args:
            x, y, z: Position (float or CVXPY variable)
            slack_u: CVXPY variable for line parameter
        
        Returns:
            np.ndarray or cvxpy expression: [x_global, y_global, z_global]
        """
        # Use current values if not provided
        x_val = x if x is not None else self.x
        y_val = y if y is not None else self.y
        z_val = z if z is not None else self.z
        
        # Local coordinates: line along length, centered in width, at bottom
        # slack_u varies along the beam's length
        if slack_u is not None:
            p_local = np.array([slack_u, 0.0, 0.0])
        else:
            # Default: center of line
            p_local = np.array([0.0, 0.0, 0.0])
        
        # Rotate
        R = self._rotation_matrix(self.theta_z)
        p_rotated = R @ p_local
        
        # Translate
        p_global = np.array([x_val, y_val, z_val]) + p_rotated
        
        return p_global
    
    def get_constraints(self, direction: int, index: Optional[int] = None) -> Union[List[ConstraintEquation], ConstraintEquation]:
        """
        SIMPLIFIED: Only bottom face (direction=5) implemented.
        Returns single constraint equation (line along length, 1 slack).
        """
        if direction == 5:  # Bottom face
            # Single constraint: line along length
            # slack_0 varies from -length/2 to +length/2 in local X
            # Note: Each constraint equation uses local indices (slack_0, slack_1, ...)
            # The solver will map these to unique global slack variables
            constraints = [ConstraintEquation("slack_0", "0", "0", slack_count=1)]
            return constraints[0] if index == 0 else constraints
        else:
            raise NotImplementedError(f"Pfette: Only bottom face (direction=5) implemented, got {direction}")
    
    def get_parameters(self) -> Dict:
        return {
            'values': {
                'theta_z': self.theta_z,
                'x': self.x, 'y': self.y, 'z': self.z,
                'length': self.length, 'width': self.width, 'height': self.height,
            },
            'metadata': {
                'theta_z': {'default': 0.0, 'ai_scale': 1.0},
                'x': {'default': 0.0, 'ai_scale': 1.0},
                'y': {'default': 0.0, 'ai_scale': 1.0},
                'z': {'default': 0.0, 'ai_scale': 1.0},
                'length': {'default': 6.0, 'ai_scale': 1.0},
                'width': {'default': 0.12, 'ai_scale': 1.0},
                'height': {'default': 0.16, 'ai_scale': 1.0},
            },
            'morphology_keys': ['length', 'width', 'height'],
            'pose_keys': ['theta_z', 'x', 'y', 'z']
        }
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'x': (-50.0, 50.0),
            'y': (-50.0, 50.0),
            'z': (0.0, 20.0),
            'theta_z': (0, 2*np.pi),
            'length': (1.0, 15.0),
            'width': (0.08, 0.3),
            'height': (0.1, 0.4),
        }
    
    def get_model(self) -> 'Part':
        """Generate build123d model using SAME geometry logic"""
        if not BUILD123D_AVAILABLE:
            raise ImportError("build123d required")
        
        # Create box centered at origin
        box = Box(self.length, self.width, self.height,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # Apply rotation and translation
        loc = Location((self.x, self.y, self.z)) * Rotation(0, 0, np.degrees(self.theta_z))
        
        return box.move(loc)


# Type registry for easy lookup
BEAM_TYPES = {0: Pfosten, 1: Pfette}
BEAM_NAMES = {0: "Pfosten", 1: "Pfette"}