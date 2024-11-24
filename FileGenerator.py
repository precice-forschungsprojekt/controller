from pathlib import Path
from StructureHandler import StructureHandler
from precice_struct import PS_PreCICEConfig
import yaml
from ui_struct.UI_UserInput import UI_UserInput
from myutils.UT_PCErrorLogging import UT_PCErrorLogging
from Logger import Logger

class FileGenerator:
    def __init__(self, file: Path) -> None:
        """ Class which takes care of generating the content of the necessary files
            :param file: Input yaml file that is needed for generation of the precice-config.xml file"""
        self.input_file = file
        self.precice_config = PS_PreCICEConfig()
        self.mylog = UT_PCErrorLogging()
        self.user_ui = UI_UserInput()
        self.logger = Logger()
        self.structure = StructureHandler()

    def generate_precice_config(self) -> None:
        """Generates the precice-config.xml file based on the topology.yaml file."""
        
        # Try to open the yaml file and get the configuration
        try:
            with open(self.input_file, "r") as config_file:
                config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
                self.logger.info(f"Input YAML file: {self.input_file}")
        except FileNotFoundError:
            self.logger.error(f"Input YAML file {self.input_file} not found.")
            return
        except Exception as e:
            self.logger.error(f"Error reading input YAML file: {str(e)}")
            return

        # Build the ui
        self.logger.info("Building the user input info...")
        self.user_ui.init_from_yaml(config, self.mylog)

        # Generate the precice-config.xml file
        self.logger.info("Generating preCICE config...")
        self.precice_config.create_config(self.user_ui)

        # Set the target of the file and write out to it
        # Warning: self.structure.precice_config is of type Path, so it needs to be converted to str
        target = str(self.structure.precice_config)
        try:
            self.logger.info(f"Writing preCICE config to {target}...")
            self.precice_config.write_precice_xml_config(target, self.mylog)
        except Exception as e:
            self.logger.error(f"Failed to write preCICE XML config: {str(e)}")
            return

        self.logger.success(f"XML generation completed successfully: {target}")

if __name__ == "__main__":
    fileGenerator = FileGenerator(Path("./examples/1/topology.yaml"))
    fileGenerator.generate_precice_config()
