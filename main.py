#!/usr/bin/python

import os
import logging
import yaml
import argparse
from pathlib import Path
from dotenv import load_dotenv

from myutils.UT_PCErrorLogging import UT_PCErrorLogging
from ui_struct.UI_UserInput import UI_UserInput
from precice_struct import PS_PreCICEConfig

# Load environment variables
load_dotenv('config.env')

def resolve_path(path_str: str, base_dir: Path = None) -> Path:
    """
    Resolve a path string to an absolute path, optionally relative to a base directory.
    
    :param path_str: Path string to resolve
    :param base_dir: Optional base directory to resolve relative paths against
    :return: Resolved absolute path
    """
    path = Path(path_str)
    
    # If path is already absolute, return it
    if path.is_absolute():
        return path
    
    # If base_dir is provided, resolve relative to it
    if base_dir:
        return (base_dir / path).resolve()
    
    # Otherwise, resolve relative to the script's directory
    return (Path(__file__).parent / path).resolve()

def configure_logging(log_level: str = None, log_file: str = None):
    """
    Configure logging with flexible level and file output.
    
    :param log_level: Logging level (e.g., 'INFO', 'DEBUG')
    :param log_file: Optional log file path
    """
    # Determine log level
    numeric_level = getattr(logging, (log_level or 'INFO').upper(), logging.INFO)
    
    # Configure basic logging
    logging_config = {
        'level': numeric_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    # Add file handler if log file is specified
    if log_file:
        log_path = resolve_path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logging_config['filename'] = str(log_path)
    
    logging.basicConfig(**logging_config)

def run_one_generate(input_file: str = None, output_file: str = None):
    """
    Generate preCICE configuration from a topology file.
    
    :param input_file: Path to input topology YAML
    :param output_file: Path to output XML configuration
    """
    mylog = UT_PCErrorLogging()

    # Resolve input and output paths
    base_dir = Path(__file__).parent
    input_path = resolve_path(input_file or os.getenv('INPUT_TOPOLOGY', './examples/1/topology.yaml'), base_dir)
    output_path = resolve_path(output_file or os.getenv('OUTPUT_XML', './precice-config.xml'), base_dir)

    try: 
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Open and parse the YAML file
        with input_path.open('r') as config_file:
            config = yaml.safe_load(config_file)
        
        logging.info(f"Input YML file: {input_path}")
        logging.info("Building the user input info...")

        user_ui = UI_UserInput()
        user_ui.init_from_yaml(config, mylog)

        # Generate preCICE config
        precice_config = PS_PreCICEConfig()
        logging.info("Generating preCICE config...")
        precice_config.create_config(user_ui)

        # Write XML config
        logging.info(f"Writing preCICE config to {output_path}")
        precice_config.write_precice_xml_config(str(output_path), mylog)

        logging.info("Configuration generation complete")

    except Exception as e:
        logging.error(f"Error during XML generation: {e}")
        raise

def main():
    # Configure logging from environment
    configure_logging(
        log_level=os.getenv('LOG_LEVEL'),
        log_file=os.getenv('LOG_FILE')
    )

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='preCICE Configuration Generator')
    parser.add_argument('--input', help='Input topology YAML file')
    parser.add_argument('--output', help='Output XML configuration file')
    args = parser.parse_args()

    # Generate configuration
    run_one_generate(args.input, args.output)

if __name__ == "__main__":
    main()
