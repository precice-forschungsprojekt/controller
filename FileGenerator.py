#!/usr/bin/python

import os
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv
from StructureHandler import StructureHandler
from precice_struct import PS_PreCICEConfig
from ui_struct.UI_UserInput import UI_UserInput
from myutils.UT_PCErrorLogging import UT_PCErrorLogging
from Logger import Logger
import shutil
import sys

# Load environment variables securely
load_dotenv('config.env', override=False)

def resolve_path(path_str: str, base_dir: Path = None, create: bool = False, 
                 must_exist: bool = False, file_type: str = None) -> Path:
    """
    Securely resolve and validate file paths.
    
    :param path_str: Path string to resolve
    :param base_dir: Optional base directory to resolve relative paths against
    :param create: Create directory/file if it doesn't exist
    :param must_exist: Require the path to already exist
    :param file_type: Optional type constraint ('dir', 'file')
    :return: Resolved absolute path
    :raises ValueError: For invalid path configurations
    :raises PermissionError: For unauthorized path access
    """
    # Sanitize input path
    path_str = str(path_str).strip()
    
    # Prevent path traversal attacks
    if '..' in path_str or path_str.startswith('/'):
        raise ValueError(f"Potentially unsafe path: {path_str}")
    
    # Resolve path
    path = Path(path_str)
    if not path.is_absolute():
        # Use base directory if provided, otherwise use script directory
        base = base_dir or Path(__file__).parent
        path = (base / path).resolve()
    
    # Normalize and resolve to absolute path
    path = path.resolve()
    
    # Validate path is within project root
    project_root = Path(__file__).parent.resolve()
    try:
        path.relative_to(project_root)
    except ValueError:
        raise PermissionError(f"Path {path} is outside project root")
    
    # Type-specific checks
    if file_type == 'dir' and not path.is_dir():
        if create:
            path.mkdir(parents=True, exist_ok=True)
        elif must_exist:
            raise ValueError(f"Directory not found: {path}")
    
    elif file_type == 'file' and not path.is_file():
        if create:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        elif must_exist:
            raise ValueError(f"File not found: {path}")
    
    return path

class FileGenerator:
    def __init__(self, file: Path, 
                 topology_dir: str = None, 
                 generated_dir: str = None):
        """
        Initialize FileGenerator with secure path handling.
        
        :param file: Input YAML file for configuration
        :param topology_dir: Optional topology directory path
        :param generated_dir: Optional generated files directory path
        """
        # Secure base directory resolution
        self.base_dir = Path(__file__).parent.resolve()
        
        # Resolve input file with strict validation
        self.input_file = resolve_path(
            str(file), 
            self.base_dir, 
            must_exist=True, 
            file_type='file'
        )
        
        # Resolve topology directory with security checks
        self.topology_dir = resolve_path(
            topology_dir or os.getenv('TOPOLOGY_DIR', './topologies'),
            self.base_dir,
            create=True,
            file_type='dir'
        )
        
        # Resolve generated directory with security checks
        self.generated_dir = resolve_path(
            generated_dir or os.getenv('GENERATED_DIR', './_generated'),
            self.base_dir,
            create=True,
            file_type='dir'
        )
        
        # Secure logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    resolve_path(
                        os.getenv('LOG_FILE', './logs/file_generator.log'), 
                        self.base_dir, 
                        create=True, 
                        file_type='file'
                    )
                )
            ]
        )
        
        # Initialize components
        self.precice_config = PS_PreCICEConfig()
        self.mylog = UT_PCErrorLogging()
        self.user_ui = UI_UserInput()
        self.logger = Logger()
        self.structure_handler = StructureHandler()

    def generate_precice_config(self) -> None:
        """Generates the precice-config.xml file based on the topology.yaml file."""
        
        # Try to open the yaml file and get the configuration
        try:
            with self.input_file.open('r') as config_file:
                config = yaml.safe_load(config_file)
                self.logger.info(f"Input YAML file: {self.input_file}")
        except FileNotFoundError:
            self.logger.error(f"Input YAML file {self.input_file} not found.")
            return
        except Exception as e:
            self.logger.error(f"Error reading input YAML file: {str(e)}")
            return

        # Build the ui
        self.logger.info("Building the user input info...")
        self.user_ui.init_from_yaml(config, self.mylog)

        # Generate the precice-config.xml file
        self.logger.info("Generating preCICE config...")
        self.precice_config.create_config(self.user_ui)

        # Set the target of the file and write out to it
        # Warning: self.structure_handler.precice_config is of type Path, so it needs to be converted to str
        target = str(self.structure_handler.precice_config)
        try:
            self.logger.info(f"Writing preCICE config to {target}...")
            self.precice_config.write_precice_xml_config(target, self.mylog)
        except Exception as e:
            self.logger.error(f"Failed to write preCICE XML config: {str(e)}")
            return

        self.logger.success(f"XML generation completed successfully: {target}")

    def generate_README(self) -> None:
        """Generates the README.md file"""
        try:
            origin_template_README = resolve_path("templates/template_README.md", self.base_dir)
            self.logger.info("Reading in the template file for README.md")
            
            # Check if the template file exists
            if not origin_template_README.exists():
                raise FileNotFoundError(f"Template file not found: {origin_template_README}")
            
            # Read the template content
            template_content = origin_template_README.read_text(encoding="utf-8")
            
            # Set the target for the README.md
            target = self.structure_handler.README

            self.logger.info(f"Writing the template to the target: {str(target)}")
            
            # Write content to the target file
            with open(target, 'w', encoding="utf-8") as README:
                README.write(template_content)

            self.logger.success(f"Successfully written README.md content to: {str(target)}")

        except FileNotFoundError as fileNotFoundException:
            self.logger.error(f"File not found: {fileNotFoundException}")
        except PermissionError as premissionErrorException:
            self.logger.error(f"Permission error: {premissionErrorException}")
        except Exception as generalExcpetion:
            self.logger.error(f"An unexpected error occurred: {generalExcpetion}")

    def generate_run(self) -> None:
        """Generates the run.sh file"""
        #TODO
        pass

    def generate_clean(self) -> None:
        """Generates the clean.sh file."""
        #TODO
        pass

    def generate_adapter_config(self) -> None:
        """Generates the adapter-config.json file."""
        #TODO
        pass

if __name__ == "__main__":
    # Use environment variable or fallback to default
    example_dir = os.getenv('EXAMPLE_DIR', './examples/1')
    topology_file = os.path.join(example_dir, 'topology.yaml')
    
    fileGenerator = FileGenerator(Path(topology_file))
    fileGenerator.generate_precice_config()
    fileGenerator.generate_README()
