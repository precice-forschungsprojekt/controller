#!/usr/bin/python

# this is the main entry point for the preCICE controller

import os
import logging
import yaml
import pprint
import argparse
from myutils.UT_PCErrorLogging import UT_PCErrorLogging
from ui_struct.UI_UserInput import UI_UserInput
from precice_struct import PS_PreCICEConfig

# this is important for XML file diffing
import lxml.etree
from xml_diff import compare

# to copy file
import shutil

# ====================== START XML generation ========================
def run_one_generate(input_file_name : str, output_xml_file : str):
    """ Function to run one XML file generation """
    mylog = UT_PCErrorLogging()

    # Open and parse the YAML file
    config_file = open(input_file_name)
    config = yaml.load(config_file.read())
    logging.info("Input YML file:\t" + input_file_name)
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
# ====================== END XML generation ========================

# ==================== START MAIN =================
log_level = getattr(logging, "INFO", None)
logging.basicConfig(level=log_level)

# define the argument list of the main function
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--input-config", default="./examples/2/topology.yaml", help="Name of the input YML file")
parser.add_argument("--output-xml", default="test.xml", help="Output precice XML config file")
parser.add_argument("--test-all", default="false", help="If this is true then we run in test mode and we generate all XMLs and we compare them")

# parsing the arguments into fields
args = parser.parse_args()
input_file_name_arg = args.input_config
output_xml_file_arg = args.output_xml
test_all = args.test_all

# test if we are in test mode
if test_all == "true":
    # get all directories from the example directory and for each call the method
    logging.info("Execute all test cases ... ")
    # ./examples/*/topology.yaml
    dirs = os.listdir("./examples/")
    print( dirs )
    for dir in dirs :
        in_yaml_file_name = "./examples/" + dir + "/topology.yaml"
        file_exists = os.path.isfile(in_yaml_file_name)
        if file_exists:
            # if this YAML file exists then call the function for it
            ref_file_name = "./testing/output/" + dir + "_out_controller.xml"
            out_file_name = "./testing/output/" + dir + "_out_controller_tmp.xml"
            run_one_generate(in_yaml_file_name, out_file_name)
            # once we generated the out file then we compare it
            refernce = os.stat(ref_file_name)
            test = os.stat(out_file_name)
            #dom2 = lxml.etree.parse(out_file_name).getroot()
            #comparison = compare(dom1, dom2)
            if (refernce.st_size == test.st_size):
                # the two files are equal
                logging.info("Test " +  dir + " OK ")
                #overwrite the file
                shutil.copyfile(out_file_name, ref_file_name)
                os.unlink(out_file_name)
                pass
            else:
                # size differe, jus issue an ERROR
                logging.info("Test " + dir + " FAILED ")
                pass
            pass
    logging.info("Finished all testing ... ")
else:
    # just call with the default arguments
    run_one_generate(input_file_name_arg, output_xml_file_arg)
    pass





