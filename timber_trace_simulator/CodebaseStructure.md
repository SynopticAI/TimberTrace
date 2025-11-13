timber_trace_simulator/
│
├── simulator.py                          # Main orchestrator
├── config.py                             # Global constants, DIN standards, dimensions
│
├── beams/
│   ├── __init__.py
│   ├── base_beam.py                      # Abstract BaseBeam class
│   ├── sparren.py                        # Sparren variants (Pfettendach_Sparren, etc.)
│   ├── pfetten.py                        # Firstpfette, Mittelpfette, Fußpfette
│   ├── stuhlpfosten.py                   # Vertical support posts
│   ├── streben.py                        # Bracing beams
│   └── kehlbalken.py                     # Collar beams (for later)
│
├── generators/
│   ├── __init__.py
│   ├── base_generator.py                 # Abstract base generator interface
│   └── pfettendach_rechteck_generator.py # First concrete generator
│
├── core/
│   ├── __init__.py
│   ├── geometry_utils.py                 # Mesh generation, transformations
│   ├── xml_io.py                         # XML serialization/deserialization
│   └── visualization.py                  # Open3D visualization utilities
│
├── tests/                                # Unit tests
│   └── ...
│
└── examples/
    └── generate_simple_roof.py           # Usage example


# Instead of having generic "Sparren" + separate joint system...
# Have roof-specific beam types that know their joints:

Pfettendach_Sparren:
    - Always has Sparrenkerve (notch) at Pfette connection points
    - Knows it sits ON Pfetten
    
Sparrendach_Sparren:
    - Has ridge lap joint (Firstüberblattung) at peak
    - Knows it connects to opposing Sparren, not Pfetten

Pfette:
    - Receives notches from Sparren
    - Has mortise-tenon connections to Stuhlpfosten
```

**Benefits:**
- Simpler initial implementation
- Construction rules encoded in beam type
- No complex joint-matching logic needed
- Easy to understand which beam goes where

**Trade-off:**
- Some code duplication between similar beams
- Less flexible if you want arbitrary joint combinations
- **BUT** for timber construction, joints ARE standardized by construction type, so this matches reality!

---

## Detailed Component Breakdown

### **1. `config.py`**
```
Purpose: Central configuration and standards
Contents:
  - DIN 4074-1 standard dimensions
  - Material properties (wood species)
  - Beam type enums/constants
  - ML-related mappings (beam_type_id → name)
```

### **2. `beams/base_beam.py`**
```
BaseBeam (Abstract Class):
  Properties:
    - beam_id: int
    - beam_type: str (e.g., "Pfettendach_Sparren")
    - position: np.array([x, y, z])
    - orientation: Quaternion
    - length: float
    - cross_section: (width, height)
    
  Abstract Methods:
    - get_parameters() → dict          # For ML Stage 2
    - get_mesh() → trimesh.Trimesh     # Generate geometry
    - to_xml() → ElementTree.Element   # Serialize
    - from_xml(element) → BaseBeam     # Deserialize (classmethod)
    
  Concrete Methods:
    - transform_point()
    - get_bounding_box()
    - __repr__()
```

### **3. `beams/sparren.py`**
```
class Pfettendach_Sparren(BaseBeam):
    beam_type = "Pfettendach_Sparren"
    
    Additional Properties:
      - pitch_angle: float
      - pfette_connection_points: List[(position, Pfette_id)]
      
    Parameters for ML:
      - length, width, height
      - pitch_angle
      - notch_positions: List[float]  # normalized 0-1
      - notch_depths: List[float]
      
    get_mesh():
      1. Create rectangular beam body
      2. Apply notches at pfette_connection_points
      3. Apply orientation transformation
      4. Return mesh

class Sparrendach_Sparren(BaseBeam):
    beam_type = "Sparrendach_Sparren"
    
    Additional Properties:
      - ridge_connection_type: str  # "lap" or "tenon"
      - opposing_sparren_id: int
      
    Parameters for ML:
      - length, width, height
      - pitch_angle
      - ridge_joint_type: categorical
      
    get_mesh():
      1. Create rectangular beam body
      2. Apply ridge joint geometry (lap or tenon)
      3. Apply orientation transformation
      4. Return mesh
```

### **4. `beams/pfetten.py`**
```
class Firstpfette(BaseBeam):
    beam_type = "Firstpfette"
    
    Additional Properties:
      - sparren_connections: List[(position, Sparren_id)]
      - stuhlpfosten_connections: List[(position, Pfosten_id)]
      
    Parameters for ML:
      - length, width, height
      - mortise_positions: List[float]
      - mortise_sizes: List[(w, h)]
      
    get_mesh():
      1. Create rectangular beam body
      2. Add mortises for Stuhlpfosten connections
      3. Add seats/notches for Sparren
      4. Return mesh

# Similar for Mittelpfette, Fußpfette
```

### **5. `generators/base_generator.py`**
```
class BaseRoofGenerator(ABC):
    """Abstract interface for all roof generators"""
    
    def __init__(self, roof_params: dict):
        self.roof_params = roof_params
        self.beams: List[BaseBeam] = []
        
    @abstractmethod
    def generate(self) -> List[BaseBeam]:
        """Generate beam list for this roof type"""
        pass
        
    def validate_parameters(self):
        """Check if roof_params are valid"""
        pass
        
    def get_roof_metadata(self) -> dict:
        """Return metadata about generated roof"""
        pass
```

### **6. `generators/pfettendach_rechteck_generator.py`**
```
class PfettendachRechteckGenerator(BaseRoofGenerator):
    """
    Generates a simple rectangular Pfettendach
    """
    
    Required params:
      - building_length: float
      - building_width: float
      - roof_pitch: float (degrees)
      - sparren_spacing: float
      - pfetten_count: int (3, 5, 7)
      - support_spacing: float
      
    generate() → List[BaseBeam]:
      Step 1: Calculate derived geometry
        - ridge_height from pitch
        - pfette positions along sparren
        - number of sparren from spacing
        
      Step 2: Generate Pfetten
        - Create Firstpfette at ridge
        - Create Mittelpfetten (if pfetten_count > 3)
        - Create Fußpfetten at eaves
        
      Step 3: Generate Stuhlpfosten
        - Place at support_spacing intervals
        - Connect to Pfetten
        
      Step 4: Generate Sparren
        - Place at sparren_spacing intervals
        - Calculate connection points with Pfetten
        - Create Pfettendach_Sparren instances
        
      Step 5: Generate Streben (optional)
        - Add diagonal bracing
        
      Step 6: Assign beam_ids and connection references
      
      Return: self.beams
```

### **7. `core/xml_io.py`**
```
Functions:
  - save_roof_to_xml(beams: List[BaseBeam], filepath: str)
      Creates XML structure:
        <roof>
          <metadata>
            <generator_type>Pfettendach_Rechteck</generator_type>
            <roof_parameters>...</roof_parameters>
          </metadata>
          <beams>
            <beam id="0" type="Firstpfette">
              <position>...</position>
              <orientation>...</orientation>
              <parameters>...</parameters>
            </beam>
            ...
          </beams>
        </roof>
        
  - load_roof_from_xml(filepath: str) → List[BaseBeam]
      Parses XML, instantiates correct beam classes
      Returns list of reconstructed beams
```

### **8. `core/geometry_utils.py`**
```
Helper functions:
  - create_box_mesh(width, height, length) → trimesh
  - apply_notch(mesh, position, depth, width, angle) → trimesh
  - apply_mortise(mesh, position, width, height, depth) → trimesh
  - apply_tenon(mesh, position, width, height, length) → trimesh
  - apply_transform(mesh, position, orientation) → trimesh
  - calculate_rotation_matrix(pitch, yaw, roll) → np.array
```

### **9. `core/visualization.py`**
```
Functions:
  - visualize_beams(beams: List[BaseBeam], 
                    color_by: str = "beam_type")
      Creates Open3D visualization
      Colors beams by type or instance
      Shows coordinate axes
      
  - visualize_scene_with_labels(beams, show_beam_ids=True)
      Shows beam IDs as text labels
      
  - export_scene_to_obj(beams: List[BaseBeam], filepath: str)
      For external viewing in Blender, etc.
```

### **10. `simulator.py` (Main Orchestrator)**
```
Workflow:
  1. Parse command line args or config
  
  2. Instantiate generator:
       generator = PfettendachRechteckGenerator(roof_params)
       
  3. Generate beams:
       beams = generator.generate()
       
  4. Optional: Save to XML:
       save_roof_to_xml(beams, "output/roof_001.xml")
       
  5. Create scene meshes:
       meshes = [beam.get_mesh() for beam in beams]
       
  6. Visualize:
       visualize_beams(beams, color_by="beam_type")
       
  7. (Later) LiDAR simulation:
       point_cloud = simulate_lidar(beams, scan_params)