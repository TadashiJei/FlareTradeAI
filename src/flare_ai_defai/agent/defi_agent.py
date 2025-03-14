"""
DeFi Agent Module

This module provides the main agent interface for DeFi operations,
integrating NLP, protocol interactions, risk assessment, and wallet management.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Union

import structlog

from ..ai import GeminiProvider
from ..blockchain.attestation import AttestationValidator, Vtpm
from ..blockchain.flare import FlareProvider
from ..blockchain.protocols.factory import ProtocolFactory
from ..blockchain.risk.assessment import DeFiRiskAssessmentService, RiskLevel
from ..blockchain.transaction import TransactionSimulator, TransactionValidator
from ..blockchain.validation import FinancialOperationValidator
from ..blockchain.wallet.tee_wallet import TEEWallet
from ..nlp.defi_parser import DeFiCommandProcessor, ParsedDeFiCommand
from ..settings import settings

logger = structlog.get_logger(__name__)


class DeFiAgent:
    """
    Main agent for DeFi operations.
    
    This class integrates all components of the FlareTrade system, including
    NLP, protocol interactions, risk assessment, and wallet management.
    """
    
    def __init__(
        self,
        wallet_address: str,
        use_tee: bool = True,
        risk_threshold: str = "medium",
        simulate_transactions: bool = True,
    ):
        """
        Initialize the DeFi agent.
        
        Args:
            wallet_address (str): The wallet address to use for transactions
            use_tee (bool, optional): Whether to use TEE protection. Defaults to True.
            risk_threshold (str, optional): Risk threshold for transactions. Defaults to "medium".
            simulate_transactions (bool, optional): Whether to simulate transactions before execution. Defaults to True.
        """
        self.wallet_address = wallet_address
        self.use_tee = use_tee
        self.risk_threshold = risk_threshold
        self.simulate_transactions = simulate_transactions
        
        # Initialize logger
        self.logger = logger.bind(
            service="defi_agent",
            wallet_address=wallet_address,
            use_tee=use_tee,
        )
        
        # Initialize TEE components if enabled
        if use_tee:
            self.vtpm = Vtpm()
            self.attestation_validator = AttestationValidator()
            
            # Verify TEE environment
            env_result = self.attestation_validator.verify_environment()
            if not env_result["valid"]:
                raise RuntimeError(f"TEE environment verification failed: {env_result['errors']}")
            
            self.logger.info("tee_environment_verified")
        else:
            self.vtpm = Vtpm(simulate=True)
            self.attestation_validator = AttestationValidator(simulate=True)
            self.logger.warn("tee_disabled", message="Running without TEE protection")
        
        # Initialize Web3 provider and secure TEE wallet
        self.flare_provider = FlareProvider(web3_provider_url=settings.web3_rpc_url)
        
        # Initialize components
        self.protocol_factory = ProtocolFactory(
            web3=self.flare_provider.web3,
            address=wallet_address,
            network="flare"
        )
        self.risk_assessment = DeFiRiskAssessmentService(
            web3=self.flare_provider.web3,
            protocol_factory=self.protocol_factory
        )
        self.transaction_simulator = TransactionSimulator()
        self.transaction_validator = TransactionValidator(
            risk_assessment=self.risk_assessment,
            risk_threshold=risk_threshold,
            simulator=self.transaction_simulator,
        )
        self.financial_validator = FinancialOperationValidator(self.flare_provider.web3)
        
        # Initialize NLP components
        self.command_processor = DeFiCommandProcessor(self.protocol_factory)
        
        # Initialize AI provider
        self.ai_provider = GeminiProvider()
        
        self.logger.info("defi_agent_initialized")
    
    def process_natural_language_command(self, command: str) -> Dict:
        """
        Process a natural language command related to DeFi operations.
        
        Args:
            command (str): The command to process
            
        Returns:
            Dict: The processing results, including:
                - success: Whether the processing was successful
                - action: The action performed
                - protocol: The protocol used
                - transaction_hash: The transaction hash if a transaction was executed
                - errors: List of errors if any
                - risk_assessment: Risk assessment results
                - warnings: List of warnings
                - recommendations: List of recommendations
        """
        self.logger.info("processing_command", command=command)
        
        try:
            # Process the command using NLP
            nlp_result = self.command_processor.process_command(command)
            
            if not nlp_result["success"]:
                return {
                    "success": False,
                    "action": nlp_result.get("action", "unknown"),
                    "protocol": nlp_result.get("protocol"),
                    "errors": nlp_result.get("errors", ["Failed to process command"]),
                }
            
            # Get transaction parameters
            tx_params = nlp_result["tx_params"]
            
            # Validate financial operation parameters
            operation_validation = self.financial_validator.validate_operation_parameters(
                nlp_result["action"],
                nlp_result["params"],
            )
            
            if not operation_validation["valid"]:
                return {
                    "success": False,
                    "action": nlp_result["action"],
                    "protocol": nlp_result["protocol"],
                    "errors": operation_validation["errors"],
                }
            
            # Perform risk assessment
            risk_result = self.risk_assessment.assess_transaction(
                tx_params=tx_params,
                protocol_name=nlp_result["protocol"],
                action=nlp_result["action"],
                context=nlp_result.get("params"),
            )
            
            # Validate transaction with risk assessment
            validation_result = self.transaction_validator.validate_transaction(
                tx_params=tx_params,
                risk_assessment=risk_result,
                simulate=self.simulate_transactions,
            )
            
            # Collect warnings and recommendations
            warnings = []
            recommendations = []
            
            if risk_result:
                warnings.extend(risk_result.warnings)
                recommendations.extend(risk_result.recommendations)
            
            if validation_result["warnings"]:
                warnings.extend(validation_result["warnings"])
            
            # Check if transaction is valid
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "action": nlp_result["action"],
                    "protocol": nlp_result["protocol"],
                    "errors": validation_result["errors"],
                    "risk_assessment": risk_result,
                    "warnings": warnings,
                    "recommendations": recommendations,
                    "simulation_result": validation_result.get("simulation"),
                }
            
            # Execute transaction if validation passed
            tx_hash = self._execute_transaction(
                tx_params=tx_params,
                protocol=nlp_result["protocol"],
                action=nlp_result["action"],
            )
            
            return {
                "success": True,
                "action": nlp_result["action"],
                "protocol": nlp_result["protocol"],
                "transaction_hash": tx_hash,
                "risk_assessment": risk_result,
                "params": nlp_result["params"],
                "warnings": warnings,
                "recommendations": recommendations,
                "simulation_result": validation_result.get("simulation"),
            }
        
        except Exception as e:
            self.logger.error("command_processing_failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "errors": [str(e)],
            }
    
    def _execute_transaction(self, tx_params: Dict, protocol: str, action: str) -> str:
        """
        Execute a transaction.
        
        Args:
            tx_params (Dict): The transaction parameters
            protocol (str): The protocol to use
            action (str): The action to perform
            
        Returns:
            str: The transaction hash
        """
        self.logger.info(
            "executing_transaction",
            protocol=protocol,
            action=action,
            tx_params=tx_params,
        )
        
        try:
            # Get the protocol implementation
            protocol_impl = self.protocol_factory.get_protocol(protocol)
            
            # Execute the transaction using the flare provider's secure TEE wallet
            # First prepare the transaction
            tx_params["from"] = self.flare_provider.address
            
            # Add the transaction to the queue with a description
            self.flare_provider.add_tx_to_queue(
                msg=f"{protocol}: {action}",
                tx=tx_params
            )
            
            # Execute the transaction
            tx_hash = self.flare_provider.send_tx_in_queue()
            
            self.logger.info(
                "transaction_executed",
                protocol=protocol,
                action=action,
                tx_hash=tx_hash,
            )
            
            return tx_hash
        
        except Exception as e:
            self.logger.error(
                "transaction_execution_failed",
                protocol=protocol,
                action=action,
                error=str(e),
                exc_info=True,
            )
            raise
    
    def get_portfolio_info(self) -> Dict:
        """
        Get information about the user's portfolio.
        
        Returns:
            Dict: Portfolio information, including:
                - wallet_address: The wallet address
                - balance: The wallet balance
                - tokens: List of tokens held
                - positions: List of active positions
        """
        self.logger.info("getting_portfolio_info")
        
        try:
            # Get wallet balance using the flare provider
            balance = self.flare_provider.check_balance()
            
            # Get tokens held (will be implemented through protocol-specific calls)
            tokens = []  # This will be populated through protocol-specific token balance calls
            
            # Get active positions across protocols
            positions = []
            for protocol_name in self.protocol_factory.get_supported_protocols():
                protocol = self.protocol_factory.get_protocol(protocol_name)
                protocol_positions = protocol.get_positions(self.wallet_address)
                
                for position in protocol_positions:
                    position["protocol"] = protocol_name
                    positions.append(position)
            
            # Get risk assessment for the portfolio
            portfolio_risk = self._assess_portfolio_risk(positions)
            
            return {
                "wallet_address": self.wallet_address,
                "balance": balance,
                "tokens": tokens,
                "positions": positions,
                "risk_assessment": portfolio_risk,
            }
        
        except Exception as e:
            self.logger.error("portfolio_info_failed", error=str(e), exc_info=True)
            return {
                "wallet_address": self.wallet_address,
                "error": str(e),
            }
    
    def _assess_portfolio_risk(self, positions: List[Dict]) -> Dict:
        """
        Assess the risk of the user's portfolio.
        
        Args:
            positions (List[Dict]): List of active positions
            
        Returns:
            Dict: Risk assessment results
        """
        self.logger.info("assessing_portfolio_risk", position_count=len(positions))
        
        try:
            # Calculate risk factors
            risk_factors = []
            
            # Assess concentration risk
            if len(positions) > 0:
                protocols = set(position["protocol"] for position in positions)
                if len(protocols) == 1:
                    risk_factors.append({
                        "name": "protocol_concentration",
                        "level": RiskLevel.HIGH,
                        "score": 0.8,
                        "description": "All positions are in a single protocol",
                    })
                elif len(protocols) <= 2:
                    risk_factors.append({
                        "name": "protocol_concentration",
                        "level": RiskLevel.MEDIUM,
                        "score": 0.5,
                        "description": "Positions are concentrated in few protocols",
                    })
                else:
                    risk_factors.append({
                        "name": "protocol_concentration",
                        "level": RiskLevel.LOW,
                        "score": 0.2,
                        "description": "Positions are well diversified across protocols",
                    })
            
            # Assess position types
            leveraged_positions = [p for p in positions if p.get("leveraged", False)]
            if leveraged_positions:
                leverage_ratio = len(leveraged_positions) / len(positions) if positions else 0
                
                if leverage_ratio > 0.5:
                    risk_factors.append({
                        "name": "leverage_exposure",
                        "level": RiskLevel.HIGH,
                        "score": 0.9,
                        "description": "High exposure to leveraged positions",
                    })
                elif leverage_ratio > 0.2:
                    risk_factors.append({
                        "name": "leverage_exposure",
                        "level": RiskLevel.MEDIUM,
                        "score": 0.6,
                        "description": "Moderate exposure to leveraged positions",
                    })
                else:
                    risk_factors.append({
                        "name": "leverage_exposure",
                        "level": RiskLevel.LOW,
                        "score": 0.3,
                        "description": "Low exposure to leveraged positions",
                    })
            
            # Calculate overall risk
            if risk_factors:
                avg_score = sum(factor["score"] for factor in risk_factors) / len(risk_factors)
                
                if avg_score > 0.7:
                    overall_risk = {
                        "level": RiskLevel.HIGH,
                        "score": avg_score,
                    }
                elif avg_score > 0.4:
                    overall_risk = {
                        "level": RiskLevel.MEDIUM,
                        "score": avg_score,
                    }
                else:
                    overall_risk = {
                        "level": RiskLevel.LOW,
                        "score": avg_score,
                    }
            else:
                overall_risk = {
                    "level": RiskLevel.LOW,
                    "score": 0.1,
                }
            
            # Generate recommendations
            recommendations = []
            if overall_risk["level"] == RiskLevel.HIGH:
                recommendations.append("Consider reducing exposure to high-risk positions")
                recommendations.append("Diversify across more protocols to reduce concentration risk")
            elif overall_risk["level"] == RiskLevel.MEDIUM:
                recommendations.append("Monitor leveraged positions closely")
                recommendations.append("Consider adding more diversification to your portfolio")
            
            return {
                "overall_risk": overall_risk,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
            }
        
        except Exception as e:
            self.logger.error("portfolio_risk_assessment_failed", error=str(e), exc_info=True)
            return {
                "overall_risk": {
                    "level": RiskLevel.MEDIUM,
                    "score": 0.5,
                },
                "risk_factors": [],
                "warnings": [f"Risk assessment error: {str(e)}"],
                "recommendations": ["Unable to fully assess portfolio risk"],
            }
