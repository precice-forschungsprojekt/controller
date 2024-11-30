import os
import sys
import argparse
import json
import yaml
import logging
from typing import Optional, Dict, Any

from config_generator import PreciceConfigGenerator, TopologyGeneratorConfig

def setup_logging(log_level: str = 'INFO'):
    """
    Configure logging based on specified log level
    
    :param log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('topology_generator_cli.log', mode='a')
        ]
    )

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON or YAML file
    
    :param config_path: Path to configuration file
    :return: Configuration dictionary
    """
    if not config_path:
        return {}
    
    file_ext = os.path.splitext(config_path)[1].lower()
    
    try:
        with open(config_path, 'r') as f:
            if file_ext in ['.json']:
                return json.load(f)
            elif file_ext in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported configuration file type: {file_ext}")
    except (IOError, json.JSONDecodeError, yaml.YAMLError) as e:
        logging.error(f"Error loading configuration file: {e}")
        sys.exit(1)

def validate_topology(topology_file: str):
    """
    Validate topology configuration without generating files
    
    :param topology_file: Path to topology configuration file
    """
    try:
        generator = PreciceConfigGenerator(topology_file)
        print("✅ Topology configuration is valid!")
    except Exception as e:
        print(f"❌ Topology configuration validation failed: {e}")
        sys.exit(1)

def main():
    """
    CLI entry point for topology configuration generator
    """
    parser = argparse.ArgumentParser(
        description='preCICE Topology Configuration Generator',
        epilog='Generate and validate simulation topology configurations'
    )
    
    # Topology file (required)
    parser.add_argument(
        'topology', 
        type=str, 
        help='Path to topology configuration file (YAML)'
    )
    
    # Optional configuration file
    parser.add_argument(
        '-c', '--config', 
        type=str, 
        help='Path to generator configuration file (JSON/YAML)'
    )
    
    # Output directory
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        help='Custom output directory for generated files'
    )
    
    # Logging level
    parser.add_argument(
        '-l', '--log-level', 
        type=str, 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging verbosity'
    )
    
    # Validation-only mode
    parser.add_argument(
        '-v', '--validate', 
        action='store_true', 
        help='Validate topology configuration without generating files'
    )
    
    # Dry run mode
    parser.add_argument(
        '-n', '--dry-run', 
        action='store_true', 
        help='Simulate configuration generation without writing files'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load generator configuration
    generator_config = load_config(args.config)
    
    # Validate-only mode
    if args.validate:
        validate_topology(args.topology)
        return
    
    try:
        # Initialize generator
        generator = PreciceConfigGenerator(
            args.topology, 
            output_dir=args.output,
            generator_config=generator_config
        )
        
        # Dry run mode
        if args.dry_run:
            print("🏃 Dry run mode: Simulating configuration generation")
            print(json.dumps(generator_config, indent=2))
            return
        
        # Generate configuration
        result = generator.generate()
        
        # Print generated file paths
        print("🚀 Configuration Generated Successfully!")
        for key, path in result.items():
            print(f"- {key.replace('_', ' ').title()}: {path}")
    
    except Exception as e:
        logging.error(f"Configuration generation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
