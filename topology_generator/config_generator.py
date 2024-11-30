import os
import yaml
from typing import Dict, Any
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from topology_schema import TopologyConfig

class PreciceConfigGenerator:
    def __init__(self, topology_file: str):
        """
        Initialize the generator with a topology YAML file
        
        :param topology_file: Path to the topology YAML configuration
        """
        with open(topology_file, 'r') as f:
            topology_data = yaml.safe_load(f)
        
        # Validate topology configuration
        self.topology = TopologyConfig(**topology_data)
        
        # Create output directory
        self.output_dir = os.path.join(
            os.path.dirname(topology_file), 
            f"{self.topology.name}-simulation"
        )
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_precice_config(self) -> str:
        """
        Generate preCICE XML configuration
        
        :return: Path to generated precice-config.xml
        """
        # Create root element
        root = ET.Element("precice-configuration")
        
        # Add logging configuration
        log = ET.SubElement(root, "log")
        sink = ET.SubElement(log, "sink", {
            "filter": "%Severity% > debug and %Rank% = 0",
            "format": "---[precice] %ColorizedSeverity% %Message%",
            "enabled": "true"
        })
        
        # Add data configurations
        for data in self.topology.data:
            ET.SubElement(root, "data:" + data.type, name=data.name)
        
        # Add mesh configurations
        for mesh in self.topology.meshes:
            mesh_elem = ET.SubElement(root, "mesh", name=mesh.name, dimensions=str(mesh.dimensions))
            for data_name in mesh.data:
                ET.SubElement(mesh_elem, "use-data", name=data_name)
        
        # Add participant configurations
        for participant in self.topology.participants:
            participant_elem = ET.SubElement(root, "participant", name=participant.name)
            
            # Provide mesh
            ET.SubElement(participant_elem, "provide-mesh", name=participant.provides_mesh)
            
            # Receive meshes
            for recv_mesh in participant.receives_meshes:
                ET.SubElement(participant_elem, "receive-mesh", 
                              name=recv_mesh, 
                              _from=next(p.name for p in self.topology.participants if p.provides_mesh == recv_mesh))
            
            # Read/Write data
            for read_data in participant.read_data:
                ET.SubElement(participant_elem, "read-data", name=read_data, mesh=participant.provides_mesh)
            
            for write_data in participant.write_data:
                ET.SubElement(participant_elem, "write-data", name=write_data, mesh=participant.provides_mesh)
            
            # Mapping configurations
            if participant.mapping_type == "rbf":
                rbf_read = ET.SubElement(participant_elem, "mapping:rbf", 
                                         direction="read", 
                                         _from=participant.receives_meshes[0] if participant.receives_meshes else "",
                                         to=participant.provides_mesh,
                                         constraint=participant.mapping_constraint)
                ET.SubElement(rbf_read, "basis-function:thin-plate-splines")
                
                rbf_write = ET.SubElement(participant_elem, "mapping:rbf", 
                                          direction="write", 
                                          _from=participant.provides_mesh,
                                          to=participant.receives_meshes[0] if participant.receives_meshes else "",
                                          constraint=participant.mapping_constraint)
                ET.SubElement(rbf_write, "basis-function:thin-plate-splines")
        
        # Add communication method (default to sockets)
        if len(self.topology.participants) > 1:
            m2n = ET.SubElement(root, "m2n:sockets", 
                                acceptor=self.topology.participants[0].name, 
                                connector=self.topology.participants[1].name, 
                                exchange_directory="..")
        
        # Add coupling scheme
        coupling = ET.SubElement(root, f"coupling-scheme:{self.topology.coupling.type}")
        ET.SubElement(coupling, "time-window-size", value=str(self.topology.coupling.time_window_size))
        ET.SubElement(coupling, "max-time", value=str(self.topology.coupling.max_time))
        
        participants = ET.SubElement(coupling, "participants", 
                                     first=self.topology.participants[0].name, 
                                     second=self.topology.participants[1].name)
        
        # Add exchanges
        for exchange in self.topology.coupling.exchanges:
            ET.SubElement(coupling, "exchange", 
                          data=exchange.get('data', ''), 
                          mesh=exchange.get('mesh', ''), 
                          _from=exchange.get('from', ''), 
                          to=exchange.get('to', ''))
        
        # Convert to pretty-printed XML
        xml_str = ET.tostring(root, encoding='unicode')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        # Write to file
        config_path = os.path.join(self.output_dir, "precice-config.xml")
        with open(config_path, 'w') as f:
            f.write(pretty_xml)
        
        return config_path
    
    def generate_run_script(self) -> str:
        """
        Generate run.sh script
        
        :return: Path to generated run.sh
        """
        run_script = "#!/bin/bash\n\n"
        run_script += "# Run simulation participants\n"
        
        for participant in self.topology.participants:
            run_script += f"# Run {participant.name} participant\n"
            run_script += f"./{participant.name}_participant &\n"
        
        run_script += "\n# Wait for all participants to complete\nwait\n"
        
        run_path = os.path.join(self.output_dir, "run.sh")
        with open(run_path, 'w') as f:
            f.write(run_script)
        
        # Make executable
        os.chmod(run_path, 0o755)
        
        return run_path
    
    def generate_clean_script(self) -> str:
        """
        Generate clean.sh script
        
        :return: Path to generated clean.sh
        """
        clean_script = "#!/bin/bash\n\n"
        clean_script += "# Clean up simulation outputs and temporary files\n"
        clean_script += "rm -rf *.log\n"
        clean_script += "rm -rf precice-*.xml\n"
        clean_script += "rm -rf *.vtk\n"
        
        clean_path = os.path.join(self.output_dir, "clean.sh")
        with open(clean_path, 'w') as f:
            f.write(clean_script)
        
        # Make executable
        os.chmod(clean_path, 0o755)
        
        return clean_path
    
    def generate_readme(self) -> str:
        """
        Generate README.md
        
        :return: Path to generated README.md
        """
        readme_content = f"# {self.topology.name} Simulation\n\n"
        readme_content += "## Simulation Participants\n"
        
        for participant in self.topology.participants:
            readme_content += f"### {participant.name}\n"
            readme_content += f"- Provides Mesh: {participant.provides_mesh}\n"
            readme_content += f"- Read Data: {', '.join(participant.read_data)}\n"
            readme_content += f"- Write Data: {', '.join(participant.write_data)}\n\n"
        
        readme_content += "## Running the Simulation\n"
        readme_content += "1. Ensure all dependencies are installed\n"
        readme_content += "2. Run `./run.sh`\n"
        readme_content += "3. Use `./clean.sh` to remove output files\n"
        
        readme_path = os.path.join(self.output_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        return readme_path
    
    def generate(self):
        """
        Generate all configuration files
        """
        print(f"Generating simulation files in {self.output_dir}")
        self.generate_precice_config()
        self.generate_run_script()
        self.generate_clean_script()
        self.generate_readme()
        print("Simulation configuration generated successfully!")

def main():
    # Example usage
    topology_file = os.path.join(os.path.dirname(__file__), "example_topology.yaml")
    generator = PreciceConfigGenerator(topology_file)
    generator.generate()

if __name__ == "__main__":
    main()
