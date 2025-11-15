# FreeCAD Template Coordinate Reference

## CRITICAL: Templates Share Global Coordinates

**All templates use THE SAME coordinate system:**
- Origin (0,0,0) = Roof centerline at ground
- Beams already positioned at correct height (Z)
- Beams already positioned transversely (X)
- Beams extend longitudinally along Y-axis

**Master file workflow:**
1. Model complete roof with all beams in correct positions
2. Extract templates by hiding other beams
3. Templates retain their global positions from master file

**Python does minimal transformation:**
- Translates along Y (longitudinal position)
- Mirrors across x=0 for left/right copies
- NO rotation, NO vertical repositioning needed!

---

## Visual Guide - All Beams in Shared Coordinates

### Global Coordinate System (All Templates)

```
        Z ↑ (Vertical - Height)
          |
          |        Firstpfette (at ridge)
          |       ============
    Ridge |      /
  Height  |     /  Sparren
          |    /   (pitched)
          |   /
          |  /
    Mittel|============ Mittelpfette
   Height |  |
          |  | Stuhlpfosten
          |  | (vertical)
    Ground|==|========== Fußpfette
        0 +--+-------------+----> Y (Longitudinal)
         /   
        /    
       /     
      X (Transverse)
   (half-span)

Origin (0,0,0) = Roof centerline at ground level
```

---

## Individual Beam Template Origins

### 1. Stuhlpfosten.FCStd
```
Template modeled at GLOBAL position:
x = 0 (centerline)
z = 0 (ground) extending to z = Stuhl_Height

      ↑ Z
      |
Roof  |  (other beams here)
      |
      |  ┌─┐ ← Tenon at z = Stuhl_Height
      |  └┬┘
      |   │
      |   │  Post body
      |   │  
      |   │
  0   └───┴──── Ground (origin)
      
Template is already in final position!
Python only translates along Y-axis.
```

**Python usage:**
```python
position = np.array([0, y_position, 0])  # Just Y translation!
orientation = Rotation.identity()        # No rotation!
# Template already at x=0, z=0
```

---

### 2. Firstpfette.FCStd
```
Template modeled at GLOBAL position:
x = 0 (centerline)
z = Roof_Height (ridge)
Extends along Y-axis

      Z
      ↑
      |  ════════════════ ← Firstpfette at z=Roof_Height
      |      Mortises on bottom face
      |
      |
  0   └─────────────────→ Y (longitudinal)

Template is already at ridge height!
Python only translates along Y-axis.
```

**Python usage:**
```python
position = np.array([0, y_position, 0])  # Just Y translation!
orientation = Rotation.identity()        # No rotation!
# Template already at x=0, z=Roof_Height
```

---

### 3. Mittelpfette.FCStd
```
Template modeled at GLOBAL position:
x = ±Mittel_X (offset from centerline)
z = Mittel_Height
Extends along Y-axis

      Z
      |
      |  ════════════════ ← Mittelpfette at z=Mittel_Height
      |
      |
  0   └─────────────────→ Y

Two templates: Right (+X) and Left (-X) mirrored
Python only translates along Y-axis.
```

**Python usage:**
```python
# Template already at x=±Mittel_X, z=Mittel_Height
position = np.array([0, y_position, 0])  # Just Y!
orientation = Rotation.identity()
```

---

### 4. Fußpfette.FCStd
```
Template modeled at GLOBAL position:
x = ±Half_Width (at eaves)
z = 0 (ground)
Extends along Y-axis

      Z
      |
      |
      |
  0   ════════════════ ← Fußpfette at z=0
      └─────────────────→ Y

Simple beam, no joints
```

**Python usage:**
```python
position = np.array([0, y_position, 0])  # Just Y!
orientation = Rotation.identity()
```

---

### 5. Pfettendach_Sparren.FCStd
```
Template modeled at GLOBAL position:
x = ±Half_Width (at eaves)
z = 0 (ground)
Already pitched at Roof_Pitch angle
Extends toward ridge

          Z
          ↑        /
          |      /  ← Sparren (already pitched)
          |    /
          |  /  Notches on bottom
          |/
      0   •──────────────→ Y
       Eaves

Template is already pitched!
Two templates: Right and Left (mirrored)
Python only translates along Y-axis.
```

**Python usage:**
```python
# Template already at x=±Half_Width, z=0, pitched
position = np.array([0, y_position, 0])  # Just Y!
orientation = Rotation.identity()        # Already pitched!
```

---

## Key FreeCAD Modeling Tips

### 1. Starting a New Template

```
In FreeCAD:
1. Create new document
2. Insert Spreadsheet (Insert → Spreadsheet)
3. Add parameters with aliases (right-click cell → Properties → Alias)
4. Create PartDesign Body
5. Start sketch at XY plane (Z=0)
6. Reference spreadsheet cells in dimensions (e.g., =Spreadsheet.length)
```

### 2. Spreadsheet Aliases (Example: Stuhlpfosten)

```
Cell  | Alias        | Value    | Unit
------+--------------+----------+------
A2    | length       | 2500     | mm
A3    | width        | 120      | mm
A4    | height       | 120      | mm
A5    | tenon_length | 100      | mm
A6    | tenon_width  | =width*0.33  | (formula)
A7    | tenon_depth  | =height*0.33 | (formula)
```

### 3. Using Parameters in Sketches

When dimensioning:
- Instead of typing "120", type: `Spreadsheet.width`
- FreeCAD auto-updates when spreadsheet changes

### 4. Creating Mortise Linear Pattern (Pfetten)

```
1. Create single mortise pocket as PartDesign::Pocket
2. Select the pocket in tree
3. PartDesign → Create Linear Pattern
4. Direction: Along Z-axis
5. Length: =Spreadsheet.mortise_spacing
6. Occurrences: =Spreadsheet.mortise_count
```

### 5. Creating Conditional Notches (Sparren)

```
For each notch (1 to 10):

1. Create pocket for notch
2. In pocket depth, use formula:
   =Spreadsheet.notch1_enabled * Spreadsheet.notch1_depth
   
3. If notch1_enabled = 0, depth = 0 (invisible)
   If notch1_enabled = 1, depth = notch1_depth

4. Position sketch using:
   z_pos = Spreadsheet.length * Spreadsheet.notch1_z_normalized
```

---

## Verification Checklist

Before extracting template from master file:

- [ ] Origin is at (0, 0, 0) in template
- [ ] Beam extends from Z=0 to Z=length
- [ ] All dimensions reference spreadsheet aliases
- [ ] Spreadsheet has all required aliases
- [ ] Test with different parameter values
- [ ] Check that geometry updates correctly
- [ ] Export test mesh to verify

---

## Export Process

```
In FreeCAD Python console:

import Mesh
import FreeCAD

# Get the Body
body = FreeCAD.ActiveDocument.Body

# Export as STL
mesh = body.Shape.tessellate(0.1)  # Tolerance
Mesh.Mesh(mesh[0], mesh[1]).write("test.stl")
```

Or via GUI:
1. Select Body in tree
2. File → Export
3. Choose STL format
4. Save

---

**This guide ensures consistent template creation!**