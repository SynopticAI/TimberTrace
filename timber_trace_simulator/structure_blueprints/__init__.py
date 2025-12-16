# structure_blueprints/__init__.py
"""
Blueprint definitions for different timber structures.

Blueprints define TOPOLOGY (which beams connect and how) and provide
rough initial parameters. The constraint solver enforces geometric validity.
"""

from .simple_structures import (
    post_and_beam, 
    sparren_on_pfette_on_pfosten, 
    half_pfettendach
)
from .pfettendach import create_pfettendach

__all__ = [
    'post_and_beam',
    'sparren_on_pfette_on_pfosten',
    'half_pfettendach',
    'create_pfettendach'
]