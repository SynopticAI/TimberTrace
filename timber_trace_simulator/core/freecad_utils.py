"""
FreeCAD Utilities for Timber Trace Simulator

Headless FreeCAD execution for master file-based geometry generation.
"""

import sys
import os

# Add project to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Find FreeCAD installation
conda_prefix = os.environ.get('CONDA_PREFIX')
if conda_prefix:
    freecad_lib = os.path.join(conda_prefix, 'Library', 'bin')
    sys.path.insert(0, freecad_lib)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Headless mode

import FreeCAD
import Part
import Mesh
import MeshPart
import trimesh
import numpy as np
from pathlib import Path
from typing import Dict, Optional


def generate_mesh_from_master(
    master_file: str,
    body_name: str,
    param_updates: Optional[Dict[str, float]] = None
) -> trimesh.Trimesh:
    """
    Load master FreeCAD file, update parameters, export specific body.
    
    Args:
        master_file: Path to Master_Pfettendach.FCStd
        body_name: Name of Body object to export (e.g., "Mittelpfosten")
        param_updates: Dict of {spreadsheet_alias: new_value} (optional)
        
    Returns:
        trimesh.Trimesh in template coordinates
    """
    master_path = Path(master_file)
    if not master_path.exists():
        raise FileNotFoundError(f"Master file not found: {master_path}")
    
    # Open document
    doc = FreeCAD.openDocument(str(master_path))
    
    try:
        # Find spreadsheet
        sheet = None
        for obj in doc.Objects:
            if obj.TypeId == 'Spreadsheet::Sheet':
                sheet = obj
                break
        
        if sheet is None:
            raise ValueError(f"No spreadsheet found in {master_path}")
        
        # Update parameters if provided
        if param_updates:
            for alias, value in param_updates.items():
                cell_found = False
                for i in range(1, 100):
                    for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                        cell = f'{col}{i}'
                        try:
                            if sheet.getAlias(cell) == alias:
                                sheet.set(cell, str(value))
                                cell_found = True
                                break
                        except:
                            continue
                    if cell_found:
                        break
                
                if not cell_found:
                    print(f"Warning: Alias '{alias}' not found in spreadsheet")
        
        # Find body
        body = doc.getObject(body_name)
        if body is None or body.TypeId != 'PartDesign::Body':
            available_bodies = [obj.Name for obj in doc.Objects 
                              if obj.TypeId == 'PartDesign::Body']
            raise ValueError(f"Body '{body_name}' not found. "
                           f"Available: {available_bodies}")
        
        # CRITICAL FIX: Recompute AFTER finding body but BEFORE accessing shape
        doc.recompute()
        body.recompute()  # Recompute the body itself
        
        # Try to get shape - use Tip if available
        shape = None
        if hasattr(body, 'Tip') and body.Tip is not None:
            print(f"   Using body.Tip.Shape for {body_name}")
            shape = body.Tip.Shape
        else:
            print(f"   Using body.Shape for {body_name}")
            shape = body.Shape
        
        # Check if shape is valid
        if shape is None or shape.isNull():
            # Debug: print body state
            print(f"   Body state: {body.State}")
            if hasattr(body, 'Group'):
                print(f"   Body features: {[f.Name for f in body.Group]}")
            raise ValueError(f"Body '{body_name}' has no valid shape. "
                           f"Check FreeCAD file for errors.")
        
        print(f"   Shape valid: {not shape.isNull()}, BoundBox: {shape.BoundBox}")
        
        # Convert to mesh
        mesh_obj = MeshPart.meshFromShape(
            Shape=shape,
            LinearDeflection=0.1,
            AngularDeflection=0.5,
            Relative=False
        )
        
        # Check if mesh is empty
        if len(mesh_obj.Points) == 0:
            raise ValueError(f"Mesh tessellation produced 0 points for {body_name}")
        
        # Convert to numpy
        vertices = np.array([[p.x, p.y, p.z] for p in mesh_obj.Points])
        faces = np.array([[f.PointIndices[0], f.PointIndices[1], f.PointIndices[2]] 
                         for f in mesh_obj.Facets])
        
        # Create trimesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        print(f"   ✓ Created mesh: {len(vertices)} verts, {len(faces)} faces")
        
        return mesh
        
    finally:
        FreeCAD.closeDocument(doc.Name)


def export_shape_to_stl(shape: Part.Shape, output_path: str) -> None:
    """Export FreeCAD shape directly to STL file."""
    shape.exportStl(output_path)


def list_bodies_in_master(master_file: str) -> list:
    """List all Body objects in master file."""
    master_path = Path(master_file)
    if not master_path.exists():
        raise FileNotFoundError(f"Master file not found: {master_path}")
    
    doc = FreeCAD.openDocument(str(master_path))
    
    try:
        bodies = [(obj.Name, obj.Label) for obj in doc.Objects 
                 if obj.TypeId == 'PartDesign::Body']
        return bodies
    finally:
        FreeCAD.closeDocument(doc.Name)


def list_spreadsheet_aliases(master_file: str) -> dict:
    """List all spreadsheet aliases in master file."""
    master_path = Path(master_file)
    if not master_path.exists():
        raise FileNotFoundError(f"Master file not found: {master_path}")
    
    doc = FreeCAD.openDocument(str(master_path))
    
    try:
        sheet = None
        for obj in doc.Objects:
            if obj.TypeId == 'Spreadsheet::Sheet':
                sheet = obj
                break
        
        if sheet is None:
            return {}
        
        aliases = {}
        for i in range(1, 100):
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                cell = f'{col}{i}'
                try:
                    alias = sheet.getAlias(cell)
                    if alias:
                        value = sheet.get(cell)
                        aliases[alias] = value
                except:
                    continue
        
        return aliases
    finally:
        FreeCAD.closeDocument(doc.Name)


def debug_body_features(master_file: str, body_name: str):
    """Debug helper to inspect body features."""
    doc = FreeCAD.openDocument(master_file)
    
    try:
        body = doc.getObject(body_name)
        if body is None:
            print(f"Body {body_name} not found!")
            return
        
        print(f"\n🔍 Debugging Body: {body_name}")
        print(f"   Type: {body.TypeId}")
        print(f"   Label: {body.Label}")
        print(f"   State: {body.State}")
        
        if hasattr(body, 'Group'):
            print(f"   Features in body:")
            for feat in body.Group:
                print(f"     - {feat.Name} ({feat.TypeId})")
                if hasattr(feat, 'Shape'):
                    try:
                        print(f"       Shape valid: {not feat.Shape.isNull()}")
                    except:
                        print(f"       Shape: Error accessing")
        
        if hasattr(body, 'Tip'):
            print(f"   Tip: {body.Tip}")
            if body.Tip:
                print(f"   Tip Shape valid: {not body.Tip.Shape.isNull()}")
        
        print(f"   Body.Shape valid: {not body.Shape.isNull()}")
        
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_master_file_workflow():
    """Test master file workflow."""
    print("=" * 60)
    print("Testing Master File Workflow")
    print("=" * 60)
    
    master_file = "freecad_templates/Master_Pfettendach.FCStd"
    
    if not Path(master_file).exists():
        print(f"\n⚠ Master file not found: {master_file}")
        return
    
    print(f"\n1. Listing bodies in master file...")
    bodies = list_bodies_in_master(master_file)
    print(f"   Found {len(bodies)} bodies:")
    for name, label in bodies:
        print(f"     - {name} (Label: {label})")
    
    print(f"\n2. Listing spreadsheet aliases...")
    aliases = list_spreadsheet_aliases(master_file)
    print(f"   Found {len(aliases)} aliases:")
    for alias, value in list(aliases.items())[:10]:
        print(f"     {alias}: {value}")
    
    # TEST WITH ACTUAL BEAM BODIES (skip empty "Body")
    test_bodies = ['Body002', 'Body006']  # Firstpfette, Mittelpfosten
    
    for body_name in test_bodies:
        print(f"\n3. Testing body: {body_name}...")
        debug_body_features(master_file, body_name)
        
        print(f"\n4. Generating mesh from {body_name}...")
        try:
            mesh = generate_mesh_from_master(
                master_file=master_file,
                body_name=body_name,
                param_updates=None
            )
            
            print(f"   ✓ Mesh generated successfully")
            print(f"     Vertices: {len(mesh.vertices)}")
            print(f"     Faces: {len(mesh.faces)}")
            print(f"     Volume: {mesh.volume:.2f} mm³")
            print(f"     Bounds: {mesh.bounds}")
            
            # Export test
            output_path = f"/tmp/test_{body_name}.stl"
            mesh.export(output_path)
            print(f"   ✓ Exported to {output_path}")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✓ Test complete!")

if __name__ == "__main__":
    test_master_file_workflow()