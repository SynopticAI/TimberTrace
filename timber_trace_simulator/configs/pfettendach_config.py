"""
Pfettendach Roof Configuration

Defines all parameters, ranges, and beam structure for a traditional
German Pfettendach (purlin roof) system.
"""

from pathlib import Path

# Path to master FreeCAD file (relative to project root)
MASTER_FILE = "core/freecad_templates/Master_Pfettendach.FCStd"

# ============================================================================
# PARAMETER DEFINITIONS
# ============================================================================
# Format: "spreadsheet_alias": {"range": (min, max), "unit": "mm|deg|count"}

PARAMETERS = {
    # Firstpfette (Ridge Purlin)
    "Firstpfette_Bottom_Offset": {"range": (3500, 4500), "unit": "mm"},
    "Firstpfette_Length": {"range": (10000, 14000), "unit": "mm"},
    "Firstpfette_Height": {"range": (180, 220), "unit": "mm"},
    "Firstpfette_Width": {"range": (80, 120), "unit": "mm"},
    "Firstpfette_Extension_Length": {"range": (400, 600), "unit": "mm"},
    
    # Mittelpfette (Middle Purlin)
    "Mittelpfette_Bottom_Offset": {"range": (2000, 2400), "unit": "mm"},
    "Mittelpfette_Length": {"range": (10000, 14000), "unit": "mm"},
    "Mittelpfette_Height": {"range": (180, 220), "unit": "mm"},
    "Mittelpfette_Width": {"range": (80, 120), "unit": "mm"},
    "Mittelpfette_Extension_Length": {"range": (400, 600), "unit": "mm"},
    
    # Fusspfette (Eaves Purlin)
    "Fusspfette_Bottom_Offset": {"range": (300, 500), "unit": "mm"},
    "Fusspfette_Length": {"range": (10000, 14000), "unit": "mm"},
    "Fusspfette_Height": {"range": (180, 220), "unit": "mm"},
    "Fusspfette_Width": {"range": (80, 120), "unit": "mm"},
    "Fusspfette_Extension_Length": {"range": (0, 100), "unit": "mm"},
    
    # Sparren (Rafters)
    "Sparre_Count": {"range": (12, 18), "unit": "count"},
    "Sparre_Bottom_Offset": {"range": (300, 500), "unit": "mm"},
    "Sparre_Angle": {"range": (35, 45), "unit": "deg"},
    "Sparre_Height": {"range": (180, 220), "unit": "mm"},
    "Sparre_Width": {"range": (80, 120), "unit": "mm"},
    "Sparre_Notch_Depth": {"range": (30, 40), "unit": "mm"},
    
    # Mittelpfosten (Center Posts)
    "Mittelpfosten_Count": {"range": (2, 4), "unit": "count"},
    "Mittelpfosten_Bottom_Offset": {"range": (1, 1), "unit": "mm"},  # Always at ground
    "Mittelpfosten_Width_X": {"range": (80, 120), "unit": "mm"},
    "Mittelpfosten_Width_Y": {"range": (80, 120), "unit": "mm"},
    "Mittelpfosten_Tenon_Width_X": {"range": (35, 45), "unit": "mm"},
    "Mittelpfosten_Tenon_Width_Y": {"range": (35, 45), "unit": "mm"},
    "Mittelpfosten_Tenon_Height": {"range": (80, 120), "unit": "mm"},
    
    # Seitenpfosten (Side Posts)
    "Seitenpfosten_Bottom_Offset": {"range": (1, 1), "unit": "mm"},  # Always at ground
    "Seitenpfosten_Width_X": {"range": (80, 120), "unit": "mm"},
    "Seitenpfosten_Width_Y": {"range": (80, 120), "unit": "mm"},
    "Seitenpfosten_Tenon_Width_X": {"range": (35, 45), "unit": "mm"},
    "Seitenpfosten_Tenon_Width_Y": {"range": (35, 45), "unit": "mm"},
    "Seitenpfosten_Tenon_Height": {"range": (80, 120), "unit": "mm"},
    "Seitenpfosten_Count": {"range": (4, 6), "unit": "count"},
}

# ============================================================================
# BEAM DEFINITIONS
# ============================================================================
# Maps logical beam types to FreeCAD bodies + replication rules

BEAMS = {
    "Firstpfette": {
        "body_name": "Body002",
        "semantic_label": 0,
        "count": 1,                    # Single beam at ridge
        "y_spacing": None,             # No replication
        "x_mirror": False,             # Centered on ridge
        "description": "Ridge purlin at roof peak"
    },
    
    "Mittelpfette": {
        "body_name": "Body001",
        "semantic_label": 1,
        "count": 1,                    # One per side (x_mirror creates 2 total)
        "y_spacing": None,
        "x_mirror": True,              # Left + Right
        "description": "Middle purlin on each roof slope"
    },
    
    "Fusspfette": {
        "body_name": "Body003",
        "semantic_label": 2,
        "count": 1,                    # One per side
        "y_spacing": None,
        "x_mirror": True,              # Left + Right
        "description": "Eaves purlin at roof base"
    },
    
    "Sparren": {
        "body_name": "Body004",
        "semantic_label": 3,
        "count": "Sparre_Count",       # Derived from parameters
        "y_spacing": "auto",           # Calculated from length / count
        "x_mirror": True,              # Left + Right slope
        "description": "Rafters running from ridge to eaves"
    },
    
    "Mittelpfosten": {
        "body_name": "Body006",
        "semantic_label": 4,
        "count": "Mittelpfosten_Count",
        "y_spacing": "auto",
        "x_mirror": False,             # Centered posts
        "description": "Center support posts"
    },
    
    "Seitenpfosten": {
        "body_name": "Body005",
        "semantic_label": 5,
        "count": "Seitenpfosten_Count",
        "y_spacing": "auto",
        "x_mirror": True,              # Left + Right walls
        "description": "Side wall support posts"
    },
}

# ============================================================================
# DERIVED PARAMETERS
# ============================================================================
# Some parameters can be computed from others (e.g., spacing = length / count)

def compute_derived_parameters(sampled_params: dict) -> dict:
    """
    Compute any derived parameters after sampling.
    
    Args:
        sampled_params: Dictionary of sampled parameter values
        
    Returns:
        Updated dictionary with derived values added
    """
    derived = sampled_params.copy()
    
    # Auto-spacing for beams
    for beam_type, beam_config in BEAMS.items():
        if beam_config.get("y_spacing") == "auto":
            count_key = beam_config["count"]
            if isinstance(count_key, str):  # It's a parameter reference
                count = int(derived[count_key])
                # Use Firstpfette length as reference for spacing
                length = derived["Firstpfette_Length"]
                # Distribute evenly in positive Y direction with margins
                # Formula: margin + (count-1)*spacing + margin <= length
                # Therefore: spacing = (length - 2*margin) / (count - 1)
                margin = 500  # mm from each end
                spacing = (length - 2*margin) / max(count - 1, 1)
                derived[f"{beam_type}_Spacing"] = spacing
    
    return derived

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate config structure at import time."""
    # Check all beam body references exist
    valid_bodies = {"Body001", "Body002", "Body003", "Body004", "Body005", "Body006"}
    
    for beam_name, beam_config in BEAMS.items():
        body = beam_config["body_name"]
        if body not in valid_bodies:
            raise ValueError(f"Beam '{beam_name}' references unknown body '{body}'")
    
    # Check semantic labels are unique
    labels = [b["semantic_label"] for b in BEAMS.values()]
    if len(labels) != len(set(labels)):
        raise ValueError(f"Duplicate semantic labels found: {labels}")
    
    print("✓ Config validation passed")

# Validate on import
validate_config()