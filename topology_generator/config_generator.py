import os
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import yaml
from typing import Dict, Any, Optional

class PreciceConfigGenerator:
    """
    Generate preCICE configuration XML from topology YAML
    """
    def __init__(self, topology_file: str, output_dir: Optional[str] = None, generator_config: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration generator
        
        :param topology_file: Path to topology YAML file
        :param output_dir: Optional output directory for generated files
        :param generator_config: Optional configuration for generation process
        """
        # Load topology configuration
        with open(topology_file, 'r') as f:
            self.topology = yaml.safe_load(f)
        
        # Set output directory
        self.output_dir = output_dir or os.path.dirname(topology_file)
        
        # Default generator configuration
        self.config = {
            'log_level': 'INFO',
            'xml_pretty_print': True,
            'overwrite_existing': False,
            'backup_existing': True
        }
        
        # Update with user-provided configuration
        if generator_config:
            self.config.update(generator_config)
    
    def _create_precice_config_root(self) -> ET.Element:
        """
        Create root element for preCICE configuration
        
        :return: XML root element
        """
        root = ET.Element('precice-configuration')
        root.set('xmlns', 'http://www.precice.org/namespace/precice-config')
        return root
    
    def _add_data_elements(self, root: ET.Element):
        """
        Add data elements to configuration
        
        :param root: XML root element
        """
        data_elem = ET.SubElement(root, 'data:data-configuration')
        data_elem.set('xmlns:data', 'http://www.precice.org/namespace/precice-config/data')
        
        for data in self.topology.get('data', []):
            data_type_elem = ET.SubElement(data_elem, f'data:{data["type"]}')
            data_type_elem.set('name', data['name'])
    
    def _add_mesh_elements(self, root: ET.Element):
        """
        Add mesh elements to configuration
        
        :param root: XML root element
        """
        for mesh in self.topology.get('meshes', []):
            mesh_elem = ET.SubElement(root, 'mesh')
            mesh_elem.set('name', mesh['name'])
            mesh_elem.set('dimensions', str(mesh.get('dimensions', 3)))
            
            # Add data to mesh
            for data_name in mesh.get('data', []):
                use_data_elem = ET.SubElement(mesh_elem, 'use-data')
                use_data_elem.set('name', data_name)
    
    def _add_participant_elements(self, root: ET.Element):
        """
        Add participant elements to configuration
        
        :param root: XML root element
        """
        for participant in self.topology.get('participants', []):
            participant_elem = ET.SubElement(root, 'participant')
            participant_elem.set('name', participant['name'])
            
            # Provide mesh
            if 'provides_mesh' in participant:
                provide_mesh_elem = ET.SubElement(participant_elem, 'provide-mesh')
                provide_mesh_elem.set('name', participant['provides_mesh'])
            
            # Receive meshes
            for mesh in participant.get('receives_meshes', []):
                receive_mesh_elem = ET.SubElement(participant_elem, 'receive-mesh')
                receive_mesh_elem.set('name', mesh)
            
            # Read data
            for data in participant.get('read_data', []):
                read_data_elem = ET.SubElement(participant_elem, 'read-data')
                read_data_elem.set('name', data)
            
            # Write data
            for data in participant.get('write_data', []):
                write_data_elem = ET.SubElement(participant_elem, 'write-data')
                write_data_elem.set('name', data)
    
    def _add_coupling_scheme_elements(self, root: ET.Element):
        """
        Add coupling scheme elements to configuration
        
        :param root: XML root element
        """
        coupling = self.topology.get('coupling', {})
        
        # Determine coupling scheme type
        coupling_type_map = {
            'serial-implicit': 'serial-implicit',
            'serial-explicit': 'serial-explicit',
            'parallel-implicit': 'parallel-implicit',
            'parallel-explicit': 'parallel-explicit'
        }
        coupling_type = coupling_type_map.get(coupling.get('type', 'serial-implicit'), 'serial-implicit')
        
        # Create coupling scheme element
        coupling_scheme_elem = ET.SubElement(root, f'coupling-scheme:{coupling_type}')
        coupling_scheme_elem.set('xmlns:coupling-scheme', 'http://www.precice.org/namespace/precice-config/coupling-scheme')
        
        # Time window size
        time_window_elem = ET.SubElement(coupling_scheme_elem, 'time-window-size')
        time_window_elem.set('value', str(coupling.get('time_window_size', 0.1)))
        
        # Max time
        max_time_elem = ET.SubElement(coupling_scheme_elem, 'max-time')
        max_time_elem.set('value', str(coupling.get('max_time', 10.0)))
        
        # Participants
        participants_elem = ET.SubElement(coupling_scheme_elem, 'participants')
        participants = coupling.get('participants', [])
        if len(participants) >= 2:
            participants_elem.set('first', participants[0])
            participants_elem.set('second', participants[1])
        
        # Exchanges
        for exchange in coupling.get('exchanges', []):
            exchange_elem = ET.SubElement(coupling_scheme_elem, 'exchange')
            exchange_elem.set('data', exchange['data'])
            exchange_elem.set('mesh', exchange['mesh'])
            exchange_elem.set('_from', exchange['from'])
            exchange_elem.set('to', exchange['to'])
    
    def generate(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Generate preCICE configuration XML
        
        :param output_dir: Optional output directory override
        :return: Dictionary of generated file paths
        """
        # Determine output directory
        output_dir = output_dir or self.output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_config')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create configuration root
        root = self._create_precice_config_root()
        
        # Add configuration elements
        self._add_data_elements(root)
        self._add_mesh_elements(root)
        self._add_participant_elements(root)
        self._add_coupling_scheme_elements(root)
        
        # Create XML tree
        tree = ET.ElementTree(root)
        
        # Generate XML file path
        xml_filename = f"{self.topology.get('name', 'precice')}-config.xml"
        xml_path = os.path.join(output_dir, xml_filename)
        
        # Pretty print XML
        xml_str = ET.tostring(root, encoding='unicode')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        # Write XML file
        with open(xml_path, 'w') as f:
            f.write(pretty_xml)
        
        # Generate run script
        run_script_path = os.path.join(output_dir, 'run.sh')
        with open(run_script_path, 'w') as f:
            f.write('''#!/bin/bash
# Run simulation participants
# Add your simulation participant commands here
''')
        os.chmod(run_script_path, 0o755)  # Make executable
        
        # Generate clean script
        clean_script_path = os.path.join(output_dir, 'clean.sh')
        with open(clean_script_path, 'w') as f:
            f.write('''#!/bin/bash
# Clean up simulation artifacts
rm -f *.log
# Add additional cleanup commands
''')
        os.chmod(clean_script_path, 0o755)  # Make executable
        
        # Generate README
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(f'''# {self.topology.get('name', 'Simulation')} Configuration

## Overview
This is an automatically generated preCICE simulation configuration.

## Participants
{', '.join(p['name'] for p in self.topology.get('participants', []))}

## Coupling Scheme
Type: {self.topology.get('coupling', {}).get('type', 'Not specified')}
Time Window Size: {self.topology.get('coupling', {}).get('time_window_size', 'Not specified')}
Max Time: {self.topology.get('coupling', {}).get('max_time', 'Not specified')}
''')
        
        return {
            'precice_config': xml_path,
            'run_script': run_script_path,
            'clean_script': clean_script_path,
            'readme': readme_path
        }

def main():
    """
    Example usage of configuration generator
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_generator.py <topology_yaml_path>")
        sys.exit(1)
    
    topology_path = sys.argv[1]
    generator = PreciceConfigGenerator(topology_path)
    result = generator.generate()
    
    print("Generated Files:")
    for key, path in result.items():
        print(f"{key.replace('_', ' ').title()}: {path}")

if __name__ == '__main__':
    main()
