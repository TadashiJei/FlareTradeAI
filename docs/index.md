# FlareTrade Documentation

Welcome to the FlareTrade documentation. This documentation provides comprehensive information about the FlareTrade project, including its DeFi protocol integrations, risk assessment system, wallet management, and more.

## Table of Contents

### Core Components

- [DeFi Protocol Integrations](defi_integrations.md)
- [Protocol Factory](protocol_factory.md)
- [Risk Assessment System](risk_assessment.md)
- [Transaction Validation](transaction_validation.md)
- [Secure Wallet Management](wallet_management.md)

### Protocol Integrations

- [SparkDEX](protocols/sparkdex.md)
- [Kinetic](protocols/kinetic.md)
- [Cyclo](protocols/cyclo.md)
- [RainDEX](protocols/raindex.md)

### Development

- [Getting Started](getting_started.md)
- [Contributing](contributing.md)
- [Testing](testing.md)

## Overview

FlareTrade is an AI-driven DeFi agent that integrates with Flare's ecosystem using TEE-secured LLMs. The project aims to transform imperative commands into declarative blockchain instructions and enable multimodal blockchain interactions.

Key components include:
1. DeFi integrations with Flare ecosystem applications (SparkDEX, Kinetic, Cyclo, RainDEX)
2. Risk assessment mechanisms for transactions
3. Enhanced natural language processing for DeFi operations
4. Secure wallet management with TEE protection

The project uses Gemini AI models and runs in a Trusted Execution Environment (TEE) with vTPM attestations.

## Quick Start

To get started with FlareTrade, follow these steps:

1. Clone the repository
2. Install dependencies
3. Configure environment variables
4. Run the application

For detailed instructions, see the [Getting Started](getting_started.md) guide.

## Architecture

FlareTrade follows a modular architecture, with clear separation of concerns between different components:

- **Protocol Integrations**: Each DeFi protocol has its own module, inheriting from a common base class
- **Protocol Factory**: Provides a centralized way to access all supported protocols
- **Risk Assessment**: Evaluates the risk of DeFi operations
- **Transaction Validation**: Simulates and validates transactions before execution
- **Wallet Management**: Securely manages wallet operations within a TEE

This modular design ensures that the codebase is maintainable and extensible, allowing for easy addition of new protocols and features in the future.
