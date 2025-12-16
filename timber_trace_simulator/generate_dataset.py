# generate_dataset.py
"""
Command-line interface for generating training datasets.
"""

import argparse
from scene_generator import generate_scenes
from structure_blueprints import simple_structures
from structure_blueprints import pfettendach

def main():
    parser = argparse.ArgumentParser(
        description="Generate constraint-based timber structure dataset"
    )
    
    parser.add_argument(
        '--blueprint',
        type=str,
        default='post_and_beam',
        choices=['post_and_beam', 'two_posts_only', 'sparren_on_pfette_on_pfosten', 'half_pfettendach', 'pfettendach'],
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
        help='Perturbation scale (fraction of parameter range)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed solver output'
    )

    # Flag for pre-solve export
    parser.add_argument(
        '--export-presolve',
        action='store_true',
        help='Export scene geometry before constraint solving'
    )
    
    args = parser.parse_args()
    
    # === INTERACTIVE PROMPT ===
    # If the user didn't specify the flag, ask them interactively
    export_presolve = args.export_presolve
    if not export_presolve:
        print("\nDEBUG OPTION:")
        user_input = input("Also Export Scene before constraint solving ? (y)es or (n)o > ").strip().lower()
        if user_input.startswith('y'):
            export_presolve = True

    # Get blueprint function
    if args.blueprint == 'post_and_beam':
        blueprint_func = simple_structures.post_and_beam
    elif args.blueprint == 'two_posts_only':
        blueprint_func = getattr(simple_structures, 'two_posts_only', None)
    elif args.blueprint == 'sparren_on_pfette_on_pfosten':
        blueprint_func = simple_structures.sparren_on_pfette_on_pfosten
    elif args.blueprint == 'half_pfettendach':
        blueprint_func = simple_structures.half_pfettendach
    elif args.blueprint == 'pfettendach':
        blueprint_func = pfettendach.create_pfettendach
    else:
        raise ValueError(f"Unknown blueprint: {args.blueprint}")
    
    print("="*80)
    print("TIMBER TRACE - Constraint-Based Dataset Generator")
    print("="*80)
    print(f"Blueprint:     {args.blueprint}")
    print(f"Num scenes:    {args.num_scenes}")
    print(f"Output dir:    {args.output_dir}")
    print(f"Perturbation:  ±{args.perturbation*100:.1f}%")
    print(f"Export Pre:    {export_presolve}")
    print("="*80)
    
    # Generate dataset
    generate_scenes(
        blueprint_func=blueprint_func,
        num_scenes=args.num_scenes,
        output_dir=args.output_dir,
        perturbation_scale=args.perturbation,
        solver_verbose=args.verbose,
        export_presolve=export_presolve
    )


if __name__ == "__main__":
    main()