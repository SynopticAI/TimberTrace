# scene_generator.py
"""
Architecture-agnostic scene generator.

Takes structure blueprints (topology + rough parameters) and produces
physically valid, geometrically consistent datasets through constraint solving.
"""

import os
import json
import numpy as np
from typing import List, Dict, Callable, Tuple, Optional
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
                   solver_verbose: bool = False,
                   export_presolve: bool = False) -> None:
    """
    Generate dataset of valid structures.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n🔨 Generating {num_scenes} scenes...")
    print(f"   Blueprint:    {blueprint_func.__name__}")
    print(f"   Perturbation: ±{perturbation_scale*100:.1f}%")
    print(f"   Pre-solve:    {'YES' if export_presolve else 'NO'}")
    
    failed_scenes = []
    
    for scene_id in tqdm(range(num_scenes), desc="Generating scenes"):
        try:
            # =====================================================================
            # STEP 1: Get rough structure from blueprint
            # =====================================================================
            beams, topology = blueprint_func(seed=scene_id)
            
            # =====================================================================
            # STEP 2: Apply perturbations (Variation)
            # =====================================================================
            beams = _apply_perturbations(beams, perturbation_scale, seed=scene_id)
            
            # =====================================================================
            # OPTIONAL: Export Pre-Solve State (Debug)
            # =====================================================================
            if export_presolve:
                # We catch errors here so bad geometry doesn't stop the pipeline
                try:
                    _export_scene(scene_id, beams, topology, output_dir, prefix="unprocessed_")
                except Exception as e:
                    print(f"⚠️  Scene {scene_id}: Failed to export pre-solve state: {e}")

            # =====================================================================
            # STEP 3: Solve constraints (Enforce Validity)
            # =====================================================================
            try:
                beams = solve_constraints(
                    beams, 
                    topology,
                    max_adjustment=0.5,
                    verbose=solver_verbose
                )
            except SolverError as e:
                print(f"\n⚠️  Scene {scene_id}: Solver failed - {e}")
                failed_scenes.append((scene_id, str(e)))
                continue
            
            # =====================================================================
            # STEP 4: Export Final Scene
            # =====================================================================
            _export_scene(scene_id, beams, topology, output_dir, prefix="")
            
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
    """Apply random perturbations to morphology."""
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
                
                perturbation = np.random.uniform(-scale, scale) * param_range
                new_value = current_value + perturbation
                new_value = np.clip(new_value, min_val, max_val)
                perturbed_params[key] = new_value
        
        beam.set_parameters(perturbed_params)
    
    return beams


def _export_scene(scene_id: int,
                 beams: List[BeamBase],
                 topology: Dict,
                 output_dir: str,
                 prefix: str = "") -> None:
    """
    Export scene STL + Metadata.
    Supports optional 'prefix' for un-solved states (e.g. "unprocessed_").
    """
    scene_dir = os.path.join(output_dir, f"scene_{scene_id:04d}")
    os.makedirs(scene_dir, exist_ok=True)
    
    scene_meta = {
        'scene_id': scene_id,
        'status': 'unprocessed' if prefix else 'solved',
        'num_beams': len(beams),
        'beams': [],
        'connectivity': {},
        'identity_pairs': topology.get('identity_pairs', [])
    }
    
    all_models = []
    
    for beam_idx, beam in enumerate(beams):
        beam_type = type(beam).__name__
        from object_definitions import BEAM_TYPES, BEAM_NAMES
        
        semantic_label = None
        for label, beam_class in BEAM_TYPES.items():
            if beam_class.__name__ == beam_type:
                semantic_label = label
                break
        
        if semantic_label is None:
            raise ValueError(f"Unknown beam type: {beam_type}")
        
        stl_name = f"{prefix}beam_{beam_idx:02d}.stl"
        stl_path = os.path.join(scene_dir, stl_name)
        
        if BUILD123D_AVAILABLE:
            try:
                model = beam.get_model()
                export_stl(model, stl_path)
                all_models.append(model)
            except Exception as e:
                print(f"⚠️  Failed to export {prefix}beam {beam_idx}: {e}")
                # DEBUG: Print the parameters that caused the failure
                print(f"   🛑 BAD PARAMS: {beam.get_parameters()['values']}")
                continue
        
        beam_meta = {
            'beam_id': beam_idx,
            'beam_type': BEAM_NAMES[semantic_label],
            'stl_file': stl_name,
            'parameters': beam.get_parameters()['values']
        }
        scene_meta['beams'].append(beam_meta)
    
    # Export full scene
    if BUILD123D_AVAILABLE and all_models:
        try:
            from build123d import Compound
            full_scene = Compound(children=all_models)
            full_scene_path = os.path.join(scene_dir, f"{prefix}full_scene.stl")
            export_stl(full_scene, full_scene_path)
        except Exception as e:
            print(f"⚠️  Failed to export full scene: {e}")
    
    # Convert connectivity for JSON
    for face_name, contact_list in topology['connectivity'].items():
        scene_meta['connectivity'][face_name] = [list(c) for c in contact_list] if contact_list else []
    
    # Save metadata
    meta_path = os.path.join(scene_dir, f"{prefix}metadata.json")
    with open(meta_path, 'w') as f:
        json.dump(scene_meta, f, indent=2)


def _create_index_file(output_dir: str, num_scenes: int, failed_scenes: List) -> None:
    """Create index.json"""
    from object_definitions import BEAM_NAMES
    successful_scenes = [f"scene_{i:04d}" for i in range(num_scenes) if i not in [s[0] for s in failed_scenes]]
    
    index_data = {
        'num_scenes': num_scenes,
        'num_successful': len(successful_scenes),
        'num_failed': len(failed_scenes),
        'beam_types': BEAM_NAMES,
        'scene_dirs': successful_scenes
    }
    
    with open(os.path.join(output_dir, "index.json"), 'w') as f:
        json.dump(index_data, f, indent=2)
    
    if failed_scenes:
        with open(os.path.join(output_dir, "failed_scenes.json"), 'w') as f:
            json.dump([{'scene_id': s[0], 'error': s[1]} for s in failed_scenes], f, indent=2)