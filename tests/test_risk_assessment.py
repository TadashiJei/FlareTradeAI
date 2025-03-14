"""
Test Risk Assessment Module

This module tests the risk assessment functionality for DeFi operations.
"""

import unittest
from unittest.mock import MagicMock, patch

from web3.types import TxParams

from src.flare_ai_defai.blockchain.risk.assessment import (
    DeFiRiskAssessmentService,
    RiskAssessment,
    RiskFactor,
    RiskLevel,
)


class MockProtocol:
    """Mock protocol for testing."""
    
    def __init__(self, name="test_protocol"):
        self.name = name


class MockProtocolFactory:
    """Mock protocol factory for testing."""
    
    def get_protocol(self, protocol_name):
        return MockProtocol(protocol_name)


class TestRiskAssessment(unittest.TestCase):
    """Test the risk assessment functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        self.web3 = MagicMock()
        self.protocol_factory = MockProtocolFactory()
        self.risk_service = DeFiRiskAssessmentService(
            web3=self.web3,
            protocol_factory=self.protocol_factory,
        )
    
    def test_risk_levels(self):
        """Test risk level enumeration."""
        self.assertEqual(RiskLevel.LOW, "low")
        self.assertEqual(RiskLevel.MEDIUM, "medium")
        self.assertEqual(RiskLevel.HIGH, "high")
        self.assertEqual(RiskLevel.CRITICAL, "critical")
    
    def test_risk_factor(self):
        """Test risk factor data class."""
        factor = RiskFactor(
            name="test_factor",
            level=RiskLevel.MEDIUM,
            score=0.5,
            description="Test factor",
        )
        
        self.assertEqual(factor.name, "test_factor")
        self.assertEqual(factor.level, RiskLevel.MEDIUM)
        self.assertEqual(factor.score, 0.5)
        self.assertEqual(factor.description, "Test factor")
    
    def test_risk_assessment(self):
        """Test risk assessment data class."""
        factors = [
            RiskFactor(
                name="factor1",
                level=RiskLevel.LOW,
                score=0.2,
                description="Factor 1",
            ),
            RiskFactor(
                name="factor2",
                level=RiskLevel.MEDIUM,
                score=0.5,
                description="Factor 2",
            ),
        ]
        
        assessment = RiskAssessment(
            overall_risk=RiskLevel.MEDIUM,
            factors=factors,
            warnings=["Warning 1"],
            recommendations=["Recommendation 1"],
        )
        
        self.assertEqual(assessment.overall_risk, RiskLevel.MEDIUM)
        self.assertEqual(len(assessment.factors), 2)
        self.assertEqual(assessment.factors[0].name, "factor1")
        self.assertEqual(assessment.factors[1].name, "factor2")
        self.assertEqual(assessment.warnings, ["Warning 1"])
        self.assertEqual(assessment.recommendations, ["Recommendation 1"])
    
    def test_assess_transaction_swap(self):
        """Test assessing a swap transaction."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 1000000,
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        result = self.risk_service.assess_transaction(
            tx_params=tx_params,
            protocol_name="sparkdex",
            action="swap",
        )
        
        # Check that we got a valid risk assessment
        self.assertIsInstance(result, RiskAssessment)
        self.assertIn(result.overall_risk, [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL])
        
        # Check that we have risk factors
        self.assertGreater(len(result.factors), 0)
        
        # Check that we have a slippage risk factor for swap
        slippage_factors = [f for f in result.factors if f.name == "slippage_risk"]
        self.assertEqual(len(slippage_factors), 1)
        self.assertEqual(slippage_factors[0].level, RiskLevel.MEDIUM)
    
    def test_assess_transaction_large_value(self):
        """Test assessing a transaction with a large value."""
        tx_params = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": 2000000,  # Large value
            "gas": 200000,
            "gasPrice": 20000000000,
            "data": "0x1234567890",
        }
        
        result = self.risk_service.assess_transaction(
            tx_params=tx_params,
            protocol_name="kinetic",
            action="deposit",
        )
        
        # Check that we got a valid risk assessment
        self.assertIsInstance(result, RiskAssessment)
        
        # Check that we have a transaction size risk factor
        size_factors = [f for f in result.factors if f.name == "transaction_size"]
        self.assertEqual(len(size_factors), 1)
        self.assertEqual(size_factors[0].level, RiskLevel.HIGH)
    
    def test_calculate_overall_risk(self):
        """Test calculating overall risk."""
        # Test low risk
        factors_low = [
            RiskFactor(name="f1", level=RiskLevel.LOW, score=0.1, description=""),
            RiskFactor(name="f2", level=RiskLevel.LOW, score=0.2, description=""),
        ]
        self.assertEqual(
            self.risk_service._calculate_overall_risk(factors_low),
            RiskLevel.LOW,
        )
        
        # Test medium risk
        factors_medium = [
            RiskFactor(name="f1", level=RiskLevel.MEDIUM, score=0.4, description=""),
            RiskFactor(name="f2", level=RiskLevel.MEDIUM, score=0.5, description=""),
        ]
        self.assertEqual(
            self.risk_service._calculate_overall_risk(factors_medium),
            RiskLevel.MEDIUM,
        )
        
        # Test high risk
        factors_high = [
            RiskFactor(name="f1", level=RiskLevel.HIGH, score=0.7, description=""),
            RiskFactor(name="f2", level=RiskLevel.HIGH, score=0.8, description=""),
        ]
        self.assertEqual(
            self.risk_service._calculate_overall_risk(factors_high),
            RiskLevel.HIGH,
        )
        
        # Test critical risk
        factors_critical = [
            RiskFactor(name="f1", level=RiskLevel.CRITICAL, score=0.9, description=""),
            RiskFactor(name="f2", level=RiskLevel.CRITICAL, score=1.0, description=""),
        ]
        self.assertEqual(
            self.risk_service._calculate_overall_risk(factors_critical),
            RiskLevel.CRITICAL,
        )
        
        # Test mixed risk levels
        factors_mixed = [
            RiskFactor(name="f1", level=RiskLevel.LOW, score=0.2, description=""),
            RiskFactor(name="f2", level=RiskLevel.HIGH, score=0.8, description=""),
        ]
        self.assertEqual(
            self.risk_service._calculate_overall_risk(factors_mixed),
            RiskLevel.MEDIUM,  # Average score is 0.5
        )
        
        # Test empty factors
        self.assertEqual(
            self.risk_service._calculate_overall_risk([]),
            RiskLevel.LOW,  # Default to low risk
        )


if __name__ == "__main__":
    unittest.main()
