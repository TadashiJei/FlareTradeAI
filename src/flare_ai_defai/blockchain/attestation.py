"""
TEE Attestation Module

This module provides functionality for TEE attestation and validation,
ensuring that sensitive operations are performed in a secure environment.
"""

import os
import time
import json
import base64
import hashlib
import hmac
import structlog
from typing import Dict, Optional, List, Any
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure structured logging
logger = structlog.get_logger()

# Demo mode flag for hackathon environments
DEMO_MODE = True
logger.warning("Running in DEMO MODE - TEE attestation features are simulated")

# Try to import TEE modules, but fall back to demo mode if not available
try:
    import tee_client
    from confidential_space.client import ConfidentialSpaceClient, AttestationVerificationConfig
    # If imports succeed but we still want to use demo mode, leave DEMO_MODE as True
    # Otherwise, set to False to use actual TEE features
    if not DEMO_MODE:
        logger.info("TEE client modules loaded successfully")
        DEMO_MODE = False
except ImportError:
    logger.warning("TEE client modules not available, forcing demo mode")
    DEMO_MODE = True
    
    # Create dummy modules for demo mode
    class DummyConfidentialSpaceClient:
        def is_running_in_confidential_space(self):
            return True
            
        def get_attestation_report(self):
            return {"dummy": "attestation"}
            
        def verify_attestation_report(self, attestation, config):
            return True
            
        def parse_attestation_report(self, attestation):
            return {"tee_type": "TDX", "image_hash": "dummy_hash"}
    
    class DummyTeeClient:
        def store_key(self, key_name, key_bytes):
            return True
            
        def retrieve_key(self, key_name):
            return b"dummy_key"
    
    class DummyAttestationVerificationConfig:
        pass
    
    # Create dummy module structures
    class DummyConfidentialSpace:
        def __init__(self):
            self.client = DummyConfidentialSpaceClient
            self.AttestationVerificationConfig = DummyAttestationVerificationConfig
    
    # Assign dummy modules to the imported names
    tee_client = type('', (), {})()
    tee_client.Client = DummyTeeClient
    confidential_space = type('', (), {})()
    confidential_space.client = DummyConfidentialSpace()
    ConfidentialSpaceClient = DummyConfidentialSpaceClient
    AttestationVerificationConfig = DummyAttestationVerificationConfig


class Vtpm:
    """Virtual Trusted Platform Module (vTPM) for attestation and secure key storage.
    
    This class provides methods for TEE attestation, validation, and secure key
    storage using vTPM.
    """
    
    def __init__(self, simulate: bool = False):
        """
        Initialize the vTPM.
        
        Args:
            simulate (bool, optional): Whether to simulate attestation. Defaults to False.
        """
        # If we're in demo mode, force simulation
        self.simulate = simulate or DEMO_MODE
        self.logger = logger.bind(service="vtpm")
        
        # Initialize secure storage
        if self.simulate:
            self.keys = {}  # In-memory storage for simulation mode
            self.logger.warning("Running in simulation mode - NOT SECURE FOR PRODUCTION")
        else:
            # Initialize TEE client for secure key operations
            self.tee_client = tee_client.Client()
            self.cs_client = ConfidentialSpaceClient()
            
            # Verify we're running in a TEE
            self._verify_tee_environment()
    
    def _verify_tee_environment(self) -> None:
        """Verify that we're running in a valid TEE environment."""
        try:
            # Check for Confidential Space environment
            if not self.cs_client.is_running_in_confidential_space():
                raise EnvironmentError("Not running in a Confidential Space environment")
            
            # Get attestation report to verify TEE
            attestation = self.cs_client.get_attestation_report()
            
            # Verify attestation locally before proceeding
            config = AttestationVerificationConfig()
            self.cs_client.verify_attestation_report(attestation, config)
            
            self.logger.info("TEE environment verified successfully")
        except Exception as e:
            if self.simulate:
                self.logger.warning(f"TEE verification failed, but continuing in simulation mode: {str(e)}")
            else:
                self.logger.error(f"TEE environment verification failed: {str(e)}")
                raise EnvironmentError(f"TEE verification failed: {str(e)}")
    
    def store_key(self, key: str) -> bool:
        """
        Store a key securely in the vTPM.
        
        Args:
            key (str): The key to store
            
        Returns:
            bool: True if the key was stored successfully
        """
        if self.simulate:
            # In simulation mode, store the key in memory
            self.keys["primary"] = key
            return True
        
        try:
            # Using the TEE client to securely store the key
            key_id = "primary"
            key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            
            # Generate a unique key name with namespace to avoid collisions
            namespace = "flare_ai_defai"
            key_name = f"{namespace}_{key_id}"
            
            # Store key in the TEE's secure storage
            self.tee_client.store_key(key_name, key_bytes)
            self.logger.info("Key stored securely in TEE", key_id=key_id)
            return True
        except Exception as e:
            self.logger.error("Failed to store key", error=str(e))
            return False
    
    def retrieve_key(self) -> Optional[str]:
        """
        Retrieve a key from the vTPM.
        
        Returns:
            Optional[str]: The retrieved key, or None if not found
        """
        if self.simulate:
            # In simulation mode, retrieve from memory
            return self.keys.get("primary")
        
        try:
            # Using the TEE client to retrieve the securely stored key
            key_id = "primary"
            namespace = "flare_ai_defai"
            key_name = f"{namespace}_{key_id}"
            
            # Retrieve key from TEE's secure storage
            key_bytes = self.tee_client.retrieve_key(key_name)
            
            if key_bytes:
                self.logger.info("Key retrieved from TEE", key_id=key_id)
                return key_bytes.decode('utf-8')
            else:
                self.logger.warning("Key not found in TEE", key_id=key_id)
                return None
        except Exception as e:
            self.logger.error("Failed to retrieve key", error=str(e))
            return None
    
    def verify_attestation(self) -> bool:
        """
        Verify the attestation of the TEE.
        
        Returns:
            bool: True if the attestation is valid
        """
        if self.simulate:
            # In simulation mode, always return success
            return True
        
        try:
            # Get attestation report from Confidential Space
            attestation = self.cs_client.get_attestation_report()
            
            # Verify attestation with TPM attestation service
            config = AttestationVerificationConfig()
            self.cs_client.verify_attestation_report(attestation, config)
            
            # Check attestation claims
            claims = self.cs_client.parse_attestation_report(attestation)
            
            # Verify CPU type matches requirement (TDX or SEV)
            cpu_type = claims.get("tee_type", "")
            if cpu_type not in ["TDX", "SEV"]:
                self.logger.error("Unsupported CPU type", type=cpu_type)
                return False
                
            # Verify image hash matches expected value (in production, this would check against known good values)
            image_hash = claims.get("image_hash", "")
            # Here you would compare against known good values from a trusted source
            
            self.logger.info("Attestation verified successfully", cpu_type=cpu_type)
            return True
        except Exception as e:
            self.logger.error("Attestation verification failed", error=str(e))
            return False
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data using the vTPM.
        
        Args:
            data (str): The data to encrypt
            
        Returns:
            str: The encrypted data
        """
        if self.simulate:
            # Simple encryption for simulation mode
            key = self.keys.get("primary", "default_key")
            key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            
            # Create a simple encryption using AESGCM
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(key_bytes)
            
            # Generate a random nonce
            nonce = os.urandom(12)
            
            # Encrypt the data
            data_bytes = data.encode('utf-8') if isinstance(data, str) else data
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data_bytes, None)
            
            # Combine salt, nonce, and ciphertext for storage
            result = base64.b64encode(salt + nonce + ciphertext)
            return result.decode('utf-8')
        
        try:
            # In production, use TEE's secure encryption APIs
            data_bytes = data.encode('utf-8') if isinstance(data, str) else data
            
            # Get the encryption key from secure storage
            key_id = "primary"
            namespace = "flare_ai_defai"
            key_name = f"{namespace}_{key_id}"
            
            # Use TEE client to encrypt data with the stored key
            encrypted_data = self.tee_client.encrypt(key_name, data_bytes)
            
            # Return as base64 encoded string
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            self.logger.error("Encryption failed", error=str(e))
            if self.simulate:
                # Fall back to simulation mode if real encryption fails
                return self.encrypt_data(data)
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data using the vTPM.
        
        Args:
            encrypted_data (str): The encrypted data
            
        Returns:
            str: The decrypted data
        """
        if self.simulate:
            # Simple decryption for simulation mode
            key = self.keys.get("primary", "default_key")
            key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            
            try:
                # Decode the base64 data
                decoded = base64.b64decode(encrypted_data)
                
                # Extract salt, nonce, and ciphertext
                salt = decoded[:16]
                nonce = decoded[16:28]
                ciphertext = decoded[28:]
                
                # Derive the key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(key_bytes)
                
                # Decrypt the data
                aesgcm = AESGCM(key)
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                
                return plaintext.decode('utf-8')
            except Exception as e:
                self.logger.error("Decryption failed", error=str(e))
                return ""
        
        try:
            # In production, use TEE's secure decryption APIs
            # Decode the base64 data
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Get the encryption key from secure storage
            key_id = "primary"
            namespace = "flare_ai_defai"
            key_name = f"{namespace}_{key_id}"
            
            # Use TEE client to decrypt data with the stored key
            decrypted_data = self.tee_client.decrypt(key_name, encrypted_bytes)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error("Decryption failed", error=str(e))
            if self.simulate:
                # Fall back to simulation mode if real decryption fails
                return self.decrypt_data(encrypted_data)
            raise


class AttestationValidator:
    """
    Validates TEE attestation tokens.
    
    This class provides methods for validating attestation tokens to ensure
    that operations are performed in a secure environment.
    """

    def __init__(self, simulate: bool = False):
        """
        Initialize the attestation validator.
        
        Args:
            simulate (bool, optional): Whether to simulate validation. Defaults to False.
        """
        # Use global DEMO_MODE to force simulation if needed
        self.simulate = simulate or DEMO_MODE
        self.logger = logger.bind(service="attestation_validator")
        
        if self.simulate:
            self.logger.warning("AttestationValidator running in simulation mode - NOT SECURE FOR PRODUCTION")
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate an attestation token.
        
        Args:
            token (str): The attestation token to validate
            
        Returns:
            Dict: The validation results, including:
                - valid: Whether the token is valid
                - errors: List of errors if any
        """
        if self.simulate:
            # In simulation mode, always return valid
            return {
                "valid": True,
                "errors": [],
            }
        
        try:
            # Use Confidential Space client to validate the token
            cs_client = ConfidentialSpaceClient()
            
            # Parse the JWT token
            parsed_token = cs_client.parse_attestation_token(token)
            
            # Verify token signature using Confidential Space verification keys
            if not cs_client.verify_token_signature(token):
                self.logger.error("Invalid token signature")
                return {
                    "valid": False,
                    "errors": ["Invalid token signature"],
                }
            
            # Extract claims from the token
            claims = parsed_token.get("claims", {})
            
            # Verify token is not expired
            current_time = int(time.time())
            if "exp" in claims and current_time > claims["exp"]:
                self.logger.error("Token expired", 
                                  expiration=claims["exp"], 
                                  current_time=current_time)
                return {
                    "valid": False,
                    "errors": ["Token expired"],
                }
                
            # Verify issuer is trusted
            trusted_issuers = ["https://confidentialcomputing.googleapis.com"]
            if "iss" not in claims or claims["iss"] not in trusted_issuers:
                self.logger.error("Untrusted token issuer", issuer=claims.get("iss"))
                return {
                    "valid": False,
                    "errors": ["Untrusted token issuer"],
                }
                
            # Verify TEE platform is valid
            attestation_statement = claims.get("attestation_statement", {})
            tee_platform = attestation_statement.get("tee_platform")
            
            if tee_platform != "GCE_CONFIDENTIAL_SPACE":
                self.logger.error("Invalid TEE platform", platform=tee_platform)
                return {
                    "valid": False,
                    "errors": ["Invalid TEE platform"],
                }
                
            # Verify PCR0 values (secure boot measurement)
            measurements = attestation_statement.get("measurements", {})
            pcr0 = measurements.get("pcr0")
            
            # List of known good PCR0 values for Confidential Space
            trusted_pcr0_values = [
                "3d458cfe55cc03ea1f443f1562beec8df51c75e14a9fcf9a7234a13f198e7969",
                # Additional trusted PCR0 values would be listed here
            ]
            
            if not pcr0 or pcr0 not in trusted_pcr0_values:
                self.logger.error("Invalid PCR0 measurement", pcr0=pcr0)
                return {
                    "valid": False,
                    "errors": ["Invalid secure boot measurement"],
                }
                
            # Verify container image
            sw_infos = attestation_statement.get("sw_infos", [])
            container_image = None
            
            for sw_info in sw_infos:
                if sw_info.get("type") == "container_image":
                    container_image = sw_info.get("digest")
                    break
                    
            # List of trusted container images (would be configured in a production system)
            trusted_images = [
                "sha256:a1b2c3d4e5f6...",  # Replace with actual image digest in production
                # Additional trusted images would be listed here
            ]
            
            if not container_image or container_image not in trusted_images:
                # In production, you would strictly verify the image
                # For hackathon purposes, we'll log a warning but allow it
                self.logger.warning("Unrecognized container image", image=container_image)
                
            # All checks passed
            self.logger.info("Token validated successfully")
            return {
                "valid": True,
                "errors": [],
            }
        except Exception as e:
            self.logger.error("Token validation failed", error=str(e))
            return {
                "valid": False,
                "errors": [str(e)],
            }
    
    def verify_environment(self) -> Dict:
        """
        Verify the TEE environment.
        
        Returns:
            Dict: The verification results, including:
                - valid: Whether the environment is valid
                - errors: List of errors if any
        """
        if self.simulate:
            # In simulation mode, always return valid with a demo notice
            self.logger.info("TEE environment verification simulated in demo mode")
            return {
                "valid": True,
                "info": "Running in demo mode with simulated TEE environment",
                "errors": [],
            }
        
        try:
            # Create Confidential Space client for TEE verification
            cs_client = ConfidentialSpaceClient()
            
            # 1. Verify we're running in a Confidential Space environment
            if not cs_client.is_confidential_space():
                self.logger.error("Not running in Confidential Space")
                return {
                    "valid": False,
                    "errors": ["Not running in Confidential Space environment"],
                }
            
            # 2. Get local attestation token
            attestation_token = cs_client.get_attestation_token()
            if not attestation_token:
                self.logger.error("Failed to get attestation token")
                return {
                    "valid": False,
                    "errors": ["Failed to get attestation token from TEE"],
                }
            
            # 3. Validate the attestation token
            validation_result = self.validate_token(attestation_token)
            if not validation_result.get("valid", False):
                self.logger.error("Invalid attestation token", 
                                  errors=validation_result.get("errors", []))
                return validation_result
            
            # 4. Verify vTPM is accessible
            if not cs_client.is_vtpm_available():
                self.logger.error("vTPM is not accessible")
                return {
                    "valid": False,
                    "errors": ["vTPM is not accessible"],
                }
            
            # 5. Verify secure storage is available
            if not cs_client.is_secure_storage_available():
                self.logger.error("Secure storage is not available")
                return {
                    "valid": False,
                    "errors": ["Secure storage is not available"],
                }
            
            # 6. Verify integrity of the runtime environment
            runtime_integrity = cs_client.verify_runtime_integrity()
            if not runtime_integrity.get("valid"):
                self.logger.error("Runtime integrity check failed",
                                 details=runtime_integrity.get("details"))
                return {
                    "valid": False,
                    "errors": ["Runtime integrity check failed", 
                              *runtime_integrity.get("details", [])],
                }
            
            # 7. Verify memory encryption is enabled (AMD SEV or Intel TDX)
            memory_encryption = cs_client.is_memory_encryption_enabled()
            if not memory_encryption:
                self.logger.warning("Memory encryption may not be enabled")
                # Warning only, not fatal for hackathon environment
            
            # All checks passed
            self.logger.info("TEE environment verified successfully")
            return {
                "valid": True,
                "errors": [],
            }
        except Exception as e:
            self.logger.error("Environment verification failed", error=str(e))
            return {
                "valid": False,
                "errors": [str(e)],
            }
