"""
Tests for the DeFi natural language processing module.
"""

import unittest
from unittest.mock import MagicMock, patch

from flare_ai_defai.nlp.defi_parser import DeFiCommandParser, DeFiCommandProcessor, ParsedDeFiCommand


class TestDeFiCommandParser(unittest.TestCase):
    """Test cases for the DeFiCommandParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = DeFiCommandParser()

    def test_parse_swap_command(self):
        """Test parsing a swap command."""
        command = "Swap 10 ETH to USDC on SparkDEX with 0.5% slippage"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "swap")
        self.assertEqual(parsed.protocol, "sparkdex")
        self.assertEqual(parsed.params.get("token_in"), "ETH")
        self.assertEqual(parsed.params.get("token_out"), "USDC")
        self.assertEqual(parsed.params.get("amount_in"), "10")
        self.assertEqual(parsed.params.get("slippage"), "0.5")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_deposit_command(self):
        """Test parsing a deposit command."""
        command = "Deposit 100 USDC into Kinetic"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "deposit")
        self.assertEqual(parsed.protocol, "kinetic")
        self.assertEqual(parsed.params.get("token"), "USDC")
        self.assertEqual(parsed.params.get("amount"), "100")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_withdraw_command(self):
        """Test parsing a withdraw command."""
        command = "Withdraw 50 USDC from Kinetic"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "withdraw")
        self.assertEqual(parsed.protocol, "kinetic")
        self.assertEqual(parsed.params.get("token"), "USDC")
        self.assertEqual(parsed.params.get("amount"), "50")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_stake_command(self):
        """Test parsing a stake command."""
        command = "Stake 10 FLR on Cyclo"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "stake")
        self.assertEqual(parsed.protocol, "cyclo")
        self.assertEqual(parsed.params.get("token"), "FLR")
        self.assertEqual(parsed.params.get("amount"), "10")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_unstake_command(self):
        """Test parsing an unstake command."""
        command = "Unstake 5 FLR from Cyclo"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "unstake")
        self.assertEqual(parsed.protocol, "cyclo")
        self.assertEqual(parsed.params.get("token"), "FLR")
        self.assertEqual(parsed.params.get("amount"), "5")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_claim_rewards_command(self):
        """Test parsing a claim rewards command."""
        command = "Claim rewards from Cyclo"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "claim_rewards")
        self.assertEqual(parsed.protocol, "cyclo")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_borrow_command(self):
        """Test parsing a borrow command."""
        command = "Borrow 20 ETH from Kinetic"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "borrow")
        self.assertEqual(parsed.protocol, "kinetic")
        self.assertEqual(parsed.params.get("token"), "ETH")
        self.assertEqual(parsed.params.get("amount"), "20")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_repay_command(self):
        """Test parsing a repay command."""
        command = "Repay 15 ETH loan on Kinetic"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "repay")
        self.assertEqual(parsed.protocol, "kinetic")
        self.assertEqual(parsed.params.get("token"), "ETH")
        self.assertEqual(parsed.params.get("amount"), "15")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_unknown_action(self):
        """Test parsing a command with an unknown action."""
        command = "Do something with 10 ETH"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "unknown")
        self.assertEqual(parsed.raw_command, command)

    def test_parse_no_protocol(self):
        """Test parsing a command with no protocol specified."""
        command = "Swap 10 ETH to USDC"
        parsed = self.parser.parse_command(command)
        
        self.assertEqual(parsed.action, "swap")
        self.assertIsNone(parsed.protocol)
        self.assertEqual(parsed.params.get("token_in"), "ETH")
        self.assertEqual(parsed.params.get("token_out"), "USDC")
        self.assertEqual(parsed.params.get("amount_in"), "10")
        self.assertEqual(parsed.raw_command, command)


class TestDeFiCommandProcessor(unittest.TestCase):
    """Test cases for the DeFiCommandProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.protocol_factory = MagicMock()
        self.processor = DeFiCommandProcessor(self.protocol_factory)
        
        # Mock protocol
        self.mock_protocol = MagicMock()
        self.protocol_factory.get_protocol.return_value = self.mock_protocol

    def test_process_swap_command(self):
        """Test processing a swap command."""
        # Mock protocol methods
        self.mock_protocol.prepare_swap_transaction.return_value = {
            "to": "0x1234",
            "data": "0xabcd",
            "value": 0,
        }
        
        # Process command
        result = self.processor.process_command("Swap 10 ETH to USDC on SparkDEX with 0.5% slippage")
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "swap")
        self.assertEqual(result["protocol"], "sparkdex")
        self.assertEqual(result["params"]["token_in"], "ETH")
        self.assertEqual(result["params"]["token_out"], "USDC")
        self.assertEqual(result["params"]["amount_in"], "10")
        self.assertEqual(result["params"]["slippage"], "0.5")
        self.assertIn("tx_params", result)
        
        # Verify protocol factory was called
        self.protocol_factory.get_protocol.assert_called_once_with("sparkdex")
        
        # Verify protocol method was called
        self.mock_protocol.prepare_swap_transaction.assert_called_once()

    def test_process_deposit_command(self):
        """Test processing a deposit command."""
        # Mock protocol methods
        self.mock_protocol.prepare_deposit_transaction.return_value = {
            "to": "0x1234",
            "data": "0xabcd",
            "value": 0,
        }
        
        # Process command
        result = self.processor.process_command("Deposit 100 USDC into Kinetic")
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "deposit")
        self.assertEqual(result["protocol"], "kinetic")
        self.assertEqual(result["params"]["token"], "USDC")
        self.assertEqual(result["params"]["amount"], "100")
        self.assertIn("tx_params", result)
        
        # Verify protocol factory was called
        self.protocol_factory.get_protocol.assert_called_once_with("kinetic")
        
        # Verify protocol method was called
        self.mock_protocol.prepare_deposit_transaction.assert_called_once()

    def test_process_command_with_no_protocol(self):
        """Test processing a command with no protocol specified."""
        # Mock protocol methods
        self.mock_protocol.prepare_swap_transaction.return_value = {
            "to": "0x1234",
            "data": "0xabcd",
            "value": 0,
        }
        
        # Process command
        result = self.processor.process_command("Swap 10 ETH to USDC")
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "swap")
        self.assertEqual(result["protocol"], "sparkdex")  # Default protocol for swap
        self.assertEqual(result["params"]["token_in"], "ETH")
        self.assertEqual(result["params"]["token_out"], "USDC")
        self.assertEqual(result["params"]["amount_in"], "10")
        self.assertIn("tx_params", result)
        
        # Verify protocol factory was called
        self.protocol_factory.get_protocol.assert_called_once_with("sparkdex")
        
        # Verify protocol method was called
        self.mock_protocol.prepare_swap_transaction.assert_called_once()

    def test_process_command_with_invalid_params(self):
        """Test processing a command with invalid parameters."""
        # Process command
        result = self.processor.process_command("Swap ETH to USDC")  # Missing amount
        
        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["action"], "swap")
        self.assertIsNone(result["protocol"])
        self.assertIn("errors", result)
        self.assertIn("Missing input amount", result["errors"])
        
        # Verify protocol factory was not called
        self.protocol_factory.get_protocol.assert_not_called()

    def test_process_unknown_action(self):
        """Test processing a command with an unknown action."""
        # Process command
        result = self.processor.process_command("Do something with 10 ETH")
        
        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["action"], "unknown")
        self.assertIn("errors", result)
        self.assertIn("Unknown action", result["errors"])
        
        # Verify protocol factory was not called
        self.protocol_factory.get_protocol.assert_not_called()

    def test_process_command_with_protocol_error(self):
        """Test processing a command where the protocol raises an error."""
        # Mock protocol methods to raise an exception
        self.mock_protocol.prepare_swap_transaction.side_effect = Exception("Protocol error")
        
        # Process command
        result = self.processor.process_command("Swap 10 ETH to USDC on SparkDEX")
        
        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["action"], "swap")
        self.assertEqual(result["protocol"], "sparkdex")
        self.assertIn("errors", result)
        self.assertIn("Protocol error", result["errors"])
        
        # Verify protocol factory was called
        self.protocol_factory.get_protocol.assert_called_once_with("sparkdex")
        
        # Verify protocol method was called
        self.mock_protocol.prepare_swap_transaction.assert_called_once()


if __name__ == "__main__":
    unittest.main()
