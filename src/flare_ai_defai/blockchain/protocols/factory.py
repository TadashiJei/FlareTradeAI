"""
Protocol Factory Module

This module provides a factory class for creating and managing protocol instances.
It allows for easy access to all supported DeFi protocols in the Flare ecosystem.
"""

from typing import Dict, Type

from web3 import Web3

from ...blockchain.protocols.base import BaseProtocol
from ...blockchain.protocols.cyclo import Cyclo
from ...blockchain.protocols.kinetic import Kinetic
from ...blockchain.protocols.raindex import RainDEX
from ...blockchain.protocols.sparkdex import SparkDEX


class ProtocolFactory:
    """
    Factory class for creating and managing protocol instances.
    
    This class provides a centralized way to access all supported DeFi protocols
    in the Flare ecosystem.
    """

    PROTOCOL_MAP: Dict[str, Type[BaseProtocol]] = {
        "sparkdex": SparkDEX,
        "kinetic": Kinetic,
        "cyclo": Cyclo,
        "raindex": RainDEX,
    }

    def __init__(self, web3: Web3, address: str = None, network: str = "flare"):
        """
        Initialize the protocol factory.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
            address (str, optional): User's address for transactions
            network (str): Network to use (flare or songbird)
        """
        self.web3 = web3
        self.address = address
        self.network = network

    def get_protocol(self, protocol_name: str) -> BaseProtocol:
        """
        Get an instance of a protocol.
        
        Args:
            protocol_name (str): Name of the protocol to get
            
        Returns:
            BaseProtocol: Instance of the requested protocol
            
        Raises:
            ValueError: If protocol is not supported
        """
        protocol_class = self.PROTOCOL_MAP.get(protocol_name.lower())
        if not protocol_class:
            msg = f"Protocol '{protocol_name}' not supported"
            raise ValueError(msg)
        
        return protocol_class(self.web3, self.address, self.network)

    def get_all_protocols(self) -> Dict[str, BaseProtocol]:
        """
        Get instances of all supported protocols.
        
        Returns:
            Dict[str, BaseProtocol]: Dictionary of protocol instances
        """
        return {
            name: protocol_class(self.web3, self.address, self.network)
            for name, protocol_class in self.PROTOCOL_MAP.items()
        }

    def get_supported_protocols(self) -> Dict[str, str]:
        """
        Get information about supported protocols.
        
        Returns:
            Dict[str, str]: Dictionary mapping protocol names to descriptions
        """
        return {
            name: protocol_class.__doc__.strip() if protocol_class.__doc__ else ""
            for name, protocol_class in self.PROTOCOL_MAP.items()
        }
