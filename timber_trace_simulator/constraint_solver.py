# constraint_solver.py
"""
Core constraint solver using CVXPY quadratic programming.

Enforces physical validity by solving:
  minimize: ||θ - θ_raw||²  (stay close to initial estimates)
  subject to: Contact constraints (point-to-point, point-to-line, etc.)
              Parameter bounds
              Identity constraints (optional)

CRITICAL: theta_z (rotation) is CONSTANT during optimization.
Only positions (x,y,z) and morphology are optimized.
"""

import numpy as np
import cvxpy as cp
from typing import Dict, List, Tuple
from object_definitions import BeamBase, ConstraintEquation
from utils.cvxpy_helpers import extract_slack_tokens, evaluate_expression


class SolverError(Exception):
    """Raised when constraint problem is infeasible or solver fails"""
    pass


def solve_constraints(beams: List[BeamBase], 
                     topology: Dict,
                     max_adjustment: float = 0.5,
                     verbose: bool = False) -> List[BeamBase]:
    """
    Solve QP to enforce contact and identity constraints.
    
    Args:
        beams: List of beam objects with initial (rough) parameters
        topology: Dict containing:
            - 'connectivity': Dict[str, List[Tuple]] - contact pairs per face
            - 'identity_pairs': List[Tuple[int, int]] - beams with same morphology
        max_adjustment: Maximum allowed change per parameter (meters)
        verbose: Print solver output
    
    Returns:
        Same beam list with updated parameters
    
    Raises:
        SolverError: If constraints are infeasible
    
    Example topology:
        {
            'connectivity': {
                'top': [(0, 2, 4, 5, 0, 0)],  # (beam_i, beam_j, face_i, face_j, idx_i, idx_j)
            },
            'identity_pairs': [(0, 1)]  # Beams 0 and 1 have same morphology
        }
    """
    if verbose:
        print(f"\n🔧 Starting constraint solver for {len(beams)} beams...")
    
    # =========================================================================
    # STEP 1: Create CVXPY variables for each beam
    # =========================================================================
    # Note: theta_z is NOT a variable - it stays at initial value
    cvxpy_vars_list = []
    initial_params_list = []
    
    for beam in beams:
        params = beam.get_parameters()
        param_dict = params['values']
        morphology_keys = params['morphology_keys']
        
        # Create variables for position (x, y, z) and morphology
        beam_vars = {
            'x': cp.Variable(),
            'y': cp.Variable(),
            'z': cp.Variable(),
        }
        
        # Add morphology variables
        for key in morphology_keys:
            beam_vars[key] = cp.Variable()
        
        cvxpy_vars_list.append(beam_vars)
        initial_params_list.append(param_dict)
    
    if verbose:
        print(f"   Variables created: {sum(len(v) for v in cvxpy_vars_list)} total")
    
    # =========================================================================
    # STEP 2: Build contact constraints
    # =========================================================================
    constraints = []
    slack_vars = {}
    slack_counter = 0
    
    connectivity = topology.get('connectivity', {})
    
    for face_name, contact_list in connectivity.items():
        if not contact_list:
            continue
            
        for contact in contact_list:
            beam_i_idx, beam_j_idx, face_i, face_j, constr_idx_i, constr_idx_j = contact
            
            beam_i = beams[beam_i_idx]
            beam_j = beams[beam_j_idx]
            
            # Get constraint equations
            eq_i = beam_i.get_constraints(face_i, constr_idx_i)
            eq_j = beam_j.get_constraints(face_j, constr_idx_j)
            
            # Create slack variables for this constraint pair
            # Each constraint pair gets its own set of slacks
            # We need to map local slack names (slack_0, slack_1, ...) to unique global vars
            num_slacks_needed = max(eq_i.slack_count, eq_j.slack_count)
            
            pair_slacks = {}
            for s in range(num_slacks_needed):
                # Create mapping: local name -> global CVXPY variable
                local_slack_name = f"slack_{s}"
                global_slack_var = cp.Variable()
                pair_slacks[local_slack_name] = global_slack_var
                slack_vars[f"slack_{slack_counter}"] = global_slack_var  # Track globally
                slack_counter += 1
            
            # Evaluate constraint equations in CVXPY mode
            # Beam i point
            p_i = _evaluate_constraint_point(
                eq_i, 
                beam_i, 
                cvxpy_vars_list[beam_i_idx],
                pair_slacks  # Pass local slack mapping
            )
            
            # Beam j point
            p_j = _evaluate_constraint_point(
                eq_j,
                beam_j,
                cvxpy_vars_list[beam_j_idx],
                pair_slacks  # Same slack mapping (they share slacks)
            )
            
            # Add equality constraints (one per dimension)
            constraints.append(p_i[0] == p_j[0])  # X
            constraints.append(p_i[1] == p_j[1])  # Y
            constraints.append(p_i[2] == p_j[2])  # Z
    
    if verbose:
        print(f"   Contact constraints: {len(constraints)}")
        print(f"   Slack variables: {len(slack_vars)}")
    
    # =========================================================================
    # STEP 3: Add identity constraints (morphology only)
    # =========================================================================
    identity_pairs = topology.get('identity_pairs', [])
    
    for beam_i_idx, beam_j_idx in identity_pairs:
        beam_i = beams[beam_i_idx]
        beam_j = beams[beam_j_idx]
        
        # Get morphology keys
        morph_keys_i = beam_i.get_parameters()['morphology_keys']
        morph_keys_j = beam_j.get_parameters()['morphology_keys']
        
        # They must have same morphology structure
        if set(morph_keys_i) != set(morph_keys_j):
            raise ValueError(f"Identity pair ({beam_i_idx}, {beam_j_idx}) has incompatible types")
        
        # Add equality constraints for each morphology parameter
        for key in morph_keys_i:
            constraints.append(
                cvxpy_vars_list[beam_i_idx][key] == cvxpy_vars_list[beam_j_idx][key]
            )
    
    if verbose and identity_pairs:
        print(f"   Identity pairs: {len(identity_pairs)}")
    
    # =========================================================================
    # STEP 4: Add parameter bounds
    # =========================================================================
    for beam_idx, beam in enumerate(beams):
        bounds = beam.get_parameter_bounds()
        vars_dict = cvxpy_vars_list[beam_idx]
        
        for param_name, var in vars_dict.items():
            if param_name in bounds:
                lower, upper = bounds[param_name]
                constraints.append(var >= lower)
                constraints.append(var <= upper)
    
    # =========================================================================
    # STEP 5: Build objective function (stay close to initial values)
    # =========================================================================
    objective_terms = []
    
    for beam_idx, vars_dict in enumerate(cvxpy_vars_list):
        initial_params = initial_params_list[beam_idx]
        
        for param_name, var in vars_dict.items():
            initial_val = initial_params[param_name]
            
            # Squared deviation with max_adjustment clipping
            deviation = var - initial_val
            objective_terms.append(cp.square(deviation))
    
    objective = cp.Minimize(cp.sum(objective_terms))
    
    # =========================================================================
    # STEP 6: Solve
    # =========================================================================
    problem = cp.Problem(objective, constraints)
    
    try:
        problem.solve(solver=cp.CLARABEL, verbose=verbose)
    except Exception as e:
        raise SolverError(f"Solver failed: {e}")
    
    if problem.status not in ['optimal', 'optimal_inaccurate']:
        raise SolverError(f"Problem infeasible or unbounded. Status: {problem.status}")
    
    if verbose:
        print(f"\n✅ Solver converged: {problem.status}")
        print(f"   Objective value: {problem.value:.6f}")
    
    # =========================================================================
    # STEP 7: Update beam parameters
    # =========================================================================
    for beam_idx, beam in enumerate(beams):
        solved_params = {}
        
        for param_name, var in cvxpy_vars_list[beam_idx].items():
            solved_params[param_name] = float(var.value)
        
        beam.set_parameters(solved_params)
        
        if verbose:
            print(f"   Beam {beam_idx}: {type(beam).__name__} updated")
    
    return beams


def _evaluate_constraint_point(eq: ConstraintEquation,
                               beam: BeamBase,
                               cvxpy_vars: Dict,
                               slack_vars: Dict) -> np.ndarray:
    """
    Evaluate a constraint equation to get a 3D point in GLOBAL coordinates.
    
    Uses beam's dual-mode geometry methods.
    
    Args:
        eq: ConstraintEquation with x_expr, y_expr, z_expr
        beam: Beam object
        cvxpy_vars: Dict of CVXPY variables for this beam
        slack_vars: Dict of slack variables for this constraint pair
    
    Returns:
        np.ndarray of CVXPY expressions: [x_global, y_global, z_global]
    """
    params = beam.get_parameters()['values']
    
    # Evaluate expressions in local coordinates
    p_local_x = evaluate_expression(eq.x_expr, params, cvxpy_vars, slack_vars)
    p_local_y = evaluate_expression(eq.y_expr, params, cvxpy_vars, slack_vars)
    p_local_z = evaluate_expression(eq.z_expr, params, cvxpy_vars, slack_vars)
    
    p_local = np.array([p_local_x, p_local_y, p_local_z])
    
    # Transform to global using beam's rotation (theta_z is constant)
    R = beam._rotation_matrix(beam.theta_z)
    p_rotated = R @ p_local
    
    # Translate using CVXPY position variables
    p_global = np.array([
        cvxpy_vars['x'],
        cvxpy_vars['y'],
        cvxpy_vars['z']
    ]) + p_rotated
    
    return p_global