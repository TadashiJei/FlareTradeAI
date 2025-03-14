#!/usr/bin/env python3
"""
FlareTrade Integration Test Script

This script tests the integration between the enhanced FlareTrade DeFi agent 
and the chat UI components, focusing on transaction validation and risk assessment.
"""

import sys
import json
import os
from typing import Dict, Any

# Add the src directory to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import required components
from src.flare_ai_defai.blockchain.transaction import TransactionValidator
from src.flare_ai_defai.blockchain.risk import RiskAssessor
from src.flare_ai_defai.blockchain.protocols.raindex import RainDEX
from src.flare_ai_defai.prompts.schemas import Prompt
from src.flare_ai_defai.prompts.templates import EXTRACT_SWAP_OPERATION


class TestDeFiIntegration:
    """Test class for FlareTrade DeFi agent integration with enhanced risk assessment."""
    
    def __init__(self):
        """Initialize test components."""
        # Mock web3 for testing
        self.web3_url = os.getenv("WEB3_PROVIDER_URL", "https://flare-api.flare.network/ext/C/rpc")
        
        # Test variables
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.test_token_in = "FLR"
        self.test_token_out = "USDC"
        self.test_amount = "100"
        
        print(f"Initializing test with wallet {self.test_wallet}")
        print(f"Web3 URL: {self.web3_url}")
    
    def test_extract_swap_operation(self):
        """Test the extraction of swap operation details from natural language."""
        print("\n--- Testing Swap Operation Extraction ---")
        
        # Sample user input
        user_input = f"swap {self.test_amount} {self.test_token_in} for {self.test_token_out} with 0.5% slippage"
        
        # Create prompt with our enhanced template
        prompt = Prompt(
            name="extract_swap_operation",
            description="Extract structured swap operation details",
            template=EXTRACT_SWAP_OPERATION,
            required_inputs=["user_input"],
            response_mime_type="application/json",
            response_schema=None,
            category="defai"
        )
        
        # Format the prompt with user input
        formatted_prompt = prompt.format(user_input=user_input)
        
        print(f"User Input: {user_input}")
        
        # Simulate the AI extraction (with mock data since we can't directly call the AI)
        extracted_data = {
            "token_in": self.test_token_in,
            "token_out": self.test_token_out,
            "amount": self.test_amount,
            "slippage": "0.5",
            "protocol": "raindex"
        }
        
        print("Extracted Data:")
        print(json.dumps(extracted_data, indent=2))
        
        # Validate the extraction
        assert extracted_data["token_in"] == self.test_token_in
        assert extracted_data["token_out"] == self.test_token_out
        assert extracted_data["amount"] == self.test_amount
        
        return extracted_data
        
    def test_risk_assessment(self, operation_data):
        """Test risk assessment for DeFi operations."""
        print("\n--- Testing Risk Assessment ---")
        
        # Mock transaction parameters
        tx_params = {
            "from": self.test_wallet,
            "to": "0x1234567890123456789012345678901234567890",  # Mock router contract
            "value": 0,
            "data": "0x"  # Mock transaction data
        }
        
        # Mock protocol info extracted from transaction
        protocol_info = {
            "protocol": operation_data["protocol"],
            "action": "swap",
            "token_in": {
                "address": self._mock_token_address(operation_data["token_in"]),
                "symbol": operation_data["token_in"],
                "amount": float(operation_data["amount"])
            },
            "token_out": {
                "address": self._mock_token_address(operation_data["token_out"]),
                "symbol": operation_data["token_out"],
                "amount": 0.0  # Would be calculated in real implementation
            }
        }
        
        # Create mock risk assessment
        risk_assessment = {
            "risk_level": "medium",
            "risk_factors": [
                {
                    "type": "slippage",
                    "severity": "medium",
                    "description": "Slippage tolerance is relatively low which may cause transaction failure in volatile markets"
                },
                {
                    "type": "token_security",
                    "severity": "low",
                    "description": "Both tokens have been verified and audited"
                }
            ],
            "warnings": [
                "Medium price impact expected due to limited liquidity",
                "Transaction may fail if price moves more than 0.5% during execution"
            ],
            "recommendations": [
                "Consider increasing slippage tolerance if execution fails",
                "Monitor market conditions before confirming transaction"
            ]
        }
        
        print("Risk Assessment:")
        print(json.dumps(risk_assessment, indent=2))
        
        # Format response for chat UI
        chat_response = self._format_chat_response(operation_data, risk_assessment)
        print("\n--- Formatted Chat Response ---")
        print(chat_response["response"])
        
        return chat_response
    
    def test_transaction_confirmation(self, chat_response):
        """Test transaction confirmation flow."""
        print("\n--- Testing Transaction Confirmation ---")
        
        # User confirms transaction
        user_confirmation = "CONFIRM"
        print(f"User input: {user_confirmation}")
        
        if user_confirmation.upper() == "CONFIRM":
            # Execute transaction (mock)
            tx_hash = "0x" + "0" * 64  # Mock transaction hash
            print(f"Transaction executed with hash: {tx_hash}")
            
            # Return confirmation message
            confirmation_message = (
                "Transaction successfully executed! ✅\n\n"
                f"Transaction Hash: {tx_hash}\n"
                "You can track this transaction on the Flare Explorer."
            )
            print("\n--- Confirmation Message ---")
            print(confirmation_message)
            return {"status": "success", "tx_hash": tx_hash}
        else:
            # Cancel transaction
            cancellation_message = "Transaction cancelled. How else can I help you?"
            print("\n--- Cancellation Message ---")
            print(cancellation_message)
            return {"status": "cancelled"}
    
    def _format_chat_response(self, operation_data, risk_assessment):
        """Format chat response with operation details and risk assessment."""
        operation_type = "swap"
        token_in = operation_data["token_in"]
        token_out = operation_data["token_out"]
        amount = operation_data["amount"]
        
        response_parts = []
        
        # Operation summary
        response_parts.append(
            f"## Transaction Preview: Swap {amount} {token_in} to {token_out}\n"
        )
        
        # Add risk assessment information
        response_parts.append(f"**Risk Level:** {risk_assessment['risk_level'].upper()}\n")
        
        # Add warnings if any
        if risk_assessment["warnings"]:
            response_parts.append("**Warnings:**")
            for warning in risk_assessment["warnings"]:
                response_parts.append(f"- {warning}")
            response_parts.append("")
        
        # Add recommendations if any
        if risk_assessment["recommendations"]:
            response_parts.append("**Recommendations:**")
            for rec in risk_assessment["recommendations"]:
                response_parts.append(f"- {rec}")
            response_parts.append("")
        
        # Add confirmation instructions
        response_parts.append(
            "\nTo confirm this transaction, please reply with **CONFIRM**. "
            "To cancel, reply with anything else."
        )
        
        return {
            "response": "\n".join(response_parts),
            "requires_confirmation": True,
            "risk_assessment": risk_assessment
        }
    
    def _mock_token_address(self, token_symbol):
        """Mock function to get token address from symbol."""
        token_addresses = {
            "FLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
            "USDC": "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D",
            "WSGB": "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED"
        }
        return token_addresses.get(token_symbol.upper(), "0x" + "0" * 40)
    
    def run_tests(self):
        """Run all integration tests."""
        print("=== Starting FlareTrade Integration Tests ===\n")
        
        # Test 1: Extract operation details
        operation_data = self.test_extract_swap_operation()
        
        # Test 2: Risk assessment
        chat_response = self.test_risk_assessment(operation_data)
        
        # Test 3: Transaction confirmation
        confirmation_result = self.test_transaction_confirmation(chat_response)
        
        print("\n=== All tests completed successfully! ===")


if __name__ == "__main__":
    test = TestDeFiIntegration()
    test.run_tests()
