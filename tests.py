import os
import pytest
from FP_main import run_one_generate, generate_readme, generate_run_script, generate_clean_script

# Test cases for generating the README file
def test_generate_readme():
    dir_name = "./test_dir"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    generate_readme(dir_name)
    assert os.path.isfile(f"{dir_name}/README.md")
    with open(f"{dir_name}/README.md", "r") as readme:
        content = readme.read()
        assert "PreCICE configuration" in content
    shutil.rmtree(dir_name)

# Test cases for generating the run script
def test_generate_run_script():
    dir_name = "./test_dir"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    generate_run_script(dir_name)
    assert os.path.isfile(f"{dir_name}/run.sh")
    with open(f"{dir_name}/run.sh", "r") as run_script:
        content = run_script.read()
        assert "Starting PreCICE simulation" in content
    shutil.rmtree(dir_name)

# Test cases for generating the clean script
def test_generate_clean_script():
    dir_name = "./test_dir"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    generate_clean_script(dir_name)
    assert os.path.isfile(f"{dir_name}/clean.sh")
    with open(f"{dir_name}/clean.sh", "r") as clean_script:
        content = clean_script.read()
        assert "Cleaning up temporary files" in content
    shutil.rmtree(dir_name)

# Test cases for the main function run_one_generate
def test_run_one_generate():
    input_file_name = "./examples/2/topology.yaml"
    output_xml_file = "test.xml"
    format = "yaml"
    run_one_generate(input_file_name, output_xml_file, format)
    assert os.path.isfile(output_xml_file)
    if os.path.exists(output_xml_file):
        os.remove(output_xml_file)
    shutil.rmtree("./test_dir")

# Integration test for the entire process including generation of scripts
def test_integration():
    input_file_name = "./examples/2/topology.yaml"
    output_xml_file = "test.xml"
    format = "yaml"
    run_one_generate(input_file_name, output_xml_file, format)
    assert os.path.isfile(output_xml_file)
    if os.path.exists(output_xml_file):
        os.remove(output_xml_file)
    shutil.rmtree("./test_dir")

# Add more tests as needed to cover all functionalities and edge cases
