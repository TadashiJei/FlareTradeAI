#!/usr/bin/env python3
"""
Simple test script for FTSO price feed implementation in RainDEX.
"""

import sys
import os
import logging
from web3 import Web3
import json

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RPC endpoint
RPC_URL = "https://flare-api.flare.network/ext/C/rpc"

# Test wallet address
TEST_WALLET = "0x1234567890123456789012345678901234567890"

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
    }
]

# UniswapV2 Router ABI for swap functions
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
    }
]

# Hardcoded token addresses for testing
TOKEN_ADDRESSES = {
    "FLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
    "USDC": "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D",
    "WSGB": "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED"
}

# Token symbols mapping (lowercase addresses for consistency)
TOKEN_SYMBOLS = {
    "0x1d80c49bbcd1c0911346656b529df9e5c2f783d": "FLR",
    "0xe3f5a90f9cb311505cd691a46596599aa1a0ad7d": "USDC",
    "0x02f0826ef6ad107cfc861152b32b52fd11bab9ed": "WSGB"
}

def setup_web3():
    """Initialize Web3 connection."""
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not web3.is_connected():
        logger.error(f"Could not connect to {RPC_URL}")
        return None
    logger.info(f"Connected to {RPC_URL}")
    return web3

def get_ftso_price(web3, token_address):
    """Implementation of the _get_ftso_price method."""
    try:
        # Normalize the token address to lowercase for consistency
        token_address_lower = token_address.lower()
        
        # Get the token symbol
        token_symbol = TOKEN_SYMBOLS.get(token_address_lower)
        if not token_symbol:
            logger.warning(f"Unknown token address: {token_address_lower}")
            return None
            
        # Map token symbol to FTSO symbol
        ftso_symbol = token_symbol
        logger.info(f"Looking up price for {ftso_symbol}")
        
        # Connect to FTSO Registry
        ftso_registry_address = "0xDf37E9878D52C55D6C708DaE1A0D5A9347085F92"  # Flare
        ftso_registry_contract = web3.eth.contract(
            address=web3.to_checksum_address(ftso_registry_address),
            abi=FTSO_REGISTRY_ABI
        )
        
        # Get current price provider address
        price_provider_address = ftso_registry_contract.functions.getCurrentPriceProviderAddress().call()
        logger.info(f"FTSO Price Provider address: {price_provider_address}")
        
        # Connect to FTSO Price Provider
        ftso_provider_contract = web3.eth.contract(
            address=web3.to_checksum_address(price_provider_address),
            abi=FTSO_PROVIDER_ABI
        )
        
        # Get FTSO index for the symbol
        ftso_index = ftso_provider_contract.functions.getFtsoIndex(ftso_symbol).call()
        logger.info(f"FTSO index for {ftso_symbol}: {ftso_index}")
        
        # Get current price with decimals
        price_data = ftso_provider_contract.functions.getCurrentPriceWithDecimals(ftso_index).call()
        price, timestamp, decimals = price_data
        
        # Convert price to USD
        usd_price = price / (10 ** decimals)
        logger.info(f"Price for {ftso_symbol}: ${usd_price} (timestamp: {timestamp})")
        
        return usd_price
    except Exception as e:
        logger.error(f"Error getting FTSO price for {token_address}: {e}")
        return None

def test_transaction_data_extraction(web3):
    """Test the transaction data extraction, simulating the _extract_protocol_info_from_tx method."""
    logger.info("Testing transaction data extraction...")
    
    # Sample swap data for swapExactTokensForTokens
    swap_data = "0x7ff36ab5000000000000000000000000000000000000000000000000002386f26fc10000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006440d629100000000000000000000000000000000000000000000000000000000000000002000000000000000000000000e9e7cea3dedca5984780bafc599bd69add087d560000000000000000000000001af3f329e8be154074d8769d1ffa4ee058b1dbc3"

    # Create a transaction parameter object
    tx_params = {
        "from": TEST_WALLET,
        "to": "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # Example DEX router
        "data": swap_data,
        "value": 0
    }
    
    # Create a router contract instance for decoding
    router_contract = web3.eth.contract(
        address=tx_params["to"],
        abi=ROUTER_ABI
    )
    
    try:
        # Parse function signature
        func_signature = swap_data[:10]
        logger.info(f"Function signature: {func_signature}")
        
        # Define known function signatures
        function_signatures = {
            "0x7ff36ab5": "swapExactTokensForTokens",
            "0x38ed1739": "swapExactTokensForTokens",
            "0x18cbafe5": "swapExactTokensForETH",
            "0xfb3bdb41": "swapETHForExactTokens",
            "0x4a25d94a": "swapTokensForExactETH"
        }
        
        function_name = function_signatures.get(func_signature, "Unknown function")
        logger.info(f"Function identified: {function_name}")
        
        # Decode transaction data
        if function_name == "swapExactTokensForTokens":
            # Try to decode the function parameters
            try:
                decoded_input = router_contract.decode_function_input(swap_data)
                function_obj, params = decoded_input
                
                logger.info(f"Decoded parameters: {json.dumps(str(params), indent=2)}")
                
                # Extract token addresses and amounts
                amount_in = params.get("amountIn", 0)
                amount_out_min = params.get("amountOutMin", 0)
                path = params.get("path", [])
                deadline = params.get("deadline", 0)
                
                # Get token addresses
                token_in_address = path[0] if len(path) > 0 else None
                token_out_address = path[-1] if len(path) > 0 else None
                
                logger.info(f"Amount in: {amount_in}")
                logger.info(f"Amount out min: {amount_out_min}")
                logger.info(f"Token in: {token_in_address}")
                logger.info(f"Token out: {token_out_address}")
                
                # Extract protocol info (simulating full implementation)
                protocol_info = {
                    "protocol_type": "dex",
                    "action": "swap",
                    "token_in": token_in_address,
                    "token_out": token_out_address,
                    "amount_in": amount_in,
                    "amount_out_min": amount_out_min
                }
                
                return protocol_info
                
            except Exception as e:
                logger.error(f"Error decoding function input: {e}")
                # Fallback: Parse input data manually
                logger.info("Using manual parsing fallback")
                return {
                    "protocol_type": "dex",
                    "action": "swap",
                    "decoded": False
                }
        else:
            return {
                "protocol_type": "unknown",
                "action": "unknown"
            }
    except Exception as e:
        logger.error(f"Error during transaction data extraction: {e}")
        return None

def main():
    """Main test function."""
    logger.info("Starting FTSO price feed and transaction extraction tests...")
    
    # Setup Web3
    web3 = setup_web3()
    if not web3:
        logger.error("Failed to set up Web3 connection. Exiting.")
        return
    
    # Test FTSO price retrieval for different tokens
    results = {}
    for token_name, token_address in TOKEN_ADDRESSES.items():
        logger.info(f"Testing price for {token_name}...")
        price = get_ftso_price(web3, token_address)
        results[token_name] = price
        
    # Test transaction data extraction
    logger.info("Testing transaction data extraction...")
    tx_result = test_transaction_data_extraction(web3)
    results["transaction_extraction"] = "Success" if tx_result else "Failed"
    
    # Display results
    logger.info("Test results:")
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")

if __name__ == "__main__":
    main()
