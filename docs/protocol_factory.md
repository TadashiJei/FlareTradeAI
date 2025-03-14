# FlareTrade Protocol Factory

This document provides detailed information about the protocol factory implemented in the FlareTrade project, which serves as a central hub for accessing and managing all supported DeFi protocol integrations.

## Table of Contents

- [Overview](#overview)
- [Supported Protocols](#supported-protocols)
- [Implementation Details](#implementation-details)
- [Usage Examples](#usage-examples)
- [Extending the Factory](#extending-the-factory)

## Overview

The protocol factory in FlareTrade provides a centralized way to access all supported DeFi protocols in the Flare ecosystem. It follows the factory design pattern, allowing for easy instantiation of protocol objects without exposing the creation logic to the client code.

The factory maintains a mapping of protocol names to their respective implementation classes, making it easy to get an instance of any supported protocol by name. This approach provides several benefits:

1. **Centralized Protocol Management**: All protocol implementations are managed in one place, making it easy to add, remove, or modify protocols.
2. **Consistent Interface**: All protocols accessed through the factory adhere to the same interface, ensuring consistent behavior.
3. **Simplified Client Code**: Client code can get protocol instances without needing to know the specific implementation details.
4. **Runtime Protocol Selection**: Protocols can be selected at runtime based on user input or other factors.

## Supported Protocols

The protocol factory currently supports the following DeFi protocols:

1. **SparkDEX**: A decentralized exchange for token swaps and liquidity provision.
2. **Kinetic**: A lending and borrowing platform for depositing, withdrawing, borrowing, and repaying assets.
3. **Cyclo**: A yield farming platform for staking, unstaking, and claiming rewards.
4. **RainDEX**: Another decentralized exchange with a focus on low slippage and high capital efficiency.

Each protocol implementation inherits from the `BaseProtocol` class, ensuring a consistent interface and behavior across different protocols.

## Implementation Details

The protocol factory is implemented through the `ProtocolFactory` class:

```python
class ProtocolFactory:
    """
    Factory class for creating and managing protocol instances.
    
    This class provides a centralized way to access all supported DeFi protocols
    in the Flare ecosystem.
    """

    PROTOCOL_MAP: Dict[str, Type[BaseProtocol]] = {
        "sparkdex": SparkDEX,
        "kinetic": Kinetic,
        "cyclo": Cyclo,
        "raindex": RainDEX,
    }

    def __init__(self, web3: Web3, address: str = None, network: str = "flare"):
        """
        Initialize the protocol factory.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
            address (str, optional): User's address for transactions
            network (str): Network to use (flare or songbird)
        """
        self.web3 = web3
        self.address = address
        self.network = network

    def get_protocol(self, protocol_name: str) -> BaseProtocol:
        """
        Get an instance of a protocol.
        
        Args:
            protocol_name (str): Name of the protocol to get
            
        Returns:
            BaseProtocol: Instance of the requested protocol
            
        Raises:
            ValueError: If protocol is not supported
        """
        protocol_class = self.PROTOCOL_MAP.get(protocol_name.lower())
        if not protocol_class:
            msg = f"Protocol '{protocol_name}' not supported"
            raise ValueError(msg)
        
        return protocol_class(self.web3, self.address, self.network)

    def get_all_protocols(self) -> Dict[str, BaseProtocol]:
        """
        Get instances of all supported protocols.
        
        Returns:
            Dict[str, BaseProtocol]: Dictionary of protocol instances
        """
        return {
            name: protocol_class(self.web3, self.address, self.network)
            for name, protocol_class in self.PROTOCOL_MAP.items()
        }

    def get_supported_protocols(self) -> Dict[str, str]:
        """
        Get information about supported protocols.
        
        Returns:
            Dict[str, str]: Dictionary mapping protocol names to descriptions
        """
        return {
            name: protocol_class.__doc__.strip() if protocol_class.__doc__ else ""
            for name, protocol_class in self.PROTOCOL_MAP.items()
        }
```

## Usage Examples

### Getting a Specific Protocol

```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get the SparkDEX protocol instance
sparkdex = factory.get_protocol("sparkdex")

# Use the protocol instance
tx_params = sparkdex.prepare_swap_transaction(
    token_in_address="0x1234...",
    token_out_address="0x5678...",
    amount_in=100,
    min_amount_out=95,
    deadline=int(time.time()) + 3600,
)
```

### Getting All Protocols

```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get instances of all supported protocols
protocols = factory.get_all_protocols()

# Use the protocols
for name, protocol in protocols.items():
    print(f"Protocol: {name}")
    info = protocol.get_info()
    print(f"Description: {info.description}")
    print(f"Version: {info.version}")
    print(f"Website: {info.website}")
```

### Getting Information About Supported Protocols

```python
from flare_ai_defai.blockchain.protocols.factory import ProtocolFactory

# Initialize the protocol factory
factory = ProtocolFactory(web3, user_address)

# Get information about supported protocols
protocol_info = factory.get_supported_protocols()

# Display the information
for name, description in protocol_info.items():
    print(f"Protocol: {name}")
    print(f"Description: {description}")
```

## Extending the Factory

The protocol factory can be easily extended to support new protocols by adding them to the `PROTOCOL_MAP` dictionary. Here's an example of how to add a new protocol:

1. Implement the new protocol class, inheriting from `BaseProtocol`:

```python
class NewProtocol(BaseProtocol):
    """
    New protocol integration.
    
    This protocol provides new DeFi functionality.
    """
    
    def __init__(self, web3, address=None, network="flare"):
        super().__init__(web3, address, network)
        # Protocol-specific initialization
        
    def get_info(self):
        return ProtocolInfo(
            name="NewProtocol",
            description="New protocol integration",
            version="1.0.0",
            website="https://newprotocol.example.com",
        )
        
    # Implement other required methods
```

2. Add the new protocol to the `PROTOCOL_MAP` in the `ProtocolFactory` class:

```python
class ProtocolFactory:
    PROTOCOL_MAP: Dict[str, Type[BaseProtocol]] = {
        "sparkdex": SparkDEX,
        "kinetic": Kinetic,
        "cyclo": Cyclo,
        "raindex": RainDEX,
        "newprotocol": NewProtocol,  # Add the new protocol
    }
    
    # Rest of the class remains the same
```

3. The new protocol is now available through the factory:

```python
# Get the new protocol instance
new_protocol = factory.get_protocol("newprotocol")

# Use the new protocol
# ...
```

This extensibility makes it easy to add support for new protocols as they become available in the Flare ecosystem, without requiring changes to the client code that uses the factory.
