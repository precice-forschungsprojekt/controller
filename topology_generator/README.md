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

## 🚀 Overview

The Topology Configuration Generator is an advanced tool for automating the creation of preCICE simulation configurations. It provides a flexible, user-friendly YAML-based interface for defining complex multiphysics simulation topologies.

## ✨ Key Features

### 🔍 Comprehensive Validation
- **Robust Configuration Checking**
  - Unique participant name validation
  - Consistent data exchange verification
  - Mesh and data existence checks
  - Coupling participant validation

### 🧩 Flexible Configuration
- Support for multiple enum representations
- Intelligent type conversion
- Detailed error reporting

### 🛡️ Advanced Validation Mechanisms
- Pydantic-based schema validation
- Custom topology configuration checks
- Comprehensive error messages

## 🔧 Configuration Validation Checks

The generator performs the following comprehensive checks:

1. **Participant Validation**
   - Ensure unique participant names
   - Verify provided and received meshes exist
   - Check read/write data consistency

2. **Topology Constraints**
   - Minimum two participants required for coupling
   - Validate coupling participant definitions
   - Check data and mesh references

3. **Simulation Parameters**
   - Positive time window size
   - Valid maximum simulation time

## 📦 Enum Support

Supports flexible enum representations:
- Integer-based enum values
- String-based enum values
- Automatic conversion and validation

## 💻 Usage Example

```yaml
name: fluid-solid-interaction
participants:
  - name: Fluid
    provides_mesh: Fluid-Mesh
    mapping_type: 0  # RBF Mapping
  - name: Solid
    provides_mesh: Solid-Mesh
    mapping_type: 1  # Nearest Projection
```

## 🛠️ Error Handling

Detailed error messages with precise location and context:
```
Topology configuration validation failed:
participants -> name: Must be unique
data -> type: Invalid data type
```

## 📝 Contributing

Contributions are welcome! Please submit pull requests or open issues to improve the generator.

## 📄 License

[Your License Here]
