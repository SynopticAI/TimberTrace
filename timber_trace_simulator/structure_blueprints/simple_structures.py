import numpy as np
from typing import Tuple, List, Dict, Optional
from object_definitions import Pfosten, Pfette, Sparren, BeamBase

def post_and_beam(seed: Optional[int] = None) -> Tuple[List[BeamBase], Dict]:
    """Creates a simple structure: 2 Posts supporting 1 Purlin (Pfette)."""
    if seed is not None: np.random.seed(seed)
    
    post1 = Pfosten(height=2.2)
    post2 = Pfosten(height=2.2)
    beam = Pfette(length=3.5)
    
    post1.x, post1.z = -1.5, 0.0
    post2.x, post2.z = 1.5, 0.0
    beam.z = 2.2
    
    beams = [post1, post2, beam]
    connectivity = {'top': [], 'bottom': [], 'left': [], 'right': [], 'front': [], 'back': []}
    connectivity['top'].append((0, 2, 4, 5, 0, 0)) 
    connectivity['top'].append((1, 2, 4, 5, 0, 0))
    
    topology = {'connectivity': connectivity, 'identity_pairs': [(0, 1)]}
    return beams, topology


def sparren_on_pfette_on_pfosten(seed: Optional[int] = None) -> Tuple[List[BeamBase], Dict]:
    """
    Standard Roof Segment:
    - Ridge = Global Y Axis (X=0)
    - Pfette (Purlin) = Y-Aligned (theta=0)
    - Sparren (Rafter) = X-Aligned (theta=0)
    """
    if seed is not None:
        np.random.seed(seed)

    # 1. PARAMETERS
    pfette_width, pfette_height, pfette_len = 0.14, 0.16, 4.0
    sparren_width, sparren_height, sparren_len = 0.10, 0.16, 3.5
    steepness = 1.0
    notch_x_mittel, notch_depth = 1.5, 0.05
    
    # 2. CREATE BEAMS
    post1 = Pfosten(height=2.2)
    post2 = Pfosten(height=2.2)
    pfette = Pfette(length=pfette_len, width=pfette_width, height=pfette_height)
    
    sparren1 = Sparren(width=sparren_width, height=sparren_height, projected_length=sparren_len, steepness=steepness, notch_x_mittel=notch_x_mittel, notch_mittel_depth=notch_depth)
    sparren2 = Sparren(width=sparren_width, height=sparren_height, projected_length=sparren_len, steepness=steepness, notch_x_mittel=notch_x_mittel, notch_mittel_depth=notch_depth)

    # 3. ROUGH PLACEMENT
    
    # Pfette: Y-Aligned (No rotation needed!)
    # X Position: To sit nicely in the notch, the Purlin's RIGHT face should hit the Notch wall.
    # Notch wall is at 'notch_x'. Purlin Right face is at 'x + width/2'.
    # So x_purlin approx 'notch_x - width/2'.
    pfette.theta_z = 0.0
    pfette.x = notch_x_mittel - (pfette_width / 2)
    pfette.y = 0.0
    pfette.z = 2.2
    
    # Posts under Purlin
    post1.x = pfette.x
    post1.y, post1.z = -1.5, 0.0
    post2.x = pfette.x
    post2.y, post2.z = 1.5, 0.0
    
    # Sparren: X-Aligned
    sparren1.theta_z = 0.0
    sparren2.theta_z = 0.0
    sparren1.y, sparren1.x = -0.5, 0.0
    sparren2.y, sparren2.x = 0.5, 0.0
    
    # Z Calculation
    z_target = pfette.z + pfette.height + (steepness * notch_x_mittel) + sparren_height - notch_depth
    sparren1.z = z_target
    sparren2.z = z_target

    beams = [post1, post2, pfette, sparren1, sparren2]
    
    # 4. CONNECTIVITY
    connectivity = {'top': [], 'bottom': [], 'left': [], 'right': [], 'front': [], 'back': []}
    
    # Posts -> Pfette
    connectivity['top'].append((0, 2, 4, 5, 0, 0))
    connectivity['top'].append((1, 2, 4, 5, 0, 0))
    
    # Pfette -> Sparren
    # 1. Vertical Load: Pfette TOP (4) -> Sparren MITTEL SHELF (5, Index 1)
    connectivity['top'].append((2, 3, 4, 5, 0, 1)) 
    connectivity['top'].append((2, 4, 4, 5, 0, 1))
    
    # 2. Sliding Lock: Pfette RIGHT (0) -> Sparren NOTCH VERTICAL (0)
    # The Purlin (Right Face) pushes against the Notch (Vertical Face)
    # Both are defined as Face 0 in their classes.
    connectivity['right'].append((2, 3, 0, 1, 0, 1)) 
    connectivity['right'].append((2, 4, 0, 1, 0, 1))
    
    topology = {
        'connectivity': connectivity,
        'identity_pairs': [(0, 1), (3, 4)]
    }
    
    return beams, topology


def half_pfettendach(seed: Optional[int] = None) -> Tuple[List[BeamBase], Dict]:
    """
    3 Purlins (Fuss, Mittel, First) supporting 2 Sparren.
    """
    if seed is not None: np.random.seed(seed)

    # 1. PARAMETERS
    pfette_w, pfette_h, pfette_l = 0.14, 0.16, 4.0
    sparren_w, sparren_h, sparren_len = 0.10, 0.16, 4.0
    steepness = 1.0
    
    # Notch Locations
    notch_first = 0.08
    notch_mittel = 1.5
    notch_fuss = 2.8
    notch_depth = 0.05
    cut_depth_top = 0.0 # Top notch cut depth

    # 2. CREATE BEAMS
    # Purlins
    firstpfette = Pfette(length=pfette_l, width=pfette_w, height=pfette_h)
    mittelpfette = Pfette(length=pfette_l, width=pfette_w, height=pfette_h)
    fusspfette  = Pfette(length=pfette_l, width=pfette_w, height=pfette_h)

    # Posts for Mittelpfette (keeping the same base structure)
    post1, post2 = Pfosten(height=2.2), Pfosten(height=2.2)

    # Sparren
    sparren1 = Sparren(width=sparren_w, height=sparren_h, projected_length=sparren_len, steepness=steepness,
                       notch_x_mittel=notch_mittel, notch_mittel_depth=notch_depth,
                       notch_x_fuss=notch_fuss, notch_fuss_depth=notch_depth,
                       notch_top_length=notch_first, notch_top_cut_depth=cut_depth_top)
    sparren2 = Sparren(width=sparren_w, height=sparren_h, projected_length=sparren_len, steepness=steepness,
                       notch_x_mittel=notch_mittel, notch_mittel_depth=notch_depth,
                       notch_x_fuss=notch_fuss, notch_fuss_depth=notch_depth,
                       notch_top_length=notch_first, notch_top_cut_depth=cut_depth_top)

    # 3. ROUGH PLACEMENT
    
    # --- MITTELPFETTE (Anchor) ---
    mittelpfette.x = notch_mittel - (pfette_w / 2)
    mittelpfette.z = 2.2
    
    # Posts
    post1.x, post1.y, post1.z = mittelpfette.x, -1.5, 0.0
    post2.x, post2.y, post2.z = mittelpfette.x, 1.5, 0.0
    
    # --- SPARREN Z Calculation ---
    # Global Z of Sparren Ridge = Purlin_Z + Purlin_H + Lift_from_slope + Lift_from_Notch
    z_ridge = mittelpfette.z + pfette_h + (steepness * notch_mittel) + sparren_h - notch_depth
    sparren1.z, sparren2.z = z_ridge, z_ridge
    
    sparren1.y, sparren1.x = -0.5, 0.0
    sparren2.y, sparren2.x = 0.5, 0.0

    # --- OTHER PURLINS (Derived from Sparren Z) ---
    # Fusspfette
    fusspfette.x = notch_fuss - (pfette_w / 2)
    # Z = Ridge - (steepness * x) - Sparren_H + Depth - Pfette_H
    fusspfette.z = z_ridge - (steepness * notch_fuss) - sparren_h + notch_depth - pfette_h
    
    # Firstpfette
    firstpfette.x = notch_first - (pfette_w / 2)
    # For Top Notch: Z = Ridge - (steepness * x) ... actually the shelf is defined differently
    # Top Shelf Local Z = -H_Spar + cut_depth
    # Top Shelf Global Z = Z_Ridge - H_Spar + cut_depth
    # Pfette Z = Top Shelf Global Z - Pfette_H
    firstpfette.z = z_ridge - sparren_h + cut_depth_top - pfette_h

    # Beam List: 0,1=Posts, 2=First, 3=Mittel, 4=Fuss, 5,6=Sparren
    beams = [post1, post2, firstpfette, mittelpfette, fusspfette, sparren1, sparren2]

    # 4. CONNECTIVITY
    connectivity = {'top': [], 'bottom': [], 'left': [], 'right': [], 'front': [], 'back': []}
    
    # Posts -> Mittelpfette (Index 3)
    connectivity['top'].append((0, 3, 4, 5, 0, 0))
    connectivity['top'].append((1, 3, 4, 5, 0, 0))
    
    # Purlins -> Sparren
    for spar_idx in [5, 6]:
        # --- FIRSTPFETTE (Index 2) -> Sparren TOP NOTCH (Index 2) ---
        connectivity['top'].append((2, spar_idx, 4, 5, 0, 2))      # Vertical Load
        connectivity['right'].append((2, spar_idx, 0, 1, 0, 2))    # Sliding Lock (Purlin Right -> Sparren Left Vert)
        
        # --- MITTELPFETTE (Index 3) -> Sparren MITTEL NOTCH (Index 1) ---
        connectivity['top'].append((3, spar_idx, 4, 5, 0, 1))
        connectivity['right'].append((3, spar_idx, 0, 1, 0, 1))

        # --- FUSSPFETTE (Index 4) -> Sparren FUSS NOTCH (Index 0) ---
        connectivity['top'].append((4, spar_idx, 4, 5, 0, 0))
        connectivity['right'].append((4, spar_idx, 0, 1, 0, 0))
    
    topology = {
        'connectivity': connectivity,
        'identity_pairs': [(0, 1), (5, 6), (2, 4)] # Posts, Sparren, Fuss/First Pfetten (Identical)
    }
    
    return beams, topology