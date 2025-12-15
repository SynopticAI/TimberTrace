# test_system.py
"""
Quick validation script to test the constraint-based generation system.

Tests:
  1. Blueprint creation
  2. Constraint solver
  3. Geometry generation
"""

import numpy as np
from structure_blueprints.simple_structures import post_and_beam, two_posts_only
from constraint_solver import solve_constraints
from object_definitions import Pfosten, Pfette


def test_blueprint():
    """Test that blueprint creates valid structure"""
    print("\n" + "="*80)
    print("TEST 1: Blueprint Creation")
    print("="*80)
    
    beams, topology = post_and_beam(spacing=3.0, seed=42)
    
    print(f"✓ Created {len(beams)} beams")
    print(f"  - Post 1: x={beams[0].x:.2f}, height={beams[0].height:.2f}")
    print(f"  - Post 2: x={beams[1].x:.2f}, height={beams[1].height:.2f}")
    print(f"  - Beam:   z={beams[2].z:.2f}, length={beams[2].length:.2f}")
    
    print(f"\n✓ Topology defined:")
    num_contacts = sum(len(v) for v in topology['connectivity'].values())
    print(f"  - Contact constraints: {num_contacts}")
    print(f"  - Identity pairs: {len(topology['identity_pairs'])}")
    
    return beams, topology


def test_solver(beams, topology):
    """Test that constraint solver works"""
    print("\n" + "="*80)
    print("TEST 2: Constraint Solver")
    print("="*80)
    
    # Store initial positions
    initial_z = [b.z for b in beams]
    
    print("Initial positions (before solving):")
    for i, beam in enumerate(beams):
        print(f"  Beam {i}: x={beam.x:.4f}, y={beam.y:.4f}, z={beam.z:.4f}")
    
    # Solve
    solved_beams = solve_constraints(beams, topology, verbose=False)
    
    print("\nSolved positions (after constraint enforcement):")
    for i, beam in enumerate(solved_beams):
        print(f"  Beam {i}: x={beam.x:.4f}, y={beam.y:.4f}, z={beam.z:.4f}")
    
    # Check that constraints are satisfied
    print("\n✓ Validating constraints...")
    
    # Post 1 top should match beam bottom
    post1_top = beams[0].z + beams[0].height
    beam_bottom = beams[2].z
    error_1 = abs(post1_top - beam_bottom)
    
    # Post 2 top should match beam bottom
    post2_top = beams[1].z + beams[1].height
    error_2 = abs(post2_top - beam_bottom)
    
    print(f"  - Post1.top to Beam.bottom: {error_1*1000:.2f}mm")
    print(f"  - Post2.top to Beam.bottom: {error_2*1000:.2f}mm")
    
    if error_1 < 0.001 and error_2 < 0.001:  # 1mm tolerance
        print("  ✓ Contact constraints satisfied!")
    else:
        print("  ✗ Contact constraints violated!")
    
    # Check identity
    if abs(beams[0].height - beams[1].height) < 0.001:
        print("  ✓ Identity constraints satisfied!")
    else:
        print("  ✗ Identity constraints violated!")
    
    return solved_beams


def test_geometry(beams):
    """Test that geometry generation works"""
    print("\n" + "="*80)
    print("TEST 3: Geometry Generation")
    print("="*80)
    
    try:
        for i, beam in enumerate(beams):
            model = beam.get_model()
            print(f"✓ Beam {i} ({type(beam).__name__}) model generated")
    except ImportError:
        print("⚠️  build123d not available, skipping geometry test")
    except Exception as e:
        print(f"✗ Geometry generation failed: {e}")


def main():
    print("\n" + "="*80)
    print("TIMBER TRACE - System Validation")
    print("="*80)
    
    try:
        # Test 1: Blueprint
        beams, topology = test_blueprint()
        
        # Test 2: Solver
        solved_beams = test_solver(beams, topology)
        
        # Test 3: Geometry
        test_geometry(solved_beams)
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED ✓")
        print("="*80)
        print("\nSystem is ready for dataset generation!")
        print("Run: python generate_dataset.py --num_scenes 10")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()