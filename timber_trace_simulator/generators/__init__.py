"""
Generators Package - Timber Trace Simulator

Contains all procedural roof generator classes.
"""

from .base_generator import BaseRoofGenerator
from .pfettendach_rechteck_generator import PfettendachRechteckGenerator

__all__ = [
    'BaseRoofGenerator',
    'PfettendachRechteckGenerator',
]