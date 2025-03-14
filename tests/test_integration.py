"""
Integration Tests for End-to-End Workflows

This module contains integration tests that verify the complete workflows
from user command to blockchain transaction.
"""

import unittest
from unittest.mock import Mock, patch

from flare_ai_defai.blockchain.protocols import ProtocolFactory
from flare_ai_defai.blockchain.risk import DeFiRiskAssessmentService
from flare_ai_defai.blockchain.transaction import TransactionValidator
from flare_ai_defai.blockchain.wallet import SecureWalletManager


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.web3 = Mock()
        self.vtpm = Mock()
        self.address = "0x1234567890123456789012345678901234567890"

        self.factory = ProtocolFactory(self.web3, self.address)
        self.risk_service = DeFiRiskAssessmentService()
        self.transaction_validator = TransactionValidator(self.web3)
        self.wallet_manager = SecureWalletManager(self.web3, self.vtpm)

    @patch('web3.eth.Eth.send_raw_transaction')
    def test_swap_workflow(self, mock_send):
        # Setup
        sparkdex = self.factory.get_protocol("sparkdex")
        tx_params = sparkdex.prepare_swap_transaction(
            token_in_address="0x1",
            token_out_address="0x2",
            amount_in=100,
            min_amount_out=90,
            deadline=1234567890,
        )

        # Validate transaction
        validation = self.transaction_validator.validate_transaction(tx_params)
        self.assertTrue(validation["valid"])

        # Assess risk
        risk_assessment = self.risk_service.assess_transaction(tx_params)
        self.assertEqual(risk_assessment.overall_risk, "low")

        # Sign and send transaction
        signed_tx = self.wallet_manager.sign_transaction(tx_params)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx)

        # Verify transaction was sent
        mock_send.assert_called_once()


if __name__ == '__main__':
    unittest.main()
