"""
Base Protocol Interface Module

This module defines the base interface for all DeFi protocol integrations.
It provides a standard contract that all protocol implementations must follow
to ensure consistent interaction patterns across the application.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams

logger = structlog.get_logger(__name__)


class ProtocolType(Enum):
    """Enum representing different types of DeFi protocols."""
    DEX = "dex"  # Decentralized Exchange
    LENDING = "lending"  # Lending/Borrowing Platform
    YIELD = "yield"  # Yield Farming
    STAKING = "staking"  # Staking Platform
    BRIDGE = "bridge"  # Cross-chain Bridge


@dataclass
class ProtocolInfo:
    """
    Information about a DeFi protocol.
    
    Attributes:
        name (str): Name of the protocol
        type (ProtocolType): Type of the protocol
        description (str): Brief description of the protocol
        website (str): Official website URL
        contracts (Dict[str, str]): Dictionary of contract addresses by network
    """
    name: str
    type: ProtocolType
    description: str
    website: str
    contracts: Dict[str, str]


@dataclass
class TokenInfo:
    """
    Information about a token.
    
    Attributes:
        symbol (str): Token symbol
        name (str): Token name
        address (str): Token contract address
        decimals (int): Number of decimals
        logo_url (Optional[str]): URL to token logo
    """
    symbol: str
    name: str
    address: str
    decimals: int
    logo_url: Optional[str] = None


@dataclass
class OperationResult:
    """
    Result of a DeFi operation.
    
    Attributes:
        success (bool): Whether the operation was successful
        tx_hash (Optional[str]): Transaction hash if applicable
        data (Dict[str, Any]): Additional data related to the operation
        error (Optional[str]): Error message if operation failed
    """
    success: bool
    tx_hash: Optional[str] = None
    data: Dict[str, Any] = None
    error: Optional[str] = None


class BaseProtocol(ABC):
    """
    Base class for all DeFi protocol integrations.
    
    This abstract class defines the interface that all protocol
    implementations must follow to ensure consistent interaction
    patterns across the application.
    """
    
    def __init__(self, web3: Web3, address: Optional[ChecksumAddress] = None):
        """
        Initialize the protocol with Web3 instance and optional address.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
            address (Optional[ChecksumAddress]): User's address for transactions
        """
        self.web3 = web3
        self.address = address
        self.logger = logger.bind(protocol=self.get_info().name)
        
    @abstractmethod
    def get_info(self) -> ProtocolInfo:
        """
        Get information about the protocol.
        
        Returns:
            ProtocolInfo: Protocol information
        """
        pass
    
    @abstractmethod
    def get_supported_tokens(self) -> List[TokenInfo]:
        """
        Get list of tokens supported by the protocol.
        
        Returns:
            List[TokenInfo]: List of supported tokens
        """
        pass
    
    @abstractmethod
    def get_token_balance(self, token_address: str) -> float:
        """
        Get balance of a specific token for the current address.
        
        Args:
            token_address (str): Address of the token contract
            
        Returns:
            float: Token balance
            
        Raises:
            ValueError: If address is not set or token is not supported
        """
        pass
    
    @abstractmethod
    def prepare_transaction(self, **kwargs) -> TxParams:
        """
        Prepare a transaction for the protocol.
        
        Args:
            **kwargs: Protocol-specific parameters
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        pass
    
    @abstractmethod
    def estimate_gas(self, tx_params: TxParams) -> int:
        """
        Estimate gas for a transaction.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            int: Estimated gas
        """
        pass
    
    @abstractmethod
    def simulate_transaction(self, tx_params: TxParams) -> Dict[str, Any]:
        """
        Simulate a transaction to check for potential issues.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            Dict[str, Any]: Simulation results
        """
        pass
    
    def set_address(self, address: ChecksumAddress) -> None:
        """
        Set the address for transactions.
        
        Args:
            address (ChecksumAddress): User's address
        """
        self.address = address
        self.logger.debug("set_address", address=address)
    
    def validate_address(self) -> bool:
        """
        Validate that an address is set.
        
        Returns:
            bool: True if address is set
            
        Raises:
            ValueError: If address is not set
        """
        if not self.address:
            msg = "Address not set"
            raise ValueError(msg)
        return True
