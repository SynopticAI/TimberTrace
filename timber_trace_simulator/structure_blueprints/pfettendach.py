import numpy as np
from typing import Tuple, List, Dict, Optional
from object_definitions import Pfosten, Pfette, Sparren, BeamBase

def create_pfettendach(seed: Optional[int] = None, 
                       spar_count: int = 5, 
                       post_count: int = 3) -> Tuple[List[BeamBase], Dict]:
    """
    Full Pfettendach (Gable Roof) with:
    - 2 Slopes (Left/Right)
    - 3 Purlin Lines (First, Mittel, Fuss) x 2 sides (First is shared)
    - Variable number of Spars (Rafters)
    - Variable number of Posts (Stuhlsäulen) under Mittelpfetten
    """
    if seed is not None:
        np.random.seed(seed)

    # === 1. PARAMETERS ===
    # Roof Dimensions
    roof_len = 10.0  # Total length Y
    roof_half_span = 4.0  # Horizontal width X (one side)
    
    # Beam Dimensions
    pfette_w, pfette_h = 0.14, 0.16
    spar_w, spar_h = 0.10, 0.16
    post_h = 2.2
    
    steepness = 1.0 # 45 degrees
    
    # Notch Locations (Horizontal projection from Ridge)
    notch_first = pfette_w / 2
    notch_mittel = roof_half_span * 0.5 # Middle of slope
    notch_fuss = roof_half_span * 0.95  # Near eaves
    
    spar_proj_len = roof_half_span + 0.5 # Overhang
    notch_depth = 0.05
    
    # === 2. CREATE PURLINS & POSTS ===
    # Purlins run along Y (Length = roof_len)
    
    # 1x Firstpfette (Ridge) - Shared
    first_pfette = Pfette(length=roof_len, width=pfette_w, height=pfette_h)
    
    # 2x Mittelpfetten (Left/Right)
    mittel_pfette_r = Pfette(length=roof_len, width=pfette_w, height=pfette_h)
    mittel_pfette_l = Pfette(length=roof_len, width=pfette_w, height=pfette_h)
    
    # 2x Fusspfetten (Left/Right)
    fuss_pfette_r = Pfette(length=roof_len, width=pfette_w, height=pfette_h)
    fuss_pfette_l = Pfette(length=roof_len, width=pfette_w, height=pfette_h)
    
    beams = [first_pfette, mittel_pfette_r, mittel_pfette_l, fuss_pfette_r, fuss_pfette_l]
    # Indices: 0=First, 1=Mittel_R, 2=Mittel_L, 3=Fuss_R, 4=Fuss_L
    
    # Posts (Rows under Mittelpfetten)
    posts = []
    post_spacing = roof_len / (post_count + 1) if post_count > 0 else 0
    
    for i in range(post_count):
        # Y position distributed along roof
        y_pos = -roof_len/2 + (i + 1) * post_spacing
        
        # Right Post
        p_r = Pfosten(height=post_h)
        p_r.x = notch_mittel - pfette_w/2 # Under Mittelpfette
        p_r.y = y_pos
        p_r.z = 0.0 # Floor
        posts.append(p_r)
        
        # Left Post (Mirrored X)
        p_l = Pfosten(height=post_h)
        p_l.x = -(notch_mittel - pfette_w/2)
        p_l.y = y_pos
        p_l.z = 0.0
        posts.append(p_l)
        
    beams.extend(posts)
    post_start_idx = 5
    
    # === 3. CREATE SPARS (RAFTERS) ===
    spars = []
    spar_spacing = roof_len / (spar_count - 1) if spar_count > 1 else 0
    
    # Z Calculation (Reference Height for Ridge)
    # Mittelpfette is on posts -> Z_Mittel = post_h
    # Ridge Z = Z_Mittel + H_Purlin + (slope * notch_dist) + H_Spar - Depth
    z_mittel_purlin = post_h
    z_ridge_global = z_mittel_purlin + pfette_h + (steepness * notch_mittel) + spar_h - notch_depth
    
    for i in range(spar_count):
        y_pos = -roof_len/2 + i * spar_spacing
        
        # --- Right Spar (0 deg) ---
        s_r = Sparren(width=spar_w, height=spar_h, projected_length=spar_proj_len, steepness=steepness,
                      notch_x_mittel=notch_mittel, notch_x_fuss=notch_fuss, notch_top_length=notch_first,
                      notch_mittel_depth=notch_depth, notch_fuss_depth=notch_depth)
        s_r.theta_z = 0.0
        s_r.x = 0.0
        s_r.y = y_pos
        s_r.z = z_ridge_global
        spars.append(s_r)
        
        # --- Left Spar (180 deg) ---
        s_l = Sparren(width=spar_w, height=spar_h, projected_length=spar_proj_len, steepness=steepness,
                      notch_x_mittel=notch_mittel, notch_x_fuss=notch_fuss, notch_top_length=notch_first,
                      notch_mittel_depth=notch_depth, notch_fuss_depth=notch_depth)
        s_l.theta_z = np.pi # 180 degrees
        s_l.x = 0.0
        s_l.y = y_pos
        s_l.z = z_ridge_global
        spars.append(s_l)
        
    beams.extend(spars)
    spar_start_idx = post_start_idx + len(posts)
    
    # === 4. POSITION PURLINS ===
    # Align Purlins with Y-axis (Theta=0)
    for p in [first_pfette, mittel_pfette_r, mittel_pfette_l, fuss_pfette_r, fuss_pfette_l]:
        p.theta_z = 0.0
        p.y = 0.0 # Centered Y
    
    # X/Z Positions
    # Firstpfette (Shared Ridge)
    first_pfette.x = 0.0 
    # Z = Ridge_Z - H_Spar + Top_Cut - H_Purlin (approx)
    first_pfette.z = z_ridge_global - spar_h - pfette_h 
    
    # Mittelpfette R
    mittel_pfette_r.x = notch_mittel - pfette_w/2
    mittel_pfette_r.z = post_h
    
    # Mittelpfette L (Mirrored)
    mittel_pfette_l.x = -(notch_mittel - pfette_w/2)
    mittel_pfette_l.z = post_h
    
    # Fusspfette R
    fuss_pfette_r.x = notch_fuss - pfette_w/2
    fuss_pfette_r.z = z_ridge_global - (steepness * notch_fuss) - spar_h + notch_depth - pfette_h
    
    # Fusspfette L
    fuss_pfette_l.x = -(notch_fuss - pfette_w/2)
    fuss_pfette_l.z = fuss_pfette_r.z
    
    # === 5. CONNECTIVITY ===
    connectivity = {'top': [], 'bottom': [], 'left': [], 'right': [], 'front': [], 'back': []}
    
    # A. Posts -> Mittelpfetten
    # Even indices = Right Posts, Odd = Left Posts
    for i in range(len(posts)):
        post_idx = post_start_idx + i
        # Right Posts -> Mittelpfette R (Index 1)
        if i % 2 == 0: 
            connectivity['top'].append((post_idx, 1, 4, 5, 0, 0))
        # Left Posts -> Mittelpfette L (Index 2)
        else:
            connectivity['top'].append((post_idx, 2, 4, 5, 0, 0))
            
    # B. Purlins -> Sparren
    # Even indices = Right Spars, Odd = Left Spars
    for i in range(len(spars)):
        spar_idx = spar_start_idx + i
        is_right = (i % 2 == 0)
        
        # Determine target purlins
        if is_right:
            targets = [
                (0, 2), # Firstpfette (Index 0) -> Top Notch (Index 2)
                (1, 1), # Mittel R    (Index 1) -> Mittel Notch (Index 1)
                (3, 0)  # Fuss R      (Index 3) -> Fuss Notch (Index 0)
            ]
        else:
            targets = [
                (0, 2), # Firstpfette (Index 0)
                (2, 1), # Mittel L    (Index 2)
                (4, 0)  # Fuss L      (Index 4)
            ]
            
        for purlin_idx, notch_idx in targets:
            # 1. Vertical Load (Purlin Top -> Sparren Bottom Shelf)
            connectivity['top'].append((purlin_idx, spar_idx, 4, 5, 0, notch_idx))
            
            # 2. Sliding Lock (Purlin Side -> Sparren Vertical)
            # Purlin Uphill Side is ALWAYS Global Right (Face 0) for both L and R purlins?
            # - Right Purlin (+X): Uphill is Left (-X, Face 1)? No, Uphill is towards X=0 (-X).
            # - Left Purlin (-X): Uphill is Right (+X, Face 0).
            
            # Let's re-verify Uphill Faces:
            # Ridge is at X=0.
            # Right Purlin is at X > 0. Uphill is towards 0 (-X direction).
            # Purlin Local Left (1) points -X. So Right Purlin Uphill is Face 1.
            
            # Left Purlin is at X < 0. Uphill is towards 0 (+X direction).
            # Purlin Local Right (0) points +X. So Left Purlin Uphill is Face 0.
            
            purlin_uphill_face = 0 if is_right else 1
            
            # Sparren Vertical Face Constraint:
            # Right Spar (0 deg): Constraint on Local 1 (Left). 
            #   Mapped 0deg: Local 1 -> Global 1.
            #   So we connect Purlin Uphill (1) -> Sparren (1).
            
            # Left Spar (180 deg): Constraint on Local 1 (Left).
            #   Mapped 180deg: Local 1 -> Global 0.
            #   So we connect Purlin Uphill (0) -> Sparren (0).
            
            spar_connect_dir = 1 if is_right else 0
            
            # Add constraint (Bucket into 'right' or 'left' based on global dir, irrelevant for solver but good for JSON)
            bucket = 'left' if purlin_uphill_face == 1 else 'right'
            connectivity[bucket].append((purlin_idx, spar_idx, purlin_uphill_face, spar_connect_dir, 0, notch_idx))

    # C. Sparren -> Sparren (Ridge Connection)
    # Connect Right Spars (Global Left Face) to Left Spars (Global Right Face) at the Ridge (Index 3)
    # Right Spar (0 deg): Ridge Face is Local Left (1) -> Global Left (1)
    # Left Spar (180 deg): Ridge Face is Local Left (1) -> Global Right (0)
    for i in range(spar_count):
        idx_r = spar_start_idx + (2*i)     # Right Spar
        idx_l = spar_start_idx + (2*i) + 1 # Left Spar
        
        # Connect: Right Spar (Global Left 1) <-> Left Spar (Global Right 0)
        # Using Index 3 (Ridge Alignment Face) for both
        connectivity['left'].append((idx_r, idx_l, 1, 0, 3, 3))


    # === 6. IDENTITY PAIRS ===
    identity_pairs = []
    
    # 1. All Posts Identical
    # Link each post to the next one (0->1, 1->2, etc.)
    # This chain forces all posts in the list to share the same morphology
    for i in range(len(posts) - 1):
        idx_current = post_start_idx + i
        idx_next = post_start_idx + i + 1
        identity_pairs.append((idx_current, idx_next))

    # 2. All Spars Identical
    # Link each spar to the next one
    for i in range(len(spars) - 1):
        idx_current = spar_start_idx + i
        idx_next = spar_start_idx + i + 1
        identity_pairs.append((idx_current, idx_next))

    topology = {
        'connectivity': connectivity,
        'identity_pairs': identity_pairs
    }
    
    return beams, topology