from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum, auto

class MappingType(Enum):
    RBF = auto()
    NEAREST_PROJECTION = auto()
    CONSISTENT = auto()
    CONSERVATIVE = auto()

class CouplingSchemeType(Enum):
    SERIAL_EXPLICIT = auto()
    SERIAL_IMPLICIT = auto()
    PARALLEL_EXPLICIT = auto()
    PARALLEL_IMPLICIT = auto()

class DataType(Enum):
    SCALAR = "scalar"
    VECTOR = "vector"
    TENSOR = "tensor"

class DataConfig(BaseModel):
    """Configuration for data exchange between participants"""
    name: str
    type: DataType = DataType.VECTOR

class MeshConfig(BaseModel):
    """Configuration for participant meshes"""
    name: str
    dimensions: int = Field(ge=1, le=3, default=2)
    data: List[str] = []

    @validator('data')
    def validate_data_unique(cls, data):
        """Ensure unique data names"""
        if len(set(data)) != len(data):
            raise ValueError("Data names must be unique within a mesh")
        return data

class ParticipantConfig(BaseModel):
    """Configuration for a simulation participant"""
    name: str
    provides_mesh: str
    receives_meshes: List[str] = []
    read_data: List[str] = []
    write_data: List[str] = []
    mapping_type: MappingType = MappingType.RBF
    mapping_constraint: str = "consistent"

    @validator('provides_mesh')
    def validate_mesh_name(cls, mesh):
        """Validate mesh name is not empty"""
        if not mesh:
            raise ValueError("Participant must provide a mesh")
        return mesh

    @validator('read_data', 'write_data')
    def validate_data_consistency(cls, data, values):
        """Ensure data consistency"""
        if 'provides_mesh' in values and not data:
            raise ValueError(f"Participant must have at least one read or write data for mesh {values['provides_mesh']}")
        return data

class CouplingConfig(BaseModel):
    """Configuration for coupling scheme"""
    type: CouplingSchemeType = CouplingSchemeType.SERIAL_EXPLICIT
    time_window_size: float = Field(gt=0, default=0.025)
    max_time: float = Field(gt=0, default=2.5)
    participants: List[str] = []
    exchanges: List[Dict[str, str]] = []

    @validator('participants')
    def validate_participants(cls, participants):
        """Ensure at least two participants for coupling"""
        if len(participants) < 2:
            raise ValueError("Coupling requires at least two participants")
        return participants

class TopologyConfig(BaseModel):
    """Overall topology configuration for preCICE simulation"""
    name: str = "precice-simulation"
    data: List[DataConfig] = []
    meshes: List[MeshConfig] = []
    participants: List[ParticipantConfig] = []
    coupling: CouplingConfig = CouplingConfig()

    @validator('participants')
    def validate_participant_names(cls, participants):
        """Ensure unique participant names"""
        names = [p.name for p in participants]
        if len(set(names)) != len(names):
            raise ValueError("Participant names must be unique")
        return participants

    @validator('meshes')
    def validate_mesh_names(cls, meshes):
        """Ensure unique mesh names"""
        names = [m.name for m in meshes]
        if len(set(names)) != len(names):
            raise ValueError("Mesh names must be unique")
        return meshes

    def validate_topology(self):
        """
        Comprehensive topology validation
        
        Checks:
        - All participant meshes exist in meshes
        - All data used by participants exist in data
        - Coupling participants match topology participants
        """
        # Validate participant meshes exist
        mesh_names = {mesh.name for mesh in self.meshes}
        for participant in self.participants:
            if participant.provides_mesh not in mesh_names:
                raise ValueError(f"Participant {participant.name} provides non-existent mesh {participant.provides_mesh}")
            
            for recv_mesh in participant.receives_meshes:
                if recv_mesh not in mesh_names:
                    raise ValueError(f"Participant {participant.name} receives non-existent mesh {recv_mesh}")
        
        # Validate data exists
        data_names = {data.name for data in self.data}
        for participant in self.participants:
            for read_data in participant.read_data:
                if read_data not in data_names:
                    raise ValueError(f"Participant {participant.name} reads undefined data {read_data}")
            
            for write_data in participant.write_data:
                if write_data not in data_names:
                    raise ValueError(f"Participant {participant.name} writes undefined data {write_data}")
        
        # Validate coupling participants
        coupling_participant_names = set(self.coupling.participants)
        topology_participant_names = {p.name for p in self.participants}
        
        if not coupling_participant_names.issubset(topology_participant_names):
            raise ValueError("Coupling participants must be a subset of topology participants")
        
        return self
