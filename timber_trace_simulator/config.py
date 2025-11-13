"""
Configuration and Constants for Timber Trace Simulator

Contains:
- DIN 4074-1 standard dimensions
- Beam type definitions and enums
- Material properties
- ML model mappings
"""

import numpy as np
from enum import Enum
from typing import Dict, Tuple


# ============================================================================
# Beam Type Definitions
# ============================================================================

class BeamTypeCategory(Enum):
    """High-level beam categories"""
    SPARREN = "sparren"
    PFETTE = "pfette"
    STUHLPFOSTEN = "stuhlpfosten"
    STREBE = "strebe"
    KEHLBALKEN = "kehlbalken"


# Beam type string constants (used for beam_type attribute)
BEAM_TYPES = {
    # Sparren variants (roof-construction-specific)
    'PFETTENDACH_SPARREN': 'Pfettendach_Sparren',
    'SPARRENDACH_SPARREN': 'Sparrendach_Sparren',
    'KEHLBALKENDACH_SPARREN': 'Kehlbalkendach_Sparren',
    
    # Pfetten (generic across roof types)
    'FIRSTPFETTE': 'Firstpfette',
    'MITTELPFETTE': 'Mittelpfette',
    'FUSSPFETTE': 'Fußpfette',
    
    # Support elements
    'STUHLPFOSTEN': 'Stuhlpfosten',
    'STREBE': 'Strebe',
    'KEHLBALKEN': 'Kehlbalken',
}

# Mapping for ML models (beam_type → integer ID)
BEAM_TYPE_TO_ID = {
    BEAM_TYPES['PFETTENDACH_SPARREN']: 0,
    BEAM_TYPES['SPARRENDACH_SPARREN']: 1,
    BEAM_TYPES['KEHLBALKENDACH_SPARREN']: 2,
    BEAM_TYPES['FIRSTPFETTE']: 3,
    BEAM_TYPES['MITTELPFETTE']: 4,
    BEAM_TYPES['FUSSPFETTE']: 5,
    BEAM_TYPES['STUHLPFOSTEN']: 6,
    BEAM_TYPES['STREBE']: 7,
    BEAM_TYPES['KEHLBALKEN']: 8,
}

# Reverse mapping (integer ID → beam_type)
ID_TO_BEAM_TYPE = {v: k for k, v in BEAM_TYPE_TO_ID.items()}


# ============================================================================
# DIN 4074-1 Standard Dimensions (KVH - Konstruktionsvollholz)
# ============================================================================
# All dimensions in millimeters (mm)

# Standard cross-sections: (width, height) in mm
STANDARD_CROSS_SECTIONS = {
    # Sparren (rafters)
    'SPARREN': [
        (60, 120), (60, 140), (60, 160), (60, 180), (60, 200),
        (80, 120), (80, 140), (80, 160), (80, 180), (80, 200),
        (100, 160), (100, 180), (100, 200),
    ],
    
    # Pfetten (purlins)
    'PFETTE': [
        (80, 200), (80, 220), (80, 240),
        (100, 200), (100, 220), (100, 240),
        (120, 200), (120, 220), (120, 240), (120, 260),
        (140, 240), (140, 260),
    ],
    
    # Stuhlpfosten (posts) - typically square
    'STUHLPFOSTEN': [
        (100, 100), (120, 120), (140, 140), (160, 160),
    ],
    
    # Streben (braces)
    'STREBE': [
        (60, 120), (60, 140), (60, 160),
        (80, 120), (80, 140), (80, 160),
    ],
    
    # Kehlbalken (collar beams)
    'KEHLBALKEN': [
        (60, 120), (60, 140), (60, 160),
        (80, 140), (80, 160), (80, 180),
    ],
}

# Typical length ranges (min, max) in meters
STANDARD_LENGTH_RANGES = {
    'SPARREN': (3.0, 8.0),
    'PFETTE': (4.0, 12.0),
    'STUHLPFOSTEN': (1.5, 3.5),
    'STREBE': (1.0, 3.0),
    'KEHLBALKEN': (3.0, 8.0),
}


# ============================================================================
# Material Properties
# ============================================================================

WOOD_SPECIES = {
    'SPRUCE': {
        'name': 'Norway Spruce (Fichte)',
        'density': 450,  # kg/m³
        'strength_class': 'C24',
        'color': [0.95, 0.85, 0.70],  # RGB for visualization
    },
    'FIR': {
        'name': 'Silver Fir (Tanne)',
        'density': 460,  # kg/m³
        'strength_class': 'C24',
        'color': [0.92, 0.80, 0.65],
    },
    'OAK': {
        'name': 'European Oak (Eiche)',
        'density': 690,  # kg/m³
        'strength_class': 'D40',
        'color': [0.65, 0.50, 0.35],
    },
    'PINE': {
        'name': 'Scots Pine (Kiefer)',
        'density': 520,  # kg/m³
        'strength_class': 'C24',
        'color': [0.85, 0.70, 0.55],
    },
}

# Default wood species
DEFAULT_WOOD_SPECIES = 'SPRUCE'


# ============================================================================
# Joint Type Definitions
# ============================================================================

JOINT_TYPES = {
    # Notches (Kerven)
    'SPARRENKERVE': 'sparrenkerve',  # Rafter notch onto purlin
    'SIMPLE_NOTCH': 'simple_notch',
    
    # Mortise & Tenon (Zapfen)
    'MORTISE_TENON': 'mortise_tenon',
    'THROUGH_TENON': 'through_tenon',
    'DOUBLE_TENON': 'double_tenon',
    
    # Lap joints (Blattverbindungen)
    'RIDGE_LAP': 'ridge_lap',  # First connection at ridge
    'CROSS_LAP': 'cross_lap',
    'HALF_LAP': 'half_lap',
    
    # Dovetail
    'DOVETAIL': 'dovetail',
    
    # Simple connections
    'BEARING': 'bearing',  # Simple bearing surface
}


# ============================================================================
# Visualization Colors (by beam type category)
# ============================================================================

VISUALIZATION_COLORS = {
    BeamTypeCategory.SPARREN: [0.8, 0.4, 0.2],      # Orange-brown
    BeamTypeCategory.PFETTE: [0.6, 0.3, 0.1],       # Dark brown
    BeamTypeCategory.STUHLPFOSTEN: [0.5, 0.5, 0.5], # Gray
    BeamTypeCategory.STREBE: [0.7, 0.6, 0.4],       # Light brown
    BeamTypeCategory.KEHLBALKEN: [0.4, 0.4, 0.6],   # Blue-gray
}


# ============================================================================
# Geometric Constants
# ============================================================================

# Joint dimension ratios (as fraction of beam thickness)
JOINT_RATIOS = {
    'TENON_WIDTH': 1/3,      # Tenon width = 1/3 of beam thickness
    'MORTISE_DEPTH': 2/3,    # Mortise depth = 2/3 of beam thickness
    'NOTCH_DEPTH': 0.03,     # Notch depth in meters (30mm typical)
}

# Standard angles (degrees)
STANDARD_ROOF_PITCHES = [25, 30, 35, 40, 45, 50, 55]  # Common roof pitches
STANDARD_BRACE_ANGLE = 45  # Typical angle for Streben


# ============================================================================
# Tolerances and Precision
# ============================================================================

# Manufacturing tolerances (mm)
MANUFACTURING_TOLERANCE = 2.0  # ±2mm typical for KVH

# Geometric precision for calculations
GEOMETRIC_PRECISION = 1e-6  # meters

# Mesh resolution for beam generation
DEFAULT_MESH_RESOLUTION = 0.01  # 1cm for mesh details


# ============================================================================
# Validation Ranges
# ============================================================================

VALIDATION_RANGES = {
    'roof_pitch': (15, 65),          # degrees
    'building_length': (5.0, 30.0),   # meters
    'building_width': (4.0, 15.0),    # meters
    'sparren_spacing': (0.5, 1.2),    # meters
    'beam_width': (40, 200),          # mm
    'beam_height': (80, 300),         # mm
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_beam_type_category(beam_type: str) -> BeamTypeCategory:
    """Return the category for a given beam type string"""
    if 'Sparren' in beam_type:
        return BeamTypeCategory.SPARREN
    elif 'pfette' in beam_type:
        return BeamTypeCategory.PFETTE
    elif 'Stuhlpfosten' in beam_type:
        return BeamTypeCategory.STUHLPFOSTEN
    elif 'Strebe' in beam_type:
        return BeamTypeCategory.STREBE
    elif 'Kehlbalken' in beam_type:
        return BeamTypeCategory.KEHLBALKEN
    else:
        raise ValueError(f"Unknown beam type: {beam_type}")


def get_visualization_color(beam_type: str) -> np.ndarray:
    """Get RGB color for visualization based on beam type"""
    category = get_beam_type_category(beam_type)
    return np.array(VISUALIZATION_COLORS[category])


def validate_cross_section(width: float, height: float, beam_category: str) -> bool:
    """Check if cross-section dimensions are within valid ranges"""
    min_w, max_w = 40, 200
    min_h, max_h = 80, 300
    
    return (min_w <= width <= max_w) and (min_h <= height <= max_h)