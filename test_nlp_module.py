"""
Test script for the DeFi natural language processing module.
"""

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.flare_ai_defai.nlp.defi_parser import DeFiCommandParser

def test_parser():
    """Test the DeFiCommandParser with various commands."""
    parser = DeFiCommandParser()
    
    # Test various commands
    test_commands = [
        "Swap 10 ETH to USDC on SparkDEX with 0.5% slippage",
        "Deposit 100 USDC into Kinetic",
        "Withdraw 50 USDC from Kinetic",
        "Stake 10 FLR on Cyclo",
        "Unstake 5 FLR from Cyclo",
        "Claim rewards from Cyclo",
        "Borrow 20 ETH from Kinetic",
        "Repay 15 ETH loan on Kinetic"
    ]
    
    for command in test_commands:
        print(f"\nTesting command: '{command}'")
        parsed = parser.parse_command(command)
        
        print(f"Action: {parsed.action}")
        print(f"Protocol: {parsed.protocol}")
        print(f"Parameters: {parsed.params}")

if __name__ == "__main__":
    print("Testing DeFi NLP Module")
    print("======================")
    test_parser()
