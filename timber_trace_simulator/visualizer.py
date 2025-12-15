# visualizer.py
"""
Interactive 3D visualizer for timber beam debugging.

Usage:
    python visualizer.py
    Then open: http://localhost:5000
"""

from flask import Flask, render_template, jsonify, request
import os
import json
import numpy as np
from object_definitions import BEAM_TYPES, BEAM_NAMES, Pfosten, Pfette
from constraint_solver import solve_constraints

app = Flask(__name__)

FACE_NAMES = ['right', 'left', 'front', 'back', 'top', 'bottom']
OPPOSITE_FACES = {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4}


@app.route('/')
def index():
    """Serve main visualizer page"""
    return render_template('visualizer.html')


@app.route('/api/scenes')
def get_scenes():
    """List all available scenes in training_data"""
    training_dir = 'training_data'
    
    if not os.path.exists(training_dir):
        return jsonify({'scenes': [], 'error': 'No training_data directory found'})
    
    scenes = []
    for item in os.listdir(training_dir):
        scene_path = os.path.join(training_dir, item)
        if os.path.isdir(scene_path) and item.startswith('scene_'):
            scenes.append(item)
    
    scenes.sort()
    return jsonify({'scenes': scenes})


@app.route('/api/scene/<scene_id>')
def get_scene(scene_id):
    """Load scene data"""
    scene_dir = os.path.join('training_data', scene_id)
    metadata_path = os.path.join(scene_dir, 'metadata.json')
    
    if not os.path.exists(metadata_path):
        return jsonify({'error': 'Scene not found'}), 404
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    beams_data = []
    for beam in metadata['beams']:
        params = beam['parameters']
        beam_data = {
            'id': beam['beam_id'],
            'type': beam['beam_type'],
            'position': [params['x'], params['y'], params['z']],
            'rotation': [0, 0, params['theta_z']],
            'dimensions': []
        }
        
        if beam['beam_type'] == 'Pfosten':
            beam_data['dimensions'] = [params['width'], params['depth'], params['height']]
        elif beam['beam_type'] == 'Pfette':
            beam_data['dimensions'] = [params['length'], params['width'], params['height']]
        
        beams_data.append(beam_data)
    
    return jsonify({
        'scene_id': metadata['scene_id'],
        'num_beams': metadata['num_beams'],
        'beams': beams_data
    })


@app.route('/api/generate_beam', methods=['POST'])
def generate_beam():
    """Generate single beam"""
    data = request.json
    beam_type_id = data.get('beam_type', 0)
    
    BeamClass = BEAM_TYPES[beam_type_id]
    beam = BeamClass()
    params = beam.get_parameters()['values']
    
    beam_data = {
        'type': BEAM_NAMES[beam_type_id],
        'position': [params['x'], params['y'], params['z']],
        'rotation': [0, 0, params['theta_z']],
        'dimensions': []
    }
    
    if isinstance(beam, Pfosten):
        beam_data['dimensions'] = [params['width'], params['depth'], params['height']]
    elif isinstance(beam, Pfette):
        beam_data['dimensions'] = [params['length'], params['width'], params['height']]
    
    return jsonify(beam_data)


@app.route('/api/beam_info/<int:beam_type_id>')
def get_beam_info(beam_type_id):
    """Get constraint info"""
    BeamClass = BEAM_TYPES[beam_type_id]
    beam = BeamClass()
    
    constraints_info = {}
    for face_idx, face_name in enumerate(FACE_NAMES):
        try:
            constraints = beam.get_constraints(face_idx)
            if not isinstance(constraints, list):
                constraints = [constraints]
            
            constraints_info[face_name] = {
                'available': True,
                'count': len(constraints),
                'constraints': []
            }
            
            for idx, eq in enumerate(constraints):
                constraint_type = 'point' if eq.slack_count == 0 else ('line' if eq.slack_count == 1 else 'plane')
                constraints_info[face_name]['constraints'].append({
                    'index': idx,
                    'type': constraint_type
                })
        except NotImplementedError:
            constraints_info[face_name] = {'available': False}
    
    return jsonify({
        'beam_type': BEAM_NAMES[beam_type_id],
        'constraints': constraints_info
    })


@app.route('/api/visualize_constraint', methods=['POST'])
def visualize_constraint():
    """Get constraint geometry"""
    data = request.json
    beam_type_id = data.get('beam_type')
    face_idx = data.get('face')
    constraint_idx = data.get('constraint_index', 0)
    
    BeamClass = BEAM_TYPES[beam_type_id]
    beam = BeamClass()
    eq = beam.get_constraints(face_idx, constraint_idx)
    
    constraint_points = []
    
    if eq.slack_count == 0:
        # Point
        point = _eval_constraint_geom(eq, beam, {})
        constraint_points.append(point.tolist())
    elif eq.slack_count == 1:
        # Line
        for t in np.linspace(-1, 1, 20):
            point = _eval_constraint_geom(eq, beam, {'slack_0': t})
            constraint_points.append(point.tolist())
    elif eq.slack_count == 2:
        # Plane
        for u in np.linspace(-0.5, 0.5, 10):
            for v in np.linspace(-0.5, 0.5, 10):
                point = _eval_constraint_geom(eq, beam, {'slack_0': u, 'slack_1': v})
                constraint_points.append(point.tolist())
    
    return jsonify({
        'type': ['point', 'line', 'plane'][eq.slack_count],
        'points': constraint_points
    })


@app.route('/api/check_connection', methods=['POST'])
def check_connection():
    """Generate two beams with constraint"""
    data = request.json
    beam_a_type = data.get('beam_a_type')
    beam_b_type = data.get('beam_b_type')
    face_a = data.get('face_a')
    face_b = data.get('face_b')
    constraint_idx_a = data.get('constraint_idx_a', 0)
    constraint_idx_b = data.get('constraint_idx_b', 0)
    
    BeamA = BEAM_TYPES[beam_a_type]()
    BeamB = BEAM_TYPES[beam_b_type]()
    
    BeamA.x = -1.0
    BeamA.y = 0.0
    BeamA.z = 0.0
    
    BeamB.x = 1.0
    BeamB.y = 0.0
    BeamB.z = 2.0
    
    beams = [BeamA, BeamB]
    
    topology = {
        'connectivity': {
            FACE_NAMES[face_a]: [(0, 1, face_a, face_b, constraint_idx_a, constraint_idx_b)],
            **{name: [] for name in FACE_NAMES if name != FACE_NAMES[face_a]}
        },
        'identity_pairs': []
    }
    
    try:
        solved_beams = solve_constraints(beams, topology, verbose=False)
        
        beams_data = []
        for i, beam in enumerate(solved_beams):
            params = beam.get_parameters()['values']
            beam_data = {
                'id': i,
                'type': type(beam).__name__,
                'position': [params['x'], params['y'], params['z']],
                'rotation': [0, 0, params['theta_z']],
                'dimensions': []
            }
            
            if isinstance(beam, Pfosten):
                beam_data['dimensions'] = [params['width'], params['depth'], params['height']]
            elif isinstance(beam, Pfette):
                beam_data['dimensions'] = [params['length'], params['width'], params['height']]
            
            beams_data.append(beam_data)
        
        eq_a = BeamA.get_constraints(face_a, constraint_idx_a)
        eq_b = BeamB.get_constraints(face_b, constraint_idx_b)
        
        point_a = _eval_constraint_geom(eq_a, solved_beams[0], {})
        point_b = _eval_constraint_geom(eq_b, solved_beams[1], {})
        
        return jsonify({
            'success': True,
            'beams': beams_data,
            'connection_points': {
                'beam_a': point_a.tolist(),
                'beam_b': point_b.tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def _eval_constraint_geom(eq, beam, slack_values):
    """Evaluate constraint to 3D point"""
    from utils.cvxpy_helpers import evaluate_expression
    
    params = beam.get_parameters()['values']
    
    p_local_x = evaluate_expression(eq.x_expr, params, slack_vars=slack_values)
    p_local_y = evaluate_expression(eq.y_expr, params, slack_vars=slack_values)
    p_local_z = evaluate_expression(eq.z_expr, params, slack_vars=slack_values)
    
    p_local = np.array([p_local_x, p_local_y, p_local_z])
    
    R = beam._rotation_matrix(beam.theta_z)
    p_rotated = R @ p_local
    p_global = np.array([params['x'], params['y'], params['z']]) + p_rotated
    
    return p_global


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🎨 TIMBER TRACE - 3D Visualizer")
    print("="*80)
    print("\n👉 Open in browser: http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000)