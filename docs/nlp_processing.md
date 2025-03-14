# Natural Language Processing for DeFi Operations

This document provides an overview of the natural language processing capabilities in FlareTrade, specifically focused on DeFi operations.

## Overview

The NLP module in FlareTrade enables the AI agent to understand and process natural language commands related to DeFi operations. This allows users to interact with the system using natural language, without having to learn a specific syntax or command structure.

## Components

### DeFiCommandParser

The `DeFiCommandParser` class is responsible for parsing natural language commands and extracting relevant information such as:

- The action to perform (e.g., swap, deposit, stake)
- The protocol to use (e.g., SparkDEX, Kinetic)
- Parameters for the action (e.g., token, amount, slippage)

```python
from flare_ai_defai.nlp.defi_parser import DeFiCommandParser

parser = DeFiCommandParser()
parsed_command = parser.parse_command("Swap 10 ETH to USDC on SparkDEX with 0.5% slippage")

print(parsed_command.action)  # "swap"
print(parsed_command.protocol)  # "sparkdex"
print(parsed_command.params)  # {"token_in": "ETH", "token_out": "USDC", "amount_in": "10", "slippage": "0.5"}
```

### DeFiCommandProcessor

The `DeFiCommandProcessor` class takes the parsed command and converts it to executable actions that can be performed by the protocol integrations. It handles:

- Validating the parsed command
- Determining the protocol to use if not specified
- Converting the command to transaction parameters

```python
from flare_ai_defai.nlp.defi_parser import DeFiCommandProcessor
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

protocol_factory = ProtocolFactory()
processor = DeFiCommandProcessor(protocol_factory)

result = processor.process_command("Swap 10 ETH to USDC on SparkDEX with 0.5% slippage")

if result["success"]:
    # Execute the transaction
    tx_params = result["tx_params"]
    # ...
else:
    # Handle errors
    errors = result["errors"]
    # ...
```

## Supported Commands

The NLP module supports the following types of commands:

### Swap

Swap one token for another on a DEX.

**Examples:**
- "Swap 10 ETH to USDC"
- "Exchange 5 FLR for BTC on SparkDEX"
- "Trade 100 USDC for ETH with 1% slippage"

### Deposit

Deposit tokens into a lending protocol.

**Examples:**
- "Deposit 10 ETH into Kinetic"
- "Add 100 USDC to Kinetic"

### Withdraw

Withdraw tokens from a lending protocol.

**Examples:**
- "Withdraw 5 ETH from Kinetic"
- "Remove 50 USDC from Kinetic"

### Borrow

Borrow tokens from a lending protocol.

**Examples:**
- "Borrow 10 ETH from Kinetic"
- "Take a loan of 100 USDC from Kinetic"

### Repay

Repay a loan on a lending protocol.

**Examples:**
- "Repay 5 ETH loan on Kinetic"
- "Pay back 50 USDC to Kinetic"

### Stake

Stake tokens in a staking protocol.

**Examples:**
- "Stake 10 FLR on Cyclo"
- "Stake 100 SGB"

### Unstake

Unstake tokens from a staking protocol.

**Examples:**
- "Unstake 5 FLR from Cyclo"
- "Withdraw staked 50 SGB"

### Claim Rewards

Claim rewards from a staking protocol.

**Examples:**
- "Claim rewards from Cyclo"
- "Get rewards for staked FLR"

## Integration with Other Components

The NLP module integrates with other components of the FlareTrade system:

- **Protocol Factory**: The command processor uses the protocol factory to access the appropriate protocol for executing the command.
- **Risk Assessment**: Before executing a command, the system performs a risk assessment to ensure the operation is safe.
- **Transaction Validation**: The system validates the transaction parameters before execution.
- **Wallet Management**: The system uses the secure wallet manager to sign and send transactions.

## Extending the NLP Module

To add support for new commands or protocols:

1. Add new patterns to the `ACTION_PATTERNS` or `PROTOCOL_PATTERNS` dictionaries in `DeFiCommandParser`.
2. Implement the parameter extraction logic for the new action in `_extract_parameters`.
3. Add validation logic for the new action in `_validate_parsed_command`.
4. Implement the transaction preparation logic for the new action in `process_command`.

## Future Enhancements

Planned enhancements for the NLP module include:

- Support for more complex commands (e.g., "Swap 10 ETH to USDC and then stake the USDC")
- Improved parameter extraction using machine learning
- Support for multimodal input (text, voice, images)
- Context-aware command processing (e.g., remembering previous commands)
- Natural language feedback and explanations for users
