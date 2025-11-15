"""
Beams Package - Timber Trace Simulator (FreeCAD Version)

Contains all beam type classes for German timber roof construction.

All beam classes:
- Store parameters needed for FreeCAD templates
- Generate meshes via FreeCAD headless execution
- Use position-centric parameterization for alignment

Beam Categories:
- Sparren (rafters): Diagonal roof beams
- Pfetten (purlins): Horizontal longitudinal support beams
- Stuhlpfosten (posts): Vertical support columns

Usage:
    from beams import Pfettendach_Sparren, Firstpfette, Stuhlpfosten
"""

from .base_beam import BaseBeam

# Sparren (Rafters)
from .sparren import Pfettendach_Sparren

# Pfetten (Purlins)
from .pfetten import (
    Firstpfette,
    Mittelpfette,
    Fußpfette
)

# Support Elements
from .stuhlpfosten import Stuhlpfosten


# Beam registry for future use
BEAM_CLASS_REGISTRY = {
    'Pfettendach_Sparren': Pfettendach_Sparren,
    'Firstpfette': Firstpfette,
    'Mittelpfette': Mittelpfette,
    'Fußpfette': Fußpfette,
    'Stuhlpfosten': Stuhlpfosten,
}


def get_beam_class(beam_type: str):
    """
    Get beam class from beam type string.
    
    Args:
        beam_type: Beam type string (e.g., 'Pfettendach_Sparren')
        
    Returns:
        Beam class
        
    Raises:
        ValueError: If beam type not found
    """
    if beam_type not in BEAM_CLASS_REGISTRY:
        raise ValueError(f"Unknown beam type: {beam_type}. "
                        f"Available: {list(BEAM_CLASS_REGISTRY.keys())}")
    return BEAM_CLASS_REGISTRY[beam_type]


__all__ = [
    # Base class
    'BaseBeam',
    
    # Sparren
    'Pfettendach_Sparren',
    
    # Pfetten
    'Firstpfette',
    'Mittelpfette',
    'Fußpfette',
    
    # Support
    'Stuhlpfosten',
    
    # Utilities
    'BEAM_CLASS_REGISTRY',
    'get_beam_class',
]