#!/usr/bin/env python3
"""
FlareTrade Demo Script

This script demonstrates the capabilities of the FlareTrade DeFi agent,
showing how it can process natural language commands, perform risk assessment,
and execute transactions securely within a TEE environment.
"""

import argparse
import json
import os
import sys
from typing import Dict, List

from src.flare_ai_defai.agent.defi_agent import DeFiAgent
from src.flare_ai_defai.blockchain.attestation import AttestationValidator, Vtpm


def setup_agent(wallet_address: str, use_tee: bool = True) -> DeFiAgent:
    """
    Set up the DeFi agent.
    
    Args:
        wallet_address (str): The wallet address to use
        use_tee (bool, optional): Whether to use TEE protection. Defaults to True.
        
    Returns:
        DeFiAgent: The initialized DeFi agent
    """
    print(f"Initializing DeFi agent for wallet: {wallet_address}")
    print(f"TEE protection: {'Enabled' if use_tee else 'Disabled'}")
    
    # Check if TEE is available
    if use_tee:
        validator = AttestationValidator()
        env_result = validator.verify_environment()
        if not env_result["valid"]:
            print("WARNING: TEE environment verification failed. Running in simulation mode.")
            use_tee = False
    
    # Initialize agent
    agent = DeFiAgent(
        wallet_address=wallet_address,
        use_tee=use_tee,
        risk_threshold="medium",
        simulate_transactions=True,
    )
    
    print("DeFi agent initialized successfully!")
    return agent


def process_command(agent: DeFiAgent, command: str) -> None:
    """
    Process a natural language command.
    
    Args:
        agent (DeFiAgent): The DeFi agent
        command (str): The command to process
    """
    print(f"\n=== Processing Command: '{command}' ===")
    
    # Process the command
    result = agent.process_natural_language_command(command)
    
    # Display results
    if result["success"]:
        print("✅ Command processed successfully!")
        print(f"Action: {result['action']}")
        print(f"Protocol: {result['protocol']}")
        print(f"Parameters: {json.dumps(result['params'], indent=2)}")
        
        # Display risk assessment
        risk = result["risk_assessment"]
        print("\nRisk Assessment:")
        print(f"Overall Risk: {risk['overall_risk']['level']} ({risk['overall_risk']['score']})")
        print("Risk Factors:")
        for factor in risk["risk_factors"]:
            print(f"- {factor['name']}: {factor['level']} ({factor['score']})")
        
        # Display transaction hash if available
        if "transaction_hash" in result:
            print(f"\nTransaction Hash: {result['transaction_hash']}")
    else:
        print("❌ Command processing failed!")
        print(f"Errors: {', '.join(result['errors'])}")
        
        # Display risk assessment if available
        if "risk_assessment" in result:
            risk = result["risk_assessment"]
            print("\nRisk Assessment:")
            print(f"Overall Risk: {risk['overall_risk']['level']} ({risk['overall_risk']['score']})")
            print("Risk Factors:")
            for factor in risk["risk_factors"]:
                print(f"- {factor['name']}: {factor['level']} ({factor['score']})")


def display_portfolio(agent: DeFiAgent) -> None:
    """
    Display the user's portfolio.
    
    Args:
        agent (DeFiAgent): The DeFi agent
    """
    print("\n=== Portfolio Overview ===")
    
    # Get portfolio
    portfolio = agent.get_portfolio()
    
    # Display total value
    print(f"Total Portfolio Value: ${portfolio['total_value']:.2f} USD")
    
    # Display token balances
    print("\nToken Balances:")
    for protocol, balances in portfolio["balances"].items():
        print(f"\n{protocol.upper()}:")
        for token, balance_info in balances.items():
            print(f"- {token}: {balance_info['balance']} (${balance_info.get('usd_value', 0):.2f} USD)")
    
    # Display positions
    print("\nDeFi Positions:")
    for protocol, positions in portfolio["positions"].items():
        if positions:
            print(f"\n{protocol.upper()}:")
            for position in positions:
                print(f"- {position['type']}: {position['description']} (${position.get('usd_value', 0):.2f} USD)")


def display_transaction_history(agent: DeFiAgent) -> None:
    """
    Display the user's transaction history.
    
    Args:
        agent (DeFiAgent): The DeFi agent
    """
    print("\n=== Transaction History ===")
    
    # Get transaction history
    transactions = agent.get_transaction_history(limit=5)
    
    # Display transactions
    for i, tx in enumerate(transactions, 1):
        print(f"\nTransaction {i}:")
        print(f"Hash: {tx['hash']}")
        print(f"Protocol: {tx['protocol']}")
        print(f"Action: {tx['action']}")
        print(f"Status: {tx['status']}")
        print(f"Timestamp: {tx['timestamp']}")
        print(f"Value: ${tx.get('usd_value', 0):.2f} USD")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="FlareTrade Demo")
    parser.add_argument("--wallet", type=str, default="0x742d35Cc6634C0532925a3b844Bc454e4438f44e", help="Wallet address")
    parser.add_argument("--no-tee", action="store_true", help="Disable TEE protection")
    args = parser.parse_args()
    
    # Setup agent
    agent = setup_agent(args.wallet, not args.no_tee)
    
    # Display portfolio
    display_portfolio(agent)
    
    # Display transaction history
    display_transaction_history(agent)
    
    # Process some example commands
    example_commands = [
        "Swap 10 ETH to USDC on SparkDEX with 0.5% slippage",
        "Deposit 100 USDC into Kinetic",
        "Stake 50 FLR on Cyclo",
        "Withdraw 25 USDC from Kinetic",
        "Claim rewards from Cyclo",
    ]
    
    for command in example_commands:
        process_command(agent, command)
        input("\nPress Enter to continue...")
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()
