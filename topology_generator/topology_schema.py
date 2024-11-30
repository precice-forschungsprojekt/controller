from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator

class DataConfig(BaseModel):
    """Configuration for data exchange between participants"""
    name: str
    type: str = "vector"  # Default to vector, can be scalar or vector

class MeshConfig(BaseModel):
    """Configuration for participant meshes"""
    name: str
    dimensions: int = 2  # Default to 2D
    data: List[str] = []

class ParticipantConfig(BaseModel):
    """Configuration for a simulation participant"""
    name: str
    provides_mesh: str
    receives_meshes: List[str] = []
    read_data: List[str] = []
    write_data: List[str] = []
    mapping_type: str = "rbf"  # Default to RBF mapping
    mapping_constraint: str = "consistent"

class CouplingConfig(BaseModel):
    """Configuration for coupling scheme"""
    type: str = "serial-explicit"
    time_window_size: float = 0.025
    max_time: float = 2.5
    participants: List[str] = []
    exchanges: List[Dict[str, str]] = []

class TopologyConfig(BaseModel):
    """Overall topology configuration for preCICE simulation"""
    name: str = "precice-simulation"
    data: List[DataConfig] = []
    meshes: List[MeshConfig] = []
    participants: List[ParticipantConfig] = []
    coupling: CouplingConfig = CouplingConfig()

    @validator('participants')
    def validate_participants(cls, participants):
        """Validate that participants are consistent"""
        if not participants:
            raise ValueError("At least one participant is required")
        return participants

    @validator('coupling')
    def validate_coupling(cls, coupling, values):
        """Validate coupling configuration"""
        if 'participants' in values:
            coupling.participants = [p.name for p in values['participants']]
        return coupling
