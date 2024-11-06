import os
import logging
import yaml
import json
import argparse
from myutils.UT_PCErrorLogging import UT_PCErrorLogging
from ui_struct.UI_UserInput import UI_UserInput
from precice_struct import PS_PreCICEConfig
import shutil

# Logging setup
log_level = getattr(logging, "INFO", None)
logging.basicConfig(level=log_level)

def run_one_generate(input_file_name : str, output_xml_file : str, format: str):
    """ Function to run one XML file generation """
    mylog = UT_PCErrorLogging()

    # Open and parse the input file based on its format
    if format == "yaml":
        with open(input_file_name) as config_file:
            config = yaml.load(config_file.read())
    elif format == "json":
        with open(input_file_name) as config_file:
            config = json.load(config_file.read())
    else:
        raise ValueError("Unsupported configuration format")
    
    logging.info("Input {} file:\t".format(format) + input_file_name)
    logging.info("building the user input info ... ")

    user_ui = UI_UserInput()
    user_ui.init_from_yaml(config, mylog)

    # dummy initial and empty precice constructor
    precice_config = PS_PreCICEConfig()
    logging.info("generating preCICE config ... ")
    # build up the precice data structure
    precice_config.create_config(user_ui)

    # write our XML config
    logging.info("write preCICE config ... ")
    precice_config.write_precice_xml_config(output_xml_file, mylog)

    logging.info("End generate")
    pass

# Argument parsing
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--input-config", default="./examples/2/topology.yaml", help="Name of the input YML file")
parser.add_argument("--output-xml", default="test.xml", help="Output precice XML config file")
parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Format of the input configuration file")
parser.add_argument("--test-all", action='store_true', help="If this is true then we run in test mode and we generate all XMLs and compare them")

# parsing the arguments into fields
args = parser.parse_args()
input_file_name_arg = args.input_config
output_xml_file_arg = args.output_xml
test_all = args.test_all
format = args.format

if test_all:
    logging.info("Execute all test cases ... ")
    dirs = os.listdir("./examples/")
    for dir in dirs:
        in_yaml_file_name = "./examples/" + dir + "/topology.yaml"
        file_exists = os.path.isfile(in_yaml_file_name)
        if file_exists:
            out_file_name = "./testing/output/" + dir + "_out_controller_tmp.xml"
            run_one_generate(in_yaml_file_name, out_file_name, format)
            # Compare the generated XML with a reference
            ref_file_name = "./testing/output/" + dir + "_out_controller.xml"
            if os.path.isfile(ref_file_name):
                refernce = os.stat(ref_file_name)
                test = os.stat(out_file_name)
                if (refernce.st_size == test.st_size):
                    logging.info("Test " + dir + " OK ")
                    shutil.copyfile(out_file_name, ref_file_name)
                    os.unlink(out_file_name)
                else:
                    logging.info("Test " + dir + " FAILED ")
            else:
                shutil.copyfile(out_file_name, ref_file_name)
                os.unlink(out_file_name)
    logging.info("Finished all testing ... ")
else:
    run_one_generate(input_file_name_arg, output_xml_file_arg, format)
