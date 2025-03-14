# FlareTrade DeFi Protocol Integrations

This document provides comprehensive information about the DeFi protocol integrations implemented in the FlareTrade project, including usage instructions, supported operations, and risk assessment guidelines.

## Table of Contents

- [Overview](#overview)
- [Protocol Integrations](#protocol-integrations)
  - [SparkDEX](#sparkdex)
  - [Kinetic](#kinetic)
  - [Cyclo](#cyclo)
  - [RainDEX](#raindex)
- [Risk Assessment](#risk-assessment)
- [Transaction Validation](#transaction-validation)
- [Wallet Management](#wallet-management)
- [Usage Examples](#usage-examples)

## Overview

FlareTrade integrates with multiple DeFi protocols in the Flare ecosystem, providing a unified interface for performing various DeFi operations. The integrations are designed to be modular, maintainable, and extensible, allowing for easy addition of new protocols in the future.

All protocol integrations inherit from a common base class (`BaseProtocol`), ensuring a consistent interface and behavior across different protocols. The integrations also include risk assessment, transaction validation, and secure wallet management features.

## Protocol Integrations

### SparkDEX

SparkDEX is a decentralized exchange (DEX) that allows users to swap tokens and provide liquidity.

**Supported Operations:**
- Token swaps
- Liquidity provision
- Liquidity removal
- Price quotes

**Example Usage:**
```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get the SparkDEX protocol instance
sparkdex = factory.get_protocol("sparkdex")

# Prepare a swap transaction
tx_params = sparkdex.prepare_swap_transaction(
    token_in_address="0x1234...",
    token_out_address="0x5678...",
    amount_in=100,
    min_amount_out=95,  # 5% slippage
    deadline=int(time.time()) + 3600,  # 1 hour from now
)

# Execute the transaction
tx_hash = web3.eth.send_transaction(tx_params)
```

### Kinetic

Kinetic is a lending and borrowing platform that allows users to deposit assets as collateral and borrow other assets against that collateral.

**Supported Operations:**
- Deposit assets
- Withdraw assets
- Borrow assets
- Repay loans
- View lending rates
- View borrowing rates
- View collateral factors

**Example Usage:**
```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get the Kinetic protocol instance
kinetic = factory.get_protocol("kinetic")

# Prepare a deposit transaction
tx_params = kinetic.prepare_deposit_transaction(
    asset_address="0x1234...",
    amount=500,
)

# Execute the transaction
tx_hash = web3.eth.send_transaction(tx_params)
```

### Cyclo

Cyclo is a yield farming platform that allows users to stake tokens and earn rewards.

**Supported Operations:**
- Stake tokens
- Unstake tokens
- Claim rewards
- View APY rates
- View reward balances

**Example Usage:**
```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get the Cyclo protocol instance
cyclo = factory.get_protocol("cyclo")

# Prepare a stake transaction
tx_params = cyclo.prepare_stake_transaction(
    token_address="0x1234...",
    amount=1000,
)

# Execute the transaction
tx_hash = web3.eth.send_transaction(tx_params)
```

### RainDEX

RainDEX is another decentralized exchange with a focus on low slippage and high capital efficiency.

**Supported Operations:**
- Token swaps
- Liquidity provision
- Liquidity removal
- Price quotes

**Example Usage:**
```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get the RainDEX protocol instance
raindex = factory.get_protocol("raindex")

# Prepare a swap transaction
tx_params = raindex.prepare_swap_transaction(
    token_in_address="0x1234...",
    token_out_address="0x5678...",
    amount_in=100,
    min_amount_out=95,  # 5% slippage
    deadline=int(time.time()) + 3600,  # 1 hour from now
)

# Execute the transaction
tx_hash = web3.eth.send_transaction(tx_params)
```

## Risk Assessment

FlareTrade includes a risk assessment service that evaluates the risk of DeFi transactions and operations. The service provides risk assessments for:

- Individual transactions
- Portfolio positions
- Protocol usage

Risk levels are categorized as:
- **Low**: Minimal risk, suitable for most users
- **Medium**: Moderate risk, users should be aware of potential issues
- **High**: Significant risk, users should exercise caution
- **Critical**: Extreme risk, not recommended for most users

**Example Usage:**
```python
from flare_ai_defai.blockchain.risk.assessment import DeFiRiskAssessmentService

# Initialize the risk assessment service
risk_service = DeFiRiskAssessmentService()

# Assess the risk of a transaction
risk_assessment = risk_service.assess_transaction(tx_params)

# Check the overall risk level
if risk_assessment.overall_risk.value == "high":
    print("Warning: This transaction has a high risk level!")
    
# Print the risk factors
for factor in risk_assessment.factors:
    print(f"Risk Factor: {factor.name}")
    print(f"Description: {factor.description}")
    print(f"Level: {factor.level.value}")
    print(f"Impact: {factor.impact}")
    print(f"Mitigation: {factor.mitigation}")
```

## Transaction Validation

FlareTrade includes a transaction validation service that simulates transactions before they are executed on-chain. The service checks for:

- Transaction success/failure
- Gas estimation
- Error messages
- Risk assessment

**Example Usage:**
```python
from flare_ai_defai.blockchain.transaction import TransactionValidator

# Initialize the transaction validator
validator = TransactionValidator(web3)

# Simulate a transaction
simulation = validator.simulate_transaction(tx_params)

# Check if the simulation was successful
if not simulation["success"]:
    print("Transaction simulation failed!")
    for error in simulation["errors"]:
        print(f"Error: {error}")
else:
    print(f"Estimated gas: {simulation['gas_estimate']}")

# Validate a transaction against risk thresholds
validation = validator.validate_transaction(
    tx_params,
    context={"protocol": "sparkdex", "operation": "swap"},
    risk_threshold="medium",
)

# Check if the transaction is valid
if not validation["valid"]:
    print("Transaction validation failed!")
    for warning in validation["warnings"]:
        print(f"Warning: {warning}")
    for error in validation["errors"]:
        print(f"Error: {error}")
```

## Wallet Management

FlareTrade includes a secure wallet management system with TEE validation, ensuring that sensitive wallet operations are protected. The system provides:

- Secure account creation
- Transaction signing
- TEE-based validation
- Wallet backup and restoration

**Example Usage:**
```python
from flare_ai_defai.blockchain.wallet import SecureWalletManager
from flare_ai_defai.blockchain.attestation import Vtpm

# Initialize the wallet manager
vtpm = Vtpm()
wallet_manager = SecureWalletManager(web3, vtpm)

# Create a new account
address = wallet_manager.create_account()
print(f"New account address: {address}")

# Sign a transaction
signed_tx = wallet_manager.sign_transaction(tx_params)

# Send the signed transaction
tx_hash = web3.eth.send_raw_transaction(signed_tx)
```

## Usage Examples

### Complete Swap Workflow

```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory
from flare_ai_defai.blockchain.transaction import TransactionValidator
from flare_ai_defai.blockchain.wallet import SecureWalletManager
from flare_ai_defai.blockchain.attestation import Vtpm

# Initialize components
vtpm = Vtpm()
wallet_manager = SecureWalletManager(web3, vtpm)
validator = TransactionValidator(web3)
factory = ProtocolFactory(web3, wallet_manager.create_account())

# Get the SparkDEX protocol instance
sparkdex = factory.get_protocol("sparkdex")

# Prepare a swap transaction
tx_params = sparkdex.prepare_swap_transaction(
    token_in_address="0x1234...",
    token_out_address="0x5678...",
    amount_in=100,
    min_amount_out=95,
    deadline=int(time.time()) + 3600,
)

# Validate the transaction
validation = validator.validate_transaction(
    tx_params,
    context={"protocol": "sparkdex", "operation": "swap"},
    risk_threshold="medium",
)

# Check if the transaction is valid
if validation["valid"]:
    # Sign the transaction
    signed_tx = wallet_manager.sign_transaction(tx_params)
    
    # Send the signed transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx)
    print(f"Transaction hash: {tx_hash.hex()}")
else:
    print("Transaction validation failed!")
    for warning in validation["warnings"]:
        print(f"Warning: {warning}")
    for error in validation["errors"]:
        print(f"Error: {error}")
```

### Natural Language Interface

FlareTrade provides a natural language interface for DeFi operations, allowing users to interact with the system using simple commands. The system uses prompt templates to generate appropriate blockchain instructions based on user commands.

**Example User Commands:**
- "Swap 100 FLR for USDC with 1% slippage"
- "Deposit 500 USDC into Kinetic"
- "Withdraw 200 USDC from Kinetic"
- "Stake 1000 FLR in Cyclo"
- "Unstake 500 FLR from Cyclo"
- "Claim my FLR rewards from Cyclo"

The system will parse these commands, extract the relevant parameters, and execute the corresponding blockchain operations.
