"""
Test script for the DeFi agent with enhanced transaction validation and risk assessment.

This script demonstrates how the DeFi agent handles transaction validation and risk assessment
in different scenarios.
"""

import sys
import os
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.append('/Users/jay/Java/Hackathon/FlareTradeAI')

try:
    from src.flare_ai_defai.agent.defi_agent import DeFiAgent
    from src.flare_ai_defai.blockchain.risk.assessment import DeFiRiskAssessmentService, RiskLevel
    from src.flare_ai_defai.blockchain.transaction import TransactionSimulator, TransactionValidator
    from src.flare_ai_defai.blockchain.validation import FinancialOperationValidator
    
    # Using real imports
    USING_MOCKS = False
    print("Using real imports from the codebase")
except ImportError as e:
    print(f"ImportError: {e}")
    print("Using mock classes for testing")
    USING_MOCKS = True
    
    # Mock classes to enable testing without dependencies
    class RiskLevel:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class DeFiAgent:
        def __init__(self, wallet_address, use_tee=True, risk_threshold="medium", simulate_transactions=True):
            self.wallet_address = wallet_address
            self.use_tee = use_tee
            self.risk_threshold = risk_threshold
            self.simulate_transactions = simulate_transactions
            
            # Mock components
            self.risk_assessment = MagicMock()
            self.transaction_validator = MagicMock()
            self.transaction_simulator = MagicMock()
            self.financial_validator = MagicMock()
            
        def process_natural_language_command(self, command):
            # Mock implementation
            if "swap" in command.lower():
                if "high risk" in command.lower():
                    return self._mock_high_risk_command(command)
                else:
                    return self._mock_swap_command(command)
            else:
                return {"success": False, "errors": ["Unknown command"]}
                
        def _mock_swap_command(self, command):
            return {
                "success": True,
                "action": "swap",
                "protocol": "SparkDEX",
                "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "risk_assessment": {
                    "overall_risk": {"level": RiskLevel.LOW, "score": 0.2},
                    "risk_factors": [
                        {
                            "name": "transaction_size",
                            "level": RiskLevel.LOW,
                            "score": 0.1,
                            "description": "Transaction size is within normal range",
                        },
                        {
                            "name": "protocol_risk",
                            "level": RiskLevel.LOW,
                            "score": 0.3,
                            "description": "Protocol has been audited and is considered safe",
                        },
                    ],
                    "warnings": [],
                    "recommendations": ["Consider setting a slippage limit to protect against price movements"],
                },
                "warnings": [],
                "recommendations": ["Consider setting a slippage limit to protect against price movements"],
                "params": {
                    "token_in": "FLR",
                    "token_out": "USDC",
                    "amount_in": 100,
                    "slippage": 0.5,
                },
                "simulation_result": {
                    "success": True,
                    "gas_estimate": 150000,
                    "expected_outcome": {
                        "status": "success",
                        "token_transfers": [
                            {"token": "FLR", "amount": -100},
                            {"token": "USDC", "amount": 99.5},
                        ],
                    },
                },
            }
            
        def _mock_high_risk_command(self, command):
            return {
                "success": False,
                "action": "swap",
                "protocol": "SparkDEX",
                "errors": ["Risk level high exceeds threshold medium"],
                "risk_assessment": {
                    "overall_risk": {"level": RiskLevel.HIGH, "score": 0.8},
                    "risk_factors": [
                        {
                            "name": "transaction_size",
                            "level": RiskLevel.HIGH,
                            "score": 0.9,
                            "description": "Transaction size is extremely large",
                        },
                        {
                            "name": "protocol_risk",
                            "level": RiskLevel.MEDIUM,
                            "score": 0.5,
                            "description": "Protocol has been audited but has known issues",
                        },
                        {
                            "name": "slippage_risk",
                            "level": RiskLevel.HIGH,
                            "score": 0.8,
                            "description": "High slippage risk due to low liquidity",
                        },
                    ],
                    "warnings": ["Transaction size is unusually large", "High slippage risk detected"],
                    "recommendations": [
                        "Consider splitting the transaction into smaller amounts",
                        "Set a lower slippage tolerance",
                        "Monitor the transaction closely",
                    ],
                },
                "warnings": ["Transaction size is unusually large", "High slippage risk detected"],
                "recommendations": [
                    "Consider splitting the transaction into smaller amounts",
                    "Set a lower slippage tolerance",
                    "Monitor the transaction closely",
                ],
                "params": {
                    "token_in": "FLR",
                    "token_out": "USDC",
                    "amount_in": 10000000,
                    "slippage": 1.0,
                },
                "simulation_result": {
                    "success": True,
                    "gas_estimate": 250000,
                    "expected_outcome": {
                        "status": "success",
                        "token_transfers": [
                            {"token": "FLR", "amount": -10000000},
                            {"token": "USDC", "amount": 9900000},
                        ],
                    },
                    "warnings": ["Large transaction may cause significant market impact"],
                },
            }
        
        def get_portfolio_info(self):
            # Mock implementation
            return {
                "wallet_address": self.wallet_address,
                "balance": 123.45,
                "tokens": [
                    {"symbol": "FLR", "balance": 1000, "usd_value": 100},
                    {"symbol": "USDC", "balance": 500, "usd_value": 500},
                    {"symbol": "ETH", "balance": 0.25, "usd_value": 750},
                ],
                "positions": [
                    {
                        "protocol": "SparkDEX",
                        "type": "liquidity",
                        "token_pair": "FLR-USDC",
                        "value": 200,
                        "usd_value": 200,
                        "leveraged": False,
                    },
                    {
                        "protocol": "Kinetic",
                        "type": "staking",
                        "token": "FLR",
                        "amount": 500,
                        "usd_value": 50,
                        "leveraged": False,
                    },
                    {
                        "protocol": "Cyclo",
                        "type": "leverage",
                        "token_pair": "ETH-USDC",
                        "position_size": 1000,
                        "leverage": 3,
                        "usd_value": 1000,
                        "leveraged": True,
                    },
                ],
                "risk_assessment": {
                    "overall_risk": {"level": RiskLevel.MEDIUM, "score": 0.5},
                    "risk_factors": [
                        {
                            "name": "protocol_concentration",
                            "level": RiskLevel.MEDIUM,
                            "score": 0.5,
                            "description": "Positions are concentrated in few protocols",
                        },
                        {
                            "name": "leverage_exposure",
                            "level": RiskLevel.MEDIUM,
                            "score": 0.6,
                            "description": "Moderate exposure to leveraged positions",
                        },
                    ],
                    "recommendations": [
                        "Monitor leveraged positions closely",
                        "Consider adding more diversification to your portfolio",
                    ],
                },
            }


def test_process_safe_transaction():
    """Test processing a safe transaction."""
    print("\n\n=== Testing Safe Transaction Processing ===")
    
    # Create a DeFi agent
    agent = DeFiAgent(
        wallet_address="0x1234567890123456789012345678901234567890",
        use_tee=False,  # Disable TEE for testing
        risk_threshold="medium",
    )
    
    # Process a command for a safe transaction
    command = "Swap 100 FLR for USDC on SparkDEX with 0.5% slippage"
    print(f"Command: {command}")
    
    result = agent.process_natural_language_command(command)
    
    # Print the result
    print("\nResult:")
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Action: {result['action']}")
        print(f"Protocol: {result['protocol']}")
        print(f"Transaction Hash: {result['transaction_hash']}")
        
        if 'simulation_result' in result and result['simulation_result']:
            print("\nSimulation Result:")
            print(f"Success: {result['simulation_result']['success']}")
            print(f"Gas Estimate: {result['simulation_result']['gas_estimate']}")
            if 'expected_outcome' in result['simulation_result']:
                print("\nExpected Outcome:")
                print(f"Status: {result['simulation_result']['expected_outcome']['status']}")
                if 'token_transfers' in result['simulation_result']['expected_outcome']:
                    print("Token Transfers:")
                    for transfer in result['simulation_result']['expected_outcome']['token_transfers']:
                        print(f"  {transfer['token']}: {transfer['amount']}")
        
        print("\nRisk Assessment:")
        print(f"Overall Risk Level: {result['risk_assessment']['overall_risk']['level']}")
        print(f"Overall Risk Score: {result['risk_assessment']['overall_risk']['score']}")
        
        print("\nRisk Factors:")
        for factor in result['risk_assessment']['risk_factors']:
            print(f"- {factor['name']}: {factor['level']} ({factor['score']})")
            print(f"  {factor['description']}")
        
        print("\nWarnings:")
        if result['warnings']:
            for warning in result['warnings']:
                print(f"- {warning}")
        else:
            print("No warnings")
        
        print("\nRecommendations:")
        if result['recommendations']:
            for rec in result['recommendations']:
                print(f"- {rec}")
        else:
            print("No recommendations")
    else:
        print("\nErrors:")
        for error in result['errors']:
            print(f"- {error}")


def test_process_risky_transaction():
    """Test processing a risky transaction."""
    print("\n\n=== Testing Risky Transaction Processing ===")
    
    # Create a DeFi agent
    agent = DeFiAgent(
        wallet_address="0x1234567890123456789012345678901234567890",
        use_tee=False,  # Disable TEE for testing
        risk_threshold="medium",
    )
    
    # Process a command for a risky transaction
    command = "Swap 10000000 FLR for USDC on SparkDEX with 1% slippage (high risk)"
    print(f"Command: {command}")
    
    result = agent.process_natural_language_command(command)
    
    # Print the result
    print("\nResult:")
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Action: {result['action']}")
        print(f"Protocol: {result['protocol']}")
        print(f"Transaction Hash: {result['transaction_hash']}")
    else:
        print(f"Action: {result['action']}")
        print(f"Protocol: {result['protocol']}")
        
        print("\nErrors:")
        for error in result['errors']:
            print(f"- {error}")
        
        if 'simulation_result' in result and result['simulation_result']:
            print("\nSimulation Result:")
            print(f"Success: {result['simulation_result']['success']}")
            print(f"Gas Estimate: {result['simulation_result']['gas_estimate']}")
            
            if 'warnings' in result['simulation_result']:
                print("Simulation Warnings:")
                for warning in result['simulation_result']['warnings']:
                    print(f"- {warning}")
        
        print("\nRisk Assessment:")
        if 'risk_assessment' in result and result['risk_assessment']:
            print(f"Overall Risk Level: {result['risk_assessment']['overall_risk']['level']}")
            print(f"Overall Risk Score: {result['risk_assessment']['overall_risk']['score']}")
            
            print("\nRisk Factors:")
            for factor in result['risk_assessment']['risk_factors']:
                print(f"- {factor['name']}: {factor['level']} ({factor['score']})")
                print(f"  {factor['description']}")
        
        print("\nWarnings:")
        if result['warnings']:
            for warning in result['warnings']:
                print(f"- {warning}")
        else:
            print("No warnings")
        
        print("\nRecommendations:")
        if result['recommendations']:
            for rec in result['recommendations']:
                print(f"- {rec}")
        else:
            print("No recommendations")


def test_portfolio_risk_assessment():
    """Test portfolio risk assessment."""
    print("\n\n=== Testing Portfolio Risk Assessment ===")
    
    # Create a DeFi agent
    agent = DeFiAgent(
        wallet_address="0x1234567890123456789012345678901234567890",
        use_tee=False,  # Disable TEE for testing
    )
    
    # Get portfolio information
    print("Getting portfolio information...")
    portfolio = agent.get_portfolio_info()
    
    # Print portfolio information
    print("\nPortfolio Information:")
    print(f"Wallet Address: {portfolio['wallet_address']}")
    print(f"Balance: {portfolio['balance']}")
    
    print("\nTokens:")
    for token in portfolio['tokens']:
        print(f"- {token['symbol']}: {token['balance']} (${token['usd_value']})")
    
    print("\nPositions:")
    for position in portfolio['positions']:
        position_type = position['type']
        protocol = position['protocol']
        usd_value = position['usd_value']
        leveraged = "leveraged" if position.get('leveraged', False) else "non-leveraged"
        
        if position_type == "liquidity":
            token_pair = position.get('token_pair', 'Unknown')
            print(f"- {protocol} - {position_type}: {token_pair} (${usd_value}) - {leveraged}")
        elif position_type == "staking":
            token = position.get('token', 'Unknown')
            print(f"- {protocol} - {position_type}: {token} (${usd_value}) - {leveraged}")
        elif position_type == "leverage":
            token_pair = position.get('token_pair', 'Unknown')
            leverage = position.get('leverage', 'Unknown')
            print(f"- {protocol} - {position_type}: {token_pair} {leverage}x (${usd_value}) - {leveraged}")
        else:
            print(f"- {protocol} - {position_type}: ${usd_value} - {leveraged}")
    
    # Print risk assessment
    print("\nRisk Assessment:")
    if 'risk_assessment' in portfolio:
        print(f"Overall Risk Level: {portfolio['risk_assessment']['overall_risk']['level']}")
        print(f"Overall Risk Score: {portfolio['risk_assessment']['overall_risk']['score']}")
        
        print("\nRisk Factors:")
        for factor in portfolio['risk_assessment']['risk_factors']:
            print(f"- {factor['name']}: {factor['level']} ({factor['score']})")
            print(f"  {factor['description']}")
        
        print("\nRecommendations:")
        if portfolio['risk_assessment']['recommendations']:
            for rec in portfolio['risk_assessment']['recommendations']:
                print(f"- {rec}")
        else:
            print("No recommendations")
    else:
        print("No risk assessment available")


if __name__ == "__main__":
    print("Testing DeFi Agent with Enhanced Transaction Validation and Risk Assessment")
    print(f"Using {'mock classes' if USING_MOCKS else 'real implementations'} for testing")
    
    # Run tests
    test_process_safe_transaction()
    test_process_risky_transaction()
    test_portfolio_risk_assessment()
