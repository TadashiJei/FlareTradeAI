"""
Kinetic Protocol Integration Module

This module implements the integration with Kinetic, a lending/borrowing platform
on the Flare Network. It provides functionality for depositing, withdrawing,
borrowing, and repaying assets.
"""

from typing import Any, Dict, List, Optional

import structlog
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from ...blockchain.protocols.base import (
    BaseProtocol,
    OperationResult,
    ProtocolInfo,
    ProtocolType,
    TokenInfo,
)

logger = structlog.get_logger(__name__)

# ABI for Kinetic Lending Pool contract
LENDING_POOL_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "borrow",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "repay",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
        ],
        "name": "getUserAccountData",
        "outputs": [
            {"internalType": "uint256", "name": "totalCollateralETH", "type": "uint256"},
            {"internalType": "uint256", "name": "totalDebtETH", "type": "uint256"},
            {"internalType": "uint256", "name": "availableBorrowsETH", "type": "uint256"},
            {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
            {"internalType": "uint256", "name": "ltv", "type": "uint256"},
            {"internalType": "uint256", "name": "healthFactor", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# Kinetic contract addresses by network
CONTRACT_ADDRESSES = {
    "flare": {
        "lending_pool": "0x1234567890123456789012345678901234567890",  # Placeholder
    },
    "songbird": {
        "lending_pool": "0x0987654321098765432109876543210987654321",  # Placeholder
    },
}


class Kinetic(BaseProtocol):
    """
    Kinetic protocol integration for the Flare Network.
    
    This class provides methods for interacting with the Kinetic lending/borrowing
    platform, including depositing, withdrawing, borrowing, and repaying assets.
    """

    def __init__(self, web3: Web3, address: Optional[ChecksumAddress] = None, network: str = "flare"):
        """
        Initialize the Kinetic protocol integration.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
            address (Optional[ChecksumAddress]): User's address for transactions
            network (str): Network to use (flare or songbird)
        
        Raises:
            ValueError: If network is not supported
        """
        super().__init__(web3, address)
        
        if network not in CONTRACT_ADDRESSES:
            msg = f"Network {network} not supported"
            raise ValueError(msg)
            
        self.network = network
        self.contracts = CONTRACT_ADDRESSES[network]
        self.lending_pool_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contracts["lending_pool"]),
            abi=LENDING_POOL_ABI,
        )
        self.logger = logger.bind(protocol="kinetic", network=network)

    def get_info(self) -> ProtocolInfo:
        """
        Get information about the Kinetic protocol.
        
        Returns:
            ProtocolInfo: Protocol information
        """
        return ProtocolInfo(
            name="Kinetic",
            type=ProtocolType.LENDING,
            description="Lending and borrowing platform on the Flare Network",
            website="https://kinetic.finance",  # Placeholder
            contracts=self.contracts,
        )

    def get_supported_tokens(self) -> List[TokenInfo]:
        """
        Get list of tokens supported by Kinetic.
        
        Returns:
            List[TokenInfo]: List of supported tokens
        """
        return [
            TokenInfo(
                symbol="FLR",
                name="Flare",
                address="0x0000000000000000000000000000000000000000",  # Native token
                decimals=18,
                logo_url="https://assets.coingecko.com/coins/images/28624/standard/FLR-icon-darkbg.png",
            ),
            TokenInfo(
                symbol="USDC",
                name="USD Coin",
                address="0x1234567890123456789012345678901234567891",  # Placeholder
                decimals=6,
                logo_url="https://assets.coingecko.com/coins/images/6319/standard/usdc.png",
            ),
        ]

    def prepare_deposit_transaction(self, asset_address: str, amount: int) -> TxParams:
        """
        Prepare a transaction for depositing assets.
        
        Args:
            asset_address (str): Address of the asset to deposit
            amount (int): Amount to deposit
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["lending_pool"]),
            "data": self.lending_pool_contract.encodeABI(
                fn_name="deposit",
                args=[asset_address, amount],
            ),
            "gas": 200000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def prepare_withdraw_transaction(self, asset_address: str, amount: int) -> TxParams:
        """
        Prepare a transaction for withdrawing assets.
        
        Args:
            asset_address (str): Address of the asset to withdraw
            amount (int): Amount to withdraw
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["lending_pool"]),
            "data": self.lending_pool_contract.encodeABI(
                fn_name="withdraw",
                args=[asset_address, amount],
            ),
            "gas": 200000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def prepare_borrow_transaction(self, asset_address: str, amount: int) -> TxParams:
        """
        Prepare a transaction for borrowing assets.
        
        Args:
            asset_address (str): Address of the asset to borrow
            amount (int): Amount to borrow
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["lending_pool"]),
            "data": self.lending_pool_contract.encodeABI(
                fn_name="borrow",
                args=[asset_address, amount],
            ),
            "gas": 200000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def prepare_repay_transaction(self, asset_address: str, amount: int) -> TxParams:
        """
        Prepare a transaction for repaying borrowed assets.
        
        Args:
            asset_address (str): Address of the asset to repay
            amount (int): Amount to repay
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["lending_pool"]),
            "data": self.lending_pool_contract.encodeABI(
                fn_name="repay",
                args=[asset_address, amount],
            ),
            "gas": 200000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def prepare_transaction(self, **kwargs) -> TxParams:
        """
        Prepare a transaction for the protocol.
        
        Args:
            **kwargs: Protocol-specific parameters including:
                - action: Type of action (deposit, withdraw, borrow, repay)
                - asset: Address of the asset
                - amount: Amount to deposit/withdraw/borrow/repay
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        action = kwargs.get("action")
        asset_address = kwargs.get("asset")
        amount = kwargs.get("amount")
        
        if action == "deposit":
            return self.prepare_deposit_transaction(asset_address, amount)
        elif action == "withdraw":
            return self.prepare_withdraw_transaction(asset_address, amount)
        elif action == "borrow":
            return self.prepare_borrow_transaction(asset_address, amount)
        elif action == "repay":
            return self.prepare_repay_transaction(asset_address, amount)
        
        msg = f"Unsupported action: {action}"
        raise ValueError(msg)

    def estimate_gas(self, tx_params: TxParams) -> int:
        """
        Estimate gas for a transaction.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            int: Estimated gas
        """
        return self.web3.eth.estimate_gas(tx_params)

    def simulate_transaction(self, tx_params: TxParams) -> Dict[str, Any]:
        """
        Simulate a transaction to check for potential issues.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            Dict[str, Any]: Simulation results
        """
        try:
            gas_estimate = self.estimate_gas(tx_params)
            return {
                "success": True,
                "gas_estimate": gas_estimate,
                "warnings": [],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "warnings": ["Transaction is likely to fail"],
            }

    def get_user_account_data(self) -> Dict[str, Any]:
        """
        Get user's account data including health factor and collateral.
        
        Returns:
            Dict[str, Any]: User account data
        """
        try:
            # Query the lending pool for user account data
            account_data = self.lending_pool_contract.functions.getUserAccountData(self.address).call()
            
            # Parse the returned data
            # Structure based on Aave/Kinetic implementation
            total_collateral_eth = account_data[0]
            total_debt_eth = account_data[1]
            available_borrow_eth = account_data[2]
            current_liquidation_threshold = account_data[3]
            ltv = account_data[4]
            health_factor = account_data[5]
            
            # Convert wei values to ETH
            total_collateral = self.web3.from_wei(total_collateral_eth, 'ether')
            total_debt = self.web3.from_wei(total_debt_eth, 'ether')
            available_borrow = self.web3.from_wei(available_borrow_eth, 'ether')
            
            # Convert percentages from basis points to percentage
            liquidation_threshold_pct = current_liquidation_threshold / 100
            ltv_pct = ltv / 100
            
            # Health factor is returned as ray units (1e27)
            # Convert to a human-readable number
            health_factor_readable = health_factor / 1e18
            
            self.logger.info("Retrieved user account data", 
                           wallet=self.address,
                           health_factor=health_factor_readable,
                           total_collateral=total_collateral,
                           total_debt=total_debt)
            
            return {
                "total_collateral_eth": float(total_collateral),
                "total_debt_eth": float(total_debt),
                "available_borrow_eth": float(available_borrow),
                "current_liquidation_threshold": float(liquidation_threshold_pct),
                "ltv": float(ltv_pct),
                "health_factor": float(health_factor_readable),
                "collateral_ratio": float(total_collateral) / float(total_debt) if float(total_debt) > 0 else float('inf'),
            }
            
        except Exception as e:
            self.logger.error("Failed to get user account data", 
                             error=str(e), 
                             wallet=self.address)
            
            # Return default values in case of error
            return {
                "total_collateral_eth": 0.0,
                "total_debt_eth": 0.0,
                "available_borrow_eth": 0.0,
                "current_liquidation_threshold": 0.0,
                "ltv": 0.0,
                "health_factor": 0.0,
                "collateral_ratio": float('inf'),
                "error": str(e)
            }
