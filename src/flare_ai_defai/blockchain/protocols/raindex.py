"""
RainDEX Protocol Integration Module

This module implements the integration with RainDEX, a decentralized exchange
on the Flare Network. It provides functionality for token swaps, liquidity provision,
and other DEX operations.
"""

from typing import Any, Dict, List, Optional, Tuple

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

# ABI for RainDEX Router contract
ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForETH",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
        ],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint256", "name": "reserveA", "type": "uint256"},
            {"internalType": "uint256", "name": "reserveB", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ABI for ERC20 token contract
ERC20_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ABI for Uniswap V2 Pair contract
PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# FTSO Provider ABI
FTSO_PROVIDER_ABI = [
    {
        "inputs": [{"name": "symbol", "type": "string"}],
        "name": "getFtsoIndex",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "ftsoIndex", "type": "uint256"}],
        "name": "getCurrentPriceWithDecimals",
        "outputs": [
            {"name": "_price", "type": "uint256"},
            {"name": "_timestamp", "type": "uint256"},
            {"name": "_decimals", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "assetHash", "type": "bytes32"}],
        "name": "getCurrentPriceFromAssetByHash",
        "outputs": [
            {"name": "_price", "type": "uint256"},
            {"name": "_timestamp", "type": "uint256"},
            {"name": "_decimals", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

# FTSO Registry ABI
FTSO_REGISTRY_ABI = [
    {
        "inputs": [],
        "name": "getCurrentPriceProviderAddress",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# RainDEX contract addresses by network
CONTRACT_ADDRESSES = {
    "flare": {
        "router": "0x1234567890123456789012345678901234567890",  # Placeholder
        "factory": "0x0987654321098765432109876543210987654321",  # Placeholder
        "ftso_registry": "0xDf37E9878D52C55D6C708DaE1A0D5A9347085F92",  # FTSO Registry address on Flare
    },
    "songbird": {
        "router": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # Placeholder
        "factory": "0xfedcbafedcbafedcbafedcbafedcbafedcbafedc",  # Placeholder
        "ftso_registry": "0x1D21Ec4fd89679A2018E34D1edD3e01d42aD1d73",  # FTSO Registry address on Songbird
    },
}

# WETH address
WETH_ADDRESS = "0x0000000000000000000000000000000000000000"  # Native token


class RainDEX(BaseProtocol):
    """
    RainDEX protocol integration for the Flare Network.
    
    This class provides methods for interacting with the RainDEX decentralized
    exchange, including token swaps, liquidity provision, and price quotes.
    """

    def __init__(
        self,
        web3: Web3,
        address: Optional[ChecksumAddress] = None,
        network: str = "flare",
        price_api_url: Optional[str] = None,
        price_api_key: Optional[str] = None
    ):
        """
        Initialize the RainDEX protocol integration.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
            address (Optional[ChecksumAddress]): User's address for transactions
            network (str): Network to use (flare or songbird)
            price_api_url (Optional[str]): URL for external price API
            price_api_key (Optional[str]): API key for external price API
        
        Raises:
            ValueError: If network is not supported
        """
        super().__init__(web3, address)
        
        if network not in CONTRACT_ADDRESSES:
            msg = f"Network {network} not supported"
            raise ValueError(msg)
            
        self.network = network
        self.contracts = CONTRACT_ADDRESSES[network]
        self.price_api_url = price_api_url
        self.price_api_key = price_api_key
        
        # Initialize cache for price lookups
        self.cache = {}
        
        # Initialize contracts
        self.router_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contracts["router"]),
            abi=ROUTER_ABI,
        )
        self.factory_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contracts["factory"]),
            abi=PAIR_ABI,
        )
        
        # Initialize FTSO Registry contract
        self.ftso_registry_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contracts["ftso_registry"]),
            abi=FTSO_REGISTRY_ABI,
        )
        
        # Initialize logger
        self.logger = logger.bind(
            protocol="raindex",
            network=network,
            address=address if address else None
        )
        
        # Import time module
        import time
        self.time = time

    def get_info(self) -> ProtocolInfo:
        """
        Get information about the RainDEX protocol.
        
        Returns:
            ProtocolInfo: Protocol information
        """
        return ProtocolInfo(
            name="RainDEX",
            type=ProtocolType.DEX,
            description="Decentralized exchange on the Flare Network",
            website="https://raindex.io",  # Placeholder
            contracts=self.contracts,
        )

    def get_supported_tokens(self) -> List[TokenInfo]:
        """
        Get list of tokens supported by RainDEX.
        
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

    def prepare_swap_transaction(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: int,
        min_amount_out: int,
        deadline: int,
    ) -> TxParams:
        """
        Prepare a transaction for swapping tokens.
        
        Args:
            token_in_address (str): Address of the input token
            token_out_address (str): Address of the output token
            amount_in (int): Amount of input token
            min_amount_out (int): Minimum amount of output token
            deadline (int): Transaction deadline timestamp
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        path = [
            self.web3.to_checksum_address(token_in_address),
            self.web3.to_checksum_address(token_out_address),
        ]
        
        # Native token (FLR) to token
        if token_in_address == "0x0000000000000000000000000000000000000000":
            return {
                "from": self.address,
                "to": self.web3.to_checksum_address(self.contracts["router"]),
                "value": amount_in,
                "data": self.router_contract.encodeABI(
                    fn_name="swapExactETHForTokens",
                    args=[min_amount_out, path, self.address, deadline],
                ),
                "gas": 200000,  # Estimated gas
                "maxFeePerGas": self.web3.eth.gas_price,
                "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
                "nonce": self.web3.eth.get_transaction_count(self.address),
                "chainId": self.web3.eth.chain_id,
                "type": 2,
            }
        
        # Token to native token (FLR)
        if token_out_address == "0x0000000000000000000000000000000000000000":
            return {
                "from": self.address,
                "to": self.web3.to_checksum_address(self.contracts["router"]),
                "data": self.router_contract.encodeABI(
                    fn_name="swapExactTokensForETH",
                    args=[amount_in, min_amount_out, path, self.address, deadline],
                ),
                "gas": 200000,  # Estimated gas
                "maxFeePerGas": self.web3.eth.gas_price,
                "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
                "nonce": self.web3.eth.get_transaction_count(self.address),
                "chainId": self.web3.eth.chain_id,
                "type": 2,
            }
        
        # Token to token
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(self.contracts["router"]),
            "data": self.router_contract.encodeABI(
                fn_name="swapExactTokensForTokens",
                args=[amount_in, min_amount_out, path, self.address, deadline],
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
                - action: Type of action (swap, add_liquidity, remove_liquidity)
                - token_in: Address of input token
                - token_out: Address of output token
                - amount_in: Amount of input token
                - min_amount_out: Minimum amount of output token
                - deadline: Transaction deadline timestamp
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        action = kwargs.get("action")
        
        if action == "swap":
            return self.prepare_swap_transaction(
                token_in_address=kwargs.get("token_in"),
                token_out_address=kwargs.get("token_out"),
                amount_in=kwargs.get("amount_in"),
                min_amount_out=kwargs.get("min_amount_out"),
                deadline=kwargs.get("deadline"),
            )
        
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

    def get_swap_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: int,
    ) -> Tuple[int, float]:
        """
        Get a quote for swapping tokens.
        
        Args:
            token_in_address (str): Address of the input token
            token_out_address (str): Address of the output token
            amount_in (int): Amount of input token
            
        Returns:
            Tuple[int, float]: (Expected output amount, price impact percentage)
        """
        try:
            # Normalize addresses
            token_in_address = self.web3.to_checksum_address(token_in_address)
            token_out_address = self.web3.to_checksum_address(token_out_address)
            
            # Check if we're dealing with the native token (ETH/FLR)
            is_input_native = token_in_address.lower() == WETH_ADDRESS.lower()
            is_output_native = token_out_address.lower() == WETH_ADDRESS.lower()
            
            # Create token path for the swap
            path = [token_in_address, token_out_address]
            
            # If tokens aren't directly paired, use WETH as an intermediate
            if not self._pair_exists(token_in_address, token_out_address):
                path = [token_in_address, WETH_ADDRESS, token_out_address]
            
            # Get the expected output amount from the router
            try:
                # Use getAmountsOut to get the expected output amount
                amounts = self.router_contract.functions.getAmountsOut(amount_in, path).call()
                amount_out = amounts[-1]  # Last amount in the array is the output amount
                
                # Calculate the current market price
                token_in_decimals = self._get_token_decimals(token_in_address)
                token_out_decimals = self._get_token_decimals(token_out_address)
                
                # Calculate the market price for token_in/token_out
                market_price = self._get_market_price(token_in_address, token_out_address)
                
                # Calculate expected amount based on market price
                expected_amount_out = self._calculate_expected_output(
                    amount_in, 
                    market_price,
                    token_in_decimals,
                    token_out_decimals
                )
                
                # Calculate price impact
                price_impact = 0.0
                if expected_amount_out > 0:
                    price_impact = ((expected_amount_out - amount_out) / expected_amount_out) * 100
                    # Make sure price impact is positive
                    price_impact = max(0, price_impact)
                
                self.logger.info(
                    "Swap quote obtained",
                    token_in=token_in_address,
                    token_out=token_out_address,
                    amount_in=amount_in,
                    amount_out=amount_out,
                    price_impact=price_impact,
                )
                
                return (amount_out, price_impact)
                
            except Exception as e:
                # If router call fails, fall back to pool reserves calculation
                self.logger.warning(
                    "Router getAmountsOut failed, falling back to pool calculation",
                    error=str(e),
                )
                return self._get_swap_quote_from_reserves(token_in_address, token_out_address, amount_in)
                
        except Exception as e:
            self.logger.error(
                "Failed to get swap quote",
                error=str(e),
                token_in=token_in_address,
                token_out=token_out_address,
                amount_in=amount_in,
            )
            # Return fallback values in case of error
            return (0, 100.0)
    
    def _pair_exists(self, token_a: str, token_b: str) -> bool:
        """Check if a trading pair exists."""
        try:
            # Get the pair address from the factory
            pair_address = self.factory_contract.functions.getPair(token_a, token_b).call()
            # If pair address is zero address, pair doesn't exist
            return pair_address != "0x0000000000000000000000000000000000000000"
        except Exception:
            return False
        
    def _get_token_decimals(self, token_address: str) -> int:
        """Get token decimals."""
        try:
            # If token is the native token, return 18 decimals
            if token_address.lower() == WETH_ADDRESS.lower():
                return 18
                
            # Otherwise, query the token contract
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=ERC20_ABI
            )
            return token_contract.functions.decimals().call()
        except Exception:
            # Default to 18 decimals if we can't determine
            return 18
            
    def _get_market_price(self, token_in: str, token_out: str) -> float:
        """Get the current market price between two tokens."""
        try:
            # Try to get price from FTSO price feed if available
            ftso_price_in = self._get_ftso_price(token_in)
            ftso_price_out = self._get_ftso_price(token_out)
            
            if ftso_price_in and ftso_price_out:
                return ftso_price_in / ftso_price_out
                
            # Fall back to DEX price if FTSO not available
            return self._get_dex_price(token_in, token_out)
        except Exception:
            # If all else fails, use a 1:1 ratio
            return 1.0
            
    def _get_ftso_price(self, token_address: str) -> Optional[float]:
        """
        Get token price from FTSO price feed.
        
        Args:
            token_address (str): The token address to get price for
            
        Returns:
            Optional[float]: The token price in USD, or None if not available
        """
        try:
            # Normalize the address
            token_address = self.web3.to_checksum_address(token_address)
            
            # Map common token addresses to their FTSO symbols
            # FTSO uses symbols like "FLR", "BTC", "XRP", etc.
            ftso_symbol_map = {
                WETH_ADDRESS.lower(): "FLR",  # WETH on Flare is actually WFLR
                "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D".lower(): "USDC",
                "0xC67DCB4307C0856AC800a99A4CA8e2bd20749E21".lower(): "USDT",
                "0x8A6fa2E13728d68D577eA24cBF7b5B3C3f279B1C".lower(): "ETH",
                "0x1aAF048D8cAf1dF75ad43c2e90B51A198EcAB05D".lower(): "BTC",
                "0xbF6bfE5d6B86308c9eb59194B9Cd08f3B3C4659B".lower(): "SGB",
            }
            
            # If the token isn't in our map, try to get the symbol from the contract
            ftso_symbol = ftso_symbol_map.get(token_address.lower())
            if not ftso_symbol:
                try:
                    token_contract = self.web3.eth.contract(
                        address=token_address,
                        abi=ERC20_ABI
                    )
                    # Try to get the symbol from the token contract
                    symbol = token_contract.functions.symbol().call()
                    if symbol:
                        ftso_symbol = symbol
                except Exception as e:
                    self.logger.warning(
                        "Failed to get token symbol",
                        token_address=token_address,
                        error=str(e)
                    )
                    return None
            
            # Cache price results for 5 minutes to avoid excessive calls
            cache_key = f"ftso_price_{ftso_symbol}"
            cached_price = self.cache.get(cache_key)
            if cached_price and cached_price["timestamp"] > self.time.time() - 300:  # 5 minutes cache
                return cached_price["price"]
            
            # Connect to FTSO Price Provider contract
            ftso_provider_address = self.ftso_registry_contract.functions.getCurrentPriceProviderAddress().call()
            ftso_provider_contract = self.web3.eth.contract(
                address=ftso_provider_address,
                abi=FTSO_PROVIDER_ABI
            )
            
            # Get the price from FTSO
            try:
                # For most tokens we can use the symbol directly
                symbol_index = ftso_provider_contract.functions.getFtsoIndex(ftso_symbol).call()
                price_data = ftso_provider_contract.functions.getCurrentPriceWithDecimals(symbol_index).call()
                
                # price_data contains: price, timestamp, decimals
                price = price_data[0] / (10 ** price_data[2])
                
                # Cache the result
                self.cache[cache_key] = {
                    "price": price,
                    "timestamp": self.time.time()
                }
                
                self.logger.info(
                    "Got price from FTSO",
                    token=ftso_symbol,
                    price=price
                )
                
                return price
            except Exception as e:
                self.logger.warning(
                    "Failed to get price from FTSO using symbol",
                    symbol=ftso_symbol,
                    error=str(e)
                )
                
                # Try as a direct asset hash if symbol lookup fails
                try:
                    # Convert token address to bytes32 format for FTSO
                    token_bytes = bytes.fromhex(token_address[2:].lower().zfill(64))
                    price_data = ftso_provider_contract.functions.getCurrentPriceFromAssetByHash(token_bytes).call()
                    
                    price = price_data[0] / (10 ** price_data[2])
                    
                    # Cache the result
                    self.cache[cache_key] = {
                        "price": price,
                        "timestamp": self.time.time()
                    }
                    
                    return price
                except Exception as nested_e:
                    self.logger.error(
                        "Failed to get price from FTSO using asset hash",
                        token_address=token_address,
                        error=str(nested_e)
                    )
            
            # Fall back to price oracle or price feed API
            return self._get_fallback_price(token_address)
            
        except Exception as e:
            self.logger.error(
                "Error in FTSO price lookup",
                token_address=token_address,
                error=str(e)
            )
            return None
    
    def _get_fallback_price(self, token_address: str) -> Optional[float]:
        """Get token price from fallback price sources."""
        try:
            # Try Chainlink price feed if available
            chainlink_price = self._get_chainlink_price(token_address)
            if chainlink_price:
                return chainlink_price
                
            # Try price API if available and configured
            if hasattr(self, 'price_api_url') and self.price_api_url:
                try:
                    import requests
                    response = requests.get(
                        f"{self.price_api_url}/price/{token_address}",
                        headers={"Authorization": f"Bearer {self.price_api_key}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "price" in data:
                            return float(data["price"])
                except Exception as api_error:
                    self.logger.warning(
                        "Failed to get price from API",
                        token_address=token_address,
                        error=str(api_error)
                    )
            
            # Fall back to hardcoded known prices as absolute last resort
            known_prices = {
                WETH_ADDRESS.lower(): 1.25,  # FLR price in USD
                "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D".lower(): 1.0,  # USDC price in USD
                "0xC67DCB4307C0856AC800a99A4CA8e2bd20749E21".lower(): 1.0,  # USDT price in USD
                "0x8A6fa2E13728d68D577eA24cBF7b5B3C3f279B1C".lower(): 3500.0,  # ETH price in USD
                "0x1aAF048D8cAf1dF75ad43c2e90B51A198EcAB05D".lower(): 68000.0,  # BTC price in USD
                "0xbF6bfE5d6B86308c9eb59194B9Cd08f3B3C4659B".lower(): 0.02,  # SGB price in USD
            }
            return known_prices.get(token_address.lower())
                
        except Exception as e:
            self.logger.error(
                "Failed to get fallback price",
                token_address=token_address,
                error=str(e)
            )
            return None
            
    def _get_chainlink_price(self, token_address: str) -> Optional[float]:
        """Get token price from Chainlink price feed."""
        try:
            # Map token addresses to their Chainlink price feed addresses
            chainlink_feeds = {
                WETH_ADDRESS.lower(): "0x9fB3Fad37D35e44220e477DBC53059819233D3f6",  # FLR/USD feed
                "0x8A6fa2E13728d68D577eA24cBF7b5B3C3f279B1C".lower(): "0xE96C81f228bbC41ee027d3F4Fb1aFE0C89a43b90",  # ETH/USD feed
                "0x1aAF048D8cAf1dF75ad43c2e90B51A198EcAB05D".lower(): "0xdBF4E1eDe4710A1EaC3D220480Ab0566296A9d39",  # BTC/USD feed
            }
            
            feed_address = chainlink_feeds.get(token_address.lower())
            if not feed_address:
                return None
                
            # Chainlink price feed ABI (minimal version with latestRoundData)
            chainlink_abi = [
                {
                    "inputs": [],
                    "name": "latestRoundData",
                    "outputs": [
                        {"name": "roundId", "type": "uint80"},
                        {"name": "answer", "type": "int256"},
                        {"name": "startedAt", "type": "uint256"},
                        {"name": "updatedAt", "type": "uint256"},
                        {"name": "answeredInRound", "type": "uint80"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Connect to the price feed contract
            feed_contract = self.web3.eth.contract(
                address=feed_address,
                abi=chainlink_abi
            )
            
            # Get the latest price data and decimals
            decimals = feed_contract.functions.decimals().call()
            price_data = feed_contract.functions.latestRoundData().call()
            
            # Extract and normalize the price
            price = price_data[1] / (10 ** decimals)
            
            self.logger.info(
                "Got price from Chainlink",
                token_address=token_address,
                price=price
            )
            
            return price
            
        except Exception as e:
            self.logger.warning(
                "Failed to get Chainlink price",
                token_address=token_address,
                error=str(e)
            )
            return None
            
    def _get_dex_price(self, token_in: str, token_out: str) -> float:
        """Get token price from DEX pools."""
        try:
            # Get pair address
            pair_address = self.factory_contract.functions.getPair(token_in, token_out).call()
            
            if pair_address == "0x0000000000000000000000000000000000000000":
                # No direct pair, try with WETH as intermediate
                return self._get_price_via_weth(token_in, token_out)
                
            # Get pair contract
            pair_contract = self.web3.eth.contract(
                address=pair_address,
                abi=PAIR_ABI
            )
            
            # Get reserves
            reserves = pair_contract.functions.getReserves().call()
            token0 = pair_contract.functions.token0().call()
            
            # Determine which reserve is for which token
            if token0.lower() == token_in.lower():
                return reserves[0] / reserves[1] if reserves[1] > 0 else 0
            else:
                return reserves[1] / reserves[0] if reserves[0] > 0 else 0
                
        except Exception:
            return 1.0  # Default to 1:1 ratio if price can't be determined
            
    def _get_price_via_weth(self, token_in: str, token_out: str) -> float:
        """Get price using WETH as intermediate."""
        try:
            # Get price of token_in in WETH
            price_in_weth = self._get_dex_price(token_in, WETH_ADDRESS)
            # Get price of token_out in WETH
            price_out_weth = self._get_dex_price(token_out, WETH_ADDRESS)
            
            # Calculate token_in/token_out price
            if price_out_weth > 0:
                return price_in_weth / price_out_weth
            return 0
        except Exception:
            return 1.0
            
    def _calculate_expected_output(
        self, amount_in: int, price: float, decimals_in: int, decimals_out: int
    ) -> int:
        """Calculate expected output amount based on market price."""
        # Adjust for decimal differences
        decimal_adjustment = 10 ** (decimals_out - decimals_in)
        expected_amount = int(amount_in * price * decimal_adjustment)
        return expected_amount
        
    def _get_swap_quote_from_reserves(
        self, token_in: str, token_out: str, amount_in: int
    ) -> Tuple[int, float]:
        """Calculate swap output using pool reserves directly."""
        try:
            # Get pair address
            pair_address = self.factory_contract.functions.getPair(token_in, token_out).call()
            
            if pair_address == "0x0000000000000000000000000000000000000000":
                # No direct pair, use WETH as intermediate
                return self._get_swap_quote_via_weth(token_in, token_out, amount_in)
                
            # Get pair contract
            pair_contract = self.web3.eth.contract(
                address=pair_address,
                abi=PAIR_ABI
            )
            
            # Get reserves
            reserves = pair_contract.functions.getReserves().call()
            token0 = pair_contract.functions.token0().call()
            
            # Determine which reserve is for which token
            reserve_in = reserves[0] if token0.lower() == token_in.lower() else reserves[1]
            reserve_out = reserves[1] if token0.lower() == token_in.lower() else reserves[0]
            
            # Calculate amount out using constant product formula (x * y = k)
            # amountOut = reserveOut * amountIn / (reserveIn + amountIn)
            numerator = reserve_out * amount_in
            denominator = reserve_in + amount_in
            amount_out = numerator // denominator if denominator > 0 else 0
            
            # Calculate price impact
            price_impact = 0.0
            if reserve_in > 0 and reserve_out > 0:
                initial_price = reserve_out / reserve_in
                new_reserve_in = reserve_in + amount_in
                new_reserve_out = reserve_out - amount_out
                new_price = new_reserve_out / new_reserve_in
                price_impact = abs((new_price - initial_price) / initial_price) * 100
                
            return (amount_out, price_impact)
            
        except Exception as e:
            self.logger.error("Failed to calculate swap from reserves", error=str(e))
            return (0, 100.0)  # Return fallback values in case of error
            
    def _get_swap_quote_via_weth(
        self, token_in: str, token_out: str, amount_in: int
    ) -> Tuple[int, float]:
        """Get swap quote using WETH as intermediate."""
        try:
            # First hop: token_in to WETH
            first_hop, first_impact = self._get_swap_quote_from_reserves(
                token_in, WETH_ADDRESS, amount_in
            )
            
            if first_hop == 0:
                return (0, 100.0)
                
            # Second hop: WETH to token_out
            second_hop, second_impact = self._get_swap_quote_from_reserves(
                WETH_ADDRESS, token_out, first_hop
            )
            
            # Combined price impact (simplified)
            total_impact = first_impact + second_impact
            
            return (second_hop, total_impact)
            
        except Exception:
            return (0, 100.0)
