# scene_generator.py
"""
Architecture-agnostic scene generator.

Takes structure blueprints (topology + rough parameters) and produces
physically valid, geometrically consistent datasets through constraint solving.

This module knows nothing about "roofs" or "timber" - it just processes
objects, constraints, and relationships.
"""

import os
import json
import numpy as np
from typing import List, Dict, Callable, Tuple
from tqdm import tqdm

from object_definitions import BeamBase, BEAM_NAMES
from constraint_solver import solve_constraints, SolverError

try:
    from build123d import export_stl
    BUILD123D_AVAILABLE = True
except ImportError:
    BUILD123D_AVAILABLE = False
    print("⚠️  build123d not available - STL export will fail")


def generate_scenes(blueprint_func: Callable,
                   num_scenes: int,
                   output_dir: str,
                   perturbation_scale: float = 0.05,
                   solver_verbose: bool = False) -> None:
    """
    Generate dataset of valid structures using constraint-based approach.
    
    Workflow:
      1. Call blueprint to get rough structure + topology
      2. Apply random perturbations to morphology (for variation)
      3. Solve constraints to enforce physical validity
      4. Generate meshes and export
    
    Args:
        blueprint_func: Function returning (beams, topology)
                       e.g., structure_blueprints.simple_structures.post_and_beam
        num_scenes: Number of structure variations to generate
        output_dir: Root directory for dataset (e.g., "training_data")
        perturbation_scale: Fraction of parameter range to perturb (0.05 = ±5%)
        solver_verbose: Print detailed solver output
    
    Output Structure:
        output_dir/
            scene_0000/
                metadata.json
                beam_00.stl
                beam_01.stl
                ...
            scene_0001/
                ...
            index.json
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n🔨 Generating {num_scenes} scenes using constraint-based approach...")
    print(f"   Blueprint: {blueprint_func.__name__}")
    print(f"   Perturbation: ±{perturbation_scale*100:.1f}% of parameter range")
    
    failed_scenes = []
    
    for scene_id in tqdm(range(num_scenes), desc="Generating scenes"):
        try:
            # =====================================================================
            # STEP 1: Get rough structure from blueprint
            # =====================================================================
            beams, topology = blueprint_func(seed=scene_id)
            
            # =====================================================================
            # STEP 2: Apply perturbations for variation
            # =====================================================================
            beams = _apply_perturbations(beams, perturbation_scale, seed=scene_id)
            
            # =====================================================================
            # STEP 3: Solve constraints to ensure validity
            # =====================================================================
            try:
                beams = solve_constraints(
                    beams, 
                    topology,
                    max_adjustment=0.5,  # Allow up to 0.5m adjustment
                    verbose=solver_verbose
                )
            except SolverError as e:
                print(f"\n⚠️  Scene {scene_id}: Solver failed - {e}")
                failed_scenes.append((scene_id, str(e)))
                continue
            
            # =====================================================================
            # STEP 4: Export scene
            # =====================================================================
            _export_scene(scene_id, beams, topology, output_dir)
            
        except Exception as e:
            print(f"\n❌ Scene {scene_id}: Unexpected error - {e}")
            failed_scenes.append((scene_id, str(e)))
            continue
    
    # =========================================================================
    # Create index file
    # =========================================================================
    _create_index_file(output_dir, num_scenes, failed_scenes)
    
    print(f"\n✅ Generation complete!")
    print(f"   Successful: {num_scenes - len(failed_scenes)}/{num_scenes}")
    if failed_scenes:
        print(f"   Failed: {len(failed_scenes)}")
        print(f"   See {output_dir}/failed_scenes.json for details")


def _apply_perturbations(beams: List[BeamBase], 
                        scale: float,
                        seed: int) -> List[BeamBase]:
    """
    Apply random perturbations to morphology parameters.
    
    Position and orientation are NOT perturbed (solver handles placement).
    Only morphology (width, height, length, etc.) is varied.
    
    Args:
        beams: List of beams to perturb
        scale: Perturbation magnitude (fraction of parameter range)
        seed: Random seed
    
    Returns:
        Beams with perturbed parameters (modified in-place)
    """
    np.random.seed(seed)
    
    for beam in beams:
        params = beam.get_parameters()
        morphology_keys = params['morphology_keys']
        bounds = beam.get_parameter_bounds()
        
        perturbed_params = {}
        
        for key in morphology_keys:
            if key in bounds:
                current_value = params['values'][key]
                min_val, max_val = bounds[key]
                param_range = max_val - min_val
                
                # Add random perturbation
                perturbation = np.random.uniform(-scale, scale) * param_range
                new_value = current_value + perturbation
                
                # Clip to bounds
                new_value = np.clip(new_value, min_val, max_val)
                perturbed_params[key] = new_value
        
        beam.set_parameters(perturbed_params)
    
    return beams


def _export_scene(scene_id: int,
                 beams: List[BeamBase],
                 topology: Dict,
                 output_dir: str) -> None:
    """
    Export scene as STL files + metadata JSON.
    
    Args:
        scene_id: Scene number
        beams: List of solved beams
        topology: Connectivity and identity information
        output_dir: Root output directory
    """
    scene_dir = os.path.join(output_dir, f"scene_{scene_id:04d}")
    os.makedirs(scene_dir, exist_ok=True)
    
    # Prepare metadata
    scene_meta = {
        'scene_id': scene_id,
        'num_beams': len(beams),
        'beams': [],
        'connectivity': {},
        'identity_pairs': topology.get('identity_pairs', [])
    }
    
    # Collect all models for full scene export
    all_models = []
    
    # Export each beam
    for beam_idx, beam in enumerate(beams):
        # Get semantic label from type
        beam_type = type(beam).__name__
        from object_definitions import BEAM_TYPES, BEAM_NAMES
        
        # Find semantic label
        semantic_label = None
        for label, beam_class in BEAM_TYPES.items():
            if beam_class.__name__ == beam_type:
                semantic_label = label
                break
        
        if semantic_label is None:
            raise ValueError(f"Unknown beam type: {beam_type}")
        
        # Export STL
        stl_name = f"beam_{beam_idx:02d}.stl"
        stl_path = os.path.join(scene_dir, stl_name)
        
        if BUILD123D_AVAILABLE:
            try:
                model = beam.get_model()
                export_stl(model, stl_path)
                all_models.append(model)  # Collect for full scene export
            except Exception as e:
                print(f"⚠️  Failed to export beam {beam_idx}: {e}")
                continue
        
        # Add to metadata
        beam_meta = {
            'beam_id': beam_idx,
            'beam_type': BEAM_NAMES[semantic_label],
            'semantic_label': semantic_label,
            'stl_file': stl_name,
            'parameters': beam.get_parameters()['values']
        }
        scene_meta['beams'].append(beam_meta)
    
    # =========================================================================
    # Export full scene as single STL
    # =========================================================================
    if BUILD123D_AVAILABLE and all_models:
        try:
            # Combine all beam models into one assembly
            from build123d import Compound
            full_scene = Compound(children=all_models)
            full_scene_path = os.path.join(scene_dir, "full_scene.stl")
            export_stl(full_scene, full_scene_path)
        except Exception as e:
            print(f"⚠️  Failed to export full scene {scene_id}: {e}")
    
    # Convert connectivity to serializable format
    for face_name, contact_list in topology['connectivity'].items():
        if contact_list:
            # Convert tuples to lists for JSON
            scene_meta['connectivity'][face_name] = [list(c) for c in contact_list]
        else:
            scene_meta['connectivity'][face_name] = []
    
    # Save metadata
    meta_path = os.path.join(scene_dir, "metadata.json")
    with open(meta_path, 'w') as f:
        json.dump(scene_meta, f, indent=2)


def _create_index_file(output_dir: str, 
                      num_scenes: int,
                      failed_scenes: List[Tuple[int, str]]) -> None:
    """Create index file for dataset"""
    from object_definitions import BEAM_NAMES
    
    successful_scenes = [
        f"scene_{i:04d}" 
        for i in range(num_scenes) 
        if i not in [s[0] for s in failed_scenes]
    ]
    
    index_data = {
        'num_scenes': num_scenes,
        'num_successful': len(successful_scenes),
        'num_failed': len(failed_scenes),
        'beam_types': BEAM_NAMES,
        'scene_dirs': successful_scenes
    }
    
    with open(os.path.join(output_dir, "index.json"), 'w') as f:
        json.dump(index_data, f, indent=2)
    
    # Save failed scenes list if any
    if failed_scenes:
        with open(os.path.join(output_dir, "failed_scenes.json"), 'w') as f:
            json.dump([{'scene_id': s[0], 'error': s[1]} for s in failed_scenes], f, indent=2)