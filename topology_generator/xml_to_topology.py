import os
import xml.etree.ElementTree as ET
import yaml
from typing import Dict, List, Any

class PreciceXMLToTopologyConverter:
    def __init__(self, xml_path: str):
        """
        Initialize converter with preCICE XML configuration
        
        :param xml_path: Path to preCICE XML configuration file
        """
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        
        # Namespace handling
        self.namespaces = {
            'precice': 'http://www.precice.org/namespace/precice-config'
        }
    
    def _extract_data(self) -> List[Dict[str, str]]:
        """
        Extract data types from XML
        
        :return: List of data configurations
        """
        data_types = []
        for data_elem in self.root.findall('.//data:scalar | .//data:vector | .//data:tensor', 
                                           namespaces=self.namespaces):
            data_types.append({
                'name': data_elem.get('name'),
                'type': data_elem.tag.split('}')[-1]
            })
        return data_types
    
    def _extract_meshes(self) -> List[Dict[str, Any]]:
        """
        Extract mesh configurations from XML
        
        :return: List of mesh configurations
        """
        meshes = []
        for mesh_elem in self.root.findall('.//mesh', namespaces=self.namespaces):
            mesh_config = {
                'name': mesh_elem.get('name'),
                'dimensions': int(mesh_elem.get('dimensions', 3)),
                'data': [
                    use_data.get('name') 
                    for use_data in mesh_elem.findall('.//use-data', namespaces=self.namespaces)
                ]
            }
            meshes.append(mesh_config)
        return meshes
    
    def _extract_participants(self) -> List[Dict[str, Any]]:
        """
        Extract participant configurations from XML
        
        :return: List of participant configurations
        """
        participants = []
        for participant_elem in self.root.findall('.//participant', namespaces=self.namespaces):
            participant = {
                'name': participant_elem.get('name'),
                'provides_mesh': participant_elem.find('.//provide-mesh', namespaces=self.namespaces).get('name'),
                'receives_meshes': [
                    recv_mesh.get('name') 
                    for recv_mesh in participant_elem.findall('.//receive-mesh', namespaces=self.namespaces)
                ],
                'read_data': [
                    read_data.get('name') 
                    for read_data in participant_elem.findall('.//read-data', namespaces=self.namespaces)
                ],
                'write_data': [
                    write_data.get('name') 
                    for write_data in participant_elem.findall('.//write-data', namespaces=self.namespaces)
                ]
            }
            participants.append(participant)
        return participants
    
    def _extract_coupling(self) -> Dict[str, Any]:
        """
        Extract coupling scheme configuration from XML
        
        :return: Coupling configuration dictionary
        """
        # Find coupling scheme element
        coupling_elem = self.root.find('.//coupling-scheme:serial-explicit | .//coupling-scheme:serial-implicit | .//coupling-scheme:parallel-explicit | .//coupling-scheme:parallel-implicit', 
                                        namespaces=self.namespaces)
        
        if coupling_elem is None:
            raise ValueError("No coupling scheme found in XML")
        
        # Extract coupling type from tag
        coupling_type = coupling_elem.tag.split('}')[-1]
        
        # Extract time window and max time
        time_window_elem = coupling_elem.find('.//time-window-size', namespaces=self.namespaces)
        max_time_elem = coupling_elem.find('.//max-time', namespaces=self.namespaces)
        
        # Extract participants
        participants_elem = coupling_elem.find('.//participants', namespaces=self.namespaces)
        
        # Extract exchanges
        exchanges = []
        for exchange_elem in coupling_elem.findall('.//exchange', namespaces=self.namespaces):
            exchanges.append({
                'data': exchange_elem.get('data'),
                'mesh': exchange_elem.get('mesh'),
                'from': exchange_elem.get('_from'),
                'to': exchange_elem.get('to')
            })
        
        return {
            'type': coupling_type,
            'time_window_size': float(time_window_elem.get('value')) if time_window_elem is not None else 0.1,
            'max_time': float(max_time_elem.get('value')) if max_time_elem is not None else 10.0,
            'participants': [
                participants_elem.get('first'), 
                participants_elem.get('second')
            ] if participants_elem is not None else [],
            'exchanges': exchanges
        }
    
    def generate_topology_yaml(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate topology YAML configuration
        
        :param output_path: Optional path to save YAML file
        :return: Topology configuration dictionary
        """
        # Extract configuration components
        topology = {
            'name': os.path.splitext(os.path.basename(self.xml_path))[0],
            'data': self._extract_data(),
            'meshes': self._extract_meshes(),
            'participants': self._extract_participants(),
            'coupling': self._extract_coupling()
        }
        
        # Save to YAML if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                yaml.safe_dump(topology, f, default_flow_style=False)
        
        return topology

def main():
    """
    Example usage of XML to topology converter
    """
    # Path to the preCICE XML configuration
    xml_path = os.path.join(
        os.path.dirname(__file__), 
        'fluid-solid-interaction-simulation', 
        'precice-config.xml'
    )
    
    # Output YAML path
    output_yaml_path = os.path.join(
        os.path.dirname(__file__), 
        'generated_topology.yaml'
    )
    
    # Create converter
    converter = PreciceXMLToTopologyConverter(xml_path)
    
    # Generate topology YAML
    topology = converter.generate_topology_yaml(output_yaml_path)
    
    # Print generated topology
    print(yaml.safe_dump(topology, default_flow_style=False))

if __name__ == '__main__':
    main()
