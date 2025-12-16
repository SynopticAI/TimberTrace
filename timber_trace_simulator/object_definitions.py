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
    from build123d import (
        Box, Part, Location, Rotation, Align, 
        BuildPart, BuildSketch, BuildLine, Polyline, make_face, extrude, Plane
    )
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
    
    def map_global_to_local_direction(self, global_dir: int, theta_z: float) -> int:
        """
        Maps a GLOBAL direction (0-5) to a LOCAL direction (0-5) based on rotation.
        
        Global/Local Conventions (Standard Geometric):
          0: Right (+X)
          1: Left  (-X)
          2: Front (+Y)
          3: Back  (-Y)
          4: Top   (+Z)
          5: Bottom(-Z)
        """
        # Z-axis directions never change
        if global_dir >= 4:
            return global_dir
            
        # Normalize angle to 0-360 degrees
        deg = np.degrees(theta_z) % 360
        
        # 4 Separate Cases as requested
        # Case 1: ~0 degrees (Identity)
        if (deg >= 315 or deg < 45):
            return global_dir
            
        # Case 2: ~90 degrees (Global Front -> Local Right)
        # Rotated 90 deg CCW: Local X+ -> Global Y+
        elif (deg >= 45 and deg < 135):
            if global_dir == 2: return 0 # G Front -> L Right
            if global_dir == 0: return 3 # G Right -> L Back
            if global_dir == 3: return 1 # G Back  -> L Left
            if global_dir == 1: return 2 # G Left  -> L Front
            
        # Case 3: ~180 degrees (Global Front -> Local Back)
        elif (deg >= 135 and deg < 225):
            if global_dir == 2: return 3 # G Front -> L Back
            if global_dir == 3: return 2 # G Back  -> L Front
            if global_dir == 0: return 1 # G Right -> L Left
            if global_dir == 1: return 0 # G Left  -> L Right
            
        # Case 4: ~270 degrees (Global Front -> Local Left)
        elif (deg >= 225 and deg < 315):
            if global_dir == 2: return 1 # G Front -> L Left
            if global_dir == 1: return 0 # G Left  -> L Right
            if global_dir == 0: return 2 # G Right -> L Front
            if global_dir == 3: return 0 # G Back  -> L Right (Correction: L Back -> G Right at 270) -> Wait.
            # Let's verify 270 mapping:
            # L Right (+X) -> G Back (-Y). So G Back -> L Right. Correct.
            return {0: 2, 1: 0, 2: 1, 3: 0}[global_dir] # Fixed mapping dict for 270

        return global_dir # Fallback

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
    
    def get_inequality_constraints(self) -> List[Tuple[str, str]]:
        """
        Returns a list of inequality constraints strings (LHS <= RHS).
        Format: [("self.param_a", "self.param_b - 0.1"), ...]
        """
        return []

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
        local_dir = self.map_global_to_local_direction(direction, self.theta_z)
        if local_dir == 4:  # Top face
            # Single constraint: center point of top face
            constraints = [ConstraintEquation("0", "0", "self.height", slack_count=0)]
            return constraints[0] if index == 0 else constraints
        else:
            # Other faces not implemented for now
            raise NotImplementedError(f"Pfosten: Only top face (direction=4) implemented, got {local_dir}")
    
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
    Horizontal purlin. 
    Y-AXIS ALIGNED: Length is along Y, Width is along X.
    """
    
    def __init__(self, length: float = 6.0, width: float = 0.12, height: float = 0.16):
        super().__init__()
        self.length = length  # Y-direction (Global Front/Back)
        self.width = width    # X-direction (Global Right/Left)
        self.height = height  # Z-direction
    
    def get_constraints(self, direction: int, index: Optional[int] = None) -> Union[List[ConstraintEquation], ConstraintEquation]:
        """
        Constraints for Y-Aligned Pfette:
          Top (4)    -> Line along Y-axis (Length)
          Bottom (5) -> Line along Y-axis
          Right (0)  -> Line along Y-axis (Side Face at X = +width/2)
          Left (1)   -> Line along Y-axis (Side Face at X = -width/2)
          Front (2)  -> Face at Y = +length/2
          Back (3)   -> Face at Y = -length/2
        """
        local_dir = self.map_global_to_local_direction(direction, self.theta_z)
        constraints = []
        
        # --- TOP (4) & BOTTOM (5) ---
        # Line along Y-axis (slack_0 defines Y position)
        if local_dir == 4:  # Top
            constraints.append(ConstraintEquation("0", "slack_0", "self.height", slack_count=1))
        elif local_dir == 5:  # Bottom
            constraints.append(ConstraintEquation("0", "slack_0", "0", slack_count=1))
            
        # Sides (Right/Left): Plane (slack_count=2)
        # Allows contact at any Z height (fixing the infeasibility) and any Y position
        elif local_dir == 0:  # Right (+X)
            constraints.append(ConstraintEquation("self.width/2", "slack_0", "slack_1", slack_count=2))
        elif local_dir == 1:  # Left (-X)
            constraints.append(ConstraintEquation("-self.width/2", "slack_0", "slack_1", slack_count=2))
            
        # --- ENDS (FRONT 2 / BACK 3) ---
        # Vertical faces at Y ends.
        elif local_dir == 2:  # Front (+Y)
            constraints.append(ConstraintEquation("0", "self.length/2", "self.height/2", slack_count=0))
        elif local_dir == 3:  # Back (-Y)
            constraints.append(ConstraintEquation("0", "-self.length/2", "self.height/2", slack_count=0))
            
        else:
            raise NotImplementedError(f"Pfette: Face {direction} not implemented")
            
        return constraints[0] if index == 0 else constraints
    
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
            'x': (-50.0, 50.0), 'y': (-50.0, 50.0), 'z': (0.0, 20.0), 'theta_z': (0, 6.28),
            'length': (1.0, 15.0), 'width': (0.08, 0.3), 'height': (0.1, 0.4),
        }
    
    def get_model(self) -> 'Part':
        if not BUILD123D_AVAILABLE: raise ImportError("build123d required")
        # NOTE: Box dimensions swapped! X=Width, Y=Length
        box = Box(self.width, self.length, self.height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        loc = Location((self.x, self.y, self.z)) * Rotation(0, 0, np.degrees(self.theta_z))
        return box.move(loc)
    

class Sparren(BeamBase):
    def __init__(self, width=0.1, height=0.16, projected_length=3.0, steepness=1.0,
                 notch_x_mittel=1.5, notch_mittel_depth=0.05,
                 notch_x_fuss=2.8, notch_fuss_depth=0.05,
                 notch_top_length=0.08, notch_top_cut_depth=0.0):
        super().__init__()
        self.width = width
        self.height = height
        self.projected_length = projected_length
        self.steepness = steepness
        self.notch_x_mittel = notch_x_mittel
        self.notch_mittel_depth = notch_mittel_depth
        self.notch_x_fuss = notch_x_fuss
        self.notch_fuss_depth = notch_fuss_depth
        self.notch_top_length = notch_top_length
        self.notch_top_cut_depth = notch_top_cut_depth

    def get_constraints(self, direction: int, index: Optional[int] = None):
        # Map Global -> Local
        local_dir = self.map_global_to_local_direction(direction, self.theta_z)
        
        # Bottom (5)
        if local_dir == 5:
            constraints = []
            z_fuss = "-self.steepness * self.notch_x_fuss - self.height + self.notch_fuss_depth"
            constraints.append(ConstraintEquation("slack_0", "0", z_fuss, slack_count=1))
            
            z_mittel = "-self.steepness * self.notch_x_mittel - self.height + self.notch_mittel_depth"
            constraints.append(ConstraintEquation("slack_0", "0", z_mittel, slack_count=1))
            
            z_top = "-self.height + self.notch_top_cut_depth"
            constraints.append(ConstraintEquation("slack_0", "0", z_top, slack_count=1))
            return constraints[index] if index is not None else constraints

        # Left (1) - Vertical Notch Faces (-X direction)
        elif local_dir == 1:
            constraints = []
            # Vertical planes at X = notch_x
            constraints.append(ConstraintEquation("self.notch_x_fuss", "slack_0", "slack_1", slack_count=2))
            constraints.append(ConstraintEquation("self.notch_x_mittel", "slack_0", "slack_1", slack_count=2))
            constraints.append(ConstraintEquation("self.notch_top_length", "slack_0", "slack_1", slack_count=2))
            constraints.append(ConstraintEquation("0", "slack_0", "slack_1", slack_count=2))
            return constraints[index] if index is not None else constraints
            
        else:
            raise NotImplementedError(f"Sparren: Face {local_dir} not implemented")

    def get_inequality_constraints(self) -> List[Tuple[str, str]]:
        constraints = []
        constraints.append(("self.notch_mittel_depth", "0.7 * self.height"))
        constraints.append(("self.notch_fuss_depth", "0.7 * self.height"))
        
        buffer = "0.1"
        x_back_mittel = f"self.notch_x_mittel - (self.notch_mittel_depth / {self.steepness})"
        x_back_fuss = f"self.notch_x_fuss - (self.notch_fuss_depth / {self.steepness})"
        
        constraints.append(("self.notch_top_length + " + buffer, x_back_mittel))
        constraints.append(("self.notch_x_mittel + " + buffer, x_back_fuss))
        constraints.append(("self.notch_x_fuss + " + buffer, "self.projected_length"))
        return constraints

    def get_parameters(self) -> Dict:
        return {
            'values': {'theta_z': self.theta_z, 'x': self.x, 'y': self.y, 'z': self.z,
                       'width': self.width, 'height': self.height, 'projected_length': self.projected_length,
                       'steepness': self.steepness, 'notch_x_mittel': self.notch_x_mittel,
                       'notch_mittel_depth': self.notch_mittel_depth, 'notch_x_fuss': self.notch_x_fuss,
                       'notch_fuss_depth': self.notch_fuss_depth, 'notch_top_length': self.notch_top_length,
                       'notch_top_cut_depth': self.notch_top_cut_depth},
            'metadata': {},
            'morphology_keys': ['width', 'height', 'projected_length',
                'notch_x_mittel', 'notch_mittel_depth', 'notch_x_fuss', 'notch_fuss_depth',
                'notch_top_length', 'notch_top_cut_depth'],
            'pose_keys': ['theta_z', 'x', 'y', 'z']
        }
    
    def get_parameter_bounds(self) -> Dict:
        return {'x': (-50, 50), 'y': (-50, 50), 'z': (0, 20), 'theta_z': (0, 6.28),
                'width': (0.05, 0.2), 'height': (0.1, 0.3), 'projected_length': (1, 10),
                'steepness': (0.5, 2.0), 'notch_x_mittel': (0.5, 9), 'notch_x_fuss': (0.5, 9),
                'notch_top_length': (0.05, 0.5)}

    def get_model(self) -> 'Part':
        if not BUILD123D_AVAILABLE: raise ImportError
        L, m, H = float(self.projected_length), float(self.steepness), float(self.height)
        def bottom_z(x): return -m * x - H
        def top_z(x): return -m * x
        def bottom_x_from_z(z): return (-H - z) / m

        pts = [(0.0, 0.0), (L, top_z(L)), (L, bottom_z(L))]
        
        z_fuss = bottom_z(self.notch_x_fuss)
        pts.extend([(float(self.notch_x_fuss), z_fuss),
                    (float(self.notch_x_fuss), z_fuss + self.notch_fuss_depth),
                    (bottom_x_from_z(z_fuss + self.notch_fuss_depth), z_fuss + self.notch_fuss_depth)])
        
        z_mittel = bottom_z(self.notch_x_mittel)
        pts.extend([(float(self.notch_x_mittel), z_mittel),
                    (float(self.notch_x_mittel), z_mittel + self.notch_mittel_depth),
                    (bottom_x_from_z(z_mittel + self.notch_mittel_depth), z_mittel + self.notch_mittel_depth)])
        
        z_top_base = bottom_z(self.notch_top_length)
        z_top_shelf = -H + self.notch_top_cut_depth
        pts.extend([(float(self.notch_top_length), z_top_base),
                    (float(self.notch_top_length), z_top_shelf),
                    (0.0, z_top_shelf), (0.0, 0.0)])
        
        with BuildPart() as p:
            with BuildSketch(Plane.XZ):
                with BuildLine(): Polyline(pts)
                make_face()
            extrude(amount=self.width, both=True)
        return p.part.move(Location((self.x, self.y, self.z)) * Rotation(0, 0, np.degrees(self.theta_z)))

# Type registry for easy lookup
BEAM_TYPES = {
    0: Pfosten, 
    1: Pfette, 
    2: Sparren
}

BEAM_NAMES = {
    0: "Pfosten", 
    1: "Pfette", 
    2: "Sparren"
}