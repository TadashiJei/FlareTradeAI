"""
Unit Tests for Protocol Integrations

This module contains unit tests for the various DeFi protocol integrations.
"""

import unittest
from unittest.mock import Mock

from flare_ai_defai.blockchain.protocols import (
    SparkDEX,
    Kinetic,
    Cyclo,
    RainDEX,
)


class TestProtocols(unittest.TestCase):

    def setUp(self):
        self.web3 = Mock()
        self.address = "0x1234567890123456789012345678901234567890"

    def test_sparkdex_swap(self):
        sparkdex = SparkDEX(self.web3, self.address)
        tx_params = sparkdex.prepare_swap_transaction(
            token_in_address="0x1",
            token_out_address="0x2",
            amount_in=100,
            min_amount_out=90,
            deadline=1234567890,
        )
        self.assertIsNotNone(tx_params)

    def test_kinetic_deposit(self):
        kinetic = Kinetic(self.web3, self.address)
        tx_params = kinetic.prepare_deposit_transaction(
            asset_address="0x1",
            amount=500,
        )
        self.assertIsNotNone(tx_params)

    def test_cyclo_stake(self):
        cyclo = Cyclo(self.web3, self.address)
        tx_params = cyclo.prepare_stake_transaction(
            token_address="0x1",
            amount=1000,
        )
        self.assertIsNotNone(tx_params)

    def test_raindex_swap(self):
        raindex = RainDEX(self.web3, self.address)
        tx_params = raindex.prepare_swap_transaction(
            token_in_address="0x1",
            token_out_address="0x2",
            amount_in=100,
            min_amount_out=90,
            deadline=1234567890,
        )
        self.assertIsNotNone(tx_params)


if __name__ == '__main__':
    unittest.main()
