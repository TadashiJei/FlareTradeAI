#!/usr/bin/env python3
"""
Test script for FlareTrade protocol integrations.
This script tests the updated protocol implementations and transaction handling.
"""

import logging
import sys
import os
import time
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from web3 import Web3

from flare_ai_defai.blockchain.protocols.raindex import RainDEX
from flare_ai_defai.blockchain.protocols.cyclo import Cyclo
from flare_ai_defai.blockchain.protocols.kinetic import Kinetic
from flare_ai_defai.blockchain.transaction import TransactionValidator
from flare_ai_defai.blockchain.attestation import AttestationValidator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RPC endpoint - replace with your actual endpoint
RPC_URL = "https://flare-api.flare.network/ext/C/rpc"

# Test wallet address - replace with your test wallet 
TEST_WALLET = "0x1234567890123456789012345678901234567890"

# Set up Web3 connection
def setup_web3():
    """Initialize Web3 connection."""
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not web3.is_connected():
        logger.error(f"Could not connect to {RPC_URL}")
        return None
    logger.info(f"Connected to {RPC_URL}")
    return web3

def test_attestation_validation():
    """Test the enhanced attestation validation."""
    logger.info("Testing attestation validation...")
    
    attestation = AttestationValidator()
    
    try:
        result = attestation.verify_environment()
        logger.info(f"Environment verification result: {result}")
        
        # In a real test, we'd check the result for expected values
        # For now, just log the result
        return "Success!" if result else "Failed"
    except Exception as e:
        logger.error(f"Error during attestation validation: {e}")
        return f"Error: {str(e)}"

def test_transaction_data_extraction(web3: Web3):
    """Test transaction data extraction from ABI."""
    logger.info("Testing transaction data extraction...")
    
    validator = TransactionValidator(web3)
    
    # Sample swap transaction data (this would be different for your environment)
    # This is simulating a swap transaction
    swap_data = "0x7ff36ab5000000000000000000000000000000000000000000000000002386f26fc10000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006440d629100000000000000000000000000000000000000000000000000000000000000002000000000000000000000000e9e7cea3dedca5984780bafc599bd69add087d560000000000000000000000001af3f329e8be154074d8769d1ffa4ee058b1dbc3"
    
    # Create a mock transaction
    tx_params = {
        "from": TEST_WALLET,
        "to": "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # Example DEX router
        "data": swap_data,
        "value": 0
    }
    
    try:
        # Extract protocol info
        protocol_info = validator._extract_protocol_info_from_tx(tx_params)
        if protocol_info:
            logger.info(f"Extracted protocol info: {protocol_info}")
            return protocol_info
        else:
            logger.warning("Could not extract protocol info")
            return "No protocol info extracted"
    except Exception as e:
        logger.error(f"Error during transaction data extraction: {e}")
        return f"Error: {str(e)}"

def test_raindex_price_feed(web3: Web3):
    """Test RainDEX's enhanced price feed integration."""
    logger.info("Testing RainDEX price feed...")
    
    # Initialize RainDEX
    raindex = RainDEX(
        web3=web3, 
        address=TEST_WALLET,
        price_api_url="https://api.example.com/prices"  # Example API URL
    )
    
    # Test tokens (FLR and USDC)
    flr_address = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    usdc_address = "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D"
    
    try:
        # Get FLR price
        flr_price = raindex._get_ftso_price(flr_address)
        logger.info(f"FLR price: {flr_price}")
        
        # Get USDC price
        usdc_price = raindex._get_ftso_price(usdc_address)
        logger.info(f"USDC price: {usdc_price}")
        
        # Calculate FLR/USDC rate
        if flr_price and usdc_price:
            rate = flr_price / usdc_price
            logger.info(f"FLR/USDC rate: {rate}")
        
        return {
            "flr_price": flr_price,
            "usdc_price": usdc_price
        }
    except Exception as e:
        logger.error(f"Error during price feed test: {e}")
        return f"Error: {str(e)}"

def test_swap_quote(web3: Web3):
    """Test getting a swap quote."""
    logger.info("Testing swap quote functionality...")
    
    raindex = RainDEX(web3=web3, address=TEST_WALLET)
    
    # Test tokens (FLR and USDC)
    flr_address = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    usdc_address = "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D"
    
    # Amount to swap (1 FLR)
    amount_in = 1 * 10**18  # 1 FLR with 18 decimals
    
    try:
        # Get swap quote
        quote = raindex.get_swap_quote(flr_address, usdc_address, amount_in)
        logger.info(f"Swap quote: {quote}")
        
        amount_out, price_impact = quote
        logger.info(f"Expected output: {amount_out / 10**6} USDC")  # USDC has 6 decimals
        logger.info(f"Price impact: {price_impact}%")
        
        return {
            "amount_out": amount_out / 10**6,
            "price_impact": price_impact
        }
    except Exception as e:
        logger.error(f"Error during swap quote test: {e}")
        return f"Error: {str(e)}"

def main():
    """Main test function."""
    logger.info("Starting FlareTrade protocol tests...")
    
    # Setup Web3
    web3 = setup_web3()
    if not web3:
        logger.error("Failed to set up Web3 connection. Exiting.")
        return
    
    # Run tests
    results = {}
    
    # Test attestation validation
    results["attestation_validation"] = test_attestation_validation()
    
    # Test transaction data extraction
    results["transaction_data_extraction"] = test_transaction_data_extraction(web3)
    
    # Test RainDEX price feed
    results["raindex_price_feed"] = test_raindex_price_feed(web3)
    
    # Test swap quote
    results["swap_quote"] = test_swap_quote(web3)
    
    # Display results
    logger.info("Test results:")
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")

if __name__ == "__main__":
    main()
