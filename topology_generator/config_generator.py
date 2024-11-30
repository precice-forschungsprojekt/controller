import os
import yaml
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re
from pydantic import ValidationError

from controller.topology_generator.topology_schema import TopologyConfig, MappingType, CouplingSchemeType, DataType

class PreciceConfigGenerator:
    def __init__(self, topology_file: str, output_dir: Optional[str] = None):
        """
        Initialize the PreciceConfigGenerator
        
        :param topology_file: Path to the topology YAML file
        :param output_dir: Optional output directory for generated files
        """
        # Load topology file
        with open(topology_file, 'r') as f:
            topology_data = yaml.safe_load(f)
        
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
            
            raise ValueError(f"Topology configuration validation failed:\n" + 
                             "\n".join(detailed_errors)) from e
        
        # Perform additional custom validation
        self._validate_topology_configuration()
        
        # Set output directory
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(topology_file), 
            f"{self.topology.name}-simulation"
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

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
    
    def generate_run_script(self) -> str:
        """
        Generate run.sh script
        
        :return: Path to generated run.sh
        """
        run_script = "#!/bin/bash\n\n"
        run_script += "# Run simulation participants\n"
        
        for participant in self.topology.participants:
            run_script += f"# Run {participant.name} participant\n"
            run_script += f"./{participant.name}_participant &\n"
        
        run_script += "\n# Wait for all participants to complete\nwait\n"
        
        run_path = os.path.join(self.output_dir, "run.sh")
        with open(run_path, 'w') as f:
            f.write(run_script)
        
        # Make executable
        os.chmod(run_path, 0o755)
        
        return run_path
    
    def generate_clean_script(self) -> str:
        """
        Generate clean.sh script
        
        :return: Path to generated clean.sh
        """
        clean_script = "#!/bin/bash\n\n"
        clean_script += "# Clean up simulation outputs and temporary files\n"
        clean_script += "rm -rf *.log\n"
        clean_script += "rm -rf precice-*.xml\n"
        clean_script += "rm -rf *.vtk\n"
        
        clean_path = os.path.join(self.output_dir, "clean.sh")
        with open(clean_path, 'w') as f:
            f.write(clean_script)
        
        # Make executable
        os.chmod(clean_path, 0o755)
        
        return clean_path
    
    def generate_readme(self) -> str:
        """
        Generate README.md
        
        :return: Path to generated README.md
        """
        readme_content = f"# {self.topology.name} Simulation\n\n"
        readme_content += "## Simulation Participants\n"
        
        for participant in self.topology.participants:
            readme_content += f"### {participant.name}\n"
            readme_content += f"- Provides Mesh: {participant.provides_mesh}\n"
            readme_content += f"- Read Data: {', '.join(participant.read_data)}\n"
            readme_content += f"- Write Data: {', '.join(participant.write_data)}\n\n"
        
        readme_content += "## Running the Simulation\n"
        readme_content += "1. Ensure all dependencies are installed\n"
        readme_content += "2. Run `./run.sh`\n"
        readme_content += "3. Use `./clean.sh` to remove output files\n"
        
        readme_path = os.path.join(self.output_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        return readme_path
    
    def generate(self):
        """
        Generate all configuration files
        """
        print(f"Generating simulation files in {self.output_dir}")
        self.generate_precice_config()
        self.generate_run_script()
        self.generate_clean_script()
        self.generate_readme()
        print("Simulation configuration generated successfully!")

def main():
    # Example usage
    topology_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "example_topology.yaml"))
    generator = PreciceConfigGenerator(topology_file)
    generator.generate()

if __name__ == "__main__":
    main()
