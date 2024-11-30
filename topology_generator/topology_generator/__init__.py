"""
Topology Configuration Generator for preCICE Simulations

This package provides tools for generating and validating preCICE simulation configurations.
"""

from .config_generator import PreciceConfigGenerator
from .xml_to_topology import PreciceXMLToTopologyConverter

__all__ = [
    'PreciceConfigGenerator',
    'PreciceXMLToTopologyConverter'
]

__version__ = '0.1.0'
