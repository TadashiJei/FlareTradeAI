"""
Token Registry Module

This module provides a registry of tokens on various networks,
supporting dynamic resolution of token symbols to addresses and
fetching token metadata from on-chain sources.
"""

from typing import Dict, Any, Optional, List
import json
import os
import requests
from web3 import Web3
import structlog

logger = structlog.get_logger(__name__)

# Standard ERC20 ABI for interacting with tokens
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

class TokenRegistry:
    """
    Registry for token metadata and address resolution across networks.
    
    Provides methods to resolve token symbols to addresses and fetch
    token metadata from on-chain and off-chain sources.
    """
    
    def __init__(self, web3: Web3, network: str = "flare"):
        """
        Initialize the token registry.
        
        Args:
            web3: Web3 instance for blockchain interactions
            network: Network name (flare, songbird, coston, etc.)
        """
        self.web3 = web3
        self.network = network
        self.logger = logger.bind(module="token_registry", network=network)
        
        # Token cache to avoid redundant on-chain calls
        self.token_cache = {}
        
        # Load network-specific token registry
        self._load_token_registry()
        
    def _load_token_registry(self):
        """Load the token registry for the current network."""
        # Base tokens common across Flare networks
        self.tokens = {
            # Flare Mainnet tokens
            "flare": {
                "FLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
                "WFLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
                "USDC": "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D",
                "USDT": "0xC26F2AbA4C47996AbCA7Db8d8b18B2820F8C0eaa",
                "DAI": "0x8a4476cF38a7A8Ab7671C7e1633B3F8Cfa95fA29",
                "WETH": "0x8D5E1225981359591A595D86166F7122A6B3B74d",
                "WBTC": "0x735a3cD0D1287C4A8bA3cdB793CEf8e0C1eFB127"
            },
            # Songbird tokens
            "songbird": {
                "SGB": "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED",
                "WSGB": "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED",
                "USDC": "0xDC42728B0eA910349ed3c6e1c9Dc06b5FB591f98",
                "USDT": "0xC1aAE51746c2c1e2F9F8d9a3F75b2deAa5C3B2fE"
            },
            # Coston testnet tokens
            "coston": {
                "CFLR": "0x1659941d425224408c5679eeef606666c7991a8A",
                "WCFLR": "0x1659941d425224408c5679eeef606666c7991a8A",
                "USDC": "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D",
                "USDT": "0xC26F2AbA4C47996AbCA7Db8d8b18B2820F8C0eaa"
            },
            # Coston2 testnet tokens
            "coston2": {
                "C2FLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
                "WC2FLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d", 
                "USDC": "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D",
                "USDT": "0xC26F2AbA4C47996AbCA7Db8d8b18B2820F8C0eaa"
            }
        }
        
        # Try to fetch more tokens from external sources
        self._fetch_external_tokens()
    
    def _fetch_external_tokens(self):
        """Fetch additional tokens from external sources."""
        try:
            # For Flare network, try to get tokens from FlareScan
            if self.network == "flare" and os.environ.get("FLARESCAN_API_KEY"):
                api_key = os.environ.get("FLARESCAN_API_KEY")
                url = f"https://api.flarescan.com/api?module=token&action=tokenlist&apikey={api_key}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1" and data.get("result"):
                        for token in data.get("result"):
                            symbol = token.get("symbol")
                            address = token.get("address")
                            if symbol and address and symbol not in self.tokens.get(self.network, {}):
                                self.tokens.setdefault(self.network, {})[symbol] = address
        except Exception as e:
            self.logger.error("failed_to_fetch_external_tokens", error=str(e))
    
    def resolve_token(self, token: str) -> str:
        """
        Resolve token symbol to address or validate address.
        
        Args:
            token: Token symbol or address
            
        Returns:
            str: Token address (checksum format)
            
        Raises:
            ValueError: If token cannot be resolved
        """
        # Check if it's already an address
        if token.startswith("0x") and len(token) == 42:
            return self.web3.to_checksum_address(token)
        
        # Look up in the registry for the current network
        network_tokens = self.tokens.get(self.network, {})
        if token.upper() in network_tokens:
            return self.web3.to_checksum_address(network_tokens[token.upper()])
        
        # Not found in registry
        raise ValueError(f"Unknown token: {token} on network {self.network}")
    
    def get_token_metadata(self, token_address: str) -> Dict[str, Any]:
        """
        Get token metadata from on-chain or cache.
        
        Args:
            token_address: Token address
            
        Returns:
            Dict[str, Any]: Token metadata (name, symbol, decimals)
            
        Raises:
            ValueError: If metadata cannot be fetched
        """
        token_address = self.web3.to_checksum_address(token_address)
        
        # Check cache first
        if token_address in self.token_cache:
            return self.token_cache[token_address]
        
        # Fetch from chain
        try:
            token_contract = self.web3.eth.contract(address=token_address, abi=ERC20_ABI)
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            
            metadata = {
                "address": token_address,
                "name": name,
                "symbol": symbol,
                "decimals": decimals
            }
            
            # Cache result
            self.token_cache[token_address] = metadata
            return metadata
        except Exception as e:
            self.logger.error("failed_to_get_token_metadata", 
                             token_address=token_address, 
                             error=str(e))
            raise ValueError(f"Failed to get metadata for token {token_address}: {str(e)}")
    
    def get_token_balance(self, wallet_address: str, token_address: str) -> int:
        """
        Get token balance for a wallet.
        
        Args:
            wallet_address: Wallet address
            token_address: Token address
            
        Returns:
            int: Token balance in smallest units
        """
        wallet_address = self.web3.to_checksum_address(wallet_address)
        token_address = self.web3.to_checksum_address(token_address)
        
        try:
            token_contract = self.web3.eth.contract(address=token_address, abi=ERC20_ABI)
            return token_contract.functions.balanceOf(wallet_address).call()
        except Exception as e:
            self.logger.error("failed_to_get_token_balance", 
                             wallet_address=wallet_address,
                             token_address=token_address,
                             error=str(e))
            return 0
    
    def get_all_token_balances(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Get balances for all registered tokens.
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            List[Dict[str, Any]]: List of token balances with metadata
        """
        wallet_address = self.web3.to_checksum_address(wallet_address)
        network_tokens = self.tokens.get(self.network, {})
        
        balances = []
        for symbol, address in network_tokens.items():
            try:
                token_address = self.web3.to_checksum_address(address)
                metadata = self.get_token_metadata(token_address)
                balance = self.get_token_balance(wallet_address, token_address)
                
                if balance > 0:
                    balances.append({
                        "symbol": symbol,
                        "address": token_address,
                        "name": metadata.get("name", symbol),
                        "decimals": metadata.get("decimals", 18),
                        "balance": balance,
                        "balance_formatted": balance / (10 ** metadata.get("decimals", 18))
                    })
            except Exception as e:
                self.logger.error("failed_to_get_token_balance", 
                                 symbol=symbol,
                                 wallet_address=wallet_address,
                                 error=str(e))
                
        return balances
