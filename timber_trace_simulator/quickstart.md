# Quick Start Guide

## Setup (One Time)

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Every Time You Work

```powershell
# Activate virtual environment (you should see (venv) in prompt)
.\venv\Scripts\Activate.ps1
```

## Test the System

```powershell
# Run validation tests
python test_system.py
```

Expected output:
```
✓ Created 3 beams
✓ Topology defined: 2 contact constraints, 1 identity pair
✓ Constraint solver converged
✓ Contact constraints satisfied (< 1mm error)
✓ Identity constraints satisfied
ALL TESTS PASSED ✓
```

## Generate Dataset

```powershell
# Generate 10 scenes (quick test)
python generate_dataset.py --num_scenes 10

# Generate 50 scenes (default)
python generate_dataset.py

# Generate 100 scenes with custom output directory
python generate_dataset.py --num_scenes 100 --output_dir my_dataset

# Show detailed solver output
python generate_dataset.py --num_scenes 10 --verbose
```

## Check Results

After generation, you'll find:

```
training_data/
├── scene_0000/
│   ├── metadata.json    # Parameters and connectivity
│   ├── beam_00.stl      # Post 1 mesh
│   ├── beam_01.stl      # Post 2 mesh
│   └── beam_02.stl      # Beam mesh
├── scene_0001/
│   └── ...
└── index.json           # Dataset summary
```

## Visualize Results

```powershell
# Launch interactive visualizer
python visualizer.py
```

**Visualizer Features:**

**Scene Mode** (view generated structures):
- Click "Select Scene" button to cycle through scenes
- See all beams in 3D with different colors
- Rotate view with mouse

**Beam Mode** (debug individual beams):
- Click "Beam Type" to cycle through Pfosten/Pfette
- Click "Generate New Beam" for random instances
- Click "Face" to cycle through constraint faces
- Click "Index" to view different constraints on same face
- See constraint geometry overlaid (red points/lines/planes)
- Read constraint expressions in info panel

**Tip**: Use Beam Mode to verify each beam type's constraints are correctly implemented before generating full datasets.

## Viewing STL Files

Use any 3D viewer:
- **Online**: [3D Viewer Online](https://3dviewer.net/)
- **Windows**: 3D Builder (built-in) or MeshLab
- **Cross-platform**: Blender, FreeCAD

## Common Issues

**Problem**: `Activate.ps1` blocked by execution policy  
**Fix**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Problem**: build123d fails to install  
**Fix**: Continue without it - you'll see warnings but generation will work

**Problem**: Solver fails on some scenes  
**Fix**: Normal - check `training_data/failed_scenes.json` for details

## Next Steps

1. ✅ Run `test_system.py` to validate
2. ✅ Generate small dataset (10 scenes)
3. ✅ Inspect a few scenes visually
4. 🔄 Generate full dataset (50-1000 scenes)
5. 🔄 Train ML model (separate phase)

## Deactivate When Done

```powershell
deactivate
```