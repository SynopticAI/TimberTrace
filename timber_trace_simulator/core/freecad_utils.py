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
import MeshPart  # For converting Part shapes to meshes
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
    
    Master file must have:
    - Spreadsheet object named 'Parameters' with aliases
    - Multiple PartDesign::Body objects (one for each beam type)
    
    Args:
        master_file: Path to Master_Pfettendach.FCStd
        body_name: Name of Body object to export (e.g., "Mittelpfosten")
        param_updates: Dict of {spreadsheet_alias: new_value} (optional)
        
    Returns:
        trimesh.Trimesh in template coordinates (before world positioning)
        
    Raises:
        FileNotFoundError: If master file doesn't exist
        ValueError: If required objects not found
    """
    master_path = Path(master_file)
    if not master_path.exists():
        raise FileNotFoundError(f"Master file not found: {master_path}")
    
    # Open document
    doc = FreeCAD.openDocument(str(master_path))
    doc.recompute()
    
    try:
        # Find spreadsheet
        sheet = doc.getObject('Parameters')
        if sheet is None:
            # Try to find any spreadsheet
            for obj in doc.Objects:
                if obj.TypeId == 'Spreadsheet::Sheet':
                    sheet = obj
                    break
        
        if sheet is None:
            raise ValueError(f"No spreadsheet found in {master_path}")
        
        # Update parameters if provided
        if param_updates:
            for alias, value in param_updates.items():
                # Find cell with this alias
                cell_found = False
                for i in range(1, 100):  # Check first 100 rows
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
        
        # Recompute geometry
        doc.recompute()
        
        # Find specific body by name
        body = doc.getObject(body_name)
        if body is None or body.TypeId != 'PartDesign::Body':
            # List available bodies for debugging
            available_bodies = [obj.Name for obj in doc.Objects 
                              if obj.TypeId == 'PartDesign::Body']
            raise ValueError(f"Body '{body_name}' not found in {master_path}. "
                           f"Available bodies: {available_bodies}")
        
        # Convert shape to mesh using MeshPart
        mesh_obj = MeshPart.meshFromShape(
            Shape=body.Shape,
            LinearDeflection=0.1,  # 0.1mm tolerance
            AngularDeflection=0.5,  # degrees
            Relative=False
        )
        
        # Convert to numpy arrays
        vertices = np.array([[p.x, p.y, p.z] for p in mesh_obj.Points])
        faces = np.array([[f.PointIndices[0], f.PointIndices[1], f.PointIndices[2]] 
                         for f in mesh_obj.Facets])
        
        # Create trimesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        return mesh
        
    finally:
        # Always close document
        FreeCAD.closeDocument(doc.Name)


def export_shape_to_stl(shape: Part.Shape, output_path: str) -> None:
    """
    Export FreeCAD shape directly to STL file.
    
    Args:
        shape: FreeCAD Part.Shape object
        output_path: Where to save the STL file
    """
    shape.exportStl(output_path)


def list_bodies_in_master(master_file: str) -> list:
    """
    List all Body objects in master file for debugging.
    
    Args:
        master_file: Path to Master_Pfettendach.FCStd
        
    Returns:
        List of body names
    """
    master_path = Path(master_file)
    if not master_path.exists():
        raise FileNotFoundError(f"Master file not found: {master_path}")
    
    doc = FreeCAD.openDocument(str(master_path))
    
    try:
        bodies = [obj.Name for obj in doc.Objects 
                 if obj.TypeId == 'PartDesign::Body']
        return bodies
    finally:
        FreeCAD.closeDocument(doc.Name)


def list_spreadsheet_aliases(master_file: str) -> dict:
    """
    List all spreadsheet aliases in master file for debugging.
    
    Args:
        master_file: Path to Master_Pfettendach.FCStd
        
    Returns:
        Dict of {alias: value}
    """
    master_path = Path(master_file)
    if not master_path.exists():
        raise FileNotFoundError(f"Master file not found: {master_path}")
    
    doc = FreeCAD.openDocument(str(master_path))
    
    try:
        sheet = doc.getObject('Parameters')
        if sheet is None:
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


# Test function
def test_master_file_workflow():
    """Test master file workflow (requires actual master file)"""
    print("=" * 60)
    print("Testing Master File Workflow")
    print("=" * 60)
    
    # This test requires an actual Master_Pfettendach.FCStd file
    master_file = "freecad_templates/Master_Pfettendach.FCStd"
    
    if not Path(master_file).exists():
        print(f"\n⚠ Master file not found: {master_file}")
        print("  Create the master file first to run this test.")
        return
    
    print(f"\n1. Listing bodies in master file...")
    bodies = list_bodies_in_master(master_file)
    print(f"   Found {len(bodies)} bodies:")
    for body in bodies:
        print(f"     - {body}")
    
    print(f"\n2. Listing spreadsheet aliases...")
    aliases = list_spreadsheet_aliases(master_file)
    print(f"   Found {len(aliases)} aliases:")
    for alias, value in list(aliases.items())[:10]:  # Show first 10
        print(f"     {alias}: {value}")
    
    if bodies:
        print(f"\n3. Generating mesh from first body: {bodies[0]}...")
        try:
            mesh = generate_mesh_from_master(
                master_file=master_file,
                body_name=bodies[0],
                param_updates=None  # Use default values
            )
            
            print(f"   ✓ Mesh generated successfully")
            print(f"     Vertices: {len(mesh.vertices)}")
            print(f"     Faces: {len(mesh.faces)}")
            print(f"     Volume: {mesh.volume:.2f} mm³")
            
            # Export test
            output_path = "/tmp/test_master_workflow.stl"
            mesh.export(output_path)
            print(f"   ✓ Exported to {output_path}")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print("\n✓ Test complete!")


if __name__ == "__main__":
    test_master_file_workflow()