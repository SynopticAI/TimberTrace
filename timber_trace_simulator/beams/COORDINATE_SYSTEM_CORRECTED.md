# ✅ CORRECTED: Template Coordinate System

## The Right Way (Position-Centric, Master File Approach)

### All Templates = Same Global Coordinate System

**Origin (0,0,0):** Roof centerline at ground level

**Every template is already positioned correctly:**

```
Master_Pfettendach.FCStd contains all beams in final positions:

Z (height)
↑
│     Firstpfette (x=0, z=Roof_Height)
│    ═══════════════════════════
│           /              \
│         /  Sparren        \
│       /   (pitched)        \
│     /                        \
│   ════ Mittelpfette ════════════  (x=±Mittel_X, z=Mittel_Height)
│    │                        │
│    │  Stuhlpfosten         │
│    │  (x=0)                │
│    │                        │
└────┴══════════════════════┴────→ Y (longitudinal)
    Fußpfette (x=±Half_Width, z=0)

ALL beams at their correct X and Z positions!
```

### Extracting Templates

**When you extract Firstpfette.FCStd from master:**
1. Hide all other beams
2. Keep Firstpfette at x=0, z=Roof_Height
3. Save as Firstpfette.FCStd

**The template IS the master file coordinates!**

### Python Transformations (Minimal)

```python
# Example: Firstpfette
firstpfette = Firstpfette(
    beam_id=1,
    position=np.array([0, y_position, 0]),  # ✅ Just Y translation!
    orientation=Rotation.identity(),         # ✅ No rotation!
    length=10.0,
    cross_section=(100, 240),
    mortise_count=4,
    mortise_spacing=3.0,
)

# Template already at:
# - x = 0 (centerline)
# - z = Roof_Height
# Python just slides it along Y-axis!
```

### For Left/Right Beams (Mirroring)

```python
# Right Mittelpfette template: Already at +Mittel_X
mittelpfette_R = Mittelpfette(...)
mesh_R = generate_from_template("Mittelpfette_Right.FCStd", ...)
mesh_R.apply_translation([0, y_pos, 0])

# Left Mittelpfette: Use mirrored template at -Mittel_X
mittelpfette_L = Mittelpfette(...)
mesh_L = generate_from_template("Mittelpfette_Left.FCStd", ...)  # Pre-mirrored!
mesh_L.apply_translation([0, y_pos, 0])
```

Or just mirror the mesh:
```python
mesh_L = mesh_R.copy()
mesh_L.apply_scale([-1, 1, 1])  # Flip X
```

## Why This Works Perfectly

✅ **Alignment guaranteed**: Beams designed together in master file  
✅ **Shared variables**: Templates reference same Roof_Height, Mittel_X, etc.  
✅ **Visual verification**: See complete roof in FreeCAD before extracting  
✅ **Minimal Python code**: Just Y translation, maybe mirroring  
✅ **No rotation bugs**: Beams already at correct angles  
✅ **AI can average**: Shared variables ensure consistency  

## ❌ Wrong Approach (What We DON'T Do)

```python
# ❌ Don't model beams in "local coordinates" at origin
# ❌ Don't rotate beams to world orientation
# ❌ Don't calculate complex transformation matrices

# This was the OLD approach - error-prone!
mesh = create_box_at_origin()
mesh.rotate(pitch_angle)
mesh.translate([x, y, z])  # Easy to get wrong!
```

## Master File Workflow

1. **Design in FreeCAD:**
   - Create Master_Pfettendach.FCStd
   - Model ALL beams in correct positions
   - Use shared spreadsheet variables
   - Verify alignment visually

2. **Extract Templates:**
   - Firstpfette.FCStd: Hide others, keep at z=Roof_Height
   - Mittelpfette_Right.FCStd: Hide others, keep at x=+Mittel_X
   - Mittelpfette_Left.FCStd: Mirror right version
   - Stuhlpfosten.FCStd: Hide others, keep at x=0, z=0
   - Sparren_Right.FCStd: Hide others, keep pitched right
   - Sparren_Left.FCStd: Mirror right version

3. **Python Usage:**
   ```python
   # Load template (already positioned)
   mesh = generate_mesh_from_template(
       "Firstpfette.FCStd",
       {'length': 10000, 'mortise_count': 4, ...}
   )
   
   # Just translate along Y
   mesh.apply_translation([0, y_position, 0])
   
   # Done! No rotation needed.
   ```

---

**This is the correct approach!** Templates ARE the master file.
