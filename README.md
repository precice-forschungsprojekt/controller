# preCICE Controller
WIP: A configuration generator for preCICE

Original implementation by Janos Benk as part of [COPLON](http://coplon.de/), based on previous work by Lucia Cheung, in cooperation with [SimScale](https://www.simscale.com/).

## Dependencies

* `xml_diff`: e.g. `pip3 install xml_diff`

## How to run

Simply type `python3 main.py -h` to get an overview. 

## Examples

In `examples`, several example configurations are listed. `topology.yaml` is always the input and all other files are reference output files: `precice-config.xml` and potentially adapter configurations, e.g. `calculix.yaml`. 



