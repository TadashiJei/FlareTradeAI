"""
SparkDEX Protocol Integration Module

This module implements the integration with SparkDEX, a decentralized exchange
on the Flare Network. It provides functionality for token swaps, liquidity provision,
and price quotes.
"""

from typing import Any, Dict, List, Optional, Tuple
import structlog
import math
import logging
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

# ABI for SparkDEX Router contract
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

# ABI for ERC20 Token contract
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]

# ABI for FTSO Registry contract
FTSO_REGISTRY_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "symbol", "type": "string"}],
        "name": "getFtsoIndex",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "index", "type": "uint256"}],
        "name": "getFtsoByIndex",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ABI for FTSO contract
FTSO_ABI = [
    {
        "inputs": [],
        "name": "getCurrentPrice",
        "outputs": [{"internalType": "uint256", "name": "price", "type": "uint256"}, {"internalType": "uint256", "name": "decimals", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ABI for UniswapV2Pair contract
PAIR_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# ABI for UniswapV2Factory contract
FACTORY_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}],
        "name": "getPair",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# SparkDEX contract addresses by network
CONTRACT_ADDRESSES = {
    "flare": {
        "router": "0x1234567890123456789012345678901234567890",  # Placeholder
        "factory": "0x0987654321098765432109876543210987654321",  # Placeholder
        "ftso_registry": "0x1234567890123456789012345678901234567890",  # Placeholder
    },
    "songbird": {
        "router": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # Placeholder
        "factory": "0xfedcbafedcbafedcbafedcbafedcbafedcbafedc",  # Placeholder
        "ftso_registry": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # Placeholder
    },
}

# Common tokens on Flare Network
COMMON_TOKENS = [
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
    TokenInfo(
        symbol="WFLR",
        name="Wrapped Flare",
        address="0x1234567890123456789012345678901234567892",  # Placeholder
        decimals=18,
        logo_url="https://assets.coingecko.com/coins/images/28624/standard/FLR-icon-darkbg.png",
    ),
]


class SparkDEX(BaseProtocol):
    """
    SparkDEX protocol integration for the Flare Network.
    
    This class provides methods for interacting with the SparkDEX decentralized
    exchange, including token swaps, liquidity provision, and price quotes.
    """

    def __init__(self, web3: Web3, address: Optional[ChecksumAddress] = None, network: str = "flare"):
        """
        Initialize the SparkDEX protocol integration.
        
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
        self.router_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contracts["router"]),
            abi=ROUTER_ABI,
        )
        self.logger = logger.bind(protocol="sparkdex", network=network)

    def get_info(self) -> ProtocolInfo:
        """
        Get information about the SparkDEX protocol.
        
        Returns:
            ProtocolInfo: Protocol information
        """
        return ProtocolInfo(
            name="SparkDEX",
            type=ProtocolType.DEX,
            description="Decentralized exchange on the Flare Network",
            website="https://sparkdex.io",  # Placeholder
            contracts=self.contracts,
        )

    def get_supported_tokens(self) -> List[TokenInfo]:
        """
        Get list of tokens supported by SparkDEX.
        
        Returns:
            List[TokenInfo]: List of supported tokens
        """
        return COMMON_TOKENS

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
        self.validate_address()
        
        # Handle native token (FLR)
        if token_address == "0x0000000000000000000000000000000000000000":
            balance_wei = self.web3.eth.get_balance(self.address)
            return float(self.web3.from_wei(balance_wei, "ether"))
        
        # Handle ERC20 tokens
        token_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(token_address),
            abi=ERC20_ABI,
        )
        
        balance = token_contract.functions.balanceOf(self.address).call()
        decimals = token_contract.functions.decimals().call()
        
        return float(balance) / (10 ** decimals)

    def get_token_contract(self, token_address: str) -> Contract:
        """
        Get a Web3 contract instance for a token.
        
        Args:
            token_address (str): Address of the token contract
            
        Returns:
            Contract: Web3 contract instance
        """
        return self.web3.eth.contract(
            address=self.web3.to_checksum_address(token_address),
            abi=ERC20_ABI,
        )

    def get_token_allowance(self, token_address: str, spender_address: str) -> int:
        """
        Get the allowance for a spender to use a token.
        
        Args:
            token_address (str): Address of the token contract
            spender_address (str): Address of the spender
            
        Returns:
            int: Allowance amount
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        token_contract = self.get_token_contract(token_address)
        return token_contract.functions.allowance(self.address, spender_address).call()

    def approve_token(self, token_address: str, spender_address: str, amount: int) -> TxParams:
        """
        Create a transaction to approve a spender to use a token.
        
        Args:
            token_address (str): Address of the token contract
            spender_address (str): Address of the spender
            amount (int): Amount to approve
            
        Returns:
            TxParams: Transaction parameters
            
        Raises:
            ValueError: If address is not set
        """
        self.validate_address()
        
        token_contract = self.get_token_contract(token_address)
        
        return {
            "from": self.address,
            "to": self.web3.to_checksum_address(token_address),
            "data": token_contract.encodeABI(
                fn_name="approve",
                args=[spender_address, amount],
            ),
            "gas": 100000,  # Estimated gas
            "maxFeePerGas": self.web3.eth.gas_price,
            "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
            "nonce": self.web3.eth.get_transaction_count(self.address),
            "chainId": self.web3.eth.chain_id,
            "type": 2,
        }

    def get_token_price(self, token_address: str, quote_token_address: str = None) -> float:
        """
        Get the price of a token in terms of another token.
        
        Args:
            token_address (str): Address of the token
            quote_token_address (str, optional): Address of the quote token.
                Defaults to USDC.
                
        Returns:
            float: Token price in terms of quote token
        """
        if not token_address:
            raise ValueError("Token address is required")
            
        # Use USDC as default quote token if not specified
        if not quote_token_address:
            quote_token_address = next(
                (token.address for token in COMMON_TOKENS if token.symbol == "USDC"),
                None,
            )
            if not quote_token_address:
                raise ValueError("USDC token not found and no quote token specified")
        
        # Convert addresses to checksum format
        token_address = self.web3.to_checksum_address(token_address)
        quote_token_address = self.web3.to_checksum_address(quote_token_address)
        
        # If token is the same as quote token, price is 1.0
        if token_address == quote_token_address:
            return 1.0
            
        try:
            # Get token decimals
            token_contract = self.get_token_contract(token_address)
            quote_token_contract = self.get_token_contract(quote_token_address)
            
            token_decimals = token_contract.functions.decimals().call()
            quote_decimals = quote_token_contract.functions.decimals().call()
            
            # Use a production approach with multiple price sources
            # 1. First try getting price from the router (most accurate real-time price)
            try:
                # For a production implementation, get price from the SparkDEX router
                # using getAmountsOut with a small test amount
                test_amount = 10 ** token_decimals  # 1 token in wei
                path = [token_address, quote_token_address]
                
                # Call the router to get the expected output amount
                amounts_out = self.router_contract.functions.getAmountsOut(
                    test_amount, path
                ).call()
                
                if len(amounts_out) >= 2 and amounts_out[1] > 0:
                    # Calculate price with decimal adjustments
                    price = (amounts_out[1] / 10**quote_decimals) / (test_amount / 10**token_decimals)
                    self.logger.info(
                        "Got price from router",
                        token=token_address,
                        quote_token=quote_token_address,
                        price=price,
                    )
                    return price
            except Exception as e:
                self.logger.warning(
                    "Failed to get price from router, trying price feed",
                    token=token_address,
                    quote_token=quote_token_address,
                    error=str(e),
                )
                
            # 2. If router fails, try using Flare's FTSO price feed (if available)
            try:
                # For FLR, SGB, and major tokens, we can use FTSO price feed
                ftso_registry_address = self.contracts.get("ftso_registry")
                if ftso_registry_address:
                    ftso_registry = self.web3.eth.contract(
                        address=self.web3.to_checksum_address(ftso_registry_address),
                        abi=FTSO_REGISTRY_ABI,
                    )
                    
                    # Get token symbols
                    token_symbol = token_contract.functions.symbol().call()
                    quote_symbol = quote_token_contract.functions.symbol().call()
                    
                    # Get price from FTSO
                    token_price_usd = self._get_ftso_price(ftso_registry, token_symbol)
                    quote_price_usd = self._get_ftso_price(ftso_registry, quote_symbol)
                    
                    if token_price_usd > 0 and quote_price_usd > 0:
                        price = token_price_usd / quote_price_usd
                        self.logger.info(
                            "Got price from FTSO",
                            token=token_address,
                            quote_token=quote_token_address,
                            price=price,
                        )
                        return price
            except Exception as e:
                self.logger.warning(
                    "Failed to get price from FTSO, using fallback",
                    token=token_address,
                    quote_token=quote_token_address,
                    error=str(e),
                )
            
            # 3. If all else fails, check for a pool and calculate from reserves
            try:
                # Get the pool address for the token pair
                factory_address = self.contracts.get("factory")
                factory = self.web3.eth.contract(
                    address=self.web3.to_checksum_address(factory_address),
                    abi=FACTORY_ABI,
                )
                
                pool_address = factory.functions.getPair(token_address, quote_token_address).call()
                
                if pool_address and pool_address != self.web3.to_checksum_address("0x0000000000000000000000000000000000000000"):
                    pool = self.web3.eth.contract(
                        address=pool_address,
                        abi=PAIR_ABI,
                    )
                    
                    # Get reserves
                    reserves = pool.functions.getReserves().call()
                    token0 = pool.functions.token0().call()
                    
                    # Determine which reserve corresponds to which token
                    if token0 == token_address:
                        token_reserve, quote_reserve = reserves[0], reserves[1]
                    else:
                        token_reserve, quote_reserve = reserves[1], reserves[0]
                    
                    # Calculate price with decimal adjustments
                    if token_reserve > 0:
                        price = (quote_reserve / 10**quote_decimals) / (token_reserve / 10**token_decimals)
                        self.logger.info(
                            "Got price from pool reserves",
                            token=token_address,
                            quote_token=quote_token_address,
                            price=price,
                        )
                        return price
            except Exception as e:
                self.logger.warning(
                    "Failed to get price from pool reserves",
                    token=token_address,
                    quote_token=quote_token_address,
                    error=str(e),
                )
            
            # If all methods fail, log a warning and return a fallback price
            self.logger.error(
                "Could not determine price through any method",
                token=token_address,
                quote_token=quote_token_address,
            )
            raise ValueError(f"Could not determine price for {token_address} in terms of {quote_token_address}")
            
        except Exception as e:
            self.logger.error(
                "Error getting token price",
                token=token_address,
                quote_token=quote_token_address,
                error=str(e),
            )
            raise
    
    def _get_ftso_price(self, ftso_registry, symbol):
        """Get price from FTSO price feed."""
        try:
            # Get FTSO provider for the symbol
            ftso_index = ftso_registry.functions.getFtsoIndex(symbol).call()
            ftso_address = ftso_registry.functions.getFtsoByIndex(ftso_index).call()
            
            if ftso_address:
                ftso = self.web3.eth.contract(
                    address=ftso_address,
                    abi=FTSO_ABI,
                )
                
                # Get the latest price
                price_data = ftso.functions.getCurrentPrice().call()
                price = price_data[0] / (10 ** price_data[1])  # Apply the decimal factor
                return price
        except Exception as e:
            self.logger.warning(f"Failed to get FTSO price for {symbol}: {str(e)}")
        
        return 0

    def get_swap_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: int,
    ) -> Tuple[int, float]:
        """
        Get a quote for a token swap.
        
        Args:
            token_in_address (str): Address of the input token
            token_out_address (str): Address of the output token
            amount_in (int): Amount of input token
            
        Returns:
            Tuple[int, float]: (Expected output amount, price impact percentage)
        """
        if not token_in_address or not token_out_address:
            raise ValueError("Token addresses are required")
        
        if amount_in <= 0:
            raise ValueError("Amount must be greater than zero")
        
        # Convert addresses to checksum format
        token_in_address = self.web3.to_checksum_address(token_in_address)
        token_out_address = self.web3.to_checksum_address(token_out_address)
        
        # If tokens are the same, return input amount with 0 impact
        if token_in_address == token_out_address:
            return amount_in, 0.0
        
        try:
            # Get token contracts and decimals
            token_in_contract = self.get_token_contract(token_in_address)
            token_out_contract = self.get_token_contract(token_out_address)
            
            token_in_decimals = token_in_contract.functions.decimals().call()
            token_out_decimals = token_out_contract.functions.decimals().call()
            
            # 1. Use router's getAmountsOut function to get the expected output amount
            try:
                # For a production implementation, get price from the SparkDEX router
                # using getAmountsOut with a small test amount
                path = [token_in_address, token_out_address]
                
                # Call the router to get the expected output amount
                amounts_out = self.router_contract.functions.getAmountsOut(
                    amount_in, path
                ).call()
                
                if len(amounts_out) >= 2 and amounts_out[1] > 0:
                    expected_output = amounts_out[1]
                    
                    # Calculate price impact by comparing to the current market price
                    # For this, we use a smaller amount to get the current market rate
                    test_amount = 10 ** token_in_decimals  # 1 token in wei
                    
                    if amount_in != test_amount:
                        test_amounts_out = self.router_contract.functions.getAmountsOut(
                            test_amount, path
                        ).call()
                        
                        if len(test_amounts_out) >= 2 and test_amounts_out[1] > 0:
                            # Calculate the expected output based on current market rate
                            market_rate = test_amounts_out[1] / test_amount
                            expected_at_market_rate = int(market_rate * amount_in)
                            
                            # Calculate price impact as a percentage
                            if expected_at_market_rate > 0:
                                price_impact = 100 * (1 - (expected_output / expected_at_market_rate))
                                # Ensure price impact is not negative and cap at 100%
                                price_impact = max(0, min(100, price_impact))
                            else:
                                price_impact = 0.0
                        else:
                            price_impact = 0.0
                    else:
                        price_impact = 0.0
                    
                    self.logger.info(
                        "Got swap quote from router",
                        token_in=token_in_address,
                        token_out=token_out_address,
                        amount_in=amount_in,
                        expected_output=expected_output,
                        price_impact=price_impact,
                    )
                    
                    return expected_output, price_impact
                
            except Exception as e:
                self.logger.warning(
                    "Failed to get swap quote from router, trying pool reserves",
                    token_in=token_in_address,
                    token_out=token_out_address,
                    amount_in=amount_in,
                    error=str(e),
                )
            
            # 2. If router call fails, calculate based on pool reserves
            try:
                # Get the pool address for the token pair
                factory_address = self.contracts.get("factory")
                factory = self.web3.eth.contract(
                    address=self.web3.to_checksum_address(factory_address),
                    abi=FACTORY_ABI,
                )
                
                pool_address = factory.functions.getPair(token_in_address, token_out_address).call()
                
                if pool_address and pool_address != self.web3.to_checksum_address("0x0000000000000000000000000000000000000000"):
                    pool = self.web3.eth.contract(
                        address=pool_address,
                        abi=PAIR_ABI,
                    )
                    
                    # Get reserves
                    reserves = pool.functions.getReserves().call()
                    token0 = pool.functions.token0().call()
                    
                    # Determine which reserve corresponds to which token
                    if token0 == token_in_address:
                        reserve_in, reserve_out = reserves[0], reserves[1]
                    else:
                        reserve_in, reserve_out = reserves[1], reserves[0]
                    
                    # Calculate expected output using the constant product formula:
                    # xy = k, where x and y are the reserves
                    # For a given input dx, the output dy is calculated as:
                    # dy = y - k/(x + dx) = y - y*x/(x + dx) = y*dx/(x + dx)
                    
                    # Apply the 0.3% fee by reducing the input amount
                    amount_in_with_fee = amount_in * 997
                    numerator = amount_in_with_fee * reserve_out
                    denominator = (reserve_in * 1000) + amount_in_with_fee
                    
                    if denominator > 0:
                        expected_output = numerator // denominator
                        
                        # Calculate price impact
                        # Use the formula: 1 - (new_price / old_price)
                        # where price = reserve_out / reserve_in
                        old_price = reserve_out / reserve_in
                        new_reserve_in = reserve_in + amount_in
                        new_reserve_out = reserve_out - expected_output
                        
                        if new_reserve_in > 0:
                            new_price = new_reserve_out / new_reserve_in
                            price_impact = 100 * max(0, 1 - (new_price / old_price))
                            # Cap price impact at 100%
                            price_impact = min(100, price_impact)
                        else:
                            price_impact = 100.0
                        
                        self.logger.info(
                            "Got swap quote from pool reserves",
                            token_in=token_in_address,
                            token_out=token_out_address,
                            amount_in=amount_in,
                            expected_output=expected_output,
                            price_impact=price_impact,
                        )
                        
                        return int(expected_output), float(price_impact)
            
            except Exception as e:
                self.logger.warning(
                    "Failed to get swap quote from pool reserves",
                    token_in=token_in_address,
                    token_out=token_out_address,
                    amount_in=amount_in,
                    error=str(e),
                )
            
            # 3. If all else fails, use token prices to estimate if available
            try:
                token_in_price = self.get_token_price(token_in_address)
                token_out_price = self.get_token_price(token_out_address)
                
                if token_in_price > 0 and token_out_price > 0:
                    # Calculate theoretical exchange rate
                    rate = token_in_price / token_out_price
                    
                    # Apply a reasonable price impact estimate for this fallback method
                    # The larger the swap, the higher the estimated impact
                    token_in_amount_normalized = amount_in / (10 ** token_in_decimals)
                    
                    # Estimate price impact based on normalized amount (logarithmic scale)
                    estimated_impact = min(30, max(0.5, 2 * math.log10(1 + token_in_amount_normalized)))
                    
                    # Reduce expected amount by the estimated impact
                    rate_with_impact = rate * (1 - (estimated_impact / 100))
                    
                    # Calculate expected output with decimal adjustment
                    expected_output = int(
                        (amount_in / (10 ** token_in_decimals)) * 
                        rate_with_impact * 
                        (10 ** token_out_decimals)
                    )
                    
                    self.logger.info(
                        "Got swap quote from token prices (fallback method)",
                        token_in=token_in_address,
                        token_out=token_out_address,
                        amount_in=amount_in,
                        expected_output=expected_output,
                        price_impact=estimated_impact,
                    )
                    
                    return expected_output, float(estimated_impact)
            
            except Exception as e:
                self.logger.warning(
                    "Failed to get swap quote using token prices",
                    token_in=token_in_address,
                    token_out=token_out_address,
                    amount_in=amount_in,
                    error=str(e),
                )
            
            # If all methods fail, log a warning and raise an error
            self.logger.error(
                "Could not determine swap quote through any method",
                token_in=token_in_address,
                token_out=token_out_address,
                amount_in=amount_in,
            )
            raise ValueError(f"Could not determine swap quote for {token_in_address} to {token_out_address}")
            
        except Exception as e:
            self.logger.error(
                "Error getting swap quote",
                token_in=token_in_address,
                token_out=token_out_address,
                amount_in=amount_in,
                error=str(e),
            )
            raise

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
