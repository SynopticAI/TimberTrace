import numpy as np
from typing import Tuple, List, Dict, Optional
from object_definitions import Pfosten, Pfette, BeamBase

def post_and_beam(seed: Optional[int] = None) -> Tuple[List[BeamBase], Dict]:
    """
    Creates a simple structure: 2 Posts supporting 1 Purlin (Pfette).
    
    Structure:
      |   ----------------   | <- Pfette (Beam 2)
      |  |              |  |
      |  |              |  |
      |__|              |__|
     Post 1            Post 2
    (Beam 0)          (Beam 1)
    """
    if seed is not None:
        np.random.seed(seed)
        
    # 1. Create Beams
    post1 = Pfosten()
    post2 = Pfosten()
    beam = Pfette()
    
    # --- FIX: Set Rough Initial Positions via Attributes ---
    # We set the attributes directly (self.x, self.z, etc.) as defined in object_definitions.py
    
    # Post 1 (Left)
    post1.x = -1.5 
    post1.z = 0.0
    post1.height = 2.2
    
    # Post 2 (Right)
    post2.x = 1.5
    post2.z = 0.0
    post2.height = 2.2
    
    # Beam (Top)
    beam.z = 2.2      # Sit roughly on top
    beam.length = 3.5 # Ensure it's long enough to span the gap
    
    # Store in list (Index 0=Post1, 1=Post2, 2=Beam)
    beams = [post1, post2, beam]
    
    # 2. Define Connectivity (Topology)
    # Format: (beam_i_idx, beam_j_idx, face_i, face_j, constraint_idx_i, constraint_idx_j)
    # Faces: 0=Right, 1=Left, 2=Front, 3=Back, 4=Top, 5=Bottom
    
    connectivity_map = {
        'top': [], 'bottom': [], 'left': [], 'right': [], 'front': [], 'back': []
    }
    
    # Connection 1: Post 1 Top (idx 4) touches Beam Bottom (idx 5)
    # Post 1 (0) -> Beam (2)
    connectivity_map['top'].append((0, 2, 4, 5, 0, 0))
    
    # Connection 2: Post 2 Top (idx 4) touches Beam Bottom (idx 5)
    # Post 2 (1) -> Beam (2)
    # Note: We add this to 'top' because it originates from the "Top" face of the Post
    connectivity_map['top'].append((1, 2, 4, 5, 0, 0))
    
    # 3. Define Identity Pairs (Morphology Sharing)
    # Post 1 and Post 2 should be identical (same width/depth)
    identity_pairs = [
        (0, 1)  # Beam 0 and Beam 1 share morphology
    ]
    
    topology = {
        'connectivity': connectivity_map,
        'identity_pairs': identity_pairs
    }
    
    return beams, topology

def get_blueprint(name: str):
    """Factory function to retrieve blueprints by name."""
    if name == "post_and_beam":
        return post_and_beam
    else:
        raise ValueError(f"Unknown blueprint: {name}")