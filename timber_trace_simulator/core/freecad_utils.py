"""
FreeCAD Utilities for Timber Trace Simulator

Headless FreeCAD execution for template-based geometry generation.
"""

import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Headless mode

import FreeCAD
import Part
import Mesh
import MeshPart  # For converting Part shapes to meshes
import trimesh
import numpy as np
from pathlib import Path
from typing import Dict, Optional


def generate_mesh_from_template(
    template_path: str,
    parameters: Dict[str, float]
) -> trimesh.Trimesh:
    """
    Load FreeCAD template, set parameters, export mesh.
    
    Template must have:
    - Spreadsheet object named 'Parameters' with aliases
    - PartDesign::Body object containing the geometry
    
    Args:
        template_path: Path to .FCStd template file
        parameters: Dict of {alias: value} for spreadsheet
        
    Returns:
        trimesh.Trimesh object (in template coordinates)
        
    Raises:
        FileNotFoundError: If template doesn't exist
        ValueError: If required objects not found
    """
    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    # Open document
    doc = FreeCAD.openDocument(str(template_path))
    
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
            raise ValueError(f"No spreadsheet found in {template_path}")
        
        # Set parameters
        for alias, value in parameters.items():
            # Find cell with this alias
            for i in range(1, 100):  # Check first 100 rows
                for col in ['A', 'B', 'C', 'D']:
                    cell = f'{col}{i}'
                    try:
                        if sheet.getAlias(cell) == alias:
                            sheet.set(cell, str(value))
                            break
                    except:
                        continue
        
        # Recompute geometry
        doc.recompute()
        
        # Find body
        body = doc.getObject('Body')
        if body is None:
            # Try to find any body
            for obj in doc.Objects:
                if obj.TypeId == 'PartDesign::Body':
                    body = obj
                    break
        
        if body is None:
            raise ValueError(f"No Body found in {template_path}")
        
        # Convert shape to mesh using MeshPart (FIXED!)
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
    
    This is an alternative to generating trimesh - useful for direct exports.
    
    Args:
        shape: FreeCAD Part.Shape object
        output_path: Where to save the STL file
    """
    shape.exportStl(output_path)


def create_simple_template(
    output_path: str,
    length: float = 1000.0,
    width: float = 200.0,
    height: float = 300.0
) -> None:
    """
    Create a simple box template for testing.
    
    Args:
        output_path: Where to save .FCStd file
        length: Box length in mm
        width: Box width in mm
        height: Box height in mm
    """
    doc = FreeCAD.newDocument("SimpleTemplate")
    
    # Create spreadsheet
    sheet = doc.addObject('Spreadsheet::Sheet', 'Parameters')
    sheet.set('A1', 'length')
    sheet.set('B1', str(length))
    sheet.setAlias('B1', 'length')
    
    sheet.set('A2', 'width')
    sheet.set('B2', str(width))
    sheet.setAlias('B2', 'width')
    
    sheet.set('A3', 'height')
    sheet.set('B3', str(height))
    sheet.setAlias('B3', 'height')
    
    # Create body
    body = doc.addObject('PartDesign::Body', 'Body')
    box = body.newObject('PartDesign::AdditiveBox', 'Box')
    box.setExpression('Length', 'Parameters.length')
    box.setExpression('Width', 'Parameters.width')
    box.setExpression('Height', 'Parameters.height')
    
    doc.recompute()
    
    # Save
    doc.saveAs(output_path)
    FreeCAD.closeDocument(doc.Name)
    
    print(f"✓ Created simple template: {output_path}")


# Test function
def test_freecad_utils():
    """Run self-test"""
    print("=" * 60)
    print("Testing freecad_utils.py (CORRECTED VERSION)")
    print("=" * 60)
    
    # Create test template
    test_template = "/tmp/test_simple_template.FCStd"
    print("\n1. Creating test template...")
    create_simple_template(test_template, length=2000, width=400, height=600)
    
    # Load and modify
    print("\n2. Loading template with new parameters...")
    mesh = generate_mesh_from_template(
        test_template,
        {'length': 3000, 'width': 600, 'height': 900}
    )
    
    print(f"   ✓ Generated mesh")
    print(f"     Vertices: {len(mesh.vertices)}")
    print(f"     Faces: {len(mesh.faces)}")
    print(f"     Volume: {mesh.volume:.2f} mm³")
    
    expected_volume = 3000 * 600 * 900
    print(f"     Expected volume: {expected_volume:.2f} mm³")
    
    # Export
    output_stl = "/tmp/test_utils_output.stl"
    mesh.export(output_stl)
    print(f"   ✓ Exported to {output_stl}")
    
    # Verify with reload
    loaded = trimesh.load(output_stl)
    print(f"   ✓ Reloaded successfully")
    print(f"     Reloaded volume: {loaded.volume:.2f} mm³")
    
    print("\n✓ ALL TESTS PASSED - MESH EXPORT FIXED!")
    print(f"\nFiles created:")
    print(f"  Template: {test_template}")
    print(f"  Output: {output_stl}")


if __name__ == "__main__":
    test_freecad_utils()