import os
import re
import yaml
import jsonschema
from typing import Dict, Any, List, Union, Optional
from dotenv import load_dotenv

class TopologyValidator:
    def __init__(self, topology_dir: str):
        """
        Initialize the topology validator with advanced configuration checks
        
        :param topology_dir: Path to directory containing topology files
        """
        self.topology_dir = topology_dir
        self.topology_schema = self._create_topology_schema()
        self.best_practices = self._define_best_practices()

    def _define_best_practices(self) -> Dict[str, List[str]]:
        """
        Define a comprehensive set of best practices and recommendations
        
        :return: Dictionary of best practice guidelines
        """
        return {
            "coupling_scheme": [
                "Prefer implicit coupling for better convergence",
                "Use appropriate time window sizes",
                "Implement convergence measures"
            ],
            "communication": [
                "Minimize communication overhead",
                "Use efficient communication methods",
                "Consider network latency"
            ],
            "mapping": [
                "Choose mapping method carefully",
                "Ensure consistent mesh definitions",
                "Use conservative or consistent constraints"
            ],
            "performance": [
                "Optimize data exchange",
                "Minimize unnecessary data transfers",
                "Use appropriate acceleration techniques"
            ]
        }

    def _create_topology_schema(self) -> Dict[str, Any]:
        """
        Create an advanced, flexible JSON schema for topology validation
        
        :return: Comprehensive JSON schema dictionary
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "version": {
                    "type": ["number", "string"],
                    "minimum": 1.0,
                    "description": "preCICE configuration version"
                },
                "configuration": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string", 
                            "enum": ["precice", "custom"],
                            "description": "Configuration type"
                        },
                        "dimensions": {
                            "type": ["number", "string"], 
                            "enum": [1, 2, 3, "1", "2", "3"],
                            "description": "Spatial dimensions of the simulation"
                        },
                        "experimental": {
                            "type": "boolean",
                            "description": "Flag for experimental configurations"
                        }
                    },
                    "additionalProperties": True
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "level": {
                            "type": "string", 
                            "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                        },
                        "sink": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "output": {"type": "string"}
                            }
                        }
                    }
                },
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {
                                "type": "string", 
                                "enum": ["scalar", "vector", "tensor"]
                            },
                            "waveform_degree": {
                                "type": ["number", "string"],
                                "minimum": 0,
                                "maximum": 10
                            }
                        },
                        "required": ["name", "type"]
                    },
                    "uniqueItems": True
                },
                "meshes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dimensions": {
                                "type": ["number", "string"], 
                                "enum": [1, 2, 3, "1", "2", "3"]
                            },
                            "data": {
                                "type": "array", 
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "dimensions"]
                    },
                    "uniqueItems": True
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
                            "mapping": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string", 
                                            "enum": [
                                                "nearest-neighbor", 
                                                "nearest-projection", 
                                                "rbf", 
                                                "linear"
                                            ]
                                        },
                                        "constraint": {
                                            "type": "string", 
                                            "enum": ["consistent", "conservative"]
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["name"]
                    }
                },
                "communication": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string", 
                                    "enum": ["sockets", "mpi", "serial"]
                                },
                                "network": {"type": "string"}
                            }
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string", 
                                        "enum": ["sockets", "mpi", "serial"]
                                    },
                                    "network": {"type": "string"}
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
                        "time_window_size": {
                            "type": ["number", "string"],
                            "minimum": 0
                        },
                        "max_iterations": {
                            "type": ["number", "string"],
                            "minimum": 1,
                            "maximum": 1000
                        },
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
            },
            "additionalProperties": True
        }

    def _format_validation_error(self, validation_error: jsonschema.exceptions.ValidationError) -> str:
        """
        Format validation errors with more context and suggestions
        
        :param validation_error: Validation error from jsonschema
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
        
        return (f"Validation Error at {error_path}: {error_message}\n"
                f"  Suggestion: {suggestion}")

    def _validate_data_consistency(self, topology_data: Dict[str, Any]) -> List[str]:
        """
        Perform additional data consistency checks
        
        :param topology_data: Parsed topology data
        :return: List of validation warnings
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
        :return: List of validation warnings
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

    def validate_topology(self, topology_file: str) -> Dict[str, Any]:
        """
        Advanced topology validation with comprehensive checks
        
        :param topology_file: Path to the topology YAML file
        :return: Validation report with errors, warnings, and recommendations
        """
        validation_report = {
            "file": topology_file,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "best_practices": []
        }
        
        try:
            with open(topology_file, 'r') as f:
                topology_data = yaml.safe_load(f)
            
            # Preprocess and validate
            self._preprocess_data(topology_data)
            
            # JSON Schema Validation
            try:
                jsonschema.validate(instance=topology_data, schema=self.topology_schema)
            except jsonschema.exceptions.ValidationError as ve:
                validation_report["errors"].append(self._format_validation_error(ve))
            
            # Additional custom validations
            validation_report["warnings"].extend(self._validate_data_consistency(topology_data))
            validation_report["warnings"].extend(self._validate_mesh_data_references(topology_data))
            
            # Performance and best practices recommendations
            validation_report["recommendations"].extend(
                self._generate_recommendations(topology_data)
            )
            
            # Best practices guidance
            validation_report["best_practices"] = self._check_best_practices(topology_data)
            
        except yaml.YAMLError as e:
            validation_report["errors"].append(f"YAML Parsing Error: {e}")
        except FileNotFoundError:
            validation_report["errors"].append(f"File not found: {topology_file}")
        except Exception as e:
            validation_report["errors"].append(f"Unexpected error: {e}")
        
        return validation_report

    def _preprocess_data(self, data: Dict[str, Any]):
        """
        Advanced data preprocessing and normalization
        
        :param data: Topology data dictionary
        """
        # Normalize numeric values
        numeric_keys = [
            ('configuration', 'dimensions'),
            ('coupling_scheme', 'max_time'),
            ('coupling_scheme', 'time_window_size'),
            ('coupling_scheme', 'max_iterations')
        ]
        
        for section, key in numeric_keys:
            if section in data and key in data[section]:
                try:
                    data[section][key] = float(data[section][key])
                except (ValueError, TypeError):
                    pass

    def _generate_recommendations(self, topology_data: Dict[str, Any]) -> List[str]:
        """
        Generate performance and configuration recommendations
        
        :param topology_data: Parsed topology data
        :return: List of recommendations
        """
        recommendations = []
        
        # Coupling scheme recommendations
        if 'coupling_scheme' in topology_data:
            cs = topology_data['coupling_scheme']
            if cs.get('type', '').endswith('explicit'):
                recommendations.append(
                    "Consider using implicit coupling for better convergence stability"
                )
        
        # Communication recommendations
        if 'communication' in topology_data:
            comm = topology_data['communication']
            if isinstance(comm, list) and len(comm) > 1:
                recommendations.append(
                    "Multiple communication configurations detected. Verify network efficiency."
                )
        
        return recommendations

    def _check_best_practices(self, topology_data: Dict[str, Any]) -> List[str]:
        """
        Check configuration against predefined best practices
        
        :param topology_data: Parsed topology data
        :return: List of best practice recommendations
        """
        best_practices_found = []
        
        # Coupling scheme best practices
        if 'coupling_scheme' in topology_data:
            cs = topology_data['coupling_scheme']
            if cs.get('type', '').endswith('implicit'):
                best_practices_found.extend(
                    self.best_practices.get('coupling_scheme', [])
                )
        
        return best_practices_found

    def validate_all_topologies(self) -> List[Dict[str, Any]]:
        """
        Validate all topology files with comprehensive reporting
        
        :return: List of validation reports
        """
        validation_reports = []
        
        for filename in os.listdir(self.topology_dir):
            if filename.endswith('-topology.yaml'):
                filepath = os.path.join(self.topology_dir, filename)
                report = self.validate_topology(filepath)
                validation_reports.append(report)
        
        return validation_reports

def main():
    load_dotenv('config.env')
    topology_dir = os.getenv('TOPOLOGY_DIR', './topologies')
    
    # Resolve relative path
    topology_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), topology_dir))
    
    validator = TopologyValidator(topology_dir)
    
    # Validate all topologies
    validation_reports = validator.validate_all_topologies()
    
    # Display comprehensive validation results
    for report in validation_reports:
        print(f"\nValidation Report for {report['file']}:")
        
        if report['errors']:
            print("  Errors:")
            for error in report['errors']:
                print(f"    - {error}")
        
        if report['warnings']:
            print("  Warnings:")
            for warning in report['warnings']:
                print(f"    - {warning}")
        
        if report['recommendations']:
            print("  Recommendations:")
            for rec in report['recommendations']:
                print(f"    - {rec}")
        
        if report['best_practices']:
            print("  Best Practices:")
            for bp in report['best_practices']:
                print(f"    - {bp}")

if __name__ == "__main__":
    main()
