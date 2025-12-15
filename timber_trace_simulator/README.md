# Timber Trace Simulator

Constraint-based data generator for timber structure reconstruction AI training.

## Quick Start

```powershell
# Setup (one time)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Test system
python test_system.py

# Generate dataset
python generate_dataset.py --num_scenes 10

# Visualize results
python visualizer.py
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## Architecture

**Constraint-Based Generation**: Unlike traditional procedural generators that rely on perfect manual placement, this system defines rough topology and uses quadratic programming to enforce physical validity.

### Key Components

- **`object_definitions.py`**: Beam classes with dual-mode geometry (numerical + symbolic)
- **`constraint_solver.py`**: CVXPY-based QP solver for contact/identity constraints
- **`structure_blueprints/`**: Topology providers (define which beams connect)
- **`scene_generator.py`**: Architecture-agnostic orchestrator
- **`visualizer.py`**: Interactive 3D debugger

### Workflow

```
Blueprint (rough params + topology)
    ↓
Perturbations (create variation)
    ↓
Constraint Solver (enforce validity)
    ↓
Mesh Export (STL + metadata)
```

## Features

✅ **Physically Valid**: All connections guaranteed by constraint solver  
✅ **Parametric**: Single source of truth for geometry  
✅ **Debuggable**: Interactive visualizer for constraint inspection  
✅ **Modular**: Easy to add new beam types  
✅ **Reproducible**: Virtual environment + requirements.txt  

## Current Status

**Implemented**:
- 2 beam types (Pfosten, Pfette)
- Point and line constraints
- Post-and-beam test structure
- Interactive visualizer
- Dataset export (STL + JSON)

**Next Steps**:
- Add remaining beam types (4 more)
- Implement plane constraints
- Create Pfettendach blueprint
- Scale to 1000+ scenes

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)**: Essential commands and workflow
- **[SETUP.md](SETUP.md)**: Detailed environment setup (Windows/Linux)
- **[Object_Centered_Framework_spec.md](../Object_Centered_Framework_spec.md)**: Full system specification

## Project Structure

```
timber_trace_simulator/
├── object_definitions.py       # Beam classes (dual-mode geometry)
├── constraint_solver.py        # QP solver core
├── scene_generator.py          # Orchestrator
├── visualizer.py              # Interactive 3D viewer
├── generate_dataset.py         # CLI entry point
├── test_system.py             # Validation script
├── structure_blueprints/       # Topology definitions
│   ├── __init__.py
│   └── simple_structures.py   # Test cases
├── utils/                      # Helper functions
│   ├── __init__.py
│   └── cvxpy_helpers.py       # Slack variable parsing
└── training_data/             # Generated datasets (gitignored)
    └── scene_XXXX/
        ├── metadata.json
        └── beam_XX.stl
```

## Contributing

When adding new beam types:

1. Add class to `object_definitions.py`
2. Implement `get_constraints()` for each face
3. Test with visualizer: `python visualizer.py`
4. Create blueprint in `structure_blueprints/`
5. Validate with `test_system.py`

Use the visualizer's **Beam Mode** to debug constraints before integration.

## License

Internal research project - not for public distribution.