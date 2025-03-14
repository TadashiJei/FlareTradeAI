"""
DeFi Operations API Router

This module provides API endpoints for DeFi operations with enhanced risk assessment
and transaction validation. It handles DeFi-specific commands processed through
the chat interface.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from web3 import Web3
from web3.exceptions import Web3RPCError

from ...ai import GeminiProvider
from ...blockchain import FlareProvider
from ...blockchain.transaction import TransactionValidator
from ...blockchain.risk import DeFiRiskAssessmentService, RiskAssessment, RiskLevel
from ...blockchain.protocols.raindex import RainDEX
from ...blockchain.tokens import TokenRegistry
from ...prompts import PromptService
from ...settings import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

class DeFiOperation(BaseModel):
    """
    Pydantic model for DeFi operation requests.

    Attributes:
        operation_type (str): Type of DeFi operation (swap, provide_liquidity, etc.)
        token_in (Optional[str]): Input token symbol or address
        token_out (Optional[str]): Output token symbol or address
        amount (Optional[str]): Amount to use in the operation
        parameters (Optional[Dict[str, Any]]): Additional parameters for the operation
    """
    operation_type: str = Field(..., description="Type of DeFi operation")
    token_in: Optional[str] = Field(None, description="Input token symbol or address")
    token_out: Optional[str] = Field(None, description="Output token symbol or address")
    amount: Optional[str] = Field(None, description="Amount to use in the operation")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")

class RiskAssessmentResponse(BaseModel):
    """
    Pydantic model for risk assessment responses.

    Attributes:
        risk_level (str): Overall risk level (low, medium, high)
        risk_factors (List[Dict[str, Any]]): Detailed risk factors
        warnings (List[str]): Risk warnings for user awareness
        recommendations (List[str]): Recommended actions
        simulation_results (Optional[Dict[str, Any]]): Results of transaction simulation
    """
    risk_level: str
    risk_factors: List[Dict[str, Any]]
    warnings: List[str]
    recommendations: List[str]
    simulation_results: Optional[Dict[str, Any]] = None

class DeFiRouter:
    """
    Router class for handling DeFi operations with enhanced risk assessment
    and transaction validation.
    """
    def __init__(
        self,
        blockchain: FlareProvider,
        ai: GeminiProvider,
        prompts: PromptService
    ):
        """
        Initialize the DeFi operations router.

        Args:
            blockchain: Provider for blockchain operations
            ai: Provider for AI capabilities
            prompts: Service for managing prompts
        """
        self.blockchain = blockchain
        self.ai = ai
        self.prompts = prompts
        self.logger = logger.bind(router="defi_operations")
        
        # Initialize enhanced components
        self.web3 = Web3(Web3.HTTPProvider(settings.web3_rpc_url))
        self.transaction_validator = TransactionValidator(self.web3)
        self.risk_assessor = RiskAssessor(self.web3)
        
        # Initialize token registry
        self.token_registry = TokenRegistry(self.web3, network=settings.network_name)
        
        # Initialize protocol integrations with enhanced price feed support
        self.raindex = RainDEX(
            web3=self.web3,
            network=settings.network_name,
            price_api_url=settings.price_api_url,
            price_api_key=settings.price_api_key
        )
    
    async def process_defi_operation(self, operation: DeFiOperation) -> Dict[str, Any]:
        """
        Process a DeFi operation with comprehensive risk assessment.

        Args:
            operation: DeFi operation details

        Returns:
            Dict[str, Any]: Operation processing results
        """
        self.logger.info(
            "processing_defi_operation",
            operation_type=operation.operation_type,
            token_in=operation.token_in,
            token_out=operation.token_out
        )
        
        try:
            # Step 1: Validate parameters
            self._validate_operation_parameters(operation)
            
            # Step 2: Prepare transaction parameters
            tx_params = self._prepare_transaction_parameters(operation)
            
            # Step 3: Perform risk assessment with enhanced components
            risk_assessment = self._assess_operation_risk(tx_params, operation)
            
            # Step 4: If risk level is acceptable, prepare transaction for confirmation
            if risk_assessment["risk_level"] not in ["critical", "high"]:
                # Add to transaction queue for confirmation
                self.blockchain.add_tx_to_queue(
                    tx_params, 
                    f"Confirm {operation.operation_type} operation"
                )
                
                # Prepare user-friendly response
                response = self._format_operation_response(operation, risk_assessment)
                return {"response": response, "requires_confirmation": True}
            else:
                # Operation is too risky to proceed
                return {
                    "response": (
                        f"⚠️ **Operation cannot proceed due to high risk**\n\n"
                        f"Risk level: {risk_assessment['risk_level']}\n\n"
                        f"Warnings:\n" + 
                        "\n".join([f"- {w}" for w in risk_assessment["warnings"]])
                    ),
                    "requires_confirmation": False
                }
        
        except Exception as e:
            self.logger.exception("defi_operation_processing_failed", error=str(e))
            return {
                "response": f"Error processing DeFi operation: {str(e)}",
                "requires_confirmation": False
            }
    
    def _validate_operation_parameters(self, operation: DeFiOperation) -> None:
        """
        Validate operation parameters based on operation type.
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if operation.operation_type == "swap":
            if not operation.token_in or not operation.token_out:
                raise ValueError("Swap operations require both input and output tokens")
            if not operation.amount:
                raise ValueError("Amount to swap must be specified")
        
        elif operation.operation_type == "provide_liquidity":
            if not operation.token_in or not operation.token_out:
                raise ValueError("Liquidity provision requires token pair")
            if not operation.amount:
                raise ValueError("Amount to provide must be specified")
    
    def _prepare_transaction_parameters(self, operation: DeFiOperation) -> Dict[str, Any]:
        """
        Prepare transaction parameters based on operation type.
        
        Returns:
            Dict[str, Any]: Transaction parameters
        """
        # This is a simplified implementation
        # In production, this would create actual transaction parameters
        if operation.operation_type == "swap":
            # Get token addresses
            token_in_address = self._resolve_token_address(operation.token_in)
            token_out_address = self._resolve_token_address(operation.token_out)
            
            # Get quote for the swap
            amount_in = self._parse_amount(operation.amount, token_in_address)
            amount_out, price_impact = self.raindex.get_swap_quote(
                token_in_address,
                token_out_address,
                amount_in
            )
            
            # Prepare transaction parameters
            return {
                "from": self.blockchain.address,
                "to": self.raindex.contracts["router"],
                "value": 0,  # For ERC20 to ERC20 swaps
                "data": self.raindex.router_contract.functions.swapExactTokensForTokens(
                    amount_in,
                    int(amount_out * 0.99),  # 1% slippage tolerance
                    [token_in_address, token_out_address],
                    self.blockchain.address,
                    self.web3.eth.get_block('latest').timestamp + 300  # 5 minutes deadline
                ).build_transaction()["data"]
            }
        
        # Add other operation types as needed
        return {}
    
    def _assess_operation_risk(
        self, 
        tx_params: Dict[str, Any], 
        operation: DeFiOperation
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment for the operation.
        
        Returns:
            Dict[str, Any]: Risk assessment results
        """
        # Extract protocol info from transaction
        protocol_info = self.transaction_validator._extract_protocol_info_from_tx(tx_params)
        
        # Assess financial operation risk
        risk_assessment = self.risk_assessor.assess_financial_operation(
            protocol_info=protocol_info,
            operation_type=operation.operation_type,
            protocol_type="dex"  # Simplified, would be dynamically determined
        )
        
        # Assess portfolio risk if applicable
        portfolio_risk = self.risk_assessor.assess_portfolio_risk(
            wallet_address=self.blockchain.address,
            token_addresses=[
                self._resolve_token_address(operation.token_in),
                self._resolve_token_address(operation.token_out)
            ]
        )
        
        # Simulate transaction if possible
        simulation_results = self.transaction_validator.simulate_transaction(tx_params)
        
        # Combine all risk assessments
        risk_factors = risk_assessment.get("risk_factors", []) + portfolio_risk.get("risk_factors", [])
        warnings = risk_assessment.get("warnings", []) + portfolio_risk.get("warnings", [])
        
        # Determine overall risk level
        risk_level = "low"
        if any(f.get("severity") == "critical" for f in risk_factors):
            risk_level = "critical"
        elif any(f.get("severity") == "high" for f in risk_factors):
            risk_level = "high"
        elif any(f.get("severity") == "medium" for f in risk_factors):
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "warnings": warnings,
            "recommendations": risk_assessment.get("recommendations", []),
            "simulation_results": simulation_results
        }
    
    def _format_operation_response(
        self,
        operation: DeFiOperation,
        risk_assessment: Dict[str, Any]
    ) -> str:
        """
        Format a user-friendly response for the operation.
        
        Returns:
            str: Formatted response string
        """
        response_parts = []
        
        # Operation summary
        if operation.operation_type == "swap":
            response_parts.append(
                f"## Transaction Preview: Swap {operation.amount} {operation.token_in} to {operation.token_out}\n"
            )
        
        # Add risk assessment information
        response_parts.append(f"**Risk Level:** {risk_assessment['risk_level'].upper()}\n")
        
        # Add warnings if any
        if risk_assessment["warnings"]:
            response_parts.append("**Warnings:**")
            for warning in risk_assessment["warnings"]:
                response_parts.append(f"- {warning}")
            response_parts.append("")
        
        # Add recommendations if any
        if risk_assessment["recommendations"]:
            response_parts.append("**Recommendations:**")
            for rec in risk_assessment["recommendations"]:
                response_parts.append(f"- {rec}")
            response_parts.append("")
        
        # Add confirmation instructions
        response_parts.append(
            "\nTo confirm this transaction, please reply with **CONFIRM**. "
            "To cancel, reply with anything else."
        )
        
        return "\n".join(response_parts)
    
    def _resolve_token_address(self, token: str) -> str:
        """
        Resolve token symbol to address or validate address using TokenRegistry.
        
        Args:
            token: Token symbol or address
            
        Returns:
            str: Token address (checksum format)
            
        Raises:
            ValueError: If token cannot be resolved
        """
        try:
            return self.token_registry.resolve_token(token)
        except ValueError as e:
            self.logger.error("token_resolution_failed", token=token, error=str(e))
            raise ValueError(f"Unknown token: {token}. Please use a valid token symbol or address.")
    
    def _parse_amount(self, amount_str: str, token_address: str) -> int:
        """
        Parse amount string to integer with proper decimals based on token metadata.
        
        Args:
            amount_str: Amount as string (e.g., "1.5")
            token_address: Token address to determine decimals
            
        Returns:
            int: Amount in smallest units
        """
        try:
            # Get actual token decimals from on-chain metadata
            token_metadata = self.token_registry.get_token_metadata(token_address)
            decimals = token_metadata.get("decimals", 18)
            
            # Handle simple formatting
            if '.' in amount_str:
                whole, fraction = amount_str.split('.')
                # Pad fraction with zeros if needed
                fraction = fraction.ljust(decimals, '0')[:decimals]
                return int(whole) * (10 ** decimals) + int(fraction)
            else:
                return int(amount_str) * (10 ** decimals)
        except Exception as e:
            self.logger.error("amount_parsing_failed", amount=amount_str, token=token_address, error=str(e))
            # Fallback to default 18 decimals
            return int(float(amount_str) * (10 ** 18))


# Initialize API routes
@router.post("/defi")
async def handle_defi_operation(
    operation: DeFiOperation,
    blockchain: FlareProvider = Depends(lambda: FlareProvider()),
    ai: GeminiProvider = Depends(lambda: GeminiProvider()),
    prompts: PromptService = Depends(lambda: PromptService())
) -> Dict[str, Any]:
    """
    Handle DeFi operation requests with enhanced validation and risk assessment.
    
    Args:
        operation: DeFi operation details
        blockchain: Blockchain provider (injected dependency)
        ai: AI provider (injected dependency)
        prompts: Prompt service (injected dependency)
        
    Returns:
        Dict[str, Any]: Operation processing results
        
    Raises:
        HTTPException: If operation processing fails
    """
    try:
        defi_router = DeFiRouter(blockchain, ai, prompts)
        return await defi_router.process_defi_operation(operation)
    except Exception as e:
        logger.exception("defi_operation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
