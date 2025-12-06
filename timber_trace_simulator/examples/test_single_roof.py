"""
Test Single Roof Generation

Simple test script to validate the config-based roof generation system.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from roof_generator import RoofGenerator


def test_single_roof():
    """
    Generate a single roof and export for visualization.
    """
    print("=" * 70)
    print("TimberTrace - Single Roof Generation Test")
    print("=" * 70)
    
    # Step 1: Import config
    print("\n📋 Loading configuration...")
    try:
        import configs.pfettendach_config as config
        print(f"  ✓ Config loaded")
        print(f"    Parameters: {len(config.PARAMETERS)}")
        print(f"    Beam types: {len(config.BEAMS)}")
    except Exception as e:
        print(f"  ✗ Failed to load config: {e}")
        return
    
    # Step 2: Create generator
    print("\n🏗 Initializing generator...")
    try:
        generator = RoofGenerator(config)
    except Exception as e:
        print(f"  ✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Generate roof
    print("\n🎲 Generating roof...")
    try:
        roof_data = generator.generate_roof(seed=42)
        
        print("\n📊 Generation Summary:")
        print(f"  Total beams: {roof_data['metadata']['total_beams']}")
        print(f"  Beam breakdown:")
        
        # Count by type
        type_counts = {}
        for beam in roof_data['beams']:
            beam_type = beam['beam_type']
            type_counts[beam_type] = type_counts.get(beam_type, 0) + 1
        
        for beam_type, count in type_counts.items():
            print(f"    {beam_type}: {count}")
        
    except Exception as e:
        print(f"  ✗ Failed to generate: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Export visualization
    print("\n💾 Exporting visualization...")
    try:
        output_file = "test_roof_output.ply"
        generator.export_visualization(roof_data, output_file)
        
        print(f"\n✓ Test complete!")
        print(f"  Visualization saved to: {output_file}")
        print(f"  Open in MeshLab/CloudCompare to view")
        
    except Exception as e:
        print(f"  ✗ Failed to export: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Show sample parameters
    print("\n📝 Sample parameters (first 10):")
    for i, (key, val) in enumerate(list(roof_data['parameters'].items())[:10]):
        print(f"  {key}: {val:.2f}")
    print("  ...")
    
    print("\n" + "=" * 70)
    print("🎉 Test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_single_roof()
