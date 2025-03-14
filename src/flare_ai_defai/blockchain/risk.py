"""
Risk Assessment Service Module

This module provides a service interface for evaluating the risk of DeFi transactions
and operations across different protocols.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from web3.types import TxParams

logger = structlog.get_logger(__name__)


class RiskLevel(Enum):
    """Enum representing different levels of risk."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    """
    Represents a specific risk factor and its details.
    
    Attributes:
        name (str): Name of the risk factor
        description (str): Description of the risk
        level (RiskLevel): Risk level
        impact (str): Potential impact of the risk
        mitigation (str): Suggested mitigation strategy
    """
    name: str
    description: str
    level: RiskLevel
    impact: str
    mitigation: str


@dataclass
class RiskAssessment:
    """
    Represents the result of a risk assessment.
    
    Attributes:
        overall_risk (RiskLevel): Overall risk level
        factors (List[RiskFactor]): List of identified risk factors
        warnings (List[str]): List of warnings
        recommendations (List[str]): List of recommendations
    """
    overall_risk: RiskLevel
    factors: List[RiskFactor]
    warnings: List[str]
    recommendations: List[str]


class RiskAssessmentService(ABC):
    """
    Abstract base class for risk assessment services.
    
    This class defines the interface for risk assessment services that can be
    implemented for different protocols and transaction types.
    """

    @abstractmethod
    def assess_transaction(self, tx_params: TxParams, context: Dict[str, Any] = None) -> RiskAssessment:
        """
        Assess the risk of a transaction.
        
        Args:
            tx_params (TxParams): Transaction parameters to assess
            context (Dict[str, Any], optional): Additional context for the assessment
            
        Returns:
            RiskAssessment: Risk assessment result
        """
        pass

    @abstractmethod
    def assess_portfolio(self, positions: List[Dict[str, Any]]) -> RiskAssessment:
        """
        Assess the risk of a portfolio.
        
        Args:
            positions (List[Dict[str, Any]]): List of portfolio positions
            
        Returns:
            RiskAssessment: Risk assessment result
        """
        pass

    @abstractmethod
    def assess_protocol(self, protocol_name: str) -> RiskAssessment:
        """
        Assess the risk of using a specific protocol.
        
        Args:
            protocol_name (str): Name of the protocol to assess
            
        Returns:
            RiskAssessment: Risk assessment result
        """
        pass
