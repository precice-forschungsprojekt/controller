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
