"""
Simple test for DeFi NLP parsing functionality.
"""

import re
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ParsedDeFiCommand:
    """Represents a parsed DeFi command."""
    action: str
    protocol: Optional[str]
    params: Dict[str, str]
    raw_command: str

class SimpleNLPParser:
    """A simplified version of the DeFiCommandParser for testing."""
    
    # Token patterns
    TOKEN_PATTERNS = {
        "FLR": r"(?:FLR|Flare)",
        "USDC": r"(?:USDC|USD Coin)",
        "ETH": r"(?:ETH|Ethereum)",
        "BTC": r"(?:BTC|Bitcoin)",
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
    
    def parse_command(self, command: str) -> ParsedDeFiCommand:
        """Parse a natural language command related to DeFi operations."""
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
        """Extract the action from a command."""
        for action, pattern in self.ACTION_PATTERNS.items():
            if re.search(pattern, command, re.IGNORECASE):
                return action
        return "unknown"
    
    def _extract_protocol(self, command: str) -> Optional[str]:
        """Extract the protocol from a command."""
        for protocol, pattern in self.PROTOCOL_PATTERNS.items():
            if re.search(pattern, command, re.IGNORECASE):
                return protocol
        return None
    
    def _extract_parameters(self, command: str, action: str) -> Dict[str, str]:
        """Extract parameters from a command based on the action."""
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
    
    def _extract_amount_and_token(self, command: str, preposition: str = "") -> tuple:
        """Extract an amount and token from a command."""
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
        """Extract slippage from a command."""
        # Pattern for slippage
        slippage_pattern = r"(\d+(?:\.\d+)?)\s*%\s*(?:slippage|slip)"
        
        # Try to match the pattern
        match = re.search(slippage_pattern, command, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None

def test_parser():
    """Test the SimpleNLPParser with various commands."""
    parser = SimpleNLPParser()
    
    # Test various commands
    test_commands = [
        "Swap 10 ETH to USDC on SparkDEX with 0.5% slippage",
        "Deposit 100 USDC into Kinetic",
        "Withdraw 50 USDC from Kinetic",
        "Stake 10 FLR on Cyclo",
        "Unstake 5 FLR from Cyclo",
        "Claim rewards from Cyclo",
        "Borrow 20 ETH from Kinetic",
        "Repay 15 ETH loan on Kinetic"
    ]
    
    for command in test_commands:
        print(f"\nTesting command: '{command}'")
        parsed = parser.parse_command(command)
        
        print(f"Action: {parsed.action}")
        print(f"Protocol: {parsed.protocol}")
        print(f"Parameters: {parsed.params}")

if __name__ == "__main__":
    print("Testing DeFi NLP Module")
    print("======================")
    test_parser()
