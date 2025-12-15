# Adding New Beam Types - Step-by-Step Guide

This guide walks you through adding a new beam type to the system.

## Step 1: Define the Beam Class

In `object_definitions.py`, create a new class inheriting from `BeamBase`:

```python
class MyNewBeam(BeamBase):
    """
    Description of beam type.
    Default dimensions in meters.
    """
    
    def __init__(self, length: float = 5.0, width: float = 0.15, height: float = 0.20):
        super().__init__()
        # Morphology parameters (indices 4+)
        self.length = length
        self.width = width
        self.height = height
```

## Step 2: Implement get_constraints()

Define constraint equations for each face you plan to use:

```python
    def get_constraints(self, direction: int, index: Optional[int] = None):
        """
        Direction mapping:
          0=Right, 1=Left, 2=Front, 3=Back, 4=Top, 5=Bottom
        """
        if direction == 4:  # Top face
            # Example: Center point at top
            constraints = [ConstraintEquation("0", "0", "self.height", slack_count=0)]
            return constraints[0] if index == 0 else constraints
        
        elif direction == 5:  # Bottom face
            # Example: Line along length
            constraints = [ConstraintEquation("slack_0", "0", "0", slack_count=1)]
            return constraints[0] if index == 0 else constraints
        
        else:
            raise NotImplementedError(f"MyNewBeam: Face {direction} not implemented")
```

### Constraint Types (by slack_count)

**Point** (slack_count=0):
```python
ConstraintEquation("0", "0", "self.height", slack_count=0)
# Center point at height
```

**Line** (slack_count=1):
```python
ConstraintEquation("slack_0", "0", "self.height", slack_count=1)
# Line along X-axis at height
```

**Plane** (slack_count=2):
```python
ConstraintEquation("slack_0", "slack_1", "self.height", slack_count=2)
# Plane at height (spans X and Y)
```

### Coordinate System

Local coordinates (before rotation):
- X: Length direction (for horizontal beams) or width (for posts)
- Y: Width/depth direction
- Z: Height (always vertical)

## Step 3: Implement get_parameters()

```python
    def get_parameters(self) -> Dict:
        return {
            'values': {
                'theta_z': self.theta_z,
                'x': self.x, 'y': self.y, 'z': self.z,
                'length': self.length, 
                'width': self.width, 
                'height': self.height,
            },
            'metadata': {
                'theta_z': {'default': 0.0, 'ai_scale': 1.0},
                'x': {'default': 0.0, 'ai_scale': 1.0},
                'y': {'default': 0.0, 'ai_scale': 1.0},
                'z': {'default': 0.0, 'ai_scale': 1.0},
                'length': {'default': 5.0, 'ai_scale': 1.0},
                'width': {'default': 0.15, 'ai_scale': 1.0},
                'height': {'default': 0.20, 'ai_scale': 1.0},
            },
            'morphology_keys': ['length', 'width', 'height'],
            'pose_keys': ['theta_z', 'x', 'y', 'z']
        }
```

## Step 4: Implement get_parameter_bounds()

```python
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'x': (-50.0, 50.0),
            'y': (-50.0, 50.0),
            'z': (0.0, 20.0),
            'theta_z': (0, 2*np.pi),
            'length': (1.0, 15.0),  # 1m to 15m
            'width': (0.08, 0.3),    # 8cm to 30cm
            'height': (0.1, 0.5),    # 10cm to 50cm
        }
```

## Step 5: Implement get_model()

```python
    def get_model(self) -> 'Part':
        if not BUILD123D_AVAILABLE:
            raise ImportError("build123d required")
        
        # Create box
        box = Box(self.length, self.width, self.height,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # Apply rotation and translation
        loc = Location((self.x, self.y, self.z)) * Rotation(0, 0, np.degrees(self.theta_z))
        
        return box.move(loc)
```

## Step 6: Register the Beam Type

At the bottom of `object_definitions.py`:

```python
BEAM_TYPES = {
    0: Pfosten, 
    1: Pfette,
    2: MyNewBeam  # Add here
}

BEAM_NAMES = {
    0: "Pfosten", 
    1: "Pfette",
    2: "MyNewBeam"  # Add here
}
```

## Step 7: Debug with Visualizer

```powershell
python visualizer.py
```

1. Switch to **Beam Mode**
2. Click **Beam Type** until you see "MyNewBeam"
3. Click **Generate New Beam** several times
4. Cycle through **Face** options (0-5)
5. For each face, check the constraint visualization

**What to check:**
- ✅ Constraint geometry appears in correct location
- ✅ Point constraints show as red sphere
- ✅ Line constraints show as red line
- ✅ Plane constraints show as red point grid
- ✅ No NotImplementedError for faces you need

## Step 8: Create Test Blueprint

In `structure_blueprints/simple_structures.py`, add a test case:

```python
def test_my_new_beam(seed=None):
    """Test structure using MyNewBeam"""
    from object_definitions import MyNewBeam, Pfosten
    
    # Create test structure
    beam1 = MyNewBeam()
    beam1.x = 0.0
    beam1.z = 2.0
    
    post = Pfosten()
    post.x = 0.0
    post.z = 0.0
    
    beams = [post, beam1]
    
    # Define connectivity
    topology = {
        'connectivity': {
            'top': [(0, 1, 4, 5, 0, 0)],  # Post top -> Beam bottom
            'bottom': [], 'left': [], 'right': [], 'front': [], 'back': []
        },
        'identity_pairs': []
    }
    
    return beams, topology
```

## Step 9: Test with Constraint Solver

```powershell
python test_system.py
```

Modify `test_system.py` to use your new blueprint temporarily to verify the solver works.

## Step 10: Generate Test Dataset

```powershell
python generate_dataset.py --num_scenes 5 --verbose
```

Check `training_data/` for:
- ✅ Scenes generated without errors
- ✅ STL files look correct
- ✅ Contact constraints satisfied (< 1mm error in logs)

## Common Issues

### Issue: "Failed to evaluate expression"
**Cause**: Slack variable mismatch  
**Fix**: Make sure you use `slack_0`, `slack_1`, etc. (zero-indexed)

### Issue: Constraint appears in wrong location
**Cause**: Forgot to account for rotation  
**Fix**: Constraint equations are in LOCAL coords - they're auto-transformed to global

### Issue: Solver says "infeasible"
**Cause**: Constraints are contradictory  
**Fix**: Check your constraint equations - they might be over-constrained

### Issue: Beam geometry looks wrong
**Cause**: Box dimensions don't match parameters  
**Fix**: Make sure `get_model()` uses same dimensions as `get_parameters()`

## Best Practices

1. **Start simple**: Implement one face at a time
2. **Use visualizer**: Debug constraints BEFORE testing solver
3. **Check bounds**: Make sure parameter bounds are realistic
4. **Test variations**: Generate multiple random instances
5. **Verify alignment**: Local coordinate system should match get_model()

## Example: Complete Beam Implementation

See `Pfosten` and `Pfette` classes in `object_definitions.py` for reference implementations.

**Pfosten** (vertical post):
- Top face: Point constraint (center of top)
- Simple box geometry
- Good starting point for learning

**Pfette** (horizontal beam):
- Bottom face: Line constraint (along length)
- Rotated by theta_z
- Shows how rotation works