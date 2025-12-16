# %%
# === IMPORTS ===
from build123d import *
from ocp_vscode import *
import numpy as np

# %%
# === PARAMETERS ===

# Basic dimensions
width = 0.100          # Thickness (Y)
height = 0.160         # Height (Z)
projected_length = 3.0 # Length (X)
steepness = 1.0        # Slope (m)

# Middle notch (Mittelpfette)
notch_x_mittel = 1.5      # X Position of the vertical face
notch_mittel_depth = 0.05 # Depth of the cut (vertical) - Larger as requested

# Bottom notch (Fußpfette)
notch_x_fuss = 2.8        # X Position of the vertical face
notch_fuss_depth = 0.05   # Depth of the cut (vertical) - Larger as requested

# Top notch (Firstpfette)
notch_top_length = 0.08   # X distance from ridge - Smaller as requested
notch_top_cut_depth = 0.00 # Height ABOVE bottom line (0 = flush with bottom line for strength)

# %%
# === HELPER: CALCULATE PROFILE POINTS ===
def get_profile_points(projected_length, steepness, height,
                       notch_x_mittel, notch_mittel_depth,
                       notch_x_fuss, notch_fuss_depth,
                       notch_top_length, notch_top_cut_depth):
    
    L = projected_length
    m = steepness
    H = height
    
    # Line equations
    def bottom_z(x): return -m * x - H
    def top_z(x): return -m * x
    
    # Helper to find X on bottom line given Z
    # z = -mx - H  =>  mx = -H - z  =>  x = (-H - z) / m
    def bottom_x_from_z(z): return (-H - z) / m

    pts = []
    
    # 1. RIDGE TOP
    pts.append((0, 0))
    
    # 2. EAVES TOP
    pts.append((L, top_z(L)))
    
    # 3. EAVES BOTTOM
    pts.append((L, bottom_z(L)))
    
    # 4. WALK BACK UP THE BOTTOM LINE
    
    # --- FUSS NOTCH (Lower) ---
    # Point 1: On bottom line at x_fuss
    z_fuss_bottom = bottom_z(notch_x_fuss)
    pts.append((notch_x_fuss, z_fuss_bottom))
    
    # Point 2: Vertical Face UP (The Corner)
    z_fuss_shelf = z_fuss_bottom + notch_fuss_depth
    pts.append((notch_x_fuss, z_fuss_shelf))
    
    # Point 3: Horizontal intersection with bottom line
    x_fuss_back = bottom_x_from_z(z_fuss_shelf)
    pts.append((x_fuss_back, z_fuss_shelf))
    
    # --- MITTEL NOTCH (Middle) ---
    # Point 1: On bottom line at x_mittel
    z_mittel_bottom = bottom_z(notch_x_mittel)
    pts.append((notch_x_mittel, z_mittel_bottom))
    
    # Point 2: Vertical Face UP
    z_mittel_shelf = z_mittel_bottom + notch_mittel_depth
    pts.append((notch_x_mittel, z_mittel_shelf))
    
    # Point 3: Horizontal intersection
    x_mittel_back = bottom_x_from_z(z_mittel_shelf)
    pts.append((x_mittel_back, z_mittel_shelf))
    
    # --- TOP NOTCH (Ridge) ---
    # Point 1: On bottom line at notch_top_length
    z_top_bottom = bottom_z(notch_top_length)
    pts.append((notch_top_length, z_top_bottom))
    
    # Point 2: Vertical Face UP (Right angle corner)
    # The shelf height is defined relative to H
    z_top_shelf = -H + notch_top_cut_depth
    pts.append((notch_top_length, z_top_shelf))
    
    # Point 3: Horizontal to Ridge (x=0)
    pts.append((0, z_top_shelf))
    
    # Close shape
    pts.append((0, 0))
    
    return pts

# Generate points
profile_pts = get_profile_points(
    projected_length, steepness, height,
    notch_x_mittel, notch_mittel_depth,
    notch_x_fuss, notch_fuss_depth,
    notch_top_length, notch_top_cut_depth
)

# %%
# === STEP 1: VERIFY 2D PROFILE ===
# Check if the loops are closed and triangles look right
with BuildSketch(Plane.XZ) as profile_sketch:
    with BuildLine():
        Polyline(profile_pts)
    make_face()

show(profile_sketch, axes=True, grid=(True, True, True))

# %%
# === STEP 2: 3D MODEL WITH CONSTRAINTS ===

# 1. Create the solid
with BuildPart() as rafter:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline(profile_pts)
        make_face()
    extrude(amount=width, both=True)

# 2. Visualize Constraints
def bottom_z(x): return -steepness * x - height
def bottom_x_from_z(z): return (-height - z) / steepness

constraints = []

# --- BOTTOM CONNECTIONS (Red) ---
# Constraint: Parallel to X-axis (along the shelf), Centered in Y (y=0)

# 1. Fuss Shelf
z_fuss = bottom_z(notch_x_fuss) + notch_fuss_depth
x_fuss_back = bottom_x_from_z(z_fuss)
l1 = Edge.make_line(
    (x_fuss_back, 0, z_fuss), 
    (notch_x_fuss, 0, z_fuss)
)

# 2. Mittel Shelf
z_mittel = bottom_z(notch_x_mittel) + notch_mittel_depth
x_mittel_back = bottom_x_from_z(z_mittel)
l2 = Edge.make_line(
    (x_mittel_back, 0, z_mittel), 
    (notch_x_mittel, 0, z_mittel)
)

# 3. Top Shelf (Horizontal)
z_top = -height + notch_top_cut_depth
l3 = Edge.make_line(
    (0, 0, z_top), 
    (notch_top_length, 0, z_top)
)

bottom_constraints = Compound(children=[l1, l2, l3])

# --- LEFT CONNECTIONS (Blue) ---
# Constraint: Parallel to Z-axis (vertical up the face), Centered in Y (y=0)

# 1. Fuss Vertical Face
z_fuss_bottom = bottom_z(notch_x_fuss)
l4 = Edge.make_line(
    (notch_x_fuss, 0, z_fuss_bottom), 
    (notch_x_fuss, 0, z_fuss)
)

# 2. Mittel Vertical Face
z_mittel_bottom = bottom_z(notch_x_mittel)
l5 = Edge.make_line(
    (notch_x_mittel, 0, z_mittel_bottom), 
    (notch_x_mittel, 0, z_mittel)
)

# 3. Top Notch Vertical Face
l6 = Edge.make_line(
    (notch_top_length, 0, bottom_z(notch_top_length)), 
    (notch_top_length, 0, -height+notch_top_cut_depth)
)

# 4. Ridge Vertical Face (Opposing Sparren)
l7 = Edge.make_line(
    (0, 0, -height+notch_top_cut_depth), 
    (0, 0, 0)
)

left_constraints = Compound(children=[l4, l5, l6, l7])

print("Visualizing: Red = Bottom Constraints (X-parallel), Blue = Left Constraints (Z-parallel)")
show(rafter, bottom_constraints, left_constraints, 
     colors=[None, "red", "blue"], 
     axes=True, transparent=True)

# %%
# === STEP 3: CODE GENERATOR FOR object_definitions.py ===

print("="*60)
print("PASTE THIS INTO object_definitions.py")
print("="*60)

print("""
    def get_constraints(self, direction: int, index: int = 0):
        # Helper for Z calculation
        def get_z_at(x): return -self.steepness * x - self.height
        
        # Helper for X calculation from Z (for shelf start points)
        def get_x_from_z(z): return (-self.height - z) / self.steepness

        # DIRECTION 5: BOTTOM (Horizontal Notch Faces)
        # Constraint Line: Parallel to X-axis (slack_0 defines X pos), Fixed Y=0, Fixed Z
        if direction == 5:
            if index == 0: # Fuss Notch Shelf
                z_val = get_z_at(self.notch_x_fuss) + self.notch_fuss_depth
                return ConstraintEquation(
                    x_expr = "slack_0", 
                    y_expr = "0",
                    z_expr = f"{z_val}",
                    slack_count = 1
                )
            elif index == 1: # Mittel Notch Shelf
                z_val = get_z_at(self.notch_x_mittel) + self.notch_mittel_depth
                return ConstraintEquation(
                    x_expr = "slack_0",
                    y_expr = "0",
                    z_expr = f"{z_val}",
                    slack_count = 1
                )
            elif index == 2: # Top Notch Shelf
                z_val = -self.height + self.notch_top_cut_depth
                return ConstraintEquation(
                    x_expr = "slack_0", 
                    y_expr = "0",
                    z_expr = f"{z_val}",
                    slack_count = 1
                )

        # DIRECTION 1: LEFT (Vertical Notch Faces)
        # Constraint Line: Parallel to Z-axis (slack_0 defines Z pos), Fixed X, Fixed Y=0
        elif direction == 1:
            if index == 0: # Fuss Vertical
                return ConstraintEquation(
                    x_expr = "self.notch_x_fuss",
                    y_expr = "0",
                    z_expr = "slack_0",
                    slack_count = 1
                )
            elif index == 1: # Mittel Vertical
                return ConstraintEquation(
                    x_expr = "self.notch_x_mittel",
                    y_expr = "0",
                    z_expr = "slack_0",
                    slack_count = 1
                )
            elif index == 2: # Top Notch Vertical
                return ConstraintEquation(
                    x_expr = "self.notch_top_length",
                    y_expr = "0",
                    z_expr = "slack_0",
                    slack_count = 1
                )
            elif index == 3: # Ridge Vertical (Alignment)
                return ConstraintEquation(
                    x_expr = "0",
                    y_expr = "0",
                    z_expr = "slack_0",
                    slack_count = 1
                )
""")