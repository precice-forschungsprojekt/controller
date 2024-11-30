# preCICE Controller
WIP: A configuration generator for preCICE

Original implementation by Janos Benk as part of [COPLON](http://coplon.de/), based on previous work by Lucia Cheung, in cooperation with [SimScale](https://www.simscale.com/).

## Dependencies

* `xml_diff`: e.g. `pip3 install xml_diff`

## How to run

Simply type `python3 main.py -h` to get an overview. 

## Examples

In `examples`, several example configurations are listed. `topology.yaml` is always the input and all other files are reference output files: `precice-config.xml` and potentially adapter configurations, e.g. `calculix.yaml`. 

## Topology Validation Mechanism

### Overview
This directory contains tools for validating preCICE topology configurations converted from XML to YAML.

### Validation Mechanism

#### `topology_validator.py`
A comprehensive validation script that performs multiple checks on topology files:

1. **Schema Validation**
   - Validates against a predefined JSON schema
   - Checks structure, required fields, and data types
   - Ensures configuration integrity

2. **Data Consistency Checks**
   - Verifies unique data and mesh names
   - Prevents duplicate references

3. **Reference Validation**
   - Confirms data references are valid across meshes and participants
   - Catches mismatched or undefined data types

### Running the Validator
```bash
python topology_validator.py
```
### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```
### Validation Criteria
- YAML parsing
- Schema compliance
- Data type consistency
- Reference integrity
- Structural validation

### Supported Topology Configurations
- Supports preCICE tutorial topology files
- Handles 1D, 2D, and 3D configurations
- Validates serial and parallel coupling schemes

### Future Improvements
- Add more granular validation rules
- Support custom validation configurations
- Integrate with CI/CD pipelines
