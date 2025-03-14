"""
DeFi Prompt Templates Module

This module contains prompt templates for various DeFi operations, helping the AI agent
generate appropriate blockchain instructions based on user commands.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DeFiPromptTemplate:
    """
    Template for generating DeFi operation prompts.
    
    Attributes:
        operation (str): Type of DeFi operation
        description (str): Description of the operation
        parameters (List[str]): List of required parameters
        example (str): Example prompt and response
    """
    operation: str
    description: str
    parameters: List[str]
    example: str


class DeFiPromptTemplates:
    """
    Collection of prompt templates for DeFi operations.
    
    This class provides a centralized way to access prompt templates for various
    DeFi operations across different protocols.
    """

    TEMPLATES: Dict[str, DeFiPromptTemplate] = {
        "swap": DeFiPromptTemplate(
            operation="swap",
            description="Swap tokens on a decentralized exchange",
            parameters=["token_in", "token_out", "amount_in", "slippage"],
            example="""
            User: Swap 100 FLR for USDC with 1% slippage
            AI: Executing swap: 100 FLR → USDC (max slippage: 1%)
            """,
        ),
        "deposit": DeFiPromptTemplate(
            operation="deposit",
            description="Deposit assets into a lending protocol",
            parameters=["token", "amount"],
            example="""
            User: Deposit 500 USDC into Kinetic
            AI: Executing deposit: 500 USDC into Kinetic
            """,
        ),
        "withdraw": DeFiPromptTemplate(
            operation="withdraw",
            description="Withdraw assets from a lending protocol",
            parameters=["token", "amount"],
            example="""
            User: Withdraw 200 USDC from Kinetic
            AI: Executing withdrawal: 200 USDC from Kinetic
            """,
        ),
        "stake": DeFiPromptTemplate(
            operation="stake",
            description="Stake tokens in a yield farming protocol",
            parameters=["token", "amount"],
            example="""
            User: Stake 1000 FLR in Cyclo
            AI: Executing stake: 1000 FLR in Cyclo
            """,
        ),
        "unstake": DeFiPromptTemplate(
            operation="unstake",
            description="Unstake tokens from a yield farming protocol",
            parameters=["token", "amount"],
            example="""
            User: Unstake 500 FLR from Cyclo
            AI: Executing unstake: 500 FLR from Cyclo
            """,
        ),
        "claim_rewards": DeFiPromptTemplate(
            operation="claim_rewards",
            description="Claim rewards from a yield farming protocol",
            parameters=["token"],
            example="""
            User: Claim my FLR rewards from Cyclo
            AI: Executing reward claim: FLR rewards from Cyclo
            """,
        ),
    }

    @classmethod
    def get_template(cls, operation: str) -> DeFiPromptTemplate:
        """
        Get the prompt template for a specific operation.
        
        Args:
            operation (str): Name of the operation
            
        Returns:
            DeFiPromptTemplate: The prompt template
            
        Raises:
            ValueError: If the operation is not supported
        """
        template = cls.TEMPLATES.get(operation)
        if not template:
            msg = f"Operation '{operation}' not supported"
            raise ValueError(msg)
        return template

    @classmethod
    def get_all_templates(cls) -> Dict[str, DeFiPromptTemplate]:
        """
        Get all available prompt templates.
        
        Returns:
            Dict[str, DeFiPromptTemplate]: Dictionary of all prompt templates
        """
        return cls.TEMPLATES
