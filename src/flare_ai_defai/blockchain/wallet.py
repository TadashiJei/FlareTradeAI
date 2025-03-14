"""
Secure Wallet Management Module

This module provides secure wallet management functionality with TEE validation,
ensuring that sensitive wallet operations are protected.
"""

from enum import Enum
from typing import Dict, List, Optional, Union

import structlog
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams

from ..blockchain.attestation import Vtpm

logger = structlog.get_logger(__name__)


class WalletType(Enum):
    """Enum for different wallet types."""
    TEE = "tee"  # Trusted Execution Environment wallet
    METAMASK = "metamask"  # MetaMask wallet
    WALLETCONNECT = "walletconnect"  # WalletConnect
    LEDGER = "ledger"  # Ledger hardware wallet
    EXTERNAL = "external"  # Generic external wallet


class WalletInfo:
    """Stores information about a connected wallet."""
    
    def __init__(
        self, 
        address: ChecksumAddress, 
        wallet_type: WalletType, 
        chain_id: Optional[str] = None,
        label: Optional[str] = None
    ):
        self.address = address
        self.wallet_type = wallet_type
        self.chain_id = chain_id
        self.label = label or f"{wallet_type.value.capitalize()} Wallet"


class SecureWalletManager:
    """
    Manages wallet operations with TEE validation and external wallet integration.
    
    This class provides secure wallet management functionality, including account
    creation, transaction signing, and TEE-based validation. It also supports
    connecting to external wallets like MetaMask and WalletConnect.
    """

    def __init__(self, web3: Web3, vtpm: Vtpm):
        """
        Initialize the secure wallet manager.
        
        Args:
            web3 (Web3): Web3 instance for blockchain interactions
            vtpm (Vtpm): vTPM instance for attestation and validation
        """
        self.web3 = web3
        self.vtpm = vtpm
        self.account: Optional[Account] = None
        self.external_wallets: Dict[ChecksumAddress, WalletInfo] = {}
        self.active_wallet: Optional[Union[ChecksumAddress, Account]] = None
        self.logger = logger.bind(service="wallet_manager")

    def create_account(self) -> ChecksumAddress:
        """
        Create a new wallet account with TEE protection.
        
        Returns:
            ChecksumAddress: The address of the newly created account
        """
        # Generate a new account
        self.account = Account.create()
        
        # Store the private key securely in the TEE
        self.vtpm.store_key(self.account.key.hex())
        
        # Set this as the active wallet by default
        address = self.web3.to_checksum_address(self.account.address)
        self.active_wallet = self.account
        
        self.logger.debug("created_tee_account", address=address)
        return address

    def sign_transaction(self, tx_params: TxParams) -> bytes:
        """
        Sign a transaction using the active wallet.
        
        Args:
            tx_params (TxParams): Transaction parameters to sign
            
        Returns:
            bytes: Signed transaction data
            
        Raises:
            ValueError: If no account is loaded or no wallet is active
            NotImplementedError: If trying to sign with an external wallet (should use frontend)
        """
        if isinstance(self.active_wallet, Account):
            # We're using the TEE wallet
            if not self.account:
                msg = "No TEE account loaded"
                raise ValueError(msg)
            
            # Retrieve the private key from the TEE
            private_key = self.vtpm.retrieve_key()
            
            # Sign the transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx_params, private_key)
            
            self.logger.debug("signed_transaction_tee", tx_hash=signed_tx.hash.hex())
            return signed_tx.rawTransaction
        elif isinstance(self.active_wallet, str):
            # We're using an external wallet
            raise NotImplementedError(
                "External wallet signing must be done on the frontend. "
                "This backend only supports transaction preparation for external wallets."
            )
        else:
            msg = "No active wallet selected"
            raise ValueError(msg)

    def validate_wallet_state(self) -> bool:
        """
        Validate the wallet state using TEE attestation.
        
        Returns:
            bool: True if the wallet state is valid
        """
        # Perform attestation to validate the TEE environment
        return self.vtpm.verify_attestation()

    def backup_wallet(self) -> str:
        """
        Create a secure backup of the wallet.
        
        Returns:
            str: Encrypted backup data
        """
        if not self.account:
            msg = "No account loaded"
            raise ValueError(msg)
        
        # Create an encrypted backup using the TEE
        return self.vtpm.encrypt_data(self.account.key.hex())

    def restore_wallet(self, backup_data: str) -> ChecksumAddress:
        """
        Restore a wallet from a secure backup.
        
        Args:
            backup_data (str): Encrypted backup data
            
        Returns:
            ChecksumAddress: The address of the restored account
        """
        # Decrypt the backup data using the TEE
        private_key = self.vtpm.decrypt_data(backup_data)
        
        # Restore the account
        self.account = Account.from_key(private_key)
        self.active_wallet = self.account
        
        self.logger.debug("restored_account", address=self.account.address)
        return self.web3.to_checksum_address(self.account.address)
        
    def connect_external_wallet(self, address: str, wallet_type: str, chain_id: Optional[str] = None) -> ChecksumAddress:
        """
        Connect an external wallet (e.g., MetaMask, WalletConnect).
        
        Args:
            address: The wallet address to connect
            wallet_type: Type of wallet (metamask, walletconnect, ledger, etc.)
            chain_id: Blockchain chain ID (optional)
            
        Returns:
            ChecksumAddress: The checksummed address
            
        Raises:
            ValueError: If the wallet type is invalid or address format is incorrect
        """
        try:
            # Convert to checksum address
            checksum_address = self.web3.to_checksum_address(address)
            
            # Validate wallet type
            try:
                wallet_enum = WalletType(wallet_type.lower())
            except ValueError:
                wallet_enum = WalletType.EXTERNAL
                
            # Create wallet info
            wallet_info = WalletInfo(
                address=checksum_address,
                wallet_type=wallet_enum,
                chain_id=chain_id,
                label=f"{wallet_enum.value.capitalize()} Wallet"
            )
            
            # Store the wallet info
            self.external_wallets[checksum_address] = wallet_info
            
            # Make this the active wallet
            self.active_wallet = checksum_address
            
            self.logger.info(
                "external_wallet_connected",
                address=checksum_address,
                type=wallet_enum.value,
                chain_id=chain_id
            )
            
            return checksum_address
        except Exception as e:
            self.logger.exception("external_wallet_connection_failed", error=str(e))
            raise ValueError(f"Failed to connect external wallet: {str(e)}") from e
    
    def disconnect_wallet(self, address: Optional[str] = None) -> None:
        """
        Disconnect a wallet. If no address provided, disconnects the active wallet.
        
        Args:
            address: The wallet address to disconnect (optional)
        """
        if address is None and self.active_wallet:
            # Disconnect active wallet
            if isinstance(self.active_wallet, str):
                # External wallet case
                checksum_address = self.active_wallet
                if checksum_address in self.external_wallets:
                    wallet_type = self.external_wallets[checksum_address].wallet_type.value
                    del self.external_wallets[checksum_address]
                    self.logger.info("external_wallet_disconnected", address=checksum_address, type=wallet_type)
            
            # Reset active wallet to TEE wallet if available, otherwise None
            self.active_wallet = self.account if self.account else None
        elif address:
            # Disconnect specific wallet by address
            try:
                checksum_address = self.web3.to_checksum_address(address)
                if checksum_address in self.external_wallets:
                    wallet_type = self.external_wallets[checksum_address].wallet_type.value
                    del self.external_wallets[checksum_address]
                    
                    # If this was the active wallet, reset active wallet
                    if self.active_wallet == checksum_address:
                        self.active_wallet = self.account if self.account else None
                        
                    self.logger.info("external_wallet_disconnected", address=checksum_address, type=wallet_type)
            except Exception as e:
                self.logger.exception("wallet_disconnect_failed", error=str(e), address=address)
    
    def get_connected_wallets(self) -> List[Dict[str, str]]:
        """
        Get a list of all connected wallets (both TEE and external).
        
        Returns:
            List of wallet info dictionaries
        """
        wallets = []
        
        # Add TEE wallet if available
        if self.account:
            tee_address = self.web3.to_checksum_address(self.account.address)
            wallets.append({
                "address": tee_address,
                "type": WalletType.TEE.value,
                "label": "TEE Protected Wallet",
                "is_active": self.active_wallet is self.account
            })
        
        # Add external wallets
        for address, info in self.external_wallets.items():
            wallets.append({
                "address": address,
                "type": info.wallet_type.value,
                "label": info.label,
                "chain_id": info.chain_id,
                "is_active": self.active_wallet == address
            })
            
        return wallets
        
    def get_wallet_balance(self, address: Optional[str] = None) -> Dict[str, any]:
        """
        Get the balance of a specific wallet or the active wallet.
        
        Args:
            address: The wallet address to check balance for (optional)
            
        Returns:
            Dictionary containing balance information:
            {
                "eth_balance": Ethereum balance in wei,
                "eth_formatted": Formatted ETH balance,
                "tokens": List of token balances (if available)
            }
        
        Raises:
            ValueError: If the wallet is not connected or address is invalid
        """
        try:
            # Determine which address to check
            check_address = None
            
            if address:
                # Use provided address
                check_address = self.web3.to_checksum_address(address)
                # Verify the wallet is connected
                if check_address not in self.external_wallets and (
                    not self.account or check_address != self.web3.to_checksum_address(self.account.address)
                ):
                    raise ValueError(f"Wallet {address} is not connected")
            elif isinstance(self.active_wallet, Account):
                # Use TEE wallet address
                check_address = self.web3.to_checksum_address(self.account.address)
            elif isinstance(self.active_wallet, str):
                # Use active external wallet
                check_address = self.active_wallet
            else:
                raise ValueError("No active wallet available")
                
            # Get ETH balance
            wei_balance = self.web3.eth.get_balance(check_address)
            eth_balance = self.web3.from_wei(wei_balance, 'ether')
            
            # Format balance with 4 decimal places
            eth_formatted = f"{float(eth_balance):.4f} ETH"
            
            # Return balance info
            balance_info = {
                "address": check_address,
                "eth_balance": wei_balance,
                "eth_formatted": eth_formatted,
                "tokens": []  # In a real implementation, we would fetch token balances here
            }
            
            # Add wallet type information
            if self.account and check_address == self.web3.to_checksum_address(self.account.address):
                balance_info["wallet_type"] = WalletType.TEE.value
            elif check_address in self.external_wallets:
                balance_info["wallet_type"] = self.external_wallets[check_address].wallet_type.value
            
            self.logger.debug(
                "wallet_balance_checked", 
                address=check_address, 
                balance_eth=eth_formatted
            )
            
            return balance_info
            
        except Exception as e:
            self.logger.exception("wallet_balance_check_failed", error=str(e), address=address)
            raise ValueError(f"Failed to check wallet balance: {str(e)}") from e
    
    def set_active_wallet(self, address: Optional[str] = None) -> None:
        """
        Set the active wallet for transactions.
        
        Args:
            address: Address of wallet to set as active. If None, uses TEE wallet.
            
        Raises:
            ValueError: If the wallet is not connected
        """
        if address is None:
            # Use TEE wallet
            if self.account:
                self.active_wallet = self.account
                self.logger.debug("tee_wallet_set_active", address=self.account.address)
            else:
                msg = "No TEE wallet available"
                raise ValueError(msg)
        else:
            # Use external wallet
            try:
                checksum_address = self.web3.to_checksum_address(address)
                if checksum_address in self.external_wallets:
                    self.active_wallet = checksum_address
                    wallet_type = self.external_wallets[checksum_address].wallet_type.value
                    self.logger.debug("external_wallet_set_active", address=checksum_address, type=wallet_type)
                else:
                    msg = f"Wallet {address} is not connected"
                    raise ValueError(msg)
            except Exception as e:
                self.logger.exception("set_active_wallet_failed", error=str(e), address=address)
                raise
