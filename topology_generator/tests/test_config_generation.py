import os
import xml.etree.ElementTree as ET
import yaml
import pytest
import difflib
from typing import Dict, Any, List, Tuple

from topology_generator.xml_to_topology import PreciceXMLToTopologyConverter
from topology_generator.config_generator import PreciceConfigGenerator

class XMLConfigComparator:
    """
    Comprehensive XML configuration comparator
    """
    @staticmethod
    def _normalize_xml(xml_path: str) -> str:
        """
        Normalize XML for comparison by removing whitespace and sorting attributes
        
        :param xml_path: Path to XML file
        :return: Normalized XML string
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        def _normalize_element(elem):
            """Recursively normalize an XML element"""
            # Sort attributes
            if elem.attrib:
                elem.attrib = dict(sorted(elem.attrib.items()))
            
            # Recursively normalize children
            for child in elem:
                _normalize_element(child)
            
            return elem
        
        # Normalize the entire tree
        _normalize_element(root)
        
        # Convert to string, removing extra whitespace
        return ET.tostring(root, encoding='unicode', method='xml').strip()
    
    @classmethod
    def compare_xml_configs(cls, original_xml: str, generated_xml: str) -> Tuple[bool, List[str]]:
        """
        Compare two XML configurations
        
        :param original_xml: Path to original XML
        :param generated_xml: Path to generated XML
        :return: Tuple of (is_identical, diff_lines)
        """
        # Normalize XMLs
        original_normalized = cls._normalize_xml(original_xml)
        generated_normalized = cls._normalize_xml(generated_xml)
        
        # Perform diff
        diff = list(difflib.unified_diff(
            original_normalized.splitlines(keepends=True),
            generated_normalized.splitlines(keepends=True),
            fromfile='Original XML',
            tofile='Generated XML'
        ))
        
        return len(diff) == 0, diff
    
    @staticmethod
    def extract_xml_details(xml_path: str) -> Dict[str, Any]:
        """
        Extract key details from XML configuration
        
        :param xml_path: Path to XML configuration
        :return: Dictionary of extracted configuration details
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Namespace handling
        namespaces = {
            'precice': 'http://www.precice.org/namespace/precice-config',
            'data': 'http://www.precice.org/namespace/precice-config/data',
            'coupling-scheme': 'http://www.precice.org/namespace/precice-config/coupling-scheme'
        }
        
        # Extract participants
        participants = [
            participant.get('name') 
            for participant in root.findall('.//participant', namespaces=namespaces)
        ]
        
        # Extract meshes
        meshes = [
            {
                'name': mesh.get('name'),
                'dimensions': int(mesh.get('dimensions', 3)),
                'data': [
                    use_data.get('name') 
                    for use_data in mesh.findall('.//use-data', namespaces=namespaces)
                ]
            }
            for mesh in root.findall('.//mesh', namespaces=namespaces)
        ]
        
        # Extract data types
        data_types = [
            {
                'name': data.get('name'),
                'type': data.tag.split('}')[-1]
            }
            for data in root.findall('.//data:scalar | .//data:vector | .//data:tensor', namespaces=namespaces)
        ]
        
        # Extract coupling scheme
        coupling_scheme_elem = root.find(
            './/coupling-scheme:serial-explicit | .//coupling-scheme:serial-implicit | '
            './/coupling-scheme:parallel-explicit | .//coupling-scheme:parallel-implicit', 
            namespaces=namespaces
        )
        
        coupling_scheme = None
        if coupling_scheme_elem is not None:
            coupling_scheme = {
                'type': coupling_scheme_elem.tag.split('}')[-1],
                'time_window_size': float(coupling_scheme_elem.find('.//time-window-size', namespaces=namespaces).get('value', 0.1)),
                'max_time': float(coupling_scheme_elem.find('.//max-time', namespaces=namespaces).get('value', 10.0) if coupling_scheme_elem.find('.//max-time', namespaces=namespaces) is not None else 10.0),
                'participants': [
                    participant.get('first'),
                    participant.get('second')
                ]
            }
        
        return {
            'participants': participants,
            'meshes': meshes,
            'data_types': data_types,
            'coupling_scheme': coupling_scheme
        }

def test_config_generation():
    """
    Comprehensive test for configuration generation workflow
    """
    # Paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    original_xml_path = os.path.join(base_dir, 'fluid-solid-interaction-simulation', 'precice-config.xml')
    topology_yaml_path = os.path.join(base_dir, 'generated_topology.yaml')
    generated_xml_path = os.path.join(base_dir, 'generated_precice_config.xml')
    
    # Step 1: Convert original XML to topology YAML
    converter = PreciceXMLToTopologyConverter(original_xml_path)
    topology = converter.generate_topology_yaml(topology_yaml_path)
    
    # Validate generated topology YAML
    assert os.path.exists(topology_yaml_path), "Topology YAML generation failed"
    
    # Step 2: Generate new configuration from topology YAML
    generator = PreciceConfigGenerator(topology_yaml_path)
    generator.generate(output_dir=os.path.dirname(generated_xml_path))
    
    # Validate generated XML exists
    assert os.path.exists(generated_xml_path), "XML configuration generation failed"
    
    # Step 3: Compare XML configurations
    is_identical, diff = XMLConfigComparator.compare_xml_configs(original_xml_path, generated_xml_path)
    
    # Print diff if not identical (for debugging)
    if not is_identical:
        print("XML Configuration Differences:")
        print(''.join(diff))
    
    # Assert configurations are identical
    assert is_identical, "Generated XML does not match original XML configuration"
    
    # Step 4: Detailed configuration comparison
    original_details = XMLConfigComparator.extract_xml_details(original_xml_path)
    generated_details = XMLConfigComparator.extract_xml_details(generated_xml_path)
    
    # Compare participants
    assert original_details['participants'] == generated_details['participants'], \
        "Participants do not match between original and generated configurations"
    
    # Compare meshes
    assert len(original_details['meshes']) == len(generated_details['meshes']), \
        "Number of meshes does not match"
    
    for orig_mesh, gen_mesh in zip(original_details['meshes'], generated_details['meshes']):
        assert orig_mesh['name'] == gen_mesh['name'], f"Mesh name mismatch: {orig_mesh['name']} vs {gen_mesh['name']}"
        assert orig_mesh['dimensions'] == gen_mesh['dimensions'], f"Mesh dimensions mismatch for {orig_mesh['name']}"
        assert set(orig_mesh['data']) == set(gen_mesh['data']), f"Mesh data mismatch for {orig_mesh['name']}"
    
    # Compare data types
    assert len(original_details['data_types']) == len(generated_details['data_types']), \
        "Number of data types does not match"
    
    for orig_data, gen_data in zip(original_details['data_types'], generated_details['data_types']):
        assert orig_data['name'] == gen_data['name'], f"Data name mismatch: {orig_data['name']} vs {gen_data['name']}"
        assert orig_data['type'] == gen_data['type'], f"Data type mismatch for {orig_data['name']}"
    
    # Compare coupling scheme
    assert original_details['coupling_scheme'] == generated_details['coupling_scheme'], \
        "Coupling scheme details do not match"
    
    print("✅ Configuration Generation Test Passed Successfully!")

def main():
    """
    Run the configuration generation test
    """
    pytest.main([__file__])

if __name__ == '__main__':
    main()
