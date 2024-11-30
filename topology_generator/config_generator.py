import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re
import time

from pydantic import ValidationError, BaseModel, Field

from controller.topology_generator.topology_schema import (
    TopologyConfig, 
    MappingType, 
    CouplingSchemeType, 
    DataType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('topology_generator.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class TopologyGeneratorConfig(BaseModel):
    """
    Advanced configuration for topology generator
    
    Allows fine-tuning of generation process and adding custom behaviors
    """
    # Logging configuration
    log_level: str = Field(default='INFO', 
                           pattern='^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    
    # XML generation options
    xml_pretty_print: bool = True
    xml_indent: str = '  '
    
    # File generation options
    overwrite_existing: bool = False
    backup_existing: bool = True
    
    # Advanced validation toggles
    strict_validation: bool = True
    warn_on_non_critical_issues: bool = True
    
    # Custom mapping and transformation rules
    custom_data_mappings: Dict[str, str] = {}
    custom_mesh_transformations: Dict[str, Dict[str, Any]] = {}
    
    # Simulation environment configuration
    default_communication_method: str = 'sockets'
    preferred_coupling_scheme: CouplingSchemeType = CouplingSchemeType.SERIAL_EXPLICIT

class PreciceConfigGenerator:
    def __init__(
        self, 
        topology_file: str, 
        output_dir: Optional[str] = None,
        generator_config: Optional[Union[Dict[str, Any], TopologyGeneratorConfig]] = None
    ):
        """
        Initialize the PreciceConfigGenerator with advanced configuration options
        
        :param topology_file: Path to the topology YAML file
        :param output_dir: Optional output directory for generated files
        :param generator_config: Optional configuration for generation process
        """
        # Set up configuration
        if isinstance(generator_config, dict):
            self.generator_config = TopologyGeneratorConfig(**generator_config)
        elif isinstance(generator_config, TopologyGeneratorConfig):
            self.generator_config = generator_config
        else:
            self.generator_config = TopologyGeneratorConfig()
        
        # Configure logging based on generator config
        logger.setLevel(getattr(logging, self.generator_config.log_level.upper()))
        
        logger.info(f"Initializing topology configuration generator for {topology_file}")
        
        try:
            # Load topology file
            with open(topology_file, 'r') as f:
                topology_data = yaml.safe_load(f)
            
            # Apply custom mappings if defined
            topology_data = self._apply_custom_mappings(topology_data)
            
            # Convert enum values
            topology_data = self._convert_enums(topology_data)
            
            # Validate topology data against schema
            try:
                self.topology = TopologyConfig(**topology_data)
            except ValidationError as e:
                # Enhance Pydantic validation error with more context
                detailed_errors = []
                for error in e.errors():
                    loc = ' -> '.join(str(x) for x in error.get('loc', []))
                    detailed_errors.append(f"{loc}: {error.get('msg', 'Validation failed')}")
                
                logger.error("Topology configuration validation failed")
                raise ValueError(f"Topology configuration validation failed:\n" + 
                                 "\n".join(detailed_errors)) from e
            
            # Perform additional custom validation
            self._validate_topology_configuration()
            
            # Set output directory
            self.output_dir = output_dir or os.path.join(
                os.path.dirname(topology_file), 
                f"{self.topology.name}-simulation"
            )
            
            # Handle existing directory
            if os.path.exists(self.output_dir):
                if not self.generator_config.overwrite_existing:
                    raise ValueError(f"Output directory {self.output_dir} already exists. "
                                     "Set overwrite_existing=True to replace.")
                
                if self.generator_config.backup_existing:
                    import shutil
                    backup_dir = f"{self.output_dir}_backup_{int(time.time())}"
                    logger.info(f"Backing up existing directory to {backup_dir}")
                    shutil.move(self.output_dir, backup_dir)
            
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            logger.info(f"Topology configuration initialized successfully")
        
        except Exception as e:
            logger.exception("Error during topology configuration initialization")
            raise

    def _apply_custom_mappings(self, topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply custom data and mesh mappings
        
        :param topology_data: Original topology configuration
        :return: Modified topology configuration
        """
        # Apply custom data mappings
        if self.generator_config.custom_data_mappings:
            logger.info("Applying custom data mappings")
            for data in topology_data.get('data', []):
                if data['name'] in self.generator_config.custom_data_mappings:
                    data['name'] = self.generator_config.custom_data_mappings[data['name']]
        
        # Apply custom mesh transformations
        if self.generator_config.custom_mesh_transformations:
            logger.info("Applying custom mesh transformations")
            for mesh in topology_data.get('meshes', []):
                if mesh['name'] in self.generator_config.custom_mesh_transformations:
                    custom_transform = self.generator_config.custom_mesh_transformations[mesh['name']]
                    mesh.update(custom_transform)
        
        return topology_data

    def generate(self):
        """
        Generate all configuration files for the simulation
        
        Generates:
        - precice-config.xml
        - run.sh
        - clean.sh
        - README.md
        """
        logger.info("Starting simulation configuration generation")
        
        # Generate XML configuration
        precice_config_path = self.generate_precice_config()
        
        # Generate run script
        run_script_path = self._generate_run_script()
        
        # Generate clean script
        clean_script_path = self._generate_clean_script()
        
        # Generate README
        readme_path = self._generate_readme()
        
        logger.info("Simulation configuration generation completed")
        
        return {
            'precice_config': precice_config_path,
            'run_script': run_script_path,
            'clean_script': clean_script_path,
            'readme': readme_path
        }

    def _generate_run_script(self) -> str:
        """
        Generate run.sh script for the simulation
        
        :return: Path to generated run script
        """
        run_script_path = os.path.join(self.output_dir, 'run.sh')
        
        # Basic run script template
        run_script_content = f'''#!/bin/bash
# Run script for {self.topology.name} simulation

# Participants
PARTICIPANTS="{' '.join(p.name for p in self.topology.participants)}"

# Run simulation
for participant in $PARTICIPANTS; do
    echo "Running participant: $participant"
    # Add participant-specific run commands here
done

echo "Simulation completed"
'''
        
        with open(run_script_path, 'w') as f:
            f.write(run_script_content)
        
        # Make script executable
        os.chmod(run_script_path, 0o755)
        
        logger.info(f"Generated run script: {run_script_path}")
        return run_script_path

    def _generate_clean_script(self) -> str:
        """
        Generate clean.sh script to reset simulation environment
        
        :return: Path to generated clean script
        """
        clean_script_path = os.path.join(self.output_dir, 'clean.sh')
        
        clean_script_content = '''#!/bin/bash
# Clean up simulation artifacts

# Remove output files
rm -f *.log
rm -f *.txt
rm -f *.vtk

# Reset any participant-specific files
echo "Simulation environment cleaned"
'''
        
        with open(clean_script_path, 'w') as f:
            f.write(clean_script_content)
        
        # Make script executable
        os.chmod(clean_script_path, 0o755)
        
        logger.info(f"Generated clean script: {clean_script_path}")
        return clean_script_path

    def _generate_readme(self) -> str:
        """
        Generate README.md for the simulation
        
        :return: Path to generated README
        """
        readme_path = os.path.join(self.output_dir, 'README.md')
        
        readme_content = f'''# {self.topology.name} Simulation

## Participants
{chr(10).join(f"- {p.name}" for p in self.topology.participants)}

## Coupling Configuration
- **Type**: {self.topology.coupling.type}
- **Time Window Size**: {self.topology.coupling.time_window_size}
- **Max Time**: {self.topology.coupling.max_time}

## Data Exchanges
{chr(10).join(f"- {e.get('data')} from {e.get('from')} to {e.get('to')}" for e in self.topology.coupling.exchanges)}

## Running the Simulation
1. Ensure all dependencies are installed
2. Run `./run.sh`
3. Use `./clean.sh` to reset the environment

Generated by preCICE Topology Configuration Generator
'''
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        logger.info(f"Generated README: {readme_path}")
        return readme_path

    def generate_precice_config(self) -> str:
        """
        Generate preCICE XML configuration
        
        :return: Path to generated precice-config.xml
        """
        # Create root element with namespace
        root = ET.Element("precice-configuration", xmlns="http://www.precice.org/namespace/precice-config")
        
        # Add logging configuration
        log = ET.SubElement(root, "log")
        sink = ET.SubElement(log, "sink", {
            "filter": "%Severity% > debug and %Rank% = 0",
            "format": "---[precice] %ColorizedSeverity% %Message%",
            "enabled": "true"
        })
        
        # Add data configurations
        for data in self.topology.data:
            ET.SubElement(root, f"data:{self._get_enum_value(data.type)}", name=data.name)
        
        # Add mesh configurations
        for mesh in self.topology.meshes:
            mesh_elem = ET.SubElement(root, "mesh", name=mesh.name, dimensions=str(mesh.dimensions))
            for data_name in mesh.data:
                ET.SubElement(mesh_elem, "use-data", name=data_name)
        
        # Add participant configurations
        for participant in self.topology.participants:
            participant_elem = ET.SubElement(root, "participant", name=participant.name)
            
            # Provide mesh
            ET.SubElement(participant_elem, "provide-mesh", name=participant.provides_mesh)
            
            # Receive meshes
            for recv_mesh in participant.receives_meshes:
                ET.SubElement(participant_elem, "receive-mesh", 
                              name=recv_mesh, 
                              _from=next(p.name for p in self.topology.participants if p.provides_mesh == recv_mesh))
            
            # Read/Write data
            for read_data in participant.read_data:
                ET.SubElement(participant_elem, "read-data", name=read_data, mesh=participant.provides_mesh)
            
            for write_data in participant.write_data:
                ET.SubElement(participant_elem, "write-data", name=write_data, mesh=participant.provides_mesh)
        
        # Add communication method (default to sockets)
        if len(self.topology.participants) > 1:
            m2n = ET.SubElement(root, "m2n:sockets", 
                                acceptor=self.topology.participants[0].name, 
                                connector=self.topology.participants[1].name, 
                                exchange_directory="..")
        
        # Add coupling scheme
        coupling = ET.SubElement(root, f"coupling-scheme:{self._get_enum_value(self.topology.coupling.type)}")
        ET.SubElement(coupling, "time-window-size", value=str(self.topology.coupling.time_window_size))
        ET.SubElement(coupling, "max-time", value=str(self.topology.coupling.max_time))
        
        participants = ET.SubElement(coupling, "participants", 
                                     first=self.topology.participants[0].name, 
                                     second=self.topology.participants[1].name)
        
        # Add exchanges
        for exchange in self.topology.coupling.exchanges:
            ET.SubElement(coupling, "exchange", 
                          data=exchange.get('data', ''), 
                          mesh=exchange.get('mesh', ''), 
                          _from=exchange.get('from', ''), 
                          to=exchange.get('to', ''))
        
        # Convert to pretty-printed XML
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        ET.register_namespace('', "http://www.precice.org/namespace/precice-config")
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # Use manual pretty printing
        xml_str = re.sub(r'>\s*<', '>\n<', xml_str)
        xml_str = xml_declaration + xml_str
        
        # Write to file
        config_path = os.path.join(self.output_dir, "precice-config.xml")
        with open(config_path, 'w') as f:
            f.write(xml_str)
        
        return config_path

    def _get_enum_value(self, enum_value):
        """
        Convert enum to its string representation for XML generation
        
        :param enum_value: Enum value to convert
        :return: String representation of the enum
        """
        enum_to_xml_map = {
            # Data Type Mapping
            DataType.SCALAR: 'scalar',
            DataType.VECTOR: 'vector',
            DataType.TENSOR: 'tensor',
            
            # Mapping Type Mapping
            MappingType.RBF: 'rbf',
            MappingType.NEAREST_PROJECTION: 'nearest-projection',
            MappingType.CONSISTENT: 'consistent',
            MappingType.CONSERVATIVE: 'conservative',
            
            # Coupling Scheme Mapping
            CouplingSchemeType.SERIAL_EXPLICIT: 'serial-explicit',
            CouplingSchemeType.SERIAL_IMPLICIT: 'serial-implicit',
            CouplingSchemeType.PARALLEL_EXPLICIT: 'parallel-explicit',
            CouplingSchemeType.PARALLEL_IMPLICIT: 'parallel-implicit'
        }
        
        return enum_to_xml_map.get(enum_value, str(enum_value))

    def _convert_enums(self, topology_data):
        """
        Convert integer enum values to their corresponding enum types
        
        :param topology_data: Raw topology configuration dictionary
        :return: Processed topology configuration dictionary
        """
        # Convert mapping type
        if 'participants' in topology_data:
            for participant in topology_data['participants']:
                if 'mapping_type' in participant:
                    # Map integer to enum, defaulting to RBF
                    mapping_type_map = {
                        0: MappingType.RBF,
                        1: MappingType.NEAREST_PROJECTION,
                        2: MappingType.CONSISTENT,
                        3: MappingType.CONSERVATIVE
                    }
                    participant['mapping_type'] = mapping_type_map.get(
                        participant['mapping_type'], 
                        MappingType.RBF
                    )
        
        # Convert coupling type
        if 'coupling' in topology_data:
            if 'type' in topology_data['coupling']:
                # Map integer to enum, defaulting to SERIAL_EXPLICIT
                coupling_type_map = {
                    0: CouplingSchemeType.SERIAL_EXPLICIT,
                    1: CouplingSchemeType.SERIAL_IMPLICIT,
                    2: CouplingSchemeType.PARALLEL_EXPLICIT,
                    3: CouplingSchemeType.PARALLEL_IMPLICIT
                }
                topology_data['coupling']['type'] = coupling_type_map.get(
                    topology_data['coupling']['type'], 
                    CouplingSchemeType.SERIAL_EXPLICIT
                )
        
        # Convert data type
        if 'data' in topology_data:
            for data in topology_data['data']:
                if 'type' in data:
                    # Map string to enum, defaulting to VECTOR
                    data_type_map = {
                        'scalar': DataType.SCALAR,
                        'vector': DataType.VECTOR,
                        'tensor': DataType.TENSOR
                    }
                    data['type'] = data_type_map.get(
                        data['type'], 
                        DataType.VECTOR
                    )
        
        return topology_data

    def _validate_topology_configuration(self):
        """
        Perform comprehensive validation of the topology configuration
        
        Checks include:
        - Unique participant names
        - Consistent data exchange
        - Mesh and data existence
        - Coupling participant validation
        
        Raises:
            ValueError: If configuration fails validation
        """
        # Check for unique participant names
        participant_names = [p.name for p in self.topology.participants]
        if len(participant_names) != len(set(participant_names)):
            raise ValueError("Participant names must be unique")
        
        # Validate meshes
        all_mesh_names = [mesh.name for mesh in self.topology.meshes]
        for participant in self.topology.participants:
            # Check provided mesh exists
            if participant.provides_mesh not in all_mesh_names:
                raise ValueError(f"Participant {participant.name} provides non-existent mesh: {participant.provides_mesh}")
            
            # Check received meshes exist
            for recv_mesh in participant.receives_meshes:
                if recv_mesh not in all_mesh_names:
                    raise ValueError(f"Participant {participant.name} receives non-existent mesh: {recv_mesh}")
        
        # Validate data
        all_data_names = [data.name for data in self.topology.data]
        for participant in self.topology.participants:
            # Check read/write data exists
            for read_data in participant.read_data:
                if read_data not in all_data_names:
                    raise ValueError(f"Participant {participant.name} reads non-existent data: {read_data}")
            
            for write_data in participant.write_data:
                if write_data not in all_data_names:
                    raise ValueError(f"Participant {participant.name} writes non-existent data: {write_data}")
        
        # Validate coupling configuration
        if len(self.topology.participants) < 2:
            raise ValueError("At least two participants are required for coupling")
        
        coupling_participant_names = set(self.topology.coupling.participants)
        config_participant_names = set(p.name for p in self.topology.participants)
        
        if not coupling_participant_names.issubset(config_participant_names):
            raise ValueError("Coupling participants must be defined in the topology")
        
        # Validate exchanges
        for exchange in self.topology.coupling.exchanges:
            # Check data exists
            if exchange.get('data') not in all_data_names:
                raise ValueError(f"Exchange references non-existent data: {exchange.get('data')}")
            
            # Check mesh exists
            if exchange.get('mesh') not in all_mesh_names:
                raise ValueError(f"Exchange references non-existent mesh: {exchange.get('mesh')}")
            
            # Check from/to participants exist
            if exchange.get('from') not in config_participant_names:
                raise ValueError(f"Exchange 'from' participant not found: {exchange.get('from')}")
            
            if exchange.get('to') not in config_participant_names:
                raise ValueError(f"Exchange 'to' participant not found: {exchange.get('to')}")
        
        # Validate time configuration
        if self.topology.coupling.time_window_size <= 0:
            raise ValueError("Time window size must be positive")
        
        if self.topology.coupling.max_time <= 0:
            raise ValueError("Maximum simulation time must be positive")

def main():
    # Example usage
    topology_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "example_topology.yaml"))
    generator = PreciceConfigGenerator(topology_file)
    generator.generate()

if __name__ == "__main__":
    main()
