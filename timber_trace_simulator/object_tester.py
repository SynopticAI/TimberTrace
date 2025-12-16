# object_tester.py
"""
Simple script to test beam geometry generation in isolation.
Uses DEFAULT parameters from the class definition (no solver, no randomization).
"""

import os
import sys
import traceback

# Try imports
try:
    from object_definitions import BEAM_TYPES, BEAM_NAMES
except ImportError as e:
    print(f"❌ Could not import object_definitions: {e}")
    sys.exit(1)

try:
    from build123d import export_stl
except ImportError:
    print("❌ build123d not found. Geometry generation will fail.")
    sys.exit(1)

def main():
    print("="*60)
    print("🛠️  TIMBER TRACE OBJECT TESTER")
    print("="*60)
    
    # 1. Select Object
    print("\nAvailable Beam Types:")
    sorted_ids = sorted(BEAM_TYPES.keys())
    for type_id in sorted_ids:
        name = BEAM_NAMES.get(type_id, "Unknown")
        print(f"  [{type_id}] {name}")
    
    try:
        selection = input("\nEnter ID to generate > ")
        type_id = int(selection)
        if type_id not in BEAM_TYPES:
            print(f"❌ Invalid ID: {type_id}")
            return
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return

    # 2. Instantiate with Defaults
    beam_name = BEAM_NAMES[type_id]
    BeamClass = BEAM_TYPES[type_id]
    
    print(f"\nInstantiating '{beam_name}' with default parameters...")
    try:
        beam = BeamClass()
        params = beam.get_parameters()['values']
        
        print("\nParameters used:")
        for k, v in params.items():
            print(f"  • {k:<20}: {v}")
            
    except Exception as e:
        print(f"\n❌ Failed to instantiate class: {e}")
        traceback.print_exc()
        return

    # 3. Generate Geometry
    print("\nAttempting get_model()...")
    try:
        part = beam.get_model()
        print("✅ Geometry generated successfully!")
        
        # FIX: is_valid is a property, not a method
        if hasattr(part, 'is_valid'):
            if not part.is_valid: 
                print("⚠️  Warning: Part reported as invalid (part.is_valid == False)")
    except Exception as e:
        print(f"\n❌ Error in get_model(): {e}")
        traceback.print_exc()
        return

    # 4. Export
    output_filename = f"test_output_{beam_name}.stl"
    print(f"\nExporting to {output_filename}...")
    try:
        export_stl(part, output_filename)
        print(f"✅ Export successful. Open {output_filename} to verify geometry.")
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()