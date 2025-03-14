"""
Test script for transaction validation and risk assessment.

This script demonstrates the integration of risk assessment and transaction validation
in the FlareTrade DeFi agent.
"""

import sys
import os
from typing import Dict, Any
from enum import Enum

# Define risk level enum for testing
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Mock classes for testing
class TransactionSimulator:
    """Mock transaction simulator for testing."""
    
    def __init__(self, web3=None):
        self.web3 = web3
    
    def simulate_transaction(self, tx_params):
        """Simulate a transaction."""
        return {
            "success": True,
            "gas_estimate": 100000,
            "expected_outcome": {
                "status": "success",
                "token_transfers": [],
                "balance_changes": [],
                "events": [],
            },
            "warnings": [],
            "errors": [],
        }
    
    def _simulate_outcome(self, tx_params):
        """Simulate the outcome of a transaction."""
        return {
            "status": "success",
            "token_transfers": [],
            "balance_changes": [],
            "events": [],
        }


class TransactionValidator:
    """Mock transaction validator for testing."""
    
    def __init__(self, risk_assessment=None, risk_threshold="medium", simulator=None):
        self.risk_assessment = risk_assessment
        self.risk_threshold = risk_threshold
        self.simulator = simulator or TransactionSimulator()
    
    def validate_transaction(self, tx_params, risk_assessment=None, simulate=True):
        """Validate a transaction."""
        warnings = []
        errors = []
        
        # Simulate the transaction if requested
        simulation = None
        if simulate:
            simulation = self.simulator.simulate_transaction(tx_params)
            if not simulation["success"]:
                errors.extend(simulation["errors"])
            warnings.extend(simulation["warnings"])
        
        # Use the provided risk assessment
        if risk_assessment:
            # Check if the transaction exceeds the risk threshold
            is_risky = self._is_risk_above_threshold(
                risk_assessment["overall_risk"]["level"], 
                self.risk_threshold
            )
            
            if is_risky:
                errors.append(f"Risk level {risk_assessment['overall_risk']['level']} exceeds threshold {self.risk_threshold}")
            
            # Add risk warnings
            if "warnings" in risk_assessment:
                warnings.extend(risk_assessment["warnings"])
        
        # Validate basic transaction parameters
        param_validation = self._validate_transaction_parameters(tx_params)
        if not param_validation["valid"]:
            errors.extend(param_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "risk_assessment": risk_assessment,
            "simulation": simulation,
            "warnings": warnings,
            "errors": errors,
        }
    
    def _is_risk_above_threshold(self, risk_level, threshold):
        """Check if a risk level exceeds the threshold."""
        risk_order = ["low", "medium", "high", "critical"]
        risk_index = risk_order.index(risk_level)
        threshold_index = risk_order.index(threshold)
        
        return risk_index > threshold_index
    
    def _validate_transaction_parameters(self, tx_params):
        """Validate transaction parameters."""
        errors = []
        
        # Check required parameters
        if "from" not in tx_params:
            errors.append("Missing 'from' address")
        
        if "to" not in tx_params:
            errors.append("Missing 'to' address")
        
        # Check for sufficient gas
        if "gas" in tx_params and tx_params["gas"] < 21000:
            errors.append("Gas limit too low")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }


def test_transaction_validation():
    """Test transaction validation with risk assessment."""
    print("Testing transaction validation with risk assessment...")
    
    # Create a sample transaction
    tx_params = {
        "from": "0x1234567890123456789012345678901234567890",
        "to": "0x0987654321098765432109876543210987654321",
        "value": 1000000,
        "gas": 200000,
        "gasPrice": 20000000000,
        "data": "0x1234567890",
    }
    
    # Create a transaction simulator
    simulator = TransactionSimulator()
    
    # Create a transaction validator
    validator = TransactionValidator(
        risk_threshold="medium",
        simulator=simulator,
    )
    
    # Create a sample risk assessment
    risk_assessment = {
        "overall_risk": {
            "level": RiskLevel.LOW,
            "score": 0.2,
        },
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
        "recommendations": [
            "Consider setting a slippage limit to protect against price movements",
        ],
    }
    
    # Validate the transaction
    result = validator.validate_transaction(
        tx_params=tx_params,
        risk_assessment=risk_assessment,
        simulate=True,
    )
    
    # Print the validation result
    print("\nTransaction Validation Result:")
    print(f"Valid: {result['valid']}")
    
    if "simulation" in result and result["simulation"]:
        print("\nSimulation Result:")
        print(f"Success: {result['simulation']['success']}")
        print(f"Gas Estimate: {result['simulation']['gas_estimate']}")
    
    print("\nRisk Assessment:")
    print(f"Overall Risk Level: {risk_assessment['overall_risk']['level']}")
    print(f"Overall Risk Score: {risk_assessment['overall_risk']['score']}")
    
    print("\nRisk Factors:")
    for factor in risk_assessment["risk_factors"]:
        print(f"- {factor['name']}: {factor['level']} ({factor['score']})")
        print(f"  {factor['description']}")
    
    print("\nWarnings:")
    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"- {warning}")
    else:
        print("No warnings")
    
    print("\nErrors:")
    if result["errors"]:
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("No errors")
    
    print("\nRecommendations:")
    if "recommendations" in risk_assessment:
        for rec in risk_assessment["recommendations"]:
            print(f"- {rec}")
    else:
        print("No recommendations")


def test_high_risk_transaction():
    """Test transaction validation with high risk assessment."""
    print("\n\nTesting transaction validation with high risk assessment...")
    
    # Create a sample transaction with high value
    tx_params = {
        "from": "0x1234567890123456789012345678901234567890",
        "to": "0x0987654321098765432109876543210987654321",
        "value": 1000000000000,  # Very high value
        "gas": 200000,
        "gasPrice": 20000000000,
        "data": "0x1234567890",
    }
    
    # Create a transaction simulator
    simulator = TransactionSimulator()
    
    # Create a transaction validator
    validator = TransactionValidator(
        risk_threshold="medium",
        simulator=simulator,
    )
    
    # Create a sample high risk assessment
    risk_assessment = {
        "overall_risk": {
            "level": RiskLevel.HIGH,
            "score": 0.8,
        },
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
        "warnings": [
            "Transaction size is unusually large",
            "High slippage risk detected",
        ],
        "recommendations": [
            "Consider splitting the transaction into smaller amounts",
            "Set a lower slippage tolerance",
            "Monitor the transaction closely",
        ],
    }
    
    # Validate the transaction
    result = validator.validate_transaction(
        tx_params=tx_params,
        risk_assessment=risk_assessment,
        simulate=True,
    )
    
    # Print the validation result
    print("\nTransaction Validation Result:")
    print(f"Valid: {result['valid']}")
    
    if "simulation" in result and result["simulation"]:
        print("\nSimulation Result:")
        print(f"Success: {result['simulation']['success']}")
        print(f"Gas Estimate: {result['simulation']['gas_estimate']}")
    
    print("\nRisk Assessment:")
    print(f"Overall Risk Level: {risk_assessment['overall_risk']['level']}")
    print(f"Overall Risk Score: {risk_assessment['overall_risk']['score']}")
    
    print("\nRisk Factors:")
    for factor in risk_assessment["risk_factors"]:
        print(f"- {factor['name']}: {factor['level']} ({factor['score']})")
        print(f"  {factor['description']}")
    
    print("\nWarnings:")
    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"- {warning}")
    else:
        print("No warnings")
    
    print("\nErrors:")
    if result["errors"]:
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("No errors")
    
    print("\nRecommendations:")
    if "recommendations" in risk_assessment:
        for rec in risk_assessment["recommendations"]:
            print(f"- {rec}")
    else:
        print("No recommendations")


if __name__ == "__main__":
    test_transaction_validation()
    test_high_risk_transaction()
