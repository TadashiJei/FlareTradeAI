"""
Structured Data Validation Module

This module provides validation for financial operations, ensuring that all transactions
and operations adhere to the required formats and constraints.
"""

from typing import Any, Dict, Optional

import structlog
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams

logger = structlog.get_logger(__name__)


class FinancialOperationValidator:
    """
    Validates financial operations and transactions.
    
    This class provides methods for validating various aspects of financial operations,
    including address formats, token amounts, and transaction parameters.
    """

    def __init__(self, web3: Web3):
        """
        Initialize the financial operation validator.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
        """
        self.web3 = web3

    def validate_address(self, address: str) -> bool:
        """
        Validate an Ethereum address.
        
        Args:
            address (str): Address to validate
            
        Returns:
            bool: True if the address is valid
        """
        try:
            checksum_address = self.web3.to_checksum_address(address)
            return self.web3.is_address(checksum_address)
        except ValueError:
            return False

    def validate_token_amount(self, amount: str, decimals: int = 18) -> bool:
        """
        Validate a token amount.
        
        Args:
            amount (str): Amount to validate
            decimals (int, optional): Number of decimals for the token. Defaults to 18.
            
        Returns:
            bool: True if the amount is valid
        """
        try:
            float(amount)
            return True
        except ValueError:
            return False

    def validate_transaction_parameters(self, tx_params: TxParams) -> Dict[str, Any]:
        """
        Validate transaction parameters.
        
        Args:
            tx_params (TxParams): Transaction parameters to validate
            
        Returns:
            Dict[str, Any]: Validation results including:
                - valid: Whether the parameters are valid
                - errors: List of errors if any
        """
        errors = []
        
        # Validate 'from' address
        if "from" in tx_params and not self.validate_address(tx_params["from"]):
            errors.append("Invalid 'from' address")
        
        # Validate 'to' address
        if "to" in tx_params and not self.validate_address(tx_params["to"]):
            errors.append("Invalid 'to' address")
        
        # Validate 'value' amount
        if "value" in tx_params and not self.validate_token_amount(str(tx_params["value"])):
            errors.append("Invalid 'value' amount")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def validate_operation_parameters(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters for a specific financial operation.
        
        Args:
            operation (str): Type of financial operation
            params (Dict[str, Any]): Operation parameters to validate
            
        Returns:
            Dict[str, Any]: Validation results including:
                - valid: Whether the parameters are valid
                - errors: List of errors if any
        """
        errors = []
        
        # Validate token addresses
        if "token" in params and not self.validate_address(params["token"]):
            errors.append("Invalid token address")
        
        if "token_in" in params and not self.validate_address(params["token_in"]):
            errors.append("Invalid input token address")
        
        if "token_out" in params and not self.validate_address(params["token_out"]):
            errors.append("Invalid output token address")
        
        # Validate amounts
        if "amount" in params and not self.validate_token_amount(str(params["amount"])):
            errors.append("Invalid amount")
        
        if "amount_in" in params and not self.validate_token_amount(str(params["amount_in"])):
            errors.append("Invalid input amount")
        
        if "amount_out" in params and not self.validate_token_amount(str(params["amount_out"])):
            errors.append("Invalid output amount")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
