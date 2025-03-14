"""
Settings Configuration Module

This module defines the configuration settings for the AI Agent API
using Pydantic's BaseSettings. It handles environment variables and
provides default values for various service configurations.

The settings can be overridden by environment variables or through a .env file.
Environment variables take precedence over values defined in the .env file.
"""

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """
    Application settings model that provides configuration for all components.
    
    Settings can be configured through environment variables or .env file.
    Environment variables take precedence over values in the .env file.
    """

    # ========== API Configuration ==========
    # API version to use at the backend
    api_version: str = "v1"
    # CORS origins for the frontend application
    cors_origins: list[str] = ["*", "http://localhost:3000"]
    
    # ========== AI Model Configuration ==========
    # API key for accessing Google's Gemini AI service
    gemini_api_key: str = ""
    # The Gemini model identifier to use
    gemini_model: str = "gemini-1.5-flash"
    
    # ========== Blockchain Configuration ==========
    # Network name (coston2, songbird, flare)
    network_name: str = "coston2"
    # URL for the Flare Network RPC provider
    web3_rpc_url: str = "https://coston2-api.flare.network/ext/C/rpc"
    # URL for the Flare Network block explorer
    web3_explorer_url: str = "https://coston2-explorer.flare.network/"
    # Chain ID for the network
    chain_id: int = 114
    
    # ========== TEE Configuration ==========
    # Flag to enable/disable attestation simulation (for development only)
    simulate_attestation: bool = False
    # Identifier for the TEE instance name
    instance_name: str = "flare-agent-tee-v1"
    # Flag to use a test wallet (for development only)
    use_test_wallet: bool = False
    # Test wallet address (for development only)
    test_wallet_address: str = ""
    # TEE service endpoint URL for remote attestation
    tee_service_url: str = ""
    # TEE attestation type (vtpm, sgx, etc.)
    tee_attestation_type: str = "vtpm"

    model_config = SettingsConfigDict(
        # This enables .env file support
        env_file=".env",
        # If .env file is not found, don't raise an error
        env_file_encoding="utf-8",
        # Optional: you can also specify multiple .env files
        extra="ignore",
    )


# Create a global settings instance
settings = Settings()

# Log settings but exclude sensitive fields
safe_settings = settings.model_dump()

# Remove sensitive fields for logging
if "gemini_api_key" in safe_settings and safe_settings["gemini_api_key"]:
    safe_settings["gemini_api_key"] = "[REDACTED]"

logger.info("application_settings_loaded", **safe_settings)
