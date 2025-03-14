"""
Wallet Module

This module provides secure wallet functionality for blockchain interactions,
including TEE-protected operations for production use.
"""

from .tee_wallet import TEEWallet

__all__ = ["TEEWallet"]
