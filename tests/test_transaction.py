"""
Test Transaction Module

This module tests the transaction simulation and validation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from web3.types import TxParams

from flare_ai_defai.blockchain.risk.assessment import (
    DeFiRiskAssessmentService,
    RiskAssessment,
    RiskFactor,
    RiskLevel,
)
from flare_ai_defai.blockchain.transaction import (
    TransactionSimulator,
    TransactionValidator,
)


class MockProtocolFactory:
    """Mock protocol factory for testing."""
    
    def get_protocol(self, protocol_name):
        return MagicMock(name=protocol_name)


class TestTransactionSimulator(unittest.TestCase):
    """Test the transaction simulator."""
    
    def setUp(self):
        """Set up the test environment."""
        self.web3 = MagicMock()
        self.web3.eth.estimate_gas.return_value = 100000
        self.simulator = TransactionSimulator(web3=self.web3)
    
    def test_simulate_transaction_success(self):
        """Test successful transaction simulation."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        result = self.simulator.simulate_transaction(tx_params)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["gas_estimate"], 100000)
        self.assertEqual(len(result["warnings"]), 0)
        self.assertEqual(len(result["errors"]), 0)
        self.assertIn("expected_outcome", result)
        self.assertIn("status", result["expected_outcome"])
    
    def test_simulate_transaction_failure(self):
        """Test failed transaction simulation."""
        # Set up web3 to raise an exception
        self.web3.eth.estimate_gas.side_effect = Exception("Simulation failed")
        
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        result = self.simulator.simulate_transaction(tx_params)
        
        self.assertFalse(result["success"])
        self.assertEqual(result["gas_estimate"], 0)
        self.assertEqual(len(result["warnings"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0], "Simulation failed")
    
    def test_simulate_outcome(self):
        """Test transaction outcome simulation."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        outcome = self.simulator._simulate_outcome(tx_params)
        
        self.assertIn("status", outcome)
        self.assertIn("token_transfers", outcome)
        self.assertIn("balance_changes", outcome)
        self.assertIn("events", outcome)


class TestTransactionValidator(unittest.TestCase):
    """Test the transaction validator."""
    
    def setUp(self):
        """Set up the test environment."""
        self.web3 = MagicMock()
        self.protocol_factory = MockProtocolFactory()
        self.risk_assessment = MagicMock(spec=DeFiRiskAssessmentService)
        self.simulator = MagicMock(spec=TransactionSimulator)
        
        # Set up simulator mock
        self.simulator.simulate_transaction.return_value = {
            "success": True,
            "gas_estimate": 100000,
            "expected_outcome": {"status": "success"},
            "warnings": [],
            "errors": [],
        }
        
        self.validator = TransactionValidator(
            risk_assessment=self.risk_assessment,
            risk_threshold="medium",
            simulator=self.simulator,
        )
    
    def test_validate_transaction_success(self):
        """Test successful transaction validation."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        # Create a risk assessment with low risk
        risk_assessment = {
            "overall_risk": {
                "level": RiskLevel.LOW,
                "score": 0.2,
            },
            "risk_factors": [],
            "warnings": [],
            "recommendations": [],
        }
        
        result = self.validator.validate_transaction(
            tx_params=tx_params,
            risk_assessment=risk_assessment,
            simulate=True,
        )
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["warnings"]), 0)
        self.assertEqual(len(result["errors"]), 0)
    
    def test_validate_transaction_high_risk(self):
        """Test transaction validation with high risk."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        # Create a risk assessment with high risk
        risk_assessment = {
            "overall_risk": {
                "level": RiskLevel.HIGH,
                "score": 0.8,
            },
            "risk_factors": [],
            "warnings": ["High risk transaction"],
            "recommendations": [],
        }
        
        result = self.validator.validate_transaction(
            tx_params=tx_params,
            risk_assessment=risk_assessment,
            simulate=True,
        )
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(result["warnings"][0], "High risk transaction")
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Risk level", result["errors"][0])
    
    def test_validate_transaction_simulation_failure(self):
        """Test transaction validation with simulation failure."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        # Set up simulator to fail
        self.simulator.simulate_transaction.return_value = {
            "success": False,
            "gas_estimate": 0,
            "expected_outcome": {},
            "warnings": [],
            "errors": ["Simulation failed"],
        }
        
        # Create a risk assessment with low risk
        risk_assessment = {
            "overall_risk": {
                "level": RiskLevel.LOW,
                "score": 0.2,
            },
            "risk_factors": [],
            "warnings": [],
            "recommendations": [],
        }
        
        result = self.validator.validate_transaction(
            tx_params=tx_params,
            risk_assessment=risk_assessment,
            simulate=True,
        )
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0], "Simulation failed")
    
    def test_validate_transaction_parameters(self):
        """Test transaction parameter validation."""
        # Missing 'from' address
        tx_params_missing_from = {
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
        }
        
        result = self.validator._validate_transaction_parameters(tx_params_missing_from)
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0], "Missing 'from' address")
        
        # Missing 'to' address
        tx_params_missing_to = {
            "from": "0x1234567890123456789012345678901234567890",
            "value": 1000000,
            "gas": 200000,
        }
        
        result = self.validator._validate_transaction_parameters(tx_params_missing_to)
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0], "Missing 'to' address")
        
        # Gas too low
        tx_params_low_gas = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 20000,  # Too low
        }
        
        result = self.validator._validate_transaction_parameters(tx_params_low_gas)
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0], "Gas limit too low")
        
        # Valid parameters
        tx_params_valid = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
        }
        
        result = self.validator._validate_transaction_parameters(tx_params_valid)
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
    
    def test_is_risk_above_threshold(self):
        """Test risk threshold checking."""
        # Low risk, medium threshold
        self.assertFalse(
            self.validator._is_risk_above_threshold(RiskLevel.LOW, "medium")
        )
        
        # Medium risk, medium threshold
        self.assertFalse(
            self.validator._is_risk_above_threshold(RiskLevel.MEDIUM, "medium")
        )
        
        # High risk, medium threshold
        self.assertTrue(
            self.validator._is_risk_above_threshold(RiskLevel.HIGH, "medium")
        )
        
        # Critical risk, medium threshold
        self.assertTrue(
            self.validator._is_risk_above_threshold(RiskLevel.CRITICAL, "medium")
        )
        
        # High risk, high threshold
        self.assertFalse(
            self.validator._is_risk_above_threshold(RiskLevel.HIGH, "high")
        )
        
        # Critical risk, high threshold
        self.assertTrue(
            self.validator._is_risk_above_threshold(RiskLevel.CRITICAL, "high")
        )


if __name__ == "__main__":
    unittest.main()
