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

import xmltodict
import json

# ====================== START XML generation ========================
def run_one_generate(input_file_name : str, output_xml_file : str):
    """ Function to run one XML file generation """
    mylog = UT_PCErrorLogging()

    # Open and parse the YAML file
    config_file = open(input_file_name)
    config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
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

# import hashlib
#
#
# def compute_canonical_hash(file_name):
#     with open(file_name, 'rb') as f:
#         xml_content = f.read()
#     root = lxml.etree.fromstring(xml_content)
#     canonical_xml = lxml.etree.tostring(root, method='c14n')
#     hash_func = hashlib.sha256()
#     hash_func.update(canonical_xml)
#     return hash_func.hexdigest()
#
# def compare_files_by_canonical_hash(ref_file_name, out_file_name):
#     reference_hash = compute_canonical_hash(ref_file_name)
#     test_hash = compute_canonical_hash(out_file_name)
#
#     if reference_hash == test_hash:
#         print("The files are identical.")
#     else:
#         print("The files are different.")
#
# # Example usage
# # ref_file_name = 'path/to/reference/file'
# # out_file_name = 'path/to/output/file'
# # compare_files_by_canonical_hash(ref_file_name, out_file_name)
#
#
#
#
# def remove_namespace_prefixes(tree):
#     for elem in tree.getiterator():
#         if not hasattr(elem.tag, 'find'):
#             continue
#         i = elem.tag.find('}')
#         if i > 0:
#             elem.tag = elem.tag[i+1:]
#     return tree
#
# def compare_xml_trees(file1, file2):
#     try:
#         tree1 = lxml.etree.parse(file1)
#         tree1 = remove_namespace_prefixes(tree1)
#     except lxml.etree.XMLSyntaxError as e:
#         print(f"Error parsing {file1}: {e}")
#         return False
#
#     try:
#         tree2 = lxml.etree.parse(file2)
#         tree2 = remove_namespace_prefixes(tree2)
#     except lxml.etree.XMLSyntaxError as e:
#         print(f"Error parsing {file2}: {e}")
#         return False
#
#     if lxml.etree.tostring(tree1) == lxml.etree.tostring(tree2):
#         print("The XML files are identical.")
#     else:
#         print("The XML files are different.")
#
# # Example usage
# # ref_file_name = 'path/to/reference/file'
# # out_file_name = 'path/to/output/file'
# # compare_xml_trees(ref_file_name, out_file_name)
#
#
#
# def normalize_xml(file_name):
#     with open(file_name, 'r') as file:
#         xml_content = file.read()
#     return xmltodict.parse(xml_content)
#
# def compare_xml_content(file1, file2):
#     xml1 = normalize_xml(file1)
#     xml2 = normalize_xml(file2)
#
#     if json.dumps(xml1, sort_keys=True) == json.dumps(xml2, sort_keys=True):
#         print("The XML files are identical.")
#     else:
#         print("The XML files are different.")
#
# # Example usage
# # ref_file_name = 'path/to/reference/file'
# # out_file_name = 'path/to/output/file'
# # compare_xml_content(ref_file_name, out_file_name)










# ==================== START MAIN =================
def main():
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

        dirs = sorted(dirs, key=int)

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

                # compare_xml_content(ref_file_name, out_file_name)

                if (refernce.st_size == test.st_size):
                    # the two files are equal
                    logging.info("Test " +  dir + " OK ")
                    #overwrite the file
                    shutil.copyfile(out_file_name, ref_file_name)
                    os.unlink(out_file_name)
                    pass
                else:
                    # size difference, jus issue an ERROR
                    logging.info("Test " + dir + " FAILED ")
                    pass
                pass
        logging.info("Finished all testing ... ")
    else:
        # just call with the default arguments
        run_one_generate(input_file_name_arg, output_xml_file_arg)
        pass

if __name__ == "__main__":
    main()



