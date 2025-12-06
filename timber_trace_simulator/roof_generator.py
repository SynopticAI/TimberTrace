"""
Generic Roof Generator

Generates synthetic timber roof structures from config-based definitions.
Works with any roof type - all structure defined in config file.
"""

import sys
import os
import numpy as np
import trimesh
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import FreeCAD utilities
sys.path.insert(0, str(Path(__file__).parent))
from core.freecad_utils import generate_mesh_from_master


class RoofGenerator:
    """
    Generic roof structure generator.
    
    Uses config files to define roof structure and parameter ranges.
    Generates diverse training data without hard-coded roof logic.
    """
    
    def __init__(self, config_module):
        """
        Initialize generator with a config module.
        
        Args:
            config_module: Python module containing:
                - MASTER_FILE: Path to FreeCAD template
                - PARAMETERS: Dict of parameter ranges
                - BEAMS: Dict of beam definitions
                - compute_derived_parameters(): Function
        """
        self.config = config_module
        self.master_file = self._resolve_master_file_path()
        
        # Validate master file exists
        if not Path(self.master_file).exists():
            raise FileNotFoundError(f"Master file not found: {self.master_file}")
        
        print(f"✓ RoofGenerator initialized")
        print(f"  Master file: {self.master_file}")
        print(f"  Parameters: {len(self.config.PARAMETERS)}")
        print(f"  Beam types: {len(self.config.BEAMS)}")
    
    def _resolve_master_file_path(self) -> str:
        """Resolve master file path relative to project root."""
        # Assume config.MASTER_FILE is relative to project root
        project_root = Path(__file__).parent
        master_path = project_root / self.config.MASTER_FILE
        return str(master_path)
    
    def sample_parameters(self, seed: Optional[int] = None) -> Dict[str, float]:
        """
        Sample random parameter values from defined ranges.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary of {parameter_name: sampled_value}
        """
        if seed is not None:
            np.random.seed(seed)
        
        sampled = {}
        
        for param_name, param_config in self.config.PARAMETERS.items():
            min_val, max_val = param_config["range"]
            unit = param_config["unit"]
            
            # Sample based on unit type
            if unit == "count":
                # Integer values for counts
                value = np.random.randint(min_val, max_val + 1)
            elif unit == "deg":
                # Continuous for angles
                value = np.random.uniform(min_val, max_val)
            else:  # mm or other continuous
                value = np.random.uniform(min_val, max_val)
            
            sampled[param_name] = value
        
        # Compute any derived parameters
        sampled = self.config.compute_derived_parameters(sampled)
        
        return sampled
    
    def generate_roof(self, seed: Optional[int] = None) -> Dict:
        """
        Generate a complete roof structure.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary containing:
                - parameters: Sampled parameter values
                - beams: List of beam instances with meshes
                - metadata: Roof-level information
        """
        print(f"\n{'='*60}")
        print(f"Generating Roof (seed={seed})")
        print(f"{'='*60}")
        
        # Step 1: Sample parameters
        params = self.sample_parameters(seed)
        print(f"\n✓ Sampled {len(params)} parameters")
        
        # Show a few examples
        print("  Sample values:")
        for i, (key, val) in enumerate(list(params.items())[:5]):
            print(f"    {key}: {val:.2f}")
        print("    ...")
        
        # Step 2: Generate beams
        print(f"\n⚙ Generating beams...")
        beams = []
        
        for beam_name, beam_config in self.config.BEAMS.items():
            print(f"\n  Processing: {beam_name}")
            print(f"    Body: {beam_config['body_name']}")
            print(f"    Label: {beam_config['semantic_label']}")
            
            # Extract base mesh from FreeCAD
            try:
                base_mesh = self._extract_base_mesh(
                    beam_config["body_name"],
                    params
                )
                print(f"    ✓ Extracted mesh: {len(base_mesh.vertices)} verts")
                
                # Create beam instances (replication logic)
                instances = self._create_beam_instances(
                    beam_name,
                    beam_config,
                    base_mesh,
                    params
                )
                
                beams.extend(instances)
                print(f"    ✓ Created {len(instances)} instances")
                
            except Exception as e:
                print(f"    ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Step 3: Assemble result
        result = {
            "parameters": params,
            "beams": beams,
            "metadata": {
                "seed": seed,
                "total_beams": len(beams),
                "beam_types": len(self.config.BEAMS)
            }
        }
        
        print(f"\n{'='*60}")
        print(f"✓ Roof generation complete")
        print(f"  Total beam instances: {len(beams)}")
        print(f"{'='*60}\n")
        
        return result
    
    def _extract_base_mesh(
        self, 
        body_name: str, 
        params: Dict[str, float]
    ) -> trimesh.Trimesh:
        """
        Extract mesh from FreeCAD body with updated parameters.
        
        Args:
            body_name: FreeCAD body name (e.g., "Body002")
            params: Full parameter dictionary
            
        Returns:
            trimesh.Trimesh in template coordinates
        """
        # Call FreeCAD utility
        mesh = generate_mesh_from_master(
            master_file=self.master_file,
            body_name=body_name,
            param_updates=params  # Pass all params
        )
        
        return mesh
    
    def _create_beam_instances(
        self,
        beam_name: str,
        beam_config: Dict,
        base_mesh: trimesh.Trimesh,
        params: Dict[str, float]
    ) -> List[Dict]:
        """
        Create beam instances based on replication rules.
        
        Args:
            beam_name: Logical beam name (e.g., "Sparren")
            beam_config: Beam configuration from config
            base_mesh: Base mesh in template coordinates
            params: Full parameter dictionary
            
        Returns:
            List of beam instance dictionaries
        """
        instances = []
        
        # Determine count
        count_spec = beam_config["count"]
        if isinstance(count_spec, str):
            # Reference to parameter
            count = int(params[count_spec])
        else:
            count = count_spec
        
        # Determine Y spacing
        y_spacing = 0
        if beam_config.get("y_spacing") == "auto":
            spacing_key = f"{beam_name}_Spacing"
            y_spacing = params.get(spacing_key, 0)
        elif beam_config.get("y_spacing"):
            y_spacing = params[beam_config["y_spacing"]]
        
        # Determine X mirroring
        x_mirror = beam_config.get("x_mirror", False)
        
        # Generate instances
        instance_id = 0
        
        # Y-direction replication
        for i in range(count):
            # Calculate Y offset
            if count > 1 and y_spacing > 0:
                # Distribute in positive Y direction with margin
                margin = 500  # mm from origin (start of purlin)
                y_offset = margin + i * y_spacing
            else:
                y_offset = 0
            
            # X-direction mirroring
            x_positions = [0]  # Default: centered
            if x_mirror:
                x_positions = [-1, 1]  # Left and right
            
            for x_side in x_positions:
                # Transform mesh
                mesh = base_mesh.copy()
                
                # Apply Y translation
                mesh.apply_translation([0, y_offset, 0])
                
                # Apply X mirroring if needed
                if x_side != 0:
                    # Mirror across YZ plane (flip X)
                    mesh.apply_scale([x_side, 1, 1])
                
                # Create instance record
                instance = {
                    "beam_type": beam_name,
                    "semantic_label": beam_config["semantic_label"],
                    "instance_id": instance_id,
                    "mesh": mesh,
                    "transform": {
                        "y_offset": y_offset,
                        "x_side": x_side
                    },
                    "metadata": {
                        "body_name": beam_config["body_name"],
                        "description": beam_config.get("description", "")
                    }
                }
                
                instances.append(instance)
                instance_id += 1
        
        return instances
    
    def export_visualization(self, roof_data: Dict, output_path: str):
        """
        Export combined mesh for visualization.
        
        Args:
            roof_data: Output from generate_roof()
            output_path: Path to save PLY file
        """
        print(f"\n📊 Exporting visualization...")
        
        # Combine all meshes
        combined = trimesh.util.concatenate([
            beam["mesh"] for beam in roof_data["beams"]
        ])
        
        # Assign colors by beam type
        colors = []
        color_map = {
            0: [255, 100, 100],  # Firstpfette - Red
            1: [100, 255, 100],  # Mittelpfette - Green
            2: [100, 100, 255],  # Fusspfette - Blue
            3: [255, 255, 100],  # Sparren - Yellow
            4: [255, 100, 255],  # Mittelpfosten - Magenta
            5: [100, 255, 255],  # Seitenpfosten - Cyan
        }
        
        for beam in roof_data["beams"]:
            label = beam["semantic_label"]
            color = color_map.get(label, [128, 128, 128])
            n_faces = len(beam["mesh"].faces)
            colors.extend([color] * n_faces)
        
        combined.visual.face_colors = colors
        
        # Export
        combined.export(output_path)
        print(f"  ✓ Saved to: {output_path}")
        print(f"  Total vertices: {len(combined.vertices)}")
        print(f"  Total faces: {len(combined.faces)}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def load_config(config_path: str):
    """
    Load a config module from file path.
    
    Args:
        config_path: Path to config .py file
        
    Returns:
        Loaded module
    """
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("roof_config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


def generate_from_config_file(config_path: str, seed: Optional[int] = None) -> Dict:
    """
    Convenience function: Generate roof from config file path.
    
    Args:
        config_path: Path to config .py file
        seed: Random seed
        
    Returns:
        Roof data dictionary
    """
    config = load_config(config_path)
    generator = RoofGenerator(config)
    return generator.generate_roof(seed)