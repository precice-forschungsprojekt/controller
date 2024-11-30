import os
import re
import yaml
import jsonschema
from typing import Dict, Any, List, Union

class TopologyValidator:
    def __init__(self, topology_dir: str):
        """
        Initialize the topology validator with the directory containing topology files
        
        :param topology_dir: Path to directory containing YAML topology files
        """
        self.topology_dir = topology_dir
        self.topology_schema = self._create_topology_schema()

    def _create_topology_schema(self) -> Dict[str, Any]:
        """
        Create a highly flexible JSON schema for validating topology files
        
        :return: JSON schema dictionary
        """
        base_schema = {
            "type": "object",
            "properties": {
                "version": {"type": ["number", "string"], "minimum": 1.0},
                "configuration": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "dimensions": {"type": ["number", "string"], "enum": [1, 2, 3, "1", "2", "3"]},
                        "experimental": {"type": "boolean"}
                    }
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "sink": {"type": "object"}
                    }
                },
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string", "enum": ["scalar", "vector"]},
                            "waveform_degree": {"type": ["number", "string"]}
                        }
                    }
                },
                "meshes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dimensions": {"type": ["number", "string"], "enum": [1, 2, 3, "1", "2", "3"]},
                            "data": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "participants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "provides_mesh": {"type": "array", "items": {"type": "string"}},
                            "receives_mesh": {"type": "array"},
                            "writes_data": {"type": "array"},
                            "reads_data": {"type": "array"},
                            "mapping": {"type": "array"},
                            "watch_point": {"type": "object"}
                        }
                    }
                },
                "communication": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "acceptor": {"type": "string"},
                                "connector": {"type": "string"},
                                "exchange_directory": {"type": "string"}
                            }
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "acceptor": {"type": "string"},
                                    "connector": {"type": "string"},
                                    "exchange_directory": {"type": "string"}
                                }
                            }
                        }
                    ]
                },
                "coupling_scheme": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string", 
                            "enum": [
                                "serial-implicit", 
                                "parallel-implicit", 
                                "serial-explicit", 
                                "parallel-explicit",
                                "aitken",
                                "IQN-IMVJ"
                            ]
                        },
                        "max_time": {"type": ["number", "string"]},
                        "time_window_size": {"type": ["number", "string"]},
                        "max_iterations": {"type": ["number", "string"]},
                        "participants": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "first": {"type": "string"},
                                    "second": {"type": "string"}
                                }
                            }
                        },
                        "acceleration": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string", 
                                    "enum": [
                                        "constant", 
                                        "IQN-ILS", 
                                        "IQN-IMVJ", 
                                        "aitken"
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        return base_schema

    def _parse_scientific_notation(self, value: Union[str, float, int]) -> float:
        """
        Parse scientific notation or numeric values safely
        
        :param value: Input value to parse
        :return: Parsed float value
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        try:
            # Use regex to handle scientific notation
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot parse numeric value: {value}")

    def validate_topology(self, topology_file: str) -> List[str]:
        """
        Validate a single topology file with enhanced error handling
        
        :param topology_file: Path to the topology YAML file
        :return: List of validation errors, empty list if valid
        """
        errors = []
        
        try:
            with open(topology_file, 'r') as f:
                topology_data = yaml.safe_load(f)
            
            # Preprocess numeric values
            self._preprocess_numeric_values(topology_data)
            
            # Validate against schema
            try:
                jsonschema.validate(instance=topology_data, schema=self.topology_schema)
            except jsonschema.exceptions.ValidationError as ve:
                errors.append(self._format_validation_error(ve, topology_file))
            
            # Additional custom validations
            errors.extend(self._validate_data_consistency(topology_data))
            errors.extend(self._validate_mesh_data_references(topology_data))
            
        except yaml.YAMLError as e:
            errors.append(f"YAML Parsing Error in {topology_file}: {e}")
        except FileNotFoundError:
            errors.append(f"File not found: {topology_file}")
        except Exception as e:
            errors.append(f"Unexpected error in {topology_file}: {e}")
        
        return errors

    def _preprocess_numeric_values(self, data: Dict[str, Any]):
        """
        Preprocess and convert string numeric values to floats
        
        :param data: Topology data dictionary
        """
        # Handle configuration dimensions
        if 'configuration' in data and 'dimensions' in data['configuration']:
            try:
                data['configuration']['dimensions'] = int(data['configuration']['dimensions'])
            except ValueError:
                pass

        # Handle coupling scheme numeric values
        if 'coupling_scheme' in data:
            cs = data['coupling_scheme']
            for key in ['max_time', 'time_window_size', 'max_iterations']:
                if key in cs:
                    try:
                        cs[key] = self._parse_scientific_notation(cs[key])
                    except ValueError:
                        pass

    def _format_validation_error(self, validation_error: jsonschema.exceptions.ValidationError, filename: str) -> str:
        """
        Format validation errors with more context and suggestions
        
        :param validation_error: Validation error from jsonschema
        :param filename: Name of the file being validated
        :return: Formatted error message
        """
        error_path = ' -> '.join(str(path) for path in validation_error.path)
        error_message = validation_error.message
        
        suggestions = {
            "coupling_scheme.type": "Use valid coupling scheme types: 'serial-implicit', 'parallel-implicit', 'serial-explicit', 'parallel-explicit'",
            "coupling_scheme.time_window_size": "Use numeric values or scientific notation (e.g., 1e-3)",
            "coupling_scheme.participants": "Ensure participants have 'first' and optionally 'second' keys",
            "configuration.dimensions": "Use numeric dimensions: 1, 2, or 3"
        }
        
        suggestion = suggestions.get(error_path, "No specific suggestion available")
        
        return (f"Validation Warning in {filename} at {error_path}: {error_message}\n"
                f"  Suggestion: {suggestion}")

    def _validate_data_consistency(self, topology_data: Dict[str, Any]) -> List[str]:
        """
        Perform additional data consistency checks
        
        :param topology_data: Parsed topology data
        :return: List of validation errors
        """
        warnings = []
        
        # Check data names are unique
        if 'data' in topology_data:
            data_names = [data.get('name', '') for data in topology_data['data']]
            if len(data_names) != len(set(data_names)):
                warnings.append("Potential issue: Duplicate data names found")
        
        # Check mesh names are unique
        if 'meshes' in topology_data:
            mesh_names = [mesh.get('name', '') for mesh in topology_data['meshes']]
            if len(mesh_names) != len(set(mesh_names)):
                warnings.append("Potential issue: Duplicate mesh names found")
        
        return warnings

    def _validate_mesh_data_references(self, topology_data: Dict[str, Any]) -> List[str]:
        """
        Validate that data references in meshes and participants are valid
        
        :param topology_data: Parsed topology data
        :return: List of validation errors
        """
        warnings = []
        
        # Get all data names
        data_names = {data.get('name', '') for data in topology_data.get('data', [])}
        
        # Validate mesh data references
        if 'meshes' in topology_data:
            for mesh in topology_data['meshes']:
                for data_name in mesh.get('data', []):
                    if data_name not in data_names:
                        warnings.append(f"Potential issue: Invalid data reference '{data_name}' in mesh '{mesh.get('name', 'Unknown')}'")
        
        # Validate participant data references
        if 'participants' in topology_data:
            for participant in topology_data['participants']:
                for data_item in participant.get('writes_data', []):
                    if data_item.get('name', '') not in data_names:
                        warnings.append(f"Potential issue: Invalid write data reference '{data_item.get('name', '')}' in participant '{participant.get('name', 'Unknown')}'")
                
                for data_item in participant.get('reads_data', []):
                    if data_item.get('name', '') not in data_names:
                        warnings.append(f"Potential issue: Invalid read data reference '{data_item.get('name', '')}' in participant '{participant.get('name', 'Unknown')}'")
        
        return warnings

    def validate_all_topologies(self) -> Dict[str, List[str]]:
        """
        Validate all topology files in the specified directory
        
        :return: Dictionary of topology files and their validation warnings
        """
        validation_results = {}
        
        for filename in os.listdir(self.topology_dir):
            if filename.endswith('-topology.yaml'):
                filepath = os.path.join(self.topology_dir, filename)
                errors = self.validate_topology(filepath)
                if errors:
                    validation_results[filename] = errors
        
        return validation_results

def main():
    topology_dir = r'c:/Users/thore/Desktop/precice/Forschungsprojekt/controller/topologies'
    validator = TopologyValidator(topology_dir)
    
    # Validate all topologies
    validation_results = validator.validate_all_topologies()
    
    if validation_results:
        print("Validation Warnings Found:")
        for filename, errors in validation_results.items():
            print(f"\n{filename}:")
            for error in errors:
                print(f"  - {error}")
    else:
        print("All topology files are valid!")

if __name__ == "__main__":
    main()
