"""
Pfettendach Rechteck Generator
(Rectangular Purlin Roof Generator)

Generates a simple rectangular Pfettendach based on input parameters.
"""

import numpy as np
from scipy.spatial.transform import Rotation
from typing import List, Dict, Any, Tuple

from .base_generator import BaseRoofGenerator
from beams import (
    BaseBeam,
    Firstpfette,
    Mittelpfette,
    Fußpfette,
    Stuhlpfosten,
    Pfettendach_Sparren,
    Strebe
)
from config import STANDARD_CROSS_SECTIONS, VALIDATION_RANGES

class PfettendachRechteckGenerator(BaseRoofGenerator):
    """
    Generates a simple rectangular Pfettendach (purlin roof).
    
    Coordinate System:
    - World X: Building span (width)
    - World Y: Building length (longitudinal)
    - World Z: Building height (vertical)
    - Origin (0,0,0): Center of the building footprint at floor level.
    """

    def validate_parameters(self, roof_params: Dict[str, Any]) -> bool:
        """Validate required parameters for a rectangular Pfettendach."""
        required_keys = [
            'building_length', 'building_width', 'roof_pitch_deg',
            'sparren_spacing', 'pfetten_count', 'support_spacing'
        ]
        
        for key in required_keys:
            if key not in roof_params:
                print(f"Error: Missing required parameter '{key}'")
                return False
        
        count = roof_params['pfetten_count']
        if count not in [3, 5, 7]:
            print(f"Error: 'pfetten_count' must be 3, 5, or 7, got {count}")
            return False
            
        pitch = roof_params['roof_pitch_deg']
        if not (VALIDATION_RANGES['roof_pitch'][0] <= pitch <= VALIDATION_RANGES['roof_pitch'][1]):
            print(f"Warning: Roof pitch {pitch}° is outside typical range.")
            
        return True

    def generate(self) -> List[BaseBeam]:
        """Generate all beams for the Pfettendach."""
        print("Starting PfettendachRechteckGenerator...")
        
        # Clear any previous generation
        self.beams = []
        self.beam_store = {}
        self.beam_id_counter = 0
        
        # Run generation steps in logical order
        self._calculate_derived_geometry()
        self._generate_pfetten()
        self._generate_stuhlpfosten()
        self._generate_sparren()
        self._generate_streben() # Optional
        
        print(f"✓ Generation complete. Created {len(self.beams)} beams.")
        return self.beams

    def _calculate_derived_geometry(self):
        """Calculate key geometric points based on roof parameters."""
        self.building_length = self.roof_params['building_length']
        self.building_width = self.roof_params['building_width']
        self.roof_pitch_deg = self.roof_params['roof_pitch_deg']
        self.roof_pitch_rad = np.deg2rad(self.roof_pitch_deg)
        self.pfetten_count = self.roof_params['pfetten_count']
        self.sparren_spacing = self.roof_params['sparren_spacing']
        self.support_spacing = self.roof_params['support_spacing']

        # Core dimensions
        self.half_width = self.building_width / 2.0
        self.ridge_height = self.half_width * np.tan(self.roof_pitch_rad)
        self.sparren_hypotenuse = self.half_width / np.cos(self.roof_pitch_rad)

        # Mittelpfette positions (if they exist)
        if self.pfetten_count >= 5:
            # Positioned halfway up the span
            self.mittel_x = self.half_width / 2.0
            self.mittel_y = self.mittel_x * np.tan(self.roof_pitch_rad)
        
        # Calculate support and sparren longitudinal positions (Y-axis)
        num_supports = int(self.building_length / self.support_spacing)
        self.support_y_coords = np.linspace(-self.building_length/2, self.building_length/2, num_supports + 1)
        
        num_sparren_pairs = int(self.building_length / self.sparren_spacing)
        self.sparren_y_coords = np.linspace(-self.building_length/2, self.building_length/2, num_sparren_pairs + 1)
        
        print(f"  - Derived geometry: Ridge height={self.ridge_height:.2f}m, Sparren length={self.sparren_hypotenuse:.2f}m")

    def _generate_pfetten(self):
        """Create the main horizontal purlins (First-, Mittel-, Fuß-)."""
        print("  - Generating Pfetten...")
        
        # Pfetten run along the Y-axis, so their local Z-axis (length)
        # is rotated 90 degrees around the X-axis.
        pfette_orientation = Rotation.from_euler('x', 90, degrees=True)
        
        # 1. Firstpfette (Ridge Purlin)
        fp_id = self._get_next_id()
        fp = Firstpfette(
            beam_id=fp_id,
            position=np.array([0, 0, self.ridge_height]), # Center of beam at (0, 0, ridge_height)
            orientation=pfette_orientation,
            length=self.building_length,
            cross_section=STANDARD_CROSS_SECTIONS['PFETTE'][2], # (100, 240)
            stuhlpfosten_connections=[], # Will be populated by Stuhlpfosten
            sparren_support_spacing=self.sparren_spacing
        )
        self.beams.append(fp)
        self.beam_store['Firstpfette'] = fp

        # 2. Fußpfetten (Eaves Purlins)
        fl_id = self._get_next_id()
        fr_id = self._get_next_id()
        fl = Fußpfette(
            beam_id=fl_id,
            position=np.array([-self.half_width, 0, 0]),
            orientation=pfette_orientation,
            length=self.building_length,
            cross_section=STANDARD_CROSS_SECTIONS['PFETTE'][0], # (80, 200)
            wall_support=True,
            sparren_support_spacing=self.sparren_spacing
        )
        fr = Fußpfette(
            beam_id=fr_id,
            position=np.array([self.half_width, 0, 0]),
            orientation=pfette_orientation,
            length=self.building_length,
            cross_section=STANDARD_CROSS_SECTIONS['PFETTE'][0],
            wall_support=True,
            sparren_support_spacing=self.sparren_spacing
        )
        self.beams.extend([fl, fr])
        self.beam_store['Fußpfette_L'] = fl
        self.beam_store['Fußpfette_R'] = fr

        # 3. Mittelpfetten (Middle Purlins)
        if self.pfetten_count >= 5:
            ml_id = self._get_next_id()
            mr_id = self._get_next_id()
            ml = Mittelpfette(
                beam_id=ml_id,
                position=np.array([-self.mittel_x, 0, self.mittel_y]),
                orientation=pfette_orientation,
                length=self.building_length,
                cross_section=STANDARD_CROSS_SECTIONS['PFETTE'][1], # (100, 220)
                support_connections=[], # Will be populated by Stuhlpfosten
                height_above_base=self.mittel_y,
                sparren_support_spacing=self.sparren_spacing
            )
            mr = Mittelpfette(
                beam_id=mr_id,
                position=np.array([self.mittel_x, 0, self.mittel_y]),
                orientation=pfette_orientation,
                length=self.building_length,
                cross_section=STANDARD_CROSS_SECTIONS['PFETTE'][1],
                support_connections=[],
                height_above_base=self.mittel_y,
                sparren_support_spacing=self.sparren_spacing
            )
            self.beams.extend([ml, mr])
            self.beam_store['Mittelpfette_L'] = ml
            self.beam_store['Mittelpfette_R'] = mr

    def _generate_stuhlpfosten(self):
        """Create vertical Stuhlpfosten to support the Pfetten."""
        print("  - Generating Stuhlpfosten...")
        
        # Posts are vertical, so their local Z-axis (length)
        # aligns with the world Z-axis (height).
        post_orientation = Rotation.identity()
        
        for y_pos in self.support_y_coords:
            # Normalized position along the Pfette's length
            pos_norm = (y_pos + self.building_length / 2.0) / self.building_length

            # 1. Support for Firstpfette
            fp_post_id = self._get_next_id()
            fp_post = Stuhlpfosten(
                beam_id=fp_post_id,
                position=np.array([0, y_pos, 0]), # Base of post
                orientation=post_orientation,
                length=self.ridge_height,
                cross_section=STANDARD_CROSS_SECTIONS['STUHLPFOSTEN'][1], # (120, 120)
                top_connection={
                    'pfette_id': self.beam_store['Firstpfette'].beam_id,
                    'joint_type': 'MORTISE_TENON',
                    'tenon_height': 0.10
                },
                bottom_connection={'base_type': 'floor_beam', 'joint_type': 'BEARING'}
            )
            self.beams.append(fp_post)
            # Add connection info back to the Pfette
            self.beam_store['Firstpfette'].stuhlpfosten_connections.append({
                'position_normalized': pos_norm,
                'stuhlpfosten_id': fp_post_id,
                'joint_type': 'MORTISE_TENON'
            })

            # 2. Support for Mittelpfetten
            if self.pfetten_count >= 5:
                # Left Mittelpfette Post
                ml_post_id = self._get_next_id()
                ml_post = Stuhlpfosten(
                    beam_id=ml_post_id,
                    position=np.array([-self.mittel_x, y_pos, 0]),
                    orientation=post_orientation,
                    length=self.mittel_y,
                    cross_section=STANDARD_CROSS_SECTIONS['STUHLPFOSTEN'][0], # (100, 100)
                    top_connection={'pfette_id': self.beam_store['Mittelpfette_L'].beam_id, 'joint_type': 'MORTISE_TENON', 'tenon_height': 0.08},
                    bottom_connection={'base_type': 'floor_beam', 'joint_type': 'BEARING'}
                )
                self.beams.append(ml_post)
                self.beam_store['Mittelpfette_L'].support_connections.append({
                    'position_normalized': pos_norm, 'support_id': ml_post_id, 'support_type': 'stuhlpfosten', 'joint_type': 'MORTISE_TENON'
                })
                
                # Right Mittelpfette Post
                mr_post_id = self._get_next_id()
                mr_post = Stuhlpfosten(
                    beam_id=mr_post_id,
                    position=np.array([self.mittel_x, y_pos, 0]),
                    orientation=post_orientation,
                    length=self.mittel_y,
                    cross_section=STANDARD_CROSS_SECTIONS['STUHLPFOSTEN'][0],
                    top_connection={'pfette_id': self.beam_store['Mittelpfette_R'].beam_id, 'joint_type': 'MORTISE_TENON', 'tenon_height': 0.08},
                    bottom_connection={'base_type': 'floor_beam', 'joint_type': 'BEARING'}
                )
                self.beams.append(mr_post)
                self.beam_store['Mittelpfette_R'].support_connections.append({
                    'position_normalized': pos_norm, 'support_id': mr_post_id, 'support_type': 'stuhlpfosten', 'joint_type': 'MORTISE_TENON'
                })

    def _generate_sparren(self):
        """Create the Sparren (rafters) that rest on the Pfetten."""
        print("  - Generating Sparren...")
        
        # Sparren are rotated "up" around the Y-axis (longitudinal)
        orientation_L = Rotation.from_euler('y', self.roof_pitch_deg, degrees=True)
        orientation_R = Rotation.from_euler('y', -self.roof_pitch_deg, degrees=True)

        # Define the connection points once
        pfette_connections_L = []
        pfette_connections_R = []

        # 1. Fußpfette connection
        pfette_connections_L.append({'position_normalized': 0.0, 'pfette_id': self.beam_store['Fußpfette_L'].beam_id, 'notch_depth': 0.03})
        pfette_connections_R.append({'position_normalized': 0.0, 'pfette_id': self.beam_store['Fußpfette_R'].beam_id, 'notch_depth': 0.03})

        # 2. Mittelpfette connection
        if self.pfetten_count >= 5:
            pfette_connections_L.append({'position_normalized': 0.5, 'pfette_id': self.beam_store['Mittelpfette_L'].beam_id, 'notch_depth': 0.03})
            pfette_connections_R.append({'position_normalized': 0.5, 'pfette_id': self.beam_store['Mittelpfette_R'].beam_id, 'notch_depth': 0.03})
        
        # 3. Firstpfette connection
        pfette_connections_L.append({'position_normalized': 1.0, 'pfette_id': self.beam_store['Firstpfette'].beam_id, 'notch_depth': 0.03})
        pfette_connections_R.append({'position_normalized': 1.0, 'pfette_id': self.beam_store['Firstpfette'].beam_id, 'notch_depth': 0.03})

        for y_pos in self.sparren_y_coords:
            # Left Sparren
            sl_id = self._get_next_id()
            sl = Pfettendach_Sparren(
                beam_id=sl_id,
                position=np.array([-self.half_width, y_pos, 0]), # Eaves start point
                orientation=orientation_L,
                length=self.sparren_hypotenuse,
                cross_section=STANDARD_CROSS_SECTIONS['SPARREN'][1], # (80, 160)
                pitch_angle=self.roof_pitch_deg,
                pfette_connections=pfette_connections_L
            )
            
            # Right Sparren
            sr_id = self._get_next_id()
            sr = Pfettendach_Sparren(
                beam_id=sr_id,
                position=np.array([self.half_width, y_pos, 0]), # Eaves start point
                orientation=orientation_R,
                length=self.sparren_hypotenuse,
                cross_section=STANDARD_CROSS_SECTIONS['SPARREN'][1],
                pitch_angle=self.roof_pitch_deg,
                pfette_connections=pfette_connections_R
            )
            self.beams.extend([sl, sr])

    def _generate_streben(self):
        """(Optional) Generate diagonal Streben (braces)."""
        # This is a complex step involving angled connections.
        # Stub for future implementation.
        print("  - Generating Streben (braces)... (SKIPPED)")
        pass