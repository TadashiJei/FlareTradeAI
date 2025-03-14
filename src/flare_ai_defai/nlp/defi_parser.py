"""
DeFi Natural Language Processing Module

This module provides functionality for parsing and understanding natural language
commands related to DeFi operations.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import structlog

from ..semantic_router.categories import DeFiActionCategory

logger = structlog.get_logger(__name__)


@dataclass
class ParsedDeFiCommand:
    """
    Represents a parsed DeFi command.
    
    Attributes:
        action (str): The action to perform (e.g., swap, deposit, stake)
        protocol (Optional[str]): The protocol to use (e.g., sparkdex, kinetic)
        params (Dict[str, str]): Parameters for the action
        raw_command (str): The original command
    """
    action: str
    protocol: Optional[str]
    params: Dict[str, str]
    raw_command: str


class DeFiCommandParser:
    """
    Parses natural language commands related to DeFi operations.
    
    This class provides methods for extracting actions, protocols, and parameters
    from natural language commands.
    """

    # Token patterns for common tokens
    TOKEN_PATTERNS = {
        "FLR": r"(?:FLR|Flare)",
        "USDC": r"(?:USDC|USD Coin)",
        "ETH": r"(?:ETH|Ethereum)",
        "BTC": r"(?:BTC|Bitcoin)",
        "SGB": r"(?:SGB|Songbird)",
    }
    
    # Protocol patterns
    PROTOCOL_PATTERNS = {
        "sparkdex": r"(?:SparkDEX|Spark DEX|Spark)",
        "kinetic": r"(?:Kinetic)",
        "cyclo": r"(?:Cyclo)",
        "raindex": r"(?:RainDEX|Rain DEX|Rain)",
    }
    
    # Action patterns
    ACTION_PATTERNS = {
        "swap": r"(?:swap|exchange|trade|convert)",
        "deposit": r"(?:deposit|add|put)",
        "withdraw": r"(?:withdraw|remove|take out)",
        "borrow": r"(?:borrow|loan|take a loan)",
        "repay": r"(?:repay|pay back|return)",
        "stake": r"(?:stake|staking)",
        "unstake": r"(?:unstake|unstaking|withdraw staked)",
        "claim_rewards": r"(?:claim rewards|claim|get rewards|collect rewards)",
    }
    
    def __init__(self):
        """Initialize the DeFi command parser."""
        self.logger = logger.bind(service="defi_parser")
    
    def parse_command(self, command: str) -> ParsedDeFiCommand:
        """
        Parse a natural language command related to DeFi operations.
        
        Args:
            command (str): The command to parse
            
        Returns:
            ParsedDeFiCommand: The parsed command
        """
        # Extract action
        action = self._extract_action(command)
        
        # Extract protocol
        protocol = self._extract_protocol(command)
        
        # Extract parameters based on action
        params = self._extract_parameters(command, action)
        
        return ParsedDeFiCommand(
            action=action,
            protocol=protocol,
            params=params,
            raw_command=command,
        )
    
    def _extract_action(self, command: str) -> str:
        """
        Extract the action from a command.
        
        Args:
            command (str): The command to extract from
            
        Returns:
            str: The extracted action, or "unknown" if not found
        """
        for action, pattern in self.ACTION_PATTERNS.items():
            if re.search(pattern, command, re.IGNORECASE):
                return action
        
        return "unknown"
    
    def _extract_protocol(self, command: str) -> Optional[str]:
        """
        Extract the protocol from a command.
        
        Args:
            command (str): The command to extract from
            
        Returns:
            Optional[str]: The extracted protocol, or None if not found
        """
        for protocol, pattern in self.PROTOCOL_PATTERNS.items():
            if re.search(pattern, command, re.IGNORECASE):
                return protocol
        
        return None
    
    def _extract_parameters(self, command: str, action: str) -> Dict[str, str]:
        """
        Extract parameters from a command based on the action.
        
        Args:
            command (str): The command to extract from
            action (str): The action to extract parameters for
            
        Returns:
            Dict[str, str]: The extracted parameters
        """
        params = {}
        
        if action == "swap":
            # Extract token_in, token_out, amount_in, slippage
            amount_in, token_in = self._extract_amount_and_token(command, "from|of")
            if amount_in and token_in:
                params["amount_in"] = amount_in
                params["token_in"] = token_in
            
            _, token_out = self._extract_amount_and_token(command, "to|for|into")
            if token_out:
                params["token_out"] = token_out
            
            slippage = self._extract_slippage(command)
            if slippage:
                params["slippage"] = slippage
        
        elif action in ["deposit", "withdraw", "stake", "unstake"]:
            # Extract token and amount
            amount, token = self._extract_amount_and_token(command)
            if amount:
                params["amount"] = amount
            if token:
                params["token"] = token
        
        elif action == "borrow":
            # Extract token and amount
            amount, token = self._extract_amount_and_token(command)
            if amount:
                params["amount"] = amount
            if token:
                params["token"] = token
        
        elif action == "repay":
            # Extract token and amount
            amount, token = self._extract_amount_and_token(command)
            if amount:
                params["amount"] = amount
            if token:
                params["token"] = token
        
        elif action == "claim_rewards":
            # Extract token
            _, token = self._extract_amount_and_token(command, "from|of")
            if token:
                params["token"] = token
        
        return params
    
    def _extract_amount_and_token(
        self, command: str, preposition: str = ""
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract an amount and token from a command.
        
        Args:
            command (str): The command to extract from
            preposition (str, optional): Preposition to look for after the amount
            
        Returns:
            Tuple[Optional[str], Optional[str]]: The extracted amount and token
        """
        # Pattern for amount followed by token
        amount_token_pattern = r"(\d+(?:\.\d+)?)\s*(?:" + preposition + r"\s+)?(" + "|".join(self.TOKEN_PATTERNS.keys()) + r")"
        
        # Try to match the pattern
        match = re.search(amount_token_pattern, command, re.IGNORECASE)
        if match:
            amount = match.group(1)
            token = match.group(2)
            
            # Normalize token
            for token_name, pattern in self.TOKEN_PATTERNS.items():
                if re.match(pattern, token, re.IGNORECASE):
                    token = token_name
                    break
            
            return amount, token
        
        return None, None
    
    def _extract_slippage(self, command: str) -> Optional[str]:
        """
        Extract slippage from a command.
        
        Args:
            command (str): The command to extract from
            
        Returns:
            Optional[str]: The extracted slippage, or None if not found
        """
        # Pattern for slippage
        slippage_pattern = r"(\d+(?:\.\d+)?)\s*%\s*(?:slippage|slip)"
        
        # Try to match the pattern
        match = re.search(slippage_pattern, command, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None


class DeFiCommandProcessor:
    """
    Processes parsed DeFi commands and converts them to executable actions.
    
    This class provides methods for validating and processing parsed DeFi commands,
    converting them to executable actions that can be performed by the protocol
    integrations.
    """
    
    def __init__(self, protocol_factory, token_registry=None, web3=None, token_registry_address=None, token_registry_abi=None, token_api_enabled=False, token_api_url=None, token_api_key=None):
        """
        Initialize the DeFi command processor.
        
        Args:
            protocol_factory: Factory for creating protocol instances
            token_registry: Token registry service
            web3: Web3 provider
            token_registry_address: Address of token registry contract
            token_registry_abi: ABI of token registry contract
            token_api_enabled: Whether to use token API
            token_api_url: URL of token API
            token_api_key: Key for token API
        """
        self.protocol_factory = protocol_factory
        self.token_registry = token_registry
        self.web3 = web3
        self.token_registry_address = token_registry_address
        self.token_registry_abi = token_registry_abi
        self.token_api_enabled = token_api_enabled
        self.token_api_url = token_api_url
        self.token_api_key = token_api_key
        self.parser = DeFiCommandParser()
        self.logger = logger.bind(service="defi_processor")
    
    def process_command(self, command: str) -> Dict:
        """
        Process a natural language command related to DeFi operations.
        
        Args:
            command (str): The command to process
            
        Returns:
            Dict: The processing results, including:
                - success: Whether the processing was successful
                - action: The action to perform
                - protocol: The protocol to use
                - params: Parameters for the action
                - errors: List of errors if any
        """
        # Parse the command
        parsed = self.parser.parse_command(command)
        
        # Validate the parsed command
        validation = self._validate_parsed_command(parsed)
        if not validation["valid"]:
            return {
                "success": False,
                "action": parsed.action,
                "protocol": parsed.protocol,
                "params": parsed.params,
                "errors": validation["errors"],
            }
        
        # Determine the protocol if not specified
        if not parsed.protocol:
            parsed.protocol = self._determine_protocol(parsed.action, parsed.params)
        
        # Convert to executable action
        try:
            protocol = self.protocol_factory.get_protocol(parsed.protocol)
            
            # Prepare transaction parameters based on action
            if parsed.action == "swap":
                tx_params = protocol.prepare_swap_transaction(
                    token_in_address=self._get_token_address(parsed.params["token_in"]),
                    token_out_address=self._get_token_address(parsed.params["token_out"]),
                    amount_in=float(parsed.params["amount_in"]),
                    min_amount_out=self._calculate_min_amount_out(
                        float(parsed.params["amount_in"]),
                        float(parsed.params.get("slippage", "1")),
                    ),
                    deadline=self._get_deadline(),
                )
            elif parsed.action == "deposit":
                tx_params = protocol.prepare_deposit_transaction(
                    asset_address=self._get_token_address(parsed.params["token"]),
                    amount=float(parsed.params["amount"]),
                )
            elif parsed.action == "withdraw":
                tx_params = protocol.prepare_withdraw_transaction(
                    asset_address=self._get_token_address(parsed.params["token"]),
                    amount=float(parsed.params["amount"]),
                )
            elif parsed.action == "stake":
                tx_params = protocol.prepare_stake_transaction(
                    token_address=self._get_token_address(parsed.params["token"]),
                    amount=float(parsed.params["amount"]),
                )
            elif parsed.action == "unstake":
                tx_params = protocol.prepare_unstake_transaction(
                    token_address=self._get_token_address(parsed.params["token"]),
                    amount=float(parsed.params["amount"]),
                )
            elif parsed.action == "claim_rewards":
                tx_params = protocol.prepare_claim_rewards_transaction(
                    token_address=self._get_token_address(parsed.params.get("token")),
                )
            else:
                return {
                    "success": False,
                    "action": parsed.action,
                    "protocol": parsed.protocol,
                    "params": parsed.params,
                    "errors": ["Unsupported action"],
                }
            
            return {
                "success": True,
                "action": parsed.action,
                "protocol": parsed.protocol,
                "params": parsed.params,
                "tx_params": tx_params,
            }
        
        except Exception as e:
            return {
                "success": False,
                "action": parsed.action,
                "protocol": parsed.protocol,
                "params": parsed.params,
                "errors": [str(e)],
            }
    
    def _validate_parsed_command(self, parsed: ParsedDeFiCommand) -> Dict:
        """
        Validate a parsed DeFi command.
        
        Args:
            parsed (ParsedDeFiCommand): The parsed command to validate
            
        Returns:
            Dict: The validation results, including:
                - valid: Whether the command is valid
                - errors: List of errors if any
        """
        errors = []
        
        # Check if action is supported
        if parsed.action == "unknown":
            errors.append("Unknown action")
        
        # Check if required parameters are present
        if parsed.action == "swap":
            if "token_in" not in parsed.params:
                errors.append("Missing input token")
            if "token_out" not in parsed.params:
                errors.append("Missing output token")
            if "amount_in" not in parsed.params:
                errors.append("Missing input amount")
        
        elif parsed.action in ["deposit", "withdraw", "stake", "unstake", "borrow", "repay"]:
            if "token" not in parsed.params:
                errors.append("Missing token")
            if "amount" not in parsed.params:
                errors.append("Missing amount")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
    
    def _determine_protocol(self, action: str, params: Dict[str, str]) -> str:
        """
        Determine the protocol to use based on the action and parameters.
        
        Args:
            action (str): The action to perform
            params (Dict[str, str]): Parameters for the action
            
        Returns:
            str: The protocol to use
        """
        # Default protocols based on action
        if action == "swap":
            return "sparkdex"
        elif action in ["deposit", "withdraw", "borrow", "repay"]:
            return "kinetic"
        elif action in ["stake", "unstake", "claim_rewards"]:
            return "cyclo"
        
        return "sparkdex"  # Default to SparkDEX
    
    def _get_token_address(self, token: str) -> str:
        """
        Look up a token address by symbol.
        
        Args:
            token (str): The token symbol
            
        Returns:
            str: The token address
        """
        try:
            # Standardize token symbol
            token = token.upper().strip()
            
            # First check if the input is already an address
            if token.startswith("0X") or token.startswith("0x"):
                if len(token) == 42:  # Standard address length with 0x prefix
                    return token
            
            # Use token registry service to get canonical addresses
            if self.token_registry:
                address = self.token_registry.get_token_address(token)
                if address:
                    self.logger.info(f"Found token address from registry", 
                                    token=token, 
                                    address=address)
                    return address
            
            # Fallback to well-known tokens on Flare network
            well_known_tokens = {
                # Flare Network Tokens
                "FLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
                "WFLR": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",  # Wrapped FLR
                
                # Stablecoins
                "USDC": "0xe3F5a90F9cb311505cd691a46596599aA1A0AD7D",
                "USDT": "0xC67DCB4307C0856AC800a99A4CA8e2bd20749E21",
                "DAI": "0x8A5eC7F68B7b6aC9BBb7C4cBcf3Ef43adF0F653c",
                
                # Major Tokens
                "ETH": "0x8A6fa2E13728d68D577eA24cBF7b5B3C3f279B1C",
                "WETH": "0x8A6fa2E13728d68D577eA24cBF7b5B3C3f279B1C",  # Wrapped ETH
                "BTC": "0x1aAF048D8cAf1dF75ad43c2e90B51A198EcAB05D",
                "WBTC": "0x1aAF048D8cAf1dF75ad43c2e90B51A198EcAB05D",  # Wrapped BTC
                
                # Songbird Tokens
                "SGB": "0xbF6bfE5d6B86308c9eb59194B9Cd08f3B3C4659B",
                "WSGB": "0xbF6bfE5d6B86308c9eb59194B9Cd08f3B3C4659B",  # Wrapped SGB
                
                # LP Tokens for common pairs
                "FLR-USDC": "0xd7E7bD6B6Bb768f6155cdB7777E4727dEe5C1dFF",
                "ETH-USDC": "0x4b0955594d3Aa6E5a83FC1C10c98c31D9151EbB6",
                "BTC-USDC": "0x0A2e6bA0262aA153F6bF9d3166b4F8E340d62d8d",
            }
            
            if token in well_known_tokens:
                self.logger.info(f"Found token in well-known list", 
                               token=token, 
                               address=well_known_tokens[token])
                return well_known_tokens[token]
            
            # If still not found, check if we can query an on-chain address registry
            # This would connect to a blockchain contract that maps symbols to addresses
            if self.web3:
                try:
                    registry_contract = self.web3.eth.contract(
                        address=self.token_registry_address,
                        abi=self.token_registry_abi
                    )
                    address = registry_contract.functions.getAddressBySymbol(token).call()
                    if address and address != "0x0000000000000000000000000000000000000000":
                        self.logger.info(f"Found token address from on-chain registry", 
                                       token=token, 
                                       address=address)
                        return address
                except Exception as e:
                    self.logger.warning(f"Failed to query on-chain registry", 
                                      token=token, 
                                      error=str(e))
            
            # Last resort: try to query a token address API
            if self.token_api_enabled:
                try:
                    import requests
                    response = requests.get(
                        f"{self.token_api_url}/token/{token}",
                        headers={"Authorization": f"Bearer {self.token_api_key}"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data and "address" in data:
                            self.logger.info(f"Found token address from API", 
                                           token=token, 
                                           address=data["address"])
                            return data["address"]
                except Exception as e:
                    self.logger.warning(f"Failed to query token API", 
                                      token=token, 
                                      error=str(e))
            
            # If we still can't find it, log a warning and return zero address
            self.logger.warning(f"Unknown token symbol", token=token)
            return "0x0000000000000000000000000000000000000000"
            
        except Exception as e:
            self.logger.error(f"Error getting token address", 
                            token=token, 
                            error=str(e))
            return "0x0000000000000000000000000000000000000000"
    
    def _calculate_min_amount_out(self, amount_in: float, slippage: float) -> float:
        """
        Calculate the minimum amount out for a swap based on slippage tolerance.
        
        Args:
            amount_in (float): Input amount
            slippage (float): Slippage tolerance percentage
            
        Returns:
            float: The minimum amount out
        """
        try:
            # Validate inputs
            if amount_in <= 0:
                self.logger.warning("Invalid amount_in for min_amount calculation", 
                                   amount_in=amount_in)
                return 0
                
            if slippage < 0:
                self.logger.warning("Negative slippage provided, using absolute value", 
                                   slippage=slippage)
                slippage = abs(slippage)
                
            # Cap slippage at a reasonable maximum (50%) to prevent mistakes
            if slippage > 50:
                self.logger.warning("Extremely high slippage provided, capping at 50%", 
                                  original_slippage=slippage)
                slippage = 50
                
            # Calculate minimum amount out with slippage tolerance
            # Slippage is applied as a percentage reduction from the expected amount
            min_amount_out = amount_in * (1 - slippage / 100)
            
            # Ensure non-negative result
            min_amount_out = max(0, min_amount_out)
            
            self.logger.info("Calculated minimum amount out", 
                           amount_in=amount_in, 
                           slippage=slippage, 
                           min_amount_out=min_amount_out)
                           
            return min_amount_out
            
        except Exception as e:
            self.logger.error("Error calculating minimum amount out", 
                             amount_in=amount_in, 
                             slippage=slippage, 
                             error=str(e))
            # Default to a conservative 1% slippage in case of error
            return amount_in * 0.99
    
    def _get_deadline(self) -> int:
        """
        Get a deadline timestamp for a transaction.
        
        Returns:
            int: The deadline timestamp
        """
        import time
        return int(time.time()) + 3600  # 1 hour from now
