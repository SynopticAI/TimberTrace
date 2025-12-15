# utils/cvxpy_helpers.py
"""
Utilities for parsing constraint equations and building CVXPY problems.
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Set


def extract_slack_tokens(constraint_equations: List['ConstraintEquation']) -> Set[str]:
    """
    Parse all constraint equations and extract unique slack variable tokens.
    
    Args:
        constraint_equations: List of ConstraintEquation objects
    
    Returns:
        Set of unique slack tokens (e.g., {'slack_1', 'slack_2'})
    
    Example:
        equations = [
            ConstraintEquation("slack_1", "0", "self.height", 1),
            ConstraintEquation("0", "slack_1", "slack_2", 2)
        ]
        -> {'slack_1', 'slack_2'}
    """
    slack_pattern = re.compile(r'slack_\d+')
    all_tokens = set()
    
    for eq in constraint_equations:
        # Search all three expressions
        all_tokens.update(slack_pattern.findall(eq.x_expr))
        all_tokens.update(slack_pattern.findall(eq.y_expr))
        all_tokens.update(slack_pattern.findall(eq.z_expr))
    
    return all_tokens


def evaluate_expression(expr_str: str, 
                       beam_params: Dict[str, float],
                       cvxpy_vars: Dict[str, 'cvxpy.Variable'] = None,
                       slack_vars: Dict[str, float] = None):
    """
    Evaluate a constraint expression string with either numerical or CVXPY values.
    
    Args:
        expr_str: Expression like "self.height" or "slack_0" or "0"
        beam_params: Dictionary of beam parameters (e.g., {'height': 2.2, 'x': 1.5})
        cvxpy_vars: Optional dict of CVXPY variables for parameters
        slack_vars: Optional dict of slack values (can be float OR cvxpy.Variable)
    
    Returns:
        Either a float (numerical mode) or cvxpy expression (symbolic mode)
    
    Examples:
        # Numerical mode
        evaluate_expression("self.height", {'height': 2.2}) -> 2.2
        evaluate_expression("slack_0", {}, slack_vars={'slack_0': 1.5}) -> 1.5
        
        # CVXPY mode
        evaluate_expression("slack_0", {}, slack_vars={'slack_0': cp.Variable()}) 
        -> cvxpy.Variable object
    """
    # Replace self.* with values from beam_params or cvxpy_vars
    result_expr = expr_str
    
    # Handle self.parameter references
    for param_name, param_value in beam_params.items():
        pattern = f'self.{param_name}'
        if pattern in result_expr:
            if cvxpy_vars and param_name in cvxpy_vars:
                # CVXPY mode: use variable
                result_expr = result_expr.replace(pattern, f'cvxpy_vars["{param_name}"]')
            else:
                # Numerical mode: use value
                result_expr = result_expr.replace(pattern, str(param_value))
    
    # Handle slack variables - check if they're in the expression
    if slack_vars:
        for slack_name, slack_value in slack_vars.items():
            if slack_name in result_expr:
                # For CVXPY mode, wrap in dict lookup; for numerical, use direct value
                if hasattr(slack_value, '__module__') and 'cvxpy' in str(type(slack_value)):
                    # CVXPY variable
                    result_expr = result_expr.replace(slack_name, f'slack_vars["{slack_name}"]')
                else:
                    # Numerical value
                    result_expr = result_expr.replace(slack_name, str(slack_value))
    
    # Evaluate the expression
    # Create evaluation context with numpy for math operations
    eval_context = {
        'cvxpy_vars': cvxpy_vars or {},
        'slack_vars': slack_vars or {},
        'np': np
    }
    
    try:
        result = eval(result_expr, {"__builtins__": {}}, eval_context)
        return result
    except Exception as e:
        raise ValueError(f"Failed to evaluate expression '{expr_str}': {e}\nProcessed as: '{result_expr}'")


def transform_local_to_global(p_local: np.ndarray, 
                              beam_params: Dict[str, float],
                              rotation_matrix: np.ndarray) -> np.ndarray:
    """
    Transform a point from local to global coordinates.
    
    Args:
        p_local: [x, y, z] in local coordinates (can be CVXPY expressions)
        beam_params: Must contain 'x', 'y', 'z' position
        rotation_matrix: 3x3 rotation matrix (numerical)
    
    Returns:
        [x, y, z] in global coordinates
    """
    # Rotate
    p_rotated = rotation_matrix @ p_local
    
    # Translate
    translation = np.array([beam_params['x'], beam_params['y'], beam_params['z']])
    p_global = translation + p_rotated
    
    return p_global