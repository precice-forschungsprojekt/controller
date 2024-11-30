#!/usr/bin/python

import os
import sys
import logging
import json
import yaml
import jsonschema
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Secure environment variable loading
load_dotenv('config.env', override=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('topology_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class TopologyValidationError(Exception):
    """Custom exception for topology validation errors."""
    def __init__(self, message, error_type='validation', details=None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}

class TopologyValidator:
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize TopologyValidator with JSON schema.
        
        :param schema_path: Optional path to custom JSON schema
        """
        # Resolve schema path
        base_dir = Path(__file__).parent
        self.schema_path = schema_path or base_dir / 'schemas' / 'topology_schema.json'
        
        # Load and validate schema
        self.schema = self._load_json_schema()
    
    def _load_json_schema(self) -> Dict[str, Any]:
        """
        Load and validate JSON schema.
        
        :return: Parsed JSON schema
        :raises TopologyValidationError: For schema loading issues
        """
        try:
            with open(self.schema_path, 'r') as schema_file:
                schema = json.load(schema_file)
            
            # Validate schema structure
            jsonschema.validators.Draft7Validator.check_schema(schema)
            return schema
        
        except (json.JSONDecodeError, jsonschema.exceptions.SchemaError) as e:
            logger.error(f"Schema validation error: {e}")
            raise TopologyValidationError(
                f"Invalid JSON schema: {e}", 
                error_type='schema_error'
            )
    
    def validate_topology(self, topology_file: str) -> Dict[str, Any]:
        """
        Comprehensive topology validation with detailed reporting.
        
        :param topology_file: Path to topology YAML file
        :return: Validation report
        :raises TopologyValidationError: For validation failures
        """
        validation_report = {
            'file': topology_file,
            'status': 'pending',
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Load topology data
            with open(topology_file, 'r') as f:
                topology_data = yaml.safe_load(f)
            
            # JSON Schema Validation
            try:
                jsonschema.validate(instance=topology_data, schema=self.schema)
                validation_report['status'] = 'valid'
            except jsonschema.exceptions.ValidationError as ve:
                validation_report['status'] = 'invalid'
                validation_report['errors'].append(self._format_validation_error(ve))
            
            # Additional custom validations
            self._validate_participant_consistency(topology_data, validation_report)
            self._validate_coupling_configuration(topology_data, validation_report)
            self._check_performance_recommendations(topology_data, validation_report)
            
            return validation_report
        
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {topology_file}: {e}")
            validation_report['status'] = 'error'
            validation_report['errors'].append(f"YAML Parsing Error: {e}")
        
        except TopologyValidationError as tve:
            logger.error(f"Topology validation error: {tve}")
            validation_report['status'] = 'invalid'
            validation_report['errors'].append(str(tve))
        
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            validation_report['status'] = 'error'
            validation_report['errors'].append(f"Unexpected Error: {e}")
        
        return validation_report
    
    def _format_validation_error(self, error: jsonschema.exceptions.ValidationError) -> str:
        """
        Format JSON schema validation errors for readability.
        
        :param error: ValidationError from jsonschema
        :return: Formatted error message
        """
        return (
            f"Validation Error at {'/'.join(str(p) for p in error.path)}: "
            f"{error.message}"
        )
    
    def _validate_participant_consistency(self, topology_data: Dict[str, Any], 
                                          report: Dict[str, Any]):
        """
        Validate participant configuration consistency.
        
        :param topology_data: Parsed topology data
        :param report: Validation report to update
        """
        participants = topology_data.get('participants', {})
        
        # Check for duplicate mesh names
        mesh_names = [
            participant.get('mesh', {}).get('name') 
            for participant in participants.values()
        ]
        duplicate_meshes = set([name for name in mesh_names if mesh_names.count(name) > 1])
        
        if duplicate_meshes:
            report['warnings'].append(
                f"Duplicate mesh names detected: {duplicate_meshes}"
            )
        
        # Validate data field consistency
        for participant_name, participant in participants.items():
            mesh = participant.get('mesh', {})
            data_fields = mesh.get('data_fields', [])
            
            # Check data field naming conventions
            for field in data_fields:
                if not field['name'].replace('_', '').isalnum():
                    report['warnings'].append(
                        f"Non-standard data field name in {participant_name}: {field['name']}"
                    )
    
    def _validate_coupling_configuration(self, topology_data: Dict[str, Any], 
                                         report: Dict[str, Any]):
        """
        Validate coupling configuration details.
        
        :param topology_data: Parsed topology data
        :param report: Validation report to update
        """
        couplings = topology_data.get('couplings', [])
        participants = topology_data.get('participants', {}).keys()
        
        for coupling in couplings:
            # Verify participants exist
            for participant in coupling.get('participants', []):
                if participant not in participants:
                    report['errors'].append(
                        f"Coupling references non-existent participant: {participant}"
                    )
            
            # Check data consistency
            for data in coupling.get('data', []):
                if data['type'] not in ['read', 'write']:
                    report['warnings'].append(
                        f"Unusual data transfer type: {data['type']}"
                    )
    
    def _check_performance_recommendations(self, topology_data: Dict[str, Any], 
                                           report: Dict[str, Any]):
        """
        Generate performance and best practice recommendations.
        
        :param topology_data: Parsed topology data
        :param report: Validation report to update
        """
        simulation = topology_data.get('simulation', {})
        time_step = simulation.get('time_step', 0)
        
        # Time step recommendations
        if time_step < 0.001:
            report['recommendations'].append(
                "Very small time step detected. Consider performance implications."
            )
        
        # Precision recommendations
        precision = simulation.get('precision', 'double')
        if precision == 'single':
            report['recommendations'].append(
                "Using single precision. Verify if this meets simulation accuracy requirements."
            )

def main():
    """
    Main entry point for topology validation.
    """
    try:
        # Use environment variable or default topology path
        topology_dir = os.getenv('TOPOLOGY_DIR', './topologies')
        
        validator = TopologyValidator()
        all_reports = []
        
        # Validate all topology files
        for filename in os.listdir(topology_dir):
            if filename.endswith('.yaml'):
                filepath = os.path.join(topology_dir, filename)
                report = validator.validate_topology(filepath)
                all_reports.append(report)
                
                # Log detailed validation results
                logger.info(f"Validation Report for {filename}:")
                logger.info(f"  Status: {report['status']}")
                
                if report['errors']:
                    logger.warning(f"  Errors: {report['errors']}")
                if report['warnings']:
                    logger.warning(f"  Warnings: {report['warnings']}")
                if report['recommendations']:
                    logger.info(f"  Recommendations: {report['recommendations']}")
        
        # Determine overall validation status
        overall_status = all(
            report['status'] in ['valid', 'pending'] 
            for report in all_reports
        )
        
        sys.exit(0 if overall_status else 1)
    
    except Exception as e:
        logger.error(f"Topology validation process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
