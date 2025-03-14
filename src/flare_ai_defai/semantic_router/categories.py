"""
Semantic Router Categories for DeFi Actions

This module defines the semantic router categories for various DeFi actions,
helping the AI agent correctly classify and route user commands.
"""

from enum import Enum


class DeFiActionCategory(Enum):
    """
    Enum representing different categories of DeFi actions.
    
    These categories are used by the semantic router to classify user commands
    and route them to the appropriate protocol handlers.
    """

    SWAP = "swap"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    BORROW = "borrow"
    REPAY = "repay"
    STAKE = "stake"
    UNSTAKE = "unstake"
    CLAIM_REWARDS = "claim_rewards"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    RISK_ASSESSMENT = "risk_assessment"
    WALLET_MANAGEMENT = "wallet_management"

    @classmethod
    def get_category(cls, action: str) -> "DeFiActionCategory":
        """
        Get the category for a specific action.
        
        Args:
            action (str): Name of the action
            
        Returns:
            DeFiActionCategory: The category for the action
            
        Raises:
            ValueError: If the action is not supported
        """
        try:
            return cls(action.lower())
        except ValueError:
            msg = f"Action '{action}' not supported"
            raise ValueError(msg)
