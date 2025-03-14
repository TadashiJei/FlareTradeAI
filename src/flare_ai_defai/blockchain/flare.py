"""
Flare Network Provider Module

This module provides a FlareProvider class for interacting with the Flare Network.
It handles account management, transaction queuing, and blockchain interactions.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import structlog
import os
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams
# Updated middleware import for web3.py 7.8.0
from web3.middleware import ExtraDataToPOAMiddleware

from .wallet.tee_wallet import TEEWallet
from ..settings import settings


@dataclass
class TxQueueElement:
    """
    Represents a transaction in the queue with its associated message.

    Attributes:
        msg (str): Description or context of the transaction
        tx (TxParams): Transaction parameters
    """

    msg: str
    tx: TxParams


@dataclass
class WalletInfo:
    """
    Represents information about a connected wallet.

    Attributes:
        address (str): The wallet address
        label (str): User-friendly label for the wallet
        wallet_type (str): Type of wallet (e.g., "metamask", "tee")
        is_active (bool): Whether this is the currently active wallet
    """

    address: str
    label: str
    wallet_type: str
    is_active: bool = False


logger = structlog.get_logger(__name__)


class FlareProvider:
    """
    Manages interactions with the Flare Network including account
    operations and transactions with TEE wallet integration.

    Attributes:
        address (ChecksumAddress | None): The account's checksum address
        tx_queue (list[TxQueueElement]): Queue of pending transactions
        web3 (Web3): Web3 instance for blockchain interactions
        wallet (TEEWallet): Secure TEE wallet for transaction signing
        logger (BoundLogger): Structured logger for the provider
    """

    def __init__(self, web3_provider_url: Optional[str] = None) -> None:
        """
        Initialize the Flare Provider with TEE wallet integration.

        Args:
            web3_provider_url (str): URL of the Web3 provider endpoint
        """
        # Initialize Web3 provider
        if web3_provider_url is None:
            web3_provider_url = settings.web3_rpc_url
            
        self.web3 = Web3(Web3.HTTPProvider(web3_provider_url))
        # Add POA middleware for Flare Network
        self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Initialize secure TEE wallet
        self.wallet = TEEWallet(self.web3)
        self.address = self.wallet.get_address()
        
        # Transaction queue
        self.tx_queue: list[TxQueueElement] = []
        
        # External wallet tracking
        self.external_wallets: Dict[str, WalletInfo] = {}
        self.active_external_wallet: Optional[str] = None
        
        # Logger
        self.logger = logger.bind(module="flare_provider", network=settings.network_name)

    def reset(self) -> None:
        """
        Reset the provider state by clearing transaction queue.
        """
        # In a TEE environment, we don't reset the wallet,
        # just the transaction queue
        self.tx_queue = []
        self.logger.info("provider_reset", address=self.address)

    def add_tx_to_queue(self, msg: str, tx: TxParams) -> None:
        """
        Add a transaction to the queue with an associated message.

        Args:
            msg (str): Description of the transaction
            tx (TxParams): Transaction parameters
            
        Raises:
            ValueError: If wallet is not initialized
        """
        if not self.address:
            raise ValueError("Wallet not initialized for transactions")
            
        # Ensure the tx has the correct from address
        tx['from'] = self.address
        
        tx_queue_element = TxQueueElement(msg=msg, tx=tx)
        self.tx_queue.append(tx_queue_element)
        self.logger.info("transaction_queued", msg=msg, to=tx.get('to'), value=tx.get('value'))

    def send_tx_in_queue(self) -> str:
        """
        Send the most recent transaction in the queue.

        Returns:
            str: Transaction hash of the sent transaction

        Raises:
            ValueError: If no transaction is found in the queue
        """
        if not self.tx_queue:
            raise ValueError("No transactions in queue to send")
            
        try:
            tx_element = self.tx_queue[-1]
            tx_hash = self.sign_and_send_transaction(tx_element.tx)
            self.logger.info("sent_tx_from_queue", tx_hash=tx_hash, msg=tx_element.msg)
            self.tx_queue.pop()
            return tx_hash
        except Exception as e:
            self.logger.error("queue_tx_sending_failed", error=str(e))
            raise ValueError(f"Failed to send transaction from queue: {str(e)}")

    def get_wallet_address(self) -> Optional[ChecksumAddress]:
        """
        Get the current wallet address.

        Returns:
            Optional[ChecksumAddress]: The wallet address or None if not initialized
        """
        # If active external wallet exists, prefer that
        if self.active_external_wallet:
            return self.web3.to_checksum_address(self.active_external_wallet)
        return self.address
        
    def set_external_wallet(self, address: str, wallet_type: str = "metamask", label: str = "External Wallet") -> None:
        """
        Set an external wallet as connected.
        
        Args:
            address: Wallet address to connect
            wallet_type: Type of external wallet
            label: User-friendly label for the wallet
            
        Raises:
            ValueError: If the address is invalid
        """
        try:
            # Validate and convert to checksum address
            checksum_address = self.web3.to_checksum_address(address)
            
            # Create wallet info and set as active
            wallet_info = WalletInfo(
                address=checksum_address,
                label=label,
                wallet_type=wallet_type,
                is_active=True
            )
            
            # Set previous active wallet to inactive
            if self.active_external_wallet and self.active_external_wallet in self.external_wallets:
                self.external_wallets[self.active_external_wallet].is_active = False
            
            # Update external wallets dictionary
            self.external_wallets[checksum_address] = wallet_info
            self.active_external_wallet = checksum_address
            
            self.logger.info(
                "external_wallet_set",
                address=checksum_address,
                wallet_type=wallet_type
            )
        except Exception as e:
            self.logger.error("set_external_wallet_failed", error=str(e), address=address)
            raise ValueError(f"Invalid wallet address: {str(e)}")
    
    def disconnect_wallet(self, address: Optional[str] = None) -> None:
        """
        Disconnect an external wallet.
        
        Args:
            address: Address of wallet to disconnect, if None, disconnect active wallet
        """
        try:
            # Determine which wallet to disconnect
            target_address = address
            if target_address is None and self.active_external_wallet:
                target_address = self.active_external_wallet
            
            # If no wallet specified and no active wallet, do nothing
            if target_address is None:
                return
                
            # Convert to checksum address
            checksum_address = self.web3.to_checksum_address(target_address)
            
            # Remove wallet from tracking
            if checksum_address in self.external_wallets:
                # Log disconnection
                self.logger.info(
                    "external_wallet_disconnected",
                    address=checksum_address,
                    wallet_type=self.external_wallets[checksum_address].wallet_type
                )
                
                # Remove from dictionary
                del self.external_wallets[checksum_address]
                
                # Clear active wallet if it's the one being disconnected
                if self.active_external_wallet == checksum_address:
                    self.active_external_wallet = None
                    
                    # Set another wallet as active if available
                    if self.external_wallets:
                        new_active = next(iter(self.external_wallets.keys()))
                        self.external_wallets[new_active].is_active = True
                        self.active_external_wallet = new_active
        except Exception as e:
            self.logger.error("disconnect_wallet_failed", error=str(e), address=address)
            raise ValueError(f"Failed to disconnect wallet: {str(e)}")
    
    def get_connected_wallets(self) -> List[Dict[str, Any]]:
        """
        Get a list of all connected wallets including the TEE wallet.
        
        Returns:
            List[Dict[str, Any]]: List of wallet information
        """
        wallets = []
        
        # Add TEE wallet if available
        if self.address:
            wallets.append({
                "address": self.address,
                "label": "TEE Secure Wallet",
                "wallet_type": "tee",
                "is_active": self.active_external_wallet is None
            })
        
        # Add all external wallets
        for wallet_info in self.external_wallets.values():
            wallets.append({
                "address": wallet_info.address,
                "label": wallet_info.label,
                "wallet_type": wallet_info.wallet_type,
                "is_active": wallet_info.is_active
            })
            
        return wallets

    def sign_and_send_transaction(self, tx: TxParams) -> str:
        """
        Sign and send a transaction to the network using TEE wallet.

        Args:
            tx (TxParams): Transaction parameters to be sent

        Returns:
            str: Transaction hash of the sent transaction

        Raises:
            ValueError: If wallet is not unlocked
        """
        if not self.wallet.is_unlocked():
            raise ValueError("Wallet is not unlocked for transaction signing")

        if not self.address:
            raise ValueError("Wallet address not available")
            
        try:
            # Ensure transaction has the right from address
            tx["from"] = self.address
            
            # Sign transaction securely within TEE
            signed_tx = self.wallet.sign_transaction(tx)
            
            # In production TEE mode, this would be handled by the TEE service
            # For now, we'll check if we're in simulation mode
            if settings.simulate_attestation:
                # This is just for development - NOT production secure
                tx["gas"] = tx.get("gas", self.web3.eth.estimate_gas({"to": tx.get("to"), "data": tx.get("data", "")}))
                tx["gasPrice"] = tx.get("gasPrice", self.web3.eth.gas_price)
                tx["nonce"] = tx.get("nonce", self.web3.eth.get_transaction_count(self.address))
                
                # Use private key from environment for dev only
                dev_key = os.environ.get("DEV_PRIVATE_KEY")
                if dev_key:
                    signed_tx = self.web3.eth.account.sign_transaction(tx, dev_key)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    # Wait for receipt
                    self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    tx_hash_hex = "0x" + tx_hash.hex()
                    self.logger.info("transaction_sent", tx_hash=tx_hash_hex)
                    return tx_hash_hex
                else:
                    # If no key available, simulate successful tx for testing
                    return f"0x{os.urandom(32).hex()}"
            else:
                # In production, TEE would handle the entire signing process
                # and return the transaction hash
                raise NotImplementedError("Production TEE transaction signing not implemented")
                
        except Exception as e:
            self.logger.error("transaction_sending_failed", error=str(e))
            raise ValueError(f"Failed to send transaction: {str(e)}")

    def check_balance(self) -> float:
        """
        Check the balance of the current account.

        Returns:
            float: Account balance in FLR

        Raises:
            ValueError: If wallet is not initialized
        """
        if not self.address:
            raise ValueError("Wallet not initialized")
            
        try:
            balance_wei = self.wallet.get_balance()
            self.logger.info("balance_checked", balance_wei=balance_wei, address=self.address)
            return float(self.web3.from_wei(balance_wei, "ether"))
        except Exception as e:
            self.logger.error("balance_check_failed", error=str(e))
            raise ValueError(f"Failed to check balance: {str(e)}")
    
    def get_wallet_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get balance information for a wallet address.
        
        Args:
            address: Specific wallet address to check, if None uses active wallet
            
        Returns:
            Dict[str, Any]: Balance information including ETH and token balances
            
        Raises:
            ValueError: If no wallet is available or the address is invalid
        """
        try:
            # Determine which address to check
            target_address = address
            wallet_type = "unknown"
            
            if target_address is None:
                # Use active external wallet if available
                if self.active_external_wallet:
                    target_address = self.active_external_wallet
                    wallet_info = self.external_wallets.get(self.active_external_wallet)
                    if wallet_info:
                        wallet_type = wallet_info.wallet_type
                # Otherwise use TEE wallet
                elif self.address:
                    target_address = self.address
                    wallet_type = "tee"
                else:
                    raise ValueError("No wallet is available")
            else:
                # Convert to checksum address
                target_address = self.web3.to_checksum_address(target_address)
                
                # Try to get wallet type if it's a known wallet
                if target_address in self.external_wallets:
                    wallet_type = self.external_wallets[target_address].wallet_type
                elif target_address == self.address:
                    wallet_type = "tee"
            
            # Get ETH balance
            balance_wei = self.web3.eth.get_balance(target_address)
            eth_balance = float(self.web3.from_wei(balance_wei, "ether"))
            
            # Format decimals to 6 places
            eth_formatted = f"{eth_balance:.6f} ETH"
            
            # Initialize response with ETH balance
            balance_info = {
                "address": target_address,
                "wallet_type": wallet_type,
                "eth_balance": eth_balance,
                "eth_formatted": eth_formatted,
                "tokens": []
            }
            
            # TODO: Add ERC20 token balances - would require token contract addresses
            # For now, this is a placeholder for future implementation
            
            self.logger.info(
                "wallet_balance_checked",
                address=target_address,
                wallet_type=wallet_type,
                eth_balance=eth_balance
            )
            
            return balance_info
        except Exception as e:
            self.logger.error("get_wallet_balance_failed", error=str(e), address=address)
            raise ValueError(f"Failed to get wallet balance: {str(e)}")

    def create_send_flr_tx(self, to_address: str, amount: float) -> TxParams:
        """
        Create a transaction to send FLR tokens.

        Args:
            to_address (str): Recipient address
            amount (float): Amount of FLR to send

        Returns:
            TxParams: Transaction parameters for sending FLR

        Raises:
            ValueError: If wallet is not initialized
        """
        if not self.address:
            raise ValueError("Wallet not initialized")
            
        try:
            tx: TxParams = {
                "from": self.address,
                "nonce": self.web3.eth.get_transaction_count(self.address),
                "to": self.web3.to_checksum_address(to_address),
                "value": self.web3.to_wei(amount, unit="ether"),
                "gas": 21000,
                "maxFeePerGas": self.web3.eth.gas_price,
                "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
                "chainId": self.web3.eth.chain_id,
                "type": 2,
            }
            self.logger.info("created_send_tx", to=to_address, amount=amount)
            return tx
        except Exception as e:
            self.logger.error("tx_creation_failed", error=str(e))
            raise ValueError(f"Failed to create transaction: {str(e)}")
