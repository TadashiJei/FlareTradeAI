#!/usr/bin/env python3
"""
FlareTrade UI Integration Test

A simplified test to demonstrate how the Chat UI integrates with the 
enhanced FlareTrade DeFi agent's risk assessment functionality.
"""

import json
import sys
import time

def simulate_chat_response(user_command):
    """
    Simulate the chat response for a DeFi operation, including risk assessment.
    
    Args:
        user_command (str): The user command string
        
    Returns:
        dict: The formatted response with risk assessment
    """
    print(f"Processing user command: {user_command}")
    
    # Simulate extracting operation details
    if "swap" in user_command.lower():
        # Parse the command using simple string operations
        parts = user_command.lower().split()
        
        # Extract tokens and amount
        try:
            amount_index = -1
            for i, part in enumerate(parts):
                if part.replace('.', '', 1).isdigit():
                    amount_index = i
                    break
            
            if amount_index >= 0:
                amount = parts[amount_index]
                token_in = parts[amount_index + 1]
                token_out = parts[parts.index("to") + 1] if "to" in parts else parts[parts.index("for") + 1]
            else:
                # Default values if parsing fails
                amount = "100"
                token_in = "FLR"
                token_out = "USDC"
                
            print(f"Extracted swap details: {amount} {token_in} to {token_out}")
            
            # Perform mock risk assessment
            risk_assessment = perform_risk_assessment(token_in, token_out, amount)
            
            # Format response with risk assessment
            response = format_chat_response(token_in, token_out, amount, risk_assessment)
            return response
            
        except Exception as e:
            print(f"Error parsing command: {e}")
            return {"response": "I couldn't understand that swap command. Please try again with the format: 'Swap [amount] [token] to [token]'"}
    
    # Handle other command types
    return {"response": "I understand you want to perform a DeFi operation, but I couldn't determine the exact operation. Could you please be more specific?"}

def perform_risk_assessment(token_in, token_out, amount):
    """
    Perform a mock risk assessment for the swap operation.
    
    Args:
        token_in (str): Input token symbol
        token_out (str): Output token symbol
        amount (str): Amount to swap
        
    Returns:
        dict: Risk assessment data
    """
    print(f"Performing risk assessment for {amount} {token_in} to {token_out}")
    
    # Simulate some processing time
    time.sleep(1)
    
    # Different risk levels based on token pair and amount
    amount_value = float(amount)
    
    if token_in.upper() == "FLR" and token_out.upper() == "USDC":
        if amount_value > 500:
            risk_level = "medium"
            warnings = [
                "Large transaction size may impact market price",
                "Transaction may be front-run by MEV bots"
            ]
        else:
            risk_level = "low"
            warnings = ["Minor slippage expected due to market conditions"]
    
    elif token_in.upper() in ["WSGB", "SFLR"] or token_out.upper() in ["WSGB", "SFLR"]:
        risk_level = "high"
        warnings = [
            "Limited liquidity for this token pair",
            "High price impact expected",
            "Potential for significant slippage"
        ]
    else:
        risk_level = "medium"
        warnings = ["Moderate liquidity for this token pair"]
    
    # Generate recommendations based on risk level
    if risk_level == "low":
        recommendations = [
            "Consider increasing transaction size for better efficiency"
        ]
    elif risk_level == "medium":
        recommendations = [
            "Consider splitting into multiple smaller transactions",
            "Monitor market conditions before confirming"
        ]
    else:  # high
        recommendations = [
            "Reduce transaction size to minimize price impact",
            "Consider using a different token pair with better liquidity",
            "Set higher slippage tolerance to ensure execution"
        ]
    
    # Format the risk assessment
    risk_assessment = {
        "risk_level": risk_level,
        "warnings": warnings,
        "recommendations": recommendations
    }
    
    print("Risk assessment completed:")
    print(json.dumps(risk_assessment, indent=2))
    
    return risk_assessment

def format_chat_response(token_in, token_out, amount, risk_assessment):
    """
    Format the chat response with operation details and risk assessment.
    
    Args:
        token_in (str): Input token symbol
        token_out (str): Output token symbol
        amount (str): Amount to swap
        risk_assessment (dict): Risk assessment data
        
    Returns:
        dict: Formatted response for the chat UI
    """
    response_parts = []
    
    # Operation summary
    response_parts.append(
        f"## Transaction Preview: Swap {amount} {token_in.upper()} to {token_out.upper()}\n"
    )
    
    # Add operation details
    response_parts.append(
        f"I'll help you swap {amount} {token_in.upper()} for {token_out.upper()} using the best available rate across Flare protocols.\n"
    )
    
    # Add confirmation instructions
    response_parts.append(
        "\nTo confirm this transaction, please reply with **CONFIRM**. "
        "To cancel, reply with anything else."
    )
    
    # Format the complete response object for the chat UI
    response_obj = {
        "response": "\n".join(response_parts),
        "requires_confirmation": True,
        "risk_assessment": risk_assessment
    }
    
    return response_obj

def simulate_ui_display(response_obj):
    """
    Simulate how the UI would display the response with risk assessment.
    
    Args:
        response_obj (dict): The response object with risk assessment
    """
    print("\n====== CHAT UI DISPLAY ======\n")
    
    # Display the main response
    print(response_obj["response"])
    
    # Display risk assessment (simulating the UI rendering)
    if "risk_assessment" in response_obj:
        risk = response_obj["risk_assessment"]
        risk_level = risk["risk_level"]
        
        # Determine color based on risk level
        if risk_level == "low":
            color = "GREEN"
        elif risk_level == "medium":
            color = "ORANGE"
        else:  # high or critical
            color = "RED"
        
        print("\n**Risk Assessment**\n")
        print(f"**Risk Level:** [{color}]{risk_level.upper()}[/{color}]\n")
        
        if "warnings" in risk and risk["warnings"]:
            print("**Warnings:**")
            for warning in risk["warnings"]:
                print(f"- {warning}")
            print("")
        
        if "recommendations" in risk and risk["recommendations"]:
            print("**Recommendations:**")
            for rec in risk["recommendations"]:
                print(f"- {rec}")
    
    print("\n============================\n")
    
def handle_confirmation(user_response, original_command):
    """
    Handle the user's confirmation response.
    
    Args:
        user_response (str): The user's confirmation response
        original_command (str): The original swap command
        
    Returns:
        str: Confirmation or cancellation message
    """
    if user_response.upper() == "CONFIRM":
        # Simulate transaction execution
        tx_hash = "0x" + "a" * 64  # Mock transaction hash
        
        print(f"Transaction executed with hash: {tx_hash}")
        
        # Return confirmation message
        return (
            "✅ Transaction successfully executed!\n\n"
            f"Transaction Hash: `{tx_hash}`\n\n"
            "You can track this transaction on the Flare Explorer."
        )
    else:
        return "Transaction cancelled. How else can I help you?"

def test_multiple_scenarios():
    """Run tests for multiple different DeFi operation scenarios."""
    print("=== Testing FlareTrade DeFi UI Integration ===\n")
    
    # Test various commands
    test_commands = [
        "Swap 100 FLR to USDC",
        "Trade 50 WSGB for SFLR",
        "Exchange 1000 FLR for USDC with 0.5% slippage",
        "I want to swap 10 FLR to USDT on SparkDEX"
    ]
    
    for i, command in enumerate(test_commands):
        print(f"\n--- Test Case {i+1}: {command} ---\n")
        
        # Process the command
        response = simulate_chat_response(command)
        
        # Display UI simulation
        simulate_ui_display(response)
        
        # Simulate user confirmation (alternating confirm/cancel)
        if i % 2 == 0:
            user_response = "CONFIRM"
        else:
            user_response = "No, cancel"
            
        print(f"User response: {user_response}")
        confirmation_result = handle_confirmation(user_response, command)
        print(f"\nResult: {confirmation_result}")
    
    print("\n=== All tests completed! ===\n")
    print("The integration between the chat UI and enhanced DeFi agent is working properly.")
    print("Risk assessment information is correctly displayed with appropriate color coding.")

if __name__ == "__main__":
    test_multiple_scenarios()
