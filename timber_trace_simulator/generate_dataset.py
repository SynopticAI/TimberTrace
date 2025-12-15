# generate_dataset.py
"""
Command-line interface for generating training datasets.

Usage:
    python generate_dataset.py

This will generate scenes using the post_and_beam blueprint.
"""

import argparse
from scene_generator import generate_scenes
from structure_blueprints import simple_structures


def main():
    parser = argparse.ArgumentParser(
        description="Generate constraint-based timber structure dataset"
    )
    
    parser.add_argument(
        '--blueprint',
        type=str,
        default='post_and_beam',
        choices=['post_and_beam', 'two_posts_only'],
        help='Structure blueprint to use'
    )
    
    parser.add_argument(
        '--num_scenes',
        type=int,
        default=50,
        help='Number of scene variations to generate'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default='training_data',
        help='Output directory for dataset'
    )
    
    parser.add_argument(
        '--perturbation',
        type=float,
        default=0.05,
        help='Perturbation scale (fraction of parameter range, e.g., 0.05 = ±5%%)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed solver output'
    )
    
    args = parser.parse_args()
    
    # Get blueprint function
    if args.blueprint == 'post_and_beam':
        blueprint_func = simple_structures.post_and_beam
    elif args.blueprint == 'two_posts_only':
        blueprint_func = simple_structures.two_posts_only
    else:
        raise ValueError(f"Unknown blueprint: {args.blueprint}")
    
    print("="*80)
    print("TIMBER TRACE - Constraint-Based Dataset Generator")
    print("="*80)
    print(f"Blueprint:     {args.blueprint}")
    print(f"Num scenes:    {args.num_scenes}")
    print(f"Output dir:    {args.output_dir}")
    print(f"Perturbation:  ±{args.perturbation*100:.1f}%")
    print("="*80)
    
    # Generate dataset
    generate_scenes(
        blueprint_func=blueprint_func,
        num_scenes=args.num_scenes,
        output_dir=args.output_dir,
        perturbation_scale=args.perturbation,
        solver_verbose=args.verbose
    )


if __name__ == "__main__":
    main()