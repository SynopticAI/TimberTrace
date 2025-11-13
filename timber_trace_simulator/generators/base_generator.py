"""
Abstract Base Class for Roof Generators
Timber Trace Simulator
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from beams.base_beam import BaseBeam

class BaseRoofGenerator(ABC):
    """
    Abstract interface for all roof generators.
    
    Each generator takes a dictionary of parameters, validates them,
    and produces a list of BaseBeam objects.
    """
    
    def __init__(self, roof_params: Dict[str, Any]):
        """
        Initialize the generator with roof parameters.
        
        Args:
            roof_params: Dictionary of parameters defining the roof.
        """
        if not self.validate_parameters(roof_params):
            raise ValueError("Invalid roof parameters provided.")
            
        self.roof_params = roof_params
        self.beams: List[BaseBeam] = []
        self.beam_id_counter = 0
        self.beam_store: Dict[str, BaseBeam] = {} # For storing key beams by name

    @abstractmethod
    def generate(self) -> List[BaseBeam]:
        """
        Generate the list of BaseBeam objects for this roof type.
        
        This is the main method to be implemented by subclasses.
        
        Returns:
            List of instantiated BaseBeam objects.
        """
        pass
        
    @abstractmethod
    def validate_parameters(self, roof_params: Dict[str, Any]) -> bool:
        """
        Check if the provided roof_params are valid for this generator.
        
        Args:
            roof_params: Dictionary of parameters to validate.
            
        Returns:
            True if parameters are valid, False otherwise.
        """
        pass
        
    def get_roof_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about the generated roof.
        
        Returns:
            Dictionary containing generator type and roof parameters.
        """
        return {
            "generator_type": self.__class__.__name__,
            "roof_parameters": self.roof_params
        }

    def _get_next_id(self) -> int:
        """Helper to increment and return a unique beam ID."""
        self.beam_id_counter += 1
        return self.beam_id_counter

    def get_beams(self) -> List[BaseBeam]:
        """Return the list of generated beams."""
        return self.beams

    def get_beam_by_name(self, name: str) -> BaseBeam:
        """Get a specific stored beam by its internal name."""
        return self.beam_store.get(name)