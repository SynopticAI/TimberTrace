# Beam Design Conventions - FreeCAD Templates

## Overview

This document defines the **positioning conventions** and **shared parameterization strategy** for all timber beam FreeCAD templates in the TimberTrace simulator.

The goal is **perfect alignment by design** - beams share common variables and reference the same coordinate system, ensuring they fit together automatically.

---

## Core Design Philosophy

### 1. Master Roof First, Extract Templates Second

**Workflow:**
1. Design complete parametric Pfettendach roof in a single FreeCAD file (`Master_Pfettendach.FCStd`)
2. All beams reference the **same shared variables** (e.g., `Roof_Height`, `Roof_Pitch`)
3. All beams use the **same origin convention** (roof centerline at ground)
4. Extract individual templates by deleting other components, keeping shared variables
5. Perfect alignment is guaranteed by shared design

**Benefits:**
- Visual verification of alignment in master file
- Shared variables prevent dimensional conflicts
- Easy to update entire roof by changing master parameters

### 2. Position-Centric Parameterization

Parameters describe **where beams are positioned**, not manufacturing details.

**Example:** `Mittelpfette_BottomHeight`
- Describes: Vertical position of Mittelpfette's bottom surface from ground
- Also equals: `Stuhlpfosten_Height_NoTenon` (post height without tenon)
- Ensures: Perfect alignment between post top and Pfette bottom

**Why this works:**
- AI can average shared variables across predictions
- Ensures consistency (if AI predicts different roof heights, average them)
- Reduces degrees of freedom (fewer independent variables to predict)

---

## Global Coordinate System

### Origin Definition

**ALL beam templates share this origin convention:**

```
Origin (0, 0, 0) = Roof centerline at ground level

        Z ↑ (vertical - height)
          |
          |    Firstpfette
          |   /
          |  /
          | / ← Sparren
          |/_____ Y (longitudinal - along roof length)
         /|
        / |
       /  |
      X   ← (transverse - roof width)
     (half-span)
```

**Coordinate Axes:**
- **X-axis**: Transverse (across roof width, from centerline)
- **Y-axis**: Longitudinal (along roof length)
- **Z-axis**: Vertical (height from ground)

### Individual Beam Positions in Templates

Each beam is already at its correct height and transverse position:

| Beam Type | Template Position | Notes |
|-----------|-------------------|-------|
| **Stuhlpfosten** | x=0, z=0 to Stuhl_Height | Centerline, on ground |
| **Firstpfette** | x=0, z=Roof_Height | Centerline, at ridge |
| **Mittelpfette** | x=±Mittel_X, z=Mittel_Height | Offset from center, mid-height |
| **Fußpfette** | x=±Half_Width, z=0 | At eaves, on ground |
| **Sparren** | x=±Half_Width, z=0, pitched | At eaves, angled toward ridge |

**Templates extend along Y-axis (longitudinal) for their length.**

---

## FreeCAD Template Conventions

### Templates Use GLOBAL Coordinates (Not Local)

**CRITICAL: All templates share THE SAME coordinate system = centerline at ground**

Templates are NOT in "local coordinates" - they're already positioned correctly in the master file coordinate system.

**Example positions in templates:**
```
Firstpfette:   Already at z = Roof_Height, x = 0
Mittelpfette:  Already at z = Mittelpfette_Height, x = ±Mittel_X  
Stuhlpfosten:  Already at z = 0 extending to z = Stuhlpfosten_Height, x = 0
Sparren:       Already at correct pitch angle from eaves
```

When you extract a template from the master file, you just hide other beams - the coordinates stay the same!

### Parameter Units

**FreeCAD spreadsheet uses:**
- **Lengths**: millimeters (mm)
- **Angles**: degrees (°)

**Python beam classes store:**
- **Lengths**: meters (m) for position, cross-sections in mm
- **Angles**: degrees (°)

**Conversion in `get_freecad_parameters()`:**
```python
'length': self.length * 1000.0,  # meters → mm
'width': self.width,              # already in mm
'pitch_angle': self.pitch_angle   # already in degrees
```

---

## Shared Variables Strategy

### Roof-Level Parameters (Shared Across All Beams)

These variables are **identical in all templates**, extracted from master file:

```
Roof_Pitch         # degrees (e.g., 45)
Roof_Width         # mm (building width)
Roof_Length        # mm (building length)
Roof_Height        # mm (ridge height from ground)
Sparren_Spacing    # mm (distance between rafters)
Support_Spacing    # mm (distance between Stuhlpfosten)
```

### Position-Based Shared Variables

Variables that ensure alignment between connected beams:

```
Mittelpfette_BottomHeight  = Stuhlpfosten_Middle_Height_NoTenon
Firstpfette_BottomHeight   = Stuhlpfosten_Ridge_Height_NoTenon

Sparren_Notch1_Height      = Fusspfette_TopHeight
Sparren_Notch2_Height      = Mittelpfette_TopHeight
Sparren_Notch3_Height      = Firstpfette_TopHeight
```

**How AI uses this:**
If the AI predicts different values for `Firstpfette_BottomHeight` and `Stuhlpfosten_Ridge_Height_NoTenon`, we average them to ensure the post reaches the Pfette.

---

## Beam-Specific Templates

### Stuhlpfosten.FCStd

**Parameters:**
```
length         # Total post height (mm) - WITHOUT tenon
width          # Cross-section width (mm)
height         # Cross-section height (mm) [same as width for square]
tenon_length   # Tenon protrusion at top (mm)
```

**Calculated in FreeCAD:**
```
tenon_width = width * 0.33
tenon_depth = height * 0.33
total_height_with_tenon = length + tenon_length
```

**Origin:** Bottom center
**Extends:** +Z from 0 to `length`, tenon from `length` to `length + tenon_length`

---

### Firstpfette.FCStd

**Parameters:**
```
length            # Total beam length (mm)
width             # Cross-section width (mm)
height            # Cross-section height (mm)
mortise_count     # Number of mortises (= number of Stuhlpfosten)
mortise_spacing   # Distance between mortises (mm)
mortise_width     # Mortise width (mm)
mortise_depth     # Mortise penetration depth (mm)
```

**Mortise Pattern:**
- FreeCAD creates linear pattern on bottom face
- First mortise at `mortise_spacing/2` from origin
- Pattern continues along +Z direction

**Origin:** One end at centerline
**Extends:** +Z from 0 to `length`

---

### Mittelpfette.FCStd

**Parameters:** Same as Firstpfette

**Origin:** One end at centerline, offset in ±X
**Extends:** +Z from 0 to `length`

---

### Fußpfette.FCStd

**Parameters:**
```
length   # Total beam length (mm)
width    # Cross-section width (mm)
height   # Cross-section height (mm)
```

**No joints** - simple rectangular beam

**Origin:** One end at centerline, offset in ±X  
**Extends:** +Z from 0 to `length`

---

### Pfettendach_Sparren.FCStd

**Parameters:**
```
length               # Total rafter length (mm)
width                # Cross-section width (mm)
height               # Cross-section height (mm)
pitch_angle          # Roof pitch (degrees)

notch1_enabled       # 1 or 0
notch1_z_normalized  # Position 0.0-1.0 along beam
notch1_depth         # Cut depth (mm)
notch1_angle         # Angle of cut (degrees, usually = pitch_angle)

notch2_enabled       # ...up to notch10_enabled
...
```

**Notch Logic in FreeCAD:**
```
notch_z_actual = length * notch_z_normalized

IF notch_enabled == 1:
    Create angled notch at notch_z_actual
    Rotate cutting tool by notch_angle
    Cut into bottom face
```

**Origin:** Eaves end (lower end)  
**Extends:** +Z from 0 to `length` toward ridge

---

## Python Generator Integration

### How Generators Use Templates

**Templates are already positioned correctly - Python only translates along Y-axis!**

```python
# Generator calculates shared parameters
ridge_height = building_width / 2 * tan(pitch_angle)
num_supports = int(building_length / support_spacing)

# Create Firstpfette - template already at z=ridge_height, x=0
firstpfette = Firstpfette(
    beam_id=1,
    position=np.array([0, y_position, 0]),  # Just Y translation!
    orientation=Rotation.identity(),         # No rotation needed!
    length=building_length,
    cross_section=(100, 240),
    mortise_count=num_supports,
    mortise_spacing=support_spacing,
)

# FreeCAD loads template (already at correct height/position)
# Python just translates along Y and mirrors for left/right
mesh = firstpfette.get_mesh()
```

### Transformations Are Minimal

**Python transformations:**
1. **Translate along Y**: Position beam longitudinally
2. **Mirror for left/right**: Copy and flip across x=0

**NO rotation needed** - beams already at correct angles in template!
**NO vertical positioning** - beams already at correct height in template!

### Symmetry and Mirroring

**Left/Right beams: Just flip X coordinate**
```python
# Right Mittelpfette (template already at +Mittel_X)
mittelpfette_R = Mittelpfette(
    position=np.array([0, y_pos, 0]),  # Load at template position
    orientation=Rotation.identity(),
    ...
)

# Left Mittelpfette (mirror template across x=0)
mittelpfette_L = Mittelpfette(
    position=np.array([0, y_pos, 0]),
    orientation=Rotation.identity(),
    mirror_x=True,  # Just flip X in template
    ...
)
```

**Sparren: Templates already pitched, just mirror**
- Right template: Already at +X, pitched right
- Left template: Mirror of right template (pitched left)
- Python only sets Y position

---

## FreeCAD File Organization

```
freecad_templates/
├── Master_Pfettendach.FCStd          # Complete roof design
│
├── Stuhlpfosten.FCStd                # Extracted templates
├── Firstpfette.FCStd
├── Mittelpfette.FCStd
├── Fusspfette.FCStd
├── Pfettendach_Sparren.FCStd
│
└── README.md                         # This file
```

---

## Validation Checklist

When creating/modifying templates:

- [ ] Origin at correct reference point (centerline at ground or offset)
- [ ] Beam extends in +Z from 0 to `length`
- [ ] All dimensions use shared variables where applicable
- [ ] Mortise/notch patterns use normalized positions (0-1)
- [ ] Tenon/mortise dimensions calculated as formulas (e.g., `width * 0.33`)
- [ ] Template validated in master roof file for alignment
- [ ] Exported template contains only relevant objects and variables

---

## Next Steps

1. **Create Master_Pfettendach.FCStd** with all beams aligned
2. **Extract individual templates** by copying and deleting components
3. **Test each template** with Python `get_freecad_parameters()`
4. **Verify alignment** by generating full roof and visual inspection

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-15