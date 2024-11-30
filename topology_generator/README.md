# preCICE Topology Generator

## Overview
This tool generates configuration files for preCICE simulations based on a simple YAML topology description.

## Features
- Generate `precice-config.xml`
- Create `run.sh` and `clean.sh` scripts
- Generate a comprehensive `README.md`
- Support for multiple simulation participants
- Flexible mapping and coupling configurations
- ✨ Dynamic YAML-based topology configuration
- 🔍 Comprehensive configuration validation
- 🛡️ Strong type checking and error handling
- 🚀 Automatic generation of preCICE configuration files
- 📦 Support for multiple simulation participants
- 🔀 Flexible mapping and coupling configurations

## Validation Checks
The topology generator performs extensive validation:
- Unique participant and mesh names
- Consistent data exchange
- Mesh and data existence
- Coupling participant validation
- Dimensional and type constraints

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python config_generator.py
```

## Topology YAML Schema
The topology YAML file defines:
- Simulation name
- Data types
- Mesh configurations
- Participant details
- Coupling scheme
The topology YAML file supports:
- Simulation metadata
- Data type definitions
- Mesh configurations
- Participant details
- Coupling scheme parameters

### Example Topology
```yaml
name: fluid-solid-interaction
data:
  - name: Force
    type: vector
  - name: Displacement
    type: vector

meshes:
  - name: Fluid-Mesh
    dimensions: 2
    data: 
      - Force
      - Displacement

participants:
  - name: Fluid
    provides_mesh: Fluid-Mesh
    read_data: 
      - Displacement
    write_data: 
      - Force
    mapping_type: RBF
    mapping_constraint: consistent

coupling:
  type: SERIAL_EXPLICIT
  time_window_size: 0.025
  max_time: 2.5
```

## Configuration Options
- `data`: Define data types for exchange
  - Supports scalar, vector, and tensor types
- `meshes`: Define participant meshes
  - 1D, 2D, and 3D support
- `participants`: Configure simulation participants
  - Mapping types: RBF, Nearest Projection
  - Mapping constraints
- `coupling`: Set coupling scheme parameters
  - Serial/Parallel
  - Explicit/Implicit schemes
- `data`: Define data types for exchange
- `meshes`: Define participant meshes
- `participants`: Configure simulation participants
- `coupling`: Set coupling scheme parameters

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🌐 preCICE Topology Configuration Generator

## 🚀 Advanced Configuration Management

### 🔧 Flexible Generation Options

The Topology Configuration Generator now supports advanced configuration through `TopologyGeneratorConfig`:

```python
config = {
    'log_level': 'DEBUG',
    'xml_pretty_print': True,
    'overwrite_existing': False,
    'backup_existing': True,
    'custom_data_mappings': {
        'Force': 'CustomForce',
        'Displacement': 'CustomDisplacement'
    }
}

generator = PreciceConfigGenerator(
    topology_file, 
    generator_config=config
)
```

### ✨ Key Configuration Features

- **Logging Control**
  - Configurable log levels
  - Logging to console and file
  - Detailed runtime information

- **File Generation Options**
  - Overwrite protection
  - Automatic backup of existing configurations
  - Custom output directory support

- **Advanced Mapping**
  - Custom data name mappings
  - Mesh transformation rules
  - Flexible enum handling

### 🛡️ Validation Enhancements

- Comprehensive topology configuration checks
- Strict and flexible validation modes
- Detailed error reporting
- Custom mapping and transformation support

## 📦 Configuration Options

### Logging Configuration
- `log_level`: Set logging verbosity
  - `'DEBUG'`: Most detailed
  - `'INFO'`: Standard logging
  - `'WARNING'`: Only warnings and errors
  - `'ERROR'`: Critical errors only

### File Generation
- `overwrite_existing`: Control file overwriting
- `backup_existing`: Create backups of existing files
- `xml_pretty_print`: Format XML with indentation

### Custom Mappings
- `custom_data_mappings`: Rename data fields
- `custom_mesh_transformations`: Modify mesh configurations

## 💻 Usage Example

```python
from controller.topology_generator import PreciceConfigGenerator

# Basic usage
generator = PreciceConfigGenerator('topology.yaml')
generator.generate()

# Advanced configuration
config = {
    'log_level': 'DEBUG',
    'custom_data_mappings': {
        'Force': 'CustomForceData'
    }
}
generator = PreciceConfigGenerator(
    'topology.yaml', 
    generator_config=config
)
result = generator.generate()
```

## 🔍 Generated Artifacts

The generator creates:
- `precice-config.xml`: preCICE configuration
- `run.sh`: Simulation execution script
- `clean.sh`: Environment cleanup script
- `README.md`: Simulation documentation

## 📝 Contributing

Contributions are welcome! Please submit pull requests or open issues.

## 📄 License

[Your License Here]
