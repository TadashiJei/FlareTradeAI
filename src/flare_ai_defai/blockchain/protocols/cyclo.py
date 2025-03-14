"""
Cyclo Protocol Integration Module

This module implements the integration with Cyclo, a yield farming platform
on the Flare Network. It provides functionality for staking, unstaking, and
claiming rewards.
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

# ABI for Cyclo Staking contract
STAKING_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "stake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "unstake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
        ],
        "name": "claimRewards",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getStakingPools",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "poolId", "type": "uint256"}],
        "name": "getPoolInfo",
        "outputs": [
            {"internalType": "address", "name": "stakingToken", "type": "address"},
            {"internalType": "address", "name": "rewardToken", "type": "address"},
            {"internalType": "uint256", "name": "lockDuration", "type": "uint256"},
            {"internalType": "uint256", "name": "apr", "type": "uint256"},
            {"internalType": "uint256", "name": "totalStaked", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "poolId", "type": "uint256"},
        ],
        "name": "getUserStakeInfo",
        "outputs": [
            {"internalType": "uint256", "name": "stakedAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "stakeTimestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "poolId", "type": "uint256"},
        ],
        "name": "pendingRewards",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Cyclo contract addresses by network
CONTRACT_ADDRESSES = {
    "flare": {
        "staking": "0x1234567890123456789012345678901234567890",  # Placeholder
    },
    "songbird": {
        "staking": "0x0987654321098765432109876543210987654321",  # Placeholder
    },
}


class Cyclo(BaseProtocol):
    """
    Cyclo protocol integration for the Flare Network.
    
    This class provides methods for interacting with the Cyclo yield farming
    platform, including staking, unstaking, and claiming rewards.
    """

    def __init__(self, web3: Web3, address: Optional[ChecksumAddress] = None, network: str = "flare"):
        """
        Initialize the Cyclo protocol integration.
        
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
        self.staking_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contracts["staking"]),
            abi=STAKING_ABI,
        )
        self.logger = logger.bind(protocol="cyclo", network=network)

    def get_info(self) -> ProtocolInfo:
        """
        Get information about the Cyclo protocol.
        
        Returns:
            ProtocolInfo: Protocol information
        """
        return ProtocolInfo(
            name="Cyclo",
            type=ProtocolType.YIELD,
            description="Yield farming platform on the Flare Network",
            website="https://cyclo.finance",  # Placeholder
            contracts=self.contracts,
        )

    def get_supported_tokens(self) -> List[TokenInfo]:
        """
        Get list of tokens supported by Cyclo.
        
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

    def prepare_stake_transaction(self, token_address: str, amount: int) -> TxParams:
        """
        Prepare a transaction for staking tokens.
        
        Args:
            token_address (str): Address of the token to stake
            amount (int): Amount to stake
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["staking"]),
            "data": self.staking_contract.encodeABI(
                fn_name="stake",
                args=[token_address, amount],
            ),
            "gas": 200000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def prepare_unstake_transaction(self, token_address: str, amount: int) -> TxParams:
        """
        Prepare a transaction for unstaking tokens.
        
        Args:
            token_address (str): Address of the token to unstake
            amount (int): Amount to unstake
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["staking"]),
            "data": self.staking_contract.encodeABI(
                fn_name="unstake",
                args=[token_address, amount],
            ),
            "gas": 200000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def prepare_claim_rewards_transaction(self, token_address: str) -> TxParams:
        """
        Prepare a transaction for claiming rewards.
        
        Args:
            token_address (str): Address of the token to claim rewards for
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["staking"]),
            "data": self.staking_contract.encodeABI(
                fn_name="claimRewards",
                args=[token_address],
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
                - action: Type of action (stake, unstake, claim_rewards)
                - token: Address of the token
                - amount: Amount to stake/unstake
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        action = kwargs.get("action")
        token_address = kwargs.get("token")
        
        if action == "stake":
            amount = kwargs.get("amount")
            return self.prepare_stake_transaction(token_address, amount)
        elif action == "unstake":
            amount = kwargs.get("amount")
            return self.prepare_unstake_transaction(token_address, amount)
        elif action == "claim_rewards":
            return self.prepare_claim_rewards_transaction(token_address)
        
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

    def get_staking_positions(self) -> List[Dict[str, Any]]:
        """
        Get user's staking positions.
        
        Returns:
            List[Dict[str, Any]]: List of staking positions
        """
        positions = []
        try:
            # Get the list of staking pools
            pools = self.staking_contract.functions.getStakingPools().call()
            
            for pool_id in pools:
                # Get pool details
                pool_info = self.staking_contract.functions.getPoolInfo(pool_id).call()
                
                # Get user's position in this pool
                user_position = self.staking_contract.functions.getUserStakeInfo(
                    self.address, 
                    pool_id
                ).call()
                
                # Calculate rewards
                pending_rewards = self.staking_contract.functions.pendingRewards(
                    self.address, 
                    pool_id
                ).call()
                
                # If user has a non-zero position, add it to the list
                if user_position[0] > 0:  # staked amount > 0
                    positions.append({
                        "pool_id": pool_id,
                        "token_address": pool_info[0],  # staking token address
                        "staked_amount": user_position[0],
                        "staked_amount_formatted": self.web3.from_wei(user_position[0], 'ether'),
                        "reward_token_address": pool_info[1],  # reward token address
                        "pending_rewards": pending_rewards,
                        "pending_rewards_formatted": self.web3.from_wei(pending_rewards, 'ether'),
                        "stake_timestamp": user_position[1],
                        "lock_duration": pool_info[2],
                        "apr": pool_info[3] / 10000,  # Convert basis points to percentage
                        "pool_total_staked": pool_info[4],
                        "can_unstake": int(time.time()) >= (user_position[1] + pool_info[2])
                    })
            
            # Sort positions by staked amount (descending)
            positions.sort(key=lambda x: x["staked_amount"], reverse=True)
            
            self.logger.info(f"Retrieved {len(positions)} staking positions", 
                            wallet=self.address)
            
        except Exception as e:
            self.logger.error("Failed to retrieve staking positions", 
                             error=str(e), 
                             wallet=self.address)
                             
        return positions
