#!/usr/bin/python

# this is the main entry point for the preCICE controller

import os
import logging
import yaml
import pprint
import argparse
from dotenv import load_dotenv
from myutils.UT_PCErrorLogging import UT_PCErrorLogging
from ui_struct.UI_UserInput import UI_UserInput
from precice_struct import PS_PreCICEConfig

# Load environment variables
load_dotenv('config.env')

# this is important for XML file diffing
import lxml.etree
from xml_diff import compare

# to copy file
import shutil

# ====================== START XML generation ========================
def run_one_generate(input_file_name : str = None, output_xml_file : str = None):
    """ Function to run one XML file generation """
    mylog = UT_PCErrorLogging()

    # Use environment variables with fallback
    if input_file_name is None:
        input_file_name = os.getenv('INPUT_TOPOLOGY', './examples/1/topology.yaml')
    
    if output_xml_file is None:
        output_xml_file = os.getenv('OUTPUT_XML', './precice-config.xml')

    # Open and parse the YAML file
    try:
        with open(input_file_name, 'r') as config_file:
            config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
        logging.info(f"Input YML file: {input_file_name}")
        logging.info("Building the user input info...")

        user_ui = UI_UserInput()
        user_ui.init_from_yaml(config, mylog)

        # dummy initial and empty precice constructor
        precice_config = PS_PreCICEConfig()
        logging.info("Generating preCICE config...")
        # build up the precice data structure
        precice_config.create_config(user_ui)

        # write our XML config
        logging.info("Writing preCICE config...")
        precice_config.write_precice_xml_config(output_xml_file, mylog)

        logging.info("End generate")
    except Exception as e:
        logging.error(f"Error during XML generation: {e}")

# ====================== END XML generation ========================

# ==================== START MAIN =================
def main():
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='preCICE Controller')
    parser.add_argument('--input', help='Input topology YAML file')
    parser.add_argument('--output', help='Output XML configuration file')
    args = parser.parse_args()

    # Use command-line args or environment variables
    input_file = args.input or os.getenv('INPUT_TOPOLOGY', './examples/1/topology.yaml')
    output_file = args.output or os.getenv('OUTPUT_XML', './precice-config.xml')

    run_one_generate(input_file, output_file)

if __name__ == "__main__":
    main()
