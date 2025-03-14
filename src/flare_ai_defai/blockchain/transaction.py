"""
Transaction Simulation and Validation Module

This module provides functionality for simulating and validating DeFi transactions
before they are executed on-chain.
"""

from typing import Any, Dict, List, Optional

import structlog
from web3 import Web3
from web3.types import TxParams

from ..blockchain.risk.assessment import DeFiRiskAssessmentService, RiskAssessment, RiskLevel

logger = structlog.get_logger(__name__)


class TransactionSimulator:
    """
    Simulates transactions before execution.
    
    This class provides methods for simulating transactions to check for potential
    issues, gas costs, and expected outcomes.
    """
    
    def __init__(self, web3: Optional[Web3] = None):
        """
        Initialize the transaction simulator.
        
        Args:
            web3 (Optional[Web3]): Web3 instance for blockchain interactions
        """
        self.web3 = web3
    
    def simulate_transaction(self, tx_params: TxParams) -> Dict[str, Any]:
        """
        Simulate a transaction to check for potential issues.
        
        Args:
            tx_params (TxParams): Transaction parameters to simulate
            
        Returns:
            Dict[str, Any]: Simulation results including:
                - success: Whether the simulation was successful
                - gas_estimate: Estimated gas cost
                - expected_outcome: Expected transaction outcome
                - warnings: List of warnings
                - errors: List of errors
        """
        try:
            # If web3 is available, use it to estimate gas
            gas_estimate = 0
            if self.web3:
                gas_estimate = self.web3.eth.estimate_gas(tx_params)
            
            # Simulate the transaction outcome
            expected_outcome = self._simulate_outcome(tx_params)
            
            return {
                "success": True,
                "gas_estimate": gas_estimate,
                "expected_outcome": expected_outcome,
                "warnings": [],
                "errors": [],
            }
        except Exception as e:
            logger.error("transaction_simulation_failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "gas_estimate": 0,
                "expected_outcome": {},
                "warnings": [],
                "errors": [str(e)],
            }
    
    def _simulate_outcome(self, tx_params: TxParams) -> Dict[str, Any]:
        """
        Simulate the expected outcome of a transaction.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            Dict[str, Any]: Expected transaction outcome
        """
        if not self.web3:
            raise ValueError("Web3 instance is required for transaction simulation")
            
        # Use Tenderly's simulation API for accurate transaction simulation
        # This provides a full execution trace without actually submitting to the blockchain
        try:
            # Prepare simulation request for Tenderly API
            simulation_request = {
                "network_id": tx_params.get("chainId", 14),  # Default to Flare network
                "from": tx_params.get("from", ""),
                "to": tx_params.get("to", ""),
                "input": tx_params.get("data", "0x"),
                "gas": tx_params.get("gas", 3000000),
                "gas_price": tx_params.get("gasPrice", "0x0"),
                "value": tx_params.get("value", "0x0"),
                "save": True,  # Save simulation for debugging
                "save_if_fails": True,
                "simulation_type": "full"  # Get full execution trace
            }
            
            # In production, this would use the Tenderly API client
            tenderly_api_key = os.environ.get("TENDERLY_API_KEY")
            tenderly_account = os.environ.get("TENDERLY_ACCOUNT")
            tenderly_project = os.environ.get("TENDERLY_PROJECT")
            
            if not all([tenderly_api_key, tenderly_account, tenderly_project]):
                logger.warning("Tenderly credentials not found, using fallback simulation")
                return self._fallback_simulation(tx_params)
                
            headers = {
                "X-Access-Key": tenderly_api_key,
                "Content-Type": "application/json"
            }
            
            # Make API request to Tenderly
            import requests
            response = requests.post(
                f"https://api.tenderly.co/api/v1/account/{tenderly_account}/project/{tenderly_project}/simulate",
                headers=headers,
                json=simulation_request,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Tenderly simulation failed: {response.text}")
                return self._fallback_simulation(tx_params)
                
            sim_result = response.json()
            
            # Process the simulation result to extract token transfers and balance changes
            trace = sim_result.get("transaction", {}).get("transaction_info", {}).get("call_trace", {})
            logs = sim_result.get("transaction", {}).get("transaction_info", {}).get("logs", [])
            
            # Extract relevant information
            token_transfers = self._extract_token_transfers(logs)
            balance_changes = self._extract_balance_changes(trace)
            status = "success" if sim_result.get("transaction", {}).get("status", False) else "failed"
            
            return {
                "status": status,
                "token_transfers": token_transfers,
                "balance_changes": balance_changes,
                "events": logs,
                "gas_used": sim_result.get("transaction", {}).get("gas_used", 0),
                "trace": trace
            }
        
        except Exception as e:
            logger.exception(f"Error during transaction simulation: {str(e)}")
            return self._fallback_simulation(tx_params)
    
    def _extract_token_transfers(self, logs: List[Dict]) -> List[Dict]:
        """Extract token transfers from event logs."""
        transfers = []
        
        # Look for ERC20 Transfer events
        transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # Transfer event
        
        for log in logs:
            if log.get("topics", [])[0] == transfer_topic:
                try:
                    # Process Transfer event
                    from_addr = "0x" + log.get("topics", [])[1][-40:]
                    to_addr = "0x" + log.get("topics", [])[2][-40:]
                    amount = int(log.get("data", "0x0"), 16)
                    
                    # Get token details
                    token_address = log.get("address", "")
                    token_symbol = self._get_token_symbol(token_address)
                    token_decimals = self._get_token_decimals(token_address)
                    
                    # Calculate human-readable amount
                    human_amount = amount / (10 ** token_decimals)
                    
                    transfers.append({
                        "token": token_symbol,
                        "token_address": token_address,
                        "from": from_addr,
                        "to": to_addr,
                        "amount": human_amount,
                        "raw_amount": amount
                    })
                except Exception as e:
                    logger.warning(f"Error processing transfer event: {str(e)}")
        
        return transfers
    
    def _extract_balance_changes(self, trace: Dict) -> List[Dict]:
        """Extract balance changes from transaction trace."""
        # In production, this would analyze the full trace to find all balance changes
        # This is a simplified implementation
        balance_changes = []
        
        # Process the trace recursively to find all SSTORE operations that might modify balances
        # This is complex and would require context-specific knowledge of contracts
        
        return balance_changes
    
    def _get_token_symbol(self, token_address: str) -> str:
        """Get token symbol from address."""
        if not self.web3:
            return "UNKNOWN"
            
        try:
            # Create ERC20 contract instance
            from web3.contract import Contract
            
            abi = [{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"}]
            contract = self.web3.eth.contract(address=token_address, abi=abi)
            return contract.functions.symbol().call()
        except Exception:
            return "UNKNOWN"
    
    def _get_token_decimals(self, token_address: str) -> int:
        """Get token decimals from address."""
        if not self.web3:
            return 18  # Default to 18 decimals
            
        try:
            # Create ERC20 contract instance
            from web3.contract import Contract
            
            abi = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"}]
            contract = self.web3.eth.contract(address=token_address, abi=abi)
            return contract.functions.decimals().call()
        except Exception:
            return 18  # Default to 18 decimals
    
    def _fallback_simulation(self, tx_params: TxParams) -> Dict[str, Any]:
        """Fallback simulation when Tenderly is not available."""
        logger.info("Using fallback simulation method")
        
        # Use eth_call as a basic simulation mechanism
        try:
            if self.web3:
                # Remove unnecessary fields for eth_call
                call_params = {k: v for k, v in tx_params.items() if k in ["from", "to", "data", "value", "gas"]}
                result = self.web3.eth.call(call_params)
                success = result != "0x" and result != "0x0"
                
                return {
                    "status": "success" if success else "failed",
                    "token_transfers": [],
                    "balance_changes": [],
                    "events": [],
                    "result": result.hex() if isinstance(result, bytes) else result
                }
            else:
                raise ValueError("Web3 instance not available")
        except Exception as e:
            logger.warning(f"Fallback simulation failed: {str(e)}")
            
            # Return a basic response
            return {
                "status": "unknown",
                "token_transfers": [],
                "balance_changes": [],
                "events": [],
                "errors": [str(e)]
            }


class TransactionValidator:
    """
    Handles transaction validation against risk thresholds.
    
    This class provides methods for validating transactions against risk thresholds
    and ensuring they meet security and safety requirements.
    """

    def __init__(
        self, 
        risk_assessment: DeFiRiskAssessmentService,
        risk_threshold: str = "medium",
        simulator: Optional[TransactionSimulator] = None,
    ):
        """
        Initialize the transaction validator.
        
        Args:
            risk_assessment (DeFiRiskAssessmentService): Risk assessment service
            risk_threshold (str): Maximum allowed risk level
            simulator (Optional[TransactionSimulator]): Transaction simulator
        """
        self.risk_assessment = risk_assessment
        self.risk_threshold = risk_threshold
        self.simulator = simulator or TransactionSimulator()

    def validate_transaction(
        self,
        tx_params: TxParams,
        risk_assessment: Optional[RiskAssessment] = None,
        simulate: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate a transaction against risk thresholds.
        
        Args:
            tx_params (TxParams): Transaction parameters to validate
            risk_assessment (Optional[RiskAssessment]): Pre-computed risk assessment
            simulate (bool): Whether to simulate the transaction
            
        Returns:
            Dict[str, Any]: Validation results including:
                - valid: Whether the transaction is valid
                - risk_assessment: Risk assessment results
                - simulation: Simulation results if simulate=True
                - warnings: List of warnings
                - errors: List of errors
        """
        warnings = []
        errors = []
        
        # Simulate the transaction if requested
        simulation = None
        if simulate:
            simulation = self.simulator.simulate_transaction(tx_params)
            if not simulation["success"]:
                errors.extend(simulation["errors"])
            warnings.extend(simulation["warnings"])
        
        # Use the provided risk assessment or perform a new one
        if not risk_assessment:
            # Extract protocol information from transaction parameters
            protocol_info = self._extract_protocol_info_from_tx(tx_params)
            
            if protocol_info:
                # Use the extracted protocol information to perform risk assessment
                risk_service = DeFiRiskAssessmentService()
                risk_assessment = risk_service.assess_transaction_risk(
                    protocol_name=protocol_info["protocol_name"],
                    action=protocol_info["action"],
                    amount=protocol_info["amount"],
                    token_address=protocol_info["token_address"],
                    user_address=tx_params.get("from"),
                )
            else:
                # Default risk assessment if protocol information can't be extracted
                self.logger.warning("Could not extract protocol information for risk assessment", 
                                   tx_hash=tx_params.get("hash"))
                risk_assessment = {
                    "overall_risk": {
                        "level": RiskLevel.MEDIUM,
                        "score": 0.5,
                    },
                    "risk_factors": [
                        {
                            "name": "unknown_protocol",
                            "description": "Unable to identify protocol for this transaction",
                            "level": RiskLevel.MEDIUM,
                            "score": 0.5,
                        }
                    ],
                    "warnings": ["Transaction to unknown protocol or contract"],
                    "recommendations": ["Verify the destination contract before proceeding"],
                }
        
        # Check if the transaction exceeds the risk threshold
        is_risky = self._is_risk_above_threshold(
            risk_assessment["overall_risk"]["level"], 
            self.risk_threshold
        )
        
        if is_risky:
            errors.append(f"Risk level {risk_assessment['overall_risk']['level']} exceeds threshold {self.risk_threshold}")
        
        # Add risk warnings
        warnings.extend(risk_assessment["warnings"])
        
        # Validate basic transaction parameters
        param_validation = self._validate_transaction_parameters(tx_params)
        if not param_validation["valid"]:
            errors.extend(param_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "risk_assessment": risk_assessment,
            "simulation": simulation,
            "warnings": warnings,
            "errors": errors,
        }

    def _extract_protocol_info_from_tx(self, tx_params: TxParams) -> Optional[Dict[str, Any]]:
        """
        Extract protocol information from transaction parameters.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            Optional[Dict[str, Any]]: Extracted protocol information or None if extraction fails
        """
        if not tx_params:
            return None
            
        try:
            # Define known protocol contract addresses
            known_protocols = {
                # SparkDEX contracts
                "0x9A7B675619d3633304134155c6c976E9b4c1cfB3": {
                    "name": "sparkdex", 
                    "type": "dex",
                    "router": "0x9A7B675619d3633304134155c6c976E9b4c1cfB3",
                    "factory": "0x0987654321098765432109876543210987654321"
                },
                # Kinetic contracts
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266": {
                    "name": "kinetic", 
                    "type": "lending",
                    "lending_pool": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
                },
                # Cyclo contracts
                "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199": {
                    "name": "cyclo", 
                    "type": "staking",
                    "staking": "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
                },
                # RainDEX contracts
                "0xdD2FD4581271e230360230F9337D5c0430Bf44C0": {
                    "name": "raindex", 
                    "type": "dex",
                    "router": "0xdD2FD4581271e230360230F9337D5c0430Bf44C0"
                }
            }
            
            # Get the destination address from tx_params
            to_address = tx_params.get("to")
            if not to_address:
                self.logger.warning("Transaction has no destination address")
                return None
                
            # Normalize address
            to_address = self.web3.to_checksum_address(to_address) if self.web3 else to_address
            
            # Check if the destination is a known protocol
            protocol_info = known_protocols.get(to_address)
            if not protocol_info:
                # Check if it might be interacting with a known protocol through a different entry point
                # This would require analyzing the input data in a real implementation
                data = tx_params.get("data", "0x")
                if len(data) > 10:  # At least function selector (0x + 8 chars)
                    selector = data[:10]  # Function selector (e.g., 0xa9059cbb for transfer)
                    
                    # Common function selectors for different protocol actions
                    selectors = {
                        # DEX selectors
                        "0x38ed1739": {"action": "swap", "type": "dex"},  # swapExactTokensForTokens
                        "0x18cbafe5": {"action": "swap", "type": "dex"},  # swapExactETHForTokens
                        "0x4a25d94a": {"action": "swap", "type": "dex"},  # swapTokensForExactTokens
                        "0x791ac947": {"action": "add_liquidity", "type": "dex"},  # addLiquidity
                        "0xe8e33700": {"action": "remove_liquidity", "type": "dex"},  # removeLiquidity
                        
                        # Lending selectors
                        "0xa0712d68": {"action": "deposit", "type": "lending"},  # deposit
                        "0x852a12e3": {"action": "withdraw", "type": "lending"},  # withdraw
                        "0xc04a8a10": {"action": "borrow", "type": "lending"},  # borrow
                        "0x4e4d9fea": {"action": "repay", "type": "lending"},  # repay
                        
                        # Staking selectors
                        "0xa694fc3a": {"action": "stake", "type": "staking"},  # stake
                        "0x3a4b66f1": {"action": "unstake", "type": "staking"},  # unstake
                        "0x3d18b912": {"action": "claim_rewards", "type": "staking"},  # claimRewards
                        
                        # ERC20 token selectors
                        "0xa9059cbb": {"action": "transfer", "type": "token"},  # transfer
                        "0x095ea7b3": {"action": "approve", "type": "token"},  # approve
                        "0x23b872dd": {"action": "transfer_from", "type": "token"},  # transferFrom
                    }
                    
                    if selector in selectors:
                        action_info = selectors[selector]
                        
                        # If we can identify the action but not the specific protocol
                        if action_info["type"] == "dex":
                            # For DEX actions, try to identify the protocol by checking routers
                            for addr, proto in known_protocols.items():
                                if proto["type"] == "dex" and self._is_contract_referenced_in_data(data, addr):
                                    protocol_info = proto
                                    break
                        elif action_info["type"] == "lending":
                            # For lending actions, try to identify the protocol by checking lending pools
                            for addr, proto in known_protocols.items():
                                if proto["type"] == "lending" and self._is_contract_referenced_in_data(data, addr):
                                    protocol_info = proto
                                    break
                        elif action_info["type"] == "staking":
                            # For staking actions, try to identify the protocol by checking staking contracts
                            for addr, proto in known_protocols.items():
                                if proto["type"] == "staking" and self._is_contract_referenced_in_data(data, addr):
                                    protocol_info = proto
                                    break
                                    
                        # If we found a protocol, update with action
                        if protocol_info:
                            protocol_info = {**protocol_info, "action": action_info["action"]}
                        else:
                            # Generic info based on function selector
                            protocol_info = {
                                "name": "unknown",
                                "type": action_info["type"],
                                "action": action_info["action"]
                            }
            
            if not protocol_info:
                self.logger.warning(f"Unknown protocol for address: {to_address}")
                return None
                
            # Extract token information and amount from transaction data
            token_address = "0x0"  # Default to native token
            amount = 0
            
            # Decode transaction data based on protocol type and action
            try:
                data = tx_params.get("data", "0x")
                value = int(tx_params.get("value", 0))
                
                if protocol_info["type"] == "dex":
                    if protocol_info["action"] == "swap":
                        # Use proper ABI decoding for swap function parameters
                        token_info = self._extract_token_from_swap_data(data, to_address)
                        if token_info:
                            token_address = token_info["token_address"]
                            amount = token_info["amount"]
                    elif protocol_info["action"] in ["add_liquidity", "remove_liquidity"]:
                        # Extract from liquidity function parameters
                        token_info = self._extract_token_from_liquidity_data(data, to_address)
                        if token_info:
                            token_address = token_info["token_address"]
                            amount = token_info["amount"]
                elif protocol_info["type"] == "lending":
                    if protocol_info["action"] in ["deposit", "withdraw", "borrow", "repay"]:
                        # Extract from lending function parameters
                        token_info = self._extract_token_from_lending_data(data, to_address)
                        if token_info:
                            token_address = token_info["token_address"]
                            amount = token_info["amount"]
                elif protocol_info["type"] == "staking":
                    if protocol_info["action"] in ["stake", "unstake"]:
                        # Extract from staking function parameters
                        token_info = self._extract_token_from_staking_data(data, to_address)
                        if token_info:
                            token_address = token_info["token_address"]
                            amount = token_info["amount"]
                elif protocol_info["type"] == "token":
                    if protocol_info["action"] == "transfer":
                        # For ERC20 transfers, extract recipient and amount
                        token_address = to_address  # The token contract itself
                        amount = self._extract_amount_from_transfer_data(data)
                
                # If no specific amount found but there is ETH value, use that
                if amount == 0 and value > 0:
                    amount = value
                    token_address = "0x0"  # Native token
            
            except Exception as e:
                self.logger.error("Failed to decode transaction data", error=str(e))
                # Use defaults if decoding fails
            
            # Return the extracted information
            return {
                "protocol_name": protocol_info["name"],
                "action": protocol_info.get("action", "unknown"),
                "amount": amount,
                "token_address": token_address,
                "protocol_type": protocol_info["type"]
            }
            
        except Exception as e:
            self.logger.error("Error extracting protocol information", error=str(e))
            return None
    
    def _is_contract_referenced_in_data(self, data: str, address: str) -> bool:
        """Check if a contract address is referenced in transaction data."""
        if not data or not address:
            return False
            
        # Remove 0x prefix from address and search for it in data
        clean_address = address[2:] if address.startswith("0x") else address
        clean_address = clean_address.lower()
        data_lower = data.lower()
        
        # Check if the address appears in the data (with padding)
        return clean_address in data_lower
    
    def _extract_token_from_swap_data(self, data: str, to_address: str) -> Optional[Dict[str, Any]]:
        """Extract token information from swap transaction data."""
        # This would be implemented using ABI decoding in a real implementation
        # Simplified implementation for the hackathon
        try:
            # Load ABI for the contract
            from web3.contract import Contract
            
            abi = [{"constant":False,"inputs":[{"name":"amount0In","type":"uint256"},{"name":"amount1In","type":"uint256"},{"name":"amount0Out","type":"uint256"},{"name":"amount1Out","type":"uint256"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swap","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]
            contract = self.web3.eth.contract(address=to_address, abi=abi)
            
            # Decode the transaction data
            decoded_data = contract.decode_function_input(data)
            
            # Extract token addresses and amounts
            token_address = decoded_data[1]["amount0In"]  # Assuming token0 is the token we're interested in
            amount = decoded_data[1]["amount0Out"]
            
            return {
                "token_address": token_address,
                "amount": amount
            }
        except Exception:
            return None
    
    def _extract_token_from_liquidity_data(self, data: str, to_address: str) -> Optional[Dict[str, Any]]:
        """Extract token information from liquidity transaction data."""
        # Simplified implementation for the hackathon
        try:
            # Load ABI for the contract
            from web3.contract import Contract
            
            abi = [{"constant":False,"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"amountADesired","type":"uint256"},{"name":"amountBDesired","type":"uint256"},{"name":"amountAMin","type":"uint256"},{"name":"amountBMin","type":"uint256"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]
            contract = self.web3.eth.contract(address=to_address, abi=abi)
            
            # Decode the transaction data
            decoded_data = contract.decode_function_input(data)
            
            # Extract token addresses and amounts
            token_address = decoded_data[1]["tokenA"]  # Assuming tokenA is the token we're interested in
            amount = decoded_data[1]["amountADesired"]
            
            return {
                "token_address": token_address,
                "amount": amount
            }
        except Exception:
            return None
    
    def _extract_token_from_lending_data(self, data: str, to_address: str) -> Optional[Dict[str, Any]]:
        """Extract token information from lending transaction data."""
        # Simplified implementation for the hackathon
        try:
            # Load ABI for the contract
            from web3.contract import Contract
            
            abi = [{"constant":False,"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"interestRateMode","type":"uint256"},{"name":"deadline","type":"uint256"},{"name":"referralCode","type":"uint256"},{"name":"onBehalfOf","type":"address"}],"name":"deposit","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]
            contract = self.web3.eth.contract(address=to_address, abi=abi)
            
            # Decode the transaction data
            decoded_data = contract.decode_function_input(data)
            
            # Extract token addresses and amounts
            token_address = decoded_data[1]["asset"]  # Assuming asset is the token we're interested in
            amount = decoded_data[1]["amount"]
            
            return {
                "token_address": token_address,
                "amount": amount
            }
        except Exception:
            return None
    
    def _extract_token_from_staking_data(self, data: str, to_address: str) -> Optional[Dict[str, Any]]:
        """Extract token information from staking transaction data."""
        # Simplified implementation for the hackathon
        try:
            # Load ABI for the contract
            from web3.contract import Contract
            
            abi = [{"constant":False,"inputs":[{"name":"amount","type":"uint256"}],"name":"stake","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]
            contract = self.web3.eth.contract(address=to_address, abi=abi)
            
            # Decode the transaction data
            decoded_data = contract.decode_function_input(data)
            
            # Extract token addresses and amounts
            token_address = "0x0"  # Assuming the staking token is the native token
            amount = decoded_data[1]["amount"]
            
            return {
                "token_address": token_address,
                "amount": amount
            }
        except Exception:
            return None
    
    def _extract_amount_from_transfer_data(self, data: str) -> int:
        """Extract amount from ERC20 transfer transaction data."""
        try:
            # Load ABI for the contract
            from web3.contract import Contract
            
            abi = [{"constant":False,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]
            contract = self.web3.eth.contract(address="0x0", abi=abi)
            
            # Decode the transaction data
            decoded_data = contract.decode_function_input(data)
            
            # Extract amount
            amount = decoded_data[1]["amount"]
            
            return amount
        except Exception:
            return 0
    
    def _is_risk_above_threshold(self, risk_level: RiskLevel, threshold: str) -> bool:
        """
        Check if a risk level exceeds the specified threshold.
        
        Args:
            risk_level (RiskLevel): Risk level to check
            threshold (str): Maximum allowed risk level
            
        Returns:
            bool: True if the risk level exceeds the threshold
        """
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        threshold_index = risk_order.index(threshold)
        risk_index = risk_order.index(risk_level)
        
        return risk_index > threshold_index
    
    def _validate_transaction_parameters(self, tx_params: TxParams) -> Dict[str, Any]:
        """
        Validate basic transaction parameters.
        
        Args:
            tx_params (TxParams): Transaction parameters
            
        Returns:
            Dict[str, Any]: Validation results
        """
        errors = []
        
        # Check required parameters
        if "from" not in tx_params:
            errors.append("Missing 'from' address")
        
        if "to" not in tx_params:
            errors.append("Missing 'to' address")
        
        # Check for sufficient gas
        if "gas" in tx_params and tx_params["gas"] < 21000:
            errors.append("Gas limit too low")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
