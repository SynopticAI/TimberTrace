"""
Beams Package - Timber Trace Simulator

Contains all beam type classes for German timber roof construction.

Beam Categories:
- Sparren (rafters): Diagonal roof beams
- Pfetten (purlins): Horizontal longitudinal support beams
- Stuhlpfosten (posts): Vertical support columns
- Streben (braces): Diagonal bracing elements
- Kehlbalken (collar beams): Horizontal tie beams between rafters

Usage:
    from beams import Pfettendach_Sparren, Firstpfette, Stuhlpfosten
"""

from .base_beam import BaseBeam

# Sparren (Rafters)
from .sparren import (
    Pfettendach_Sparren,
    Sparrendach_Sparren,
    Kehlbalkendach_Sparren
)

# Pfetten (Purlins)
from .pfetten import (
    Firstpfette,
    Mittelpfette,
    Fußpfette
)

# Support Elements
from .stuhlpfosten import Stuhlpfosten
from .streben import Strebe
from .kehlbalken import Kehlbalken


# Beam registry for XML deserialization
# Maps beam_type string to class
BEAM_CLASS_REGISTRY = {
    'Pfettendach_Sparren': Pfettendach_Sparren,
    'Sparrendach_Sparren': Sparrendach_Sparren,
    'Kehlbalkendach_Sparren': Kehlbalkendach_Sparren,
    'Firstpfette': Firstpfette,
    'Mittelpfette': Mittelpfette,
    'Fußpfette': Fußpfette,
    'Stuhlpfosten': Stuhlpfosten,
    'Strebe': Strebe,
    'Kehlbalken': Kehlbalken,
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
    'Sparrendach_Sparren',
    'Kehlbalkendach_Sparren',
    
    # Pfetten
    'Firstpfette',
    'Mittelpfette',
    'Fußpfette',
    
    # Support
    'Stuhlpfosten',
    'Strebe',
    'Kehlbalken',
    
    # Utilities
    'BEAM_CLASS_REGISTRY',
    'get_beam_class',
]