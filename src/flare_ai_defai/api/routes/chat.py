"""
Chat Router Module

This module implements the main chat routing system for the AI Agent API.
It handles message routing, blockchain interactions, attestations, and AI responses.

The module provides a ChatRouter class that integrates various services:
- AI capabilities through GeminiProvider
- Blockchain operations through FlareProvider
- Attestation services through Vtpm
- Prompt management through PromptService
"""

import json
import re
from typing import Optional, Dict, List, Any, Union

import structlog
import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import Web3RPCError

from ...ai import GeminiProvider
from ...attestation import Vtpm, VtpmAttestationError
from ...blockchain import FlareProvider
from ...prompts import PromptService, SemanticRouterResponse
from ...settings import settings
from ...agent.defi_agent import DeFiAgent
from ...blockchain.risk.assessment import RiskLevel

logger = structlog.get_logger(__name__)
router = APIRouter()


class WalletInfo(BaseModel):
    """
    Pydantic model for wallet information.

    Attributes:
        address (str): The wallet address
        type (str): The wallet type (e.g., metamask, walletconnect, ledger, tee)
        chainId (str, optional): The blockchain chain ID
    """

    address: str
    type: str
    chainId: str = None


class ChatMessage(BaseModel):
    """
    Pydantic model for chat message validation.

    Attributes:
        message (str): The chat message content, must not be empty
        wallet (WalletInfo, optional): Information about the connected wallet
    """

    message: str = Field(..., min_length=1)
    wallet: WalletInfo = None


class TransactionResult(BaseModel):
    """
    Pydantic model for transaction results.

    Attributes:
        success (bool): Whether the transaction was successful
        action (str): The action performed
        protocol (str): The protocol used
        transaction_hash (str, optional): The transaction hash if successful
        errors (list[str], optional): List of errors if unsuccessful
        risk_assessment (dict, optional): Risk assessment results
        warnings (list[str], optional): List of warnings
        recommendations (list[str], optional): List of recommendations
    """

    success: bool
    action: str
    protocol: str = None
    transaction_hash: str = None
    errors: list[str] = None
    risk_assessment: dict = None
    warnings: list[str] = None
    recommendations: list[str] = None


class ChatRouter:
    """
    Main router class handling chat messages and their routing to appropriate handlers.

    This class integrates various services and provides routing logic for different
    types of chat messages including blockchain operations, attestations, and general
    conversation.

    Attributes:
        ai (GeminiProvider): Provider for AI capabilities
        blockchain (FlareProvider): Provider for blockchain operations
        attestation (Vtpm): Provider for attestation services
        prompts (PromptService): Service for managing prompts
        logger (BoundLogger): Structured logger for the chat router
    """

    def __init__(
        self,
        ai: GeminiProvider,
        blockchain: FlareProvider,
        attestation: Vtpm,
        prompts: PromptService,
    ) -> None:
        """
        Initialize the ChatRouter with required service providers.

        Args:
            ai: Provider for AI capabilities
            blockchain: Provider for blockchain operations
            attestation: Provider for attestation services
            prompts: Service for managing prompts
        """
        self._router = APIRouter()
        self.ai = ai
        self.blockchain = blockchain
        self.attestation = attestation
        self.prompts = prompts
        self.logger = logger.bind(router="chat")
        
        # Initialize DeFi agent when wallet is connected
        self.defi_agent = None
        self.connected_wallet_address = None
        
        self._setup_routes()

    def _setup_routes(self) -> None:
        """
        Set up FastAPI routes for the chat endpoint.
        Handles message routing, command processing, and transaction confirmations.
        """

        @self._router.post("/")
        async def chat(message: ChatMessage) -> dict[str, str]:  # pyright: ignore [reportUnusedFunction]
            """
            Process incoming chat messages and route them to appropriate handlers.

            Args:
                message: Validated chat message

            Returns:
                dict[str, str]: Response containing handled message result

            Raises:
                HTTPException: If message handling fails
            """
            try:
                self.logger.debug("received_message", message=message.message, wallet=message.wallet)
                
                # Handle external wallet connection if provided
                if message.wallet and message.wallet.address:
                    self._handle_wallet_connection(message.wallet)
                    
                    # Initialize DeFi agent if wallet is connected
                    if self.connected_wallet_address != message.wallet.address:
                        self.connected_wallet_address = message.wallet.address
                        self.defi_agent = DeFiAgent(
                            wallet_address=message.wallet.address,
                            use_tee=True,
                            risk_threshold="medium",
                            simulate_transactions=True,
                        )
                        self.logger.info("defi_agent_initialized", wallet_address=message.wallet.address)
                
                # Check for natural language balance queries
                if self._is_balance_query(message.message):
                    address = message.wallet.address if message.wallet else None
                    return self._handle_wallet_balance_command(address)
                    
                # Process DeFi commands if agent is initialized and wallet is connected
                if self.defi_agent and message.wallet and message.wallet.address:
                    # Check if this might be a DeFi command before processing it as a regular message
                    if self._might_be_defi_command(message.message):
                        return await self._handle_defi_command(message.message)
                
                if message.message.startswith("/"):
                    return await self.handle_command(message.message)
                if (
                    self.blockchain.tx_queue
                    and message.message == self.blockchain.tx_queue[-1].msg
                ):
                    try:
                        tx_hash = self.blockchain.send_tx_in_queue()
                    except Web3RPCError as e:
                        self.logger.exception("send_tx_failed", error=str(e))
                        msg = (
                            f"Unfortunately the tx failed with the error:\n{e.args[0]}"
                        )
                        return {"response": msg}

                    prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                        "tx_confirmation",
                        tx_hash=tx_hash,
                        block_explorer=settings.web3_explorer_url,
                    )
                    tx_confirmation_response = self.ai.generate(
                        prompt=prompt,
                        response_mime_type=mime_type,
                        response_schema=schema,
                    )
                    return {"response": tx_confirmation_response.text}
                if self.attestation.attestation_requested:
                    try:
                        resp = self.attestation.get_token([message.message])
                    except VtpmAttestationError as e:
                        resp = f"The attestation failed with  error:\n{e.args[0]}"
                    self.attestation.attestation_requested = False
                    return {"response": resp}

                route = await self.get_semantic_route(message.message)
                return await self.route_message(route, message.message)

            except Exception as e:
                self.logger.exception("message_handling_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

    @property
    def router(self) -> APIRouter:
        """Get the FastAPI router with registered routes."""
        return self._router

    async def handle_command(self, command: str) -> dict[str, str]:
        """
        Handle special command messages starting with '/'.

        Args:
            command: Command string to process

        Returns:
            dict[str, str]: Response containing command result
        """
        if command == "/reset":
            self.blockchain.reset()
            self.ai.reset()
            return {"response": "Reset complete"}
        elif command.startswith("/connect"):
            # Parse wallet address from command
            parts = command.split()
            if len(parts) > 1:
                address = parts[1]
                wallet_type = parts[2] if len(parts) > 2 else "external"
                return self._handle_wallet_connection_command(address, wallet_type)
            return {"response": "Invalid wallet connection command. Format: /connect <address> [wallet_type]"}
        elif command.startswith("/balance"):
            # Parse specific wallet address if provided, otherwise use active wallet
            parts = command.split()
            address = None
            if len(parts) > 1:
                address = parts[1]
            return self._handle_wallet_balance_command(address)
        elif command == "/wallets":
            # List all connected wallets
            return self._handle_list_wallets_command()
        return {"response": "Unknown command"}
    
    def _handle_wallet_connection(self, wallet: WalletInfo) -> None:
        """
        Handle wallet connection from frontend.
        
        Args:
            wallet: Wallet information from the frontend
        """
        try:
            # Log wallet connection
            self.logger.info(
                "external_wallet_connected",
                address=wallet.address,
                wallet_type=wallet.type,
                chain_id=wallet.chainId
            )
            
            # Set the blockchain provider to use this wallet address
            self.blockchain.set_external_wallet(wallet.address)
            
            # Initialize DeFi agent with the connected wallet address
            self.connected_wallet_address = wallet.address
            self.defi_agent = DeFiAgent(
                wallet_address=wallet.address,
                use_tee=True,  # Use Trusted Execution Environment by default
                risk_threshold="medium",  # Default risk threshold
                simulate_transactions=True  # Simulate transactions before execution
            )
            
            self.logger.info(
                "defi_agent_initialized",
                wallet_address=wallet.address
            )
        except Exception as e:
            self.logger.exception("wallet_connection_failed", error=str(e))
    
    def _handle_wallet_connection_command(self, address: str, wallet_type: str) -> dict[str, str]:
        """
        Handle wallet connection from command.
        
        Args:
            address: Wallet address to connect
            wallet_type: Type of wallet being connected
            
        Returns:
            dict[str, str]: Response message
        """
        try:
            # Create wallet info
            wallet = WalletInfo(address=address, type=wallet_type)
            
            # Handle the connection
            self._handle_wallet_connection(wallet)
            
            return {
                "response": f"Connected to {wallet_type} wallet: {address[:6]}...{address[-4:]}"
            }
        except Exception as e:
            self.logger.exception("wallet_connection_command_failed", error=str(e))
            return {"response": f"Failed to connect wallet: {str(e)}"}
            
    def _handle_wallet_balance_command(self, address: Optional[str] = None) -> dict[str, str]:
        """
        Handle wallet balance query from command.
        
        Args:
            address: Specific wallet address to check (optional)
            
        Returns:
            dict[str, str]: Response message with balance information
        """
        try:
            # Get wallet balance from blockchain provider
            balance_info = self.blockchain.get_wallet_balance(address)
            
            # Format response with balance details
            wallet_type = balance_info.get("wallet_type", "external")
            formatted_address = f"{balance_info['address'][:6]}...{balance_info['address'][-4:]}"
            eth_balance = balance_info["eth_formatted"]
            
            # Build detailed response
            response = f"**{wallet_type.capitalize()} Wallet Balance**\n"
            response += f"Address: `{formatted_address}`\n"
            response += f"ETH Balance: **{eth_balance}**\n"
            
            # Add token balances if available
            if balance_info["tokens"] and len(balance_info["tokens"]) > 0:
                response += "\n**Token Balances:**\n"
                for token in balance_info["tokens"]:
                    response += f"- {token['symbol']}: {token['formatted_balance']}\n"
            
            self.logger.info(
                "wallet_balance_requested",
                address=balance_info["address"],
                wallet_type=wallet_type
            )
            
            return {"response": response}
        except Exception as e:
            self.logger.exception("wallet_balance_command_failed", error=str(e))
            return {"response": f"Failed to get wallet balance: {str(e)}"}
    
    def _handle_list_wallets_command(self) -> dict[str, str]:
        """
        Handle command to list all connected wallets.
        
        Returns:
            dict[str, str]: Response message with wallet information
        """
        try:
            # Get list of connected wallets
            wallets = self.blockchain.get_connected_wallets()
            
            if not wallets:
                return {"response": "No wallets are currently connected."}
            
            # Format response with wallet details
            response = "**Connected Wallets:**\n"
            for wallet in wallets:
                address = wallet["address"]
                formatted_address = f"{address[:6]}...{address[-4:]}"
                active_marker = "(Active)" if wallet.get("is_active", False) else ""
                
                response += f"- {wallet['label']} `{formatted_address}` {active_marker}\n"
            
            return {"response": response}
        except Exception as e:
            self.logger.exception("list_wallets_command_failed", error=str(e))
            return {"response": f"Failed to list wallets: {str(e)}"}

    def _is_balance_query(self, message: str) -> bool:
        """
        Check if a message is a balance query using heuristics.
        
        Args:
            message: The message to check
            
        Returns:
            bool: True if the message appears to be a balance query
        """
        # Convert to lowercase for case-insensitive matching
        text = message.lower()
        
        # Common balance query patterns
        balance_keywords = [
            "balance", "how much", "check balance", "wallet balance",
            "my balance", "account balance", "how many", "what is my balance",
            "what's my balance", "whats my balance", "what is in my wallet",
            "what do i have", "my holdings", "show me my balance", "show balance"
        ]
        
        # Check for simple balance query patterns
        for keyword in balance_keywords:
            if keyword in text:
                # Also check for wallet mentions
                wallet_keywords = ["wallet", "eth", "ethereum", "metamask", "account"]
                for wallet_keyword in wallet_keywords:
                    if wallet_keyword in text:
                        return True
                        
                # If 'balance' is specifically mentioned, it's likely a balance query
                if "balance" in text:
                    return True
        
        return False
        
    async def get_semantic_route(self, message: str) -> SemanticRouterResponse:
        """
        Determine the semantic route for a message using AI provider.

        Args:
            message: Message to route

        Returns:
            SemanticRouterResponse: Determined route for the message
        """
        try:
            prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                "semantic_router", user_input=message
            )
            route_response = self.ai.generate(
                prompt=prompt, response_mime_type=mime_type, response_schema=schema
            )
            # Trim whitespace to handle newlines in the response
            cleaned_response = route_response.text.strip()
            self.logger.debug("semantic_router_response", response=cleaned_response)
            
            # Match with known enum values - more robust handling
            for enum_value in SemanticRouterResponse:
                if cleaned_response == enum_value.value or cleaned_response.upper() == enum_value.name:
                    return enum_value
            
            # Default to conversational if no match
            self.logger.warning("semantic_router_fallback", response=cleaned_response, fallback="CONVERSATIONAL")
            return SemanticRouterResponse.CONVERSATIONAL
        except Exception as e:
            self.logger.exception("routing_failed", error=str(e))
            return SemanticRouterResponse.CONVERSATIONAL

    async def route_message(
        self, route: SemanticRouterResponse, message: str
    ) -> dict[str, str]:
        """
        Route a message to the appropriate handler based on semantic route.

        Args:
            route: Determined semantic route
            message: Original message to handle

        Returns:
            dict[str, str]: Response from the appropriate handler
        """
        # Check if this might be a DeFi command when we have a connected wallet and agent
        if self.connected_wallet_address and self.defi_agent and self._might_be_defi_command(message):
            try:
                self.logger.info("potential_defi_command_detected", message=message)
                return await self._handle_defi_command(message)
            except Exception as e:
                self.logger.exception("defi_command_handling_failed", error=str(e))
                # If DeFi command handling fails, fall back to standard routing
                self.logger.info("falling_back_to_standard_routing", message=message)
        
        # Standard routing logic
        handlers = {
            SemanticRouterResponse.GENERATE_ACCOUNT: self.handle_generate_account,
            SemanticRouterResponse.SEND_TOKEN: self.handle_send_token,
            SemanticRouterResponse.SWAP_TOKEN: self.handle_swap_token,
            SemanticRouterResponse.REQUEST_ATTESTATION: self.handle_attestation,
            SemanticRouterResponse.CONVERSATIONAL: self.handle_conversation,
        }

        handler = handlers.get(route)
        if not handler:
            return {"response": "Unsupported route"}

        return await handler(message)

    async def handle_generate_account(self, _: str) -> dict[str, str]:
        """
        Handle account generation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing new account information
                or existing account
        """
        if self.blockchain.address:
            return {"response": f"Account exists - {self.blockchain.address}"}
        address = self.blockchain.generate_account()
        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "generate_account", address=address
        )
        gen_address_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        return {"response": gen_address_response.text}

    async def handle_send_token(self, message: str) -> dict[str, str]:
        """
        Handle token sending requests.

        Args:
            message: Message containing token sending details

        Returns:
            dict[str, str]: Response containing transaction preview or follow-up prompt
        """
        if not self.blockchain.address:
            await self.handle_generate_account(message)

        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "token_send", user_input=message
        )
        send_token_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        send_token_json = json.loads(send_token_response.text)
        expected_json_len = 2
        if (
            len(send_token_json) != expected_json_len
            or send_token_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_send")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text}

        tx = self.blockchain.create_send_flr_tx(
            to_address=send_token_json.get("to_address"),
            amount=send_token_json.get("amount"),
        )
        self.logger.debug("send_token_tx", tx=tx)
        self.blockchain.add_tx_to_queue(msg=message, tx=tx)
        formatted_preview = (
            "Transaction Preview: "
            + f"Sending {Web3.from_wei(tx.get('value', 0), 'ether')} "
            + f"FLR to {tx.get('to')}\nType CONFIRM to proceed."
        )
        return {"response": formatted_preview}

    async def handle_swap_token(self, message: str) -> dict[str, str]:
        """
        Handle token swap requests with enhanced risk assessment and validation.

        Args:
            message: Message containing swap details

        Returns:
            dict[str, str]: Response containing transaction preview with risk assessment
        """
        if not self.blockchain.address:
            await self.handle_generate_account(message)

        try:
            # Use AI to extract structured swap operation from natural language
            prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                "extract_swap_operation", user_input=message
            )
            extraction_response = self.ai.generate(
                prompt=prompt, response_mime_type=mime_type, response_schema=schema
            )
            
            # Parse the structured operation data
            swap_data = json.loads(extraction_response.text)
            
            # Format as a DeFi operation for the enhanced validation API
            operation_data = {
                "operation_type": "swap",
                "token_in": swap_data.get("token_in"),
                "token_out": swap_data.get("token_out"),
                "amount": swap_data.get("amount"),
                "parameters": {
                    "slippage": swap_data.get("slippage", "1.0"),
                    "protocol": swap_data.get("protocol", "raindex")
                }
            }
            
            # Forward to the DeFi operations API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/routes/defi",
                    json=operation_data
                ) as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        self.logger.error(
                            "defi_operation_api_error",
                            status=response.status,
                            detail=error_detail
                        )
                        return {"response": f"Error processing swap operation: {error_detail}"}
                    
                    result = await response.json()
                    return result
        
        except Exception as e:
            self.logger.exception("swap_operation_handling_failed", error=str(e))
            return {"response": f"Error processing your swap request: {str(e)}"}

    async def handle_attestation(self, _: str) -> dict[str, str]:
        """
        Handle attestation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing attestation request
        """
        prompt = self.prompts.get_formatted_prompt("request_attestation")[0]
        request_attestation_response = self.ai.generate(prompt=prompt)
        self.attestation.attestation_requested = True
        return {"response": request_attestation_response.text}

    async def handle_conversation(self, message: str) -> dict[str, str]:
        """
        Handle general conversation messages.

        Args:
            message: Message to process

        Returns:
            dict[str, str]: Response from AI provider
        """
        response = self.ai.send_message(message)
        return {"response": response.text}
        
    def _might_be_defi_command(self, message: str) -> bool:
        """
        Check if a message might be a DeFi command using keyword heuristics.
        
        Args:
            message: The message to check
            
        Returns:
            bool: True if the message appears to be a DeFi command
        """
        # Convert to lowercase for case-insensitive matching
        text = message.lower()
        
        # Common DeFi operation keywords
        defi_keywords = [
            "swap", "trade", "exchange", "buy", "sell", "transfer", "send", 
            "stake", "unstake", "deposit", "withdraw", "borrow", "supply",
            "repay", "liquidity", "yield", "farm", "harvest", "claim",
            "bridge", "lend", "pool", "token", "flr", "sfin", "usdc", "usdt",
            "sparkdex", "kinetic", "cyclo", "raindex", "flare", "ftso"
        ]
        
        # Check for token symbols and amounts
        token_pattern = re.compile(r'\b\d+(\.\d+)?\s*([a-zA-Z]{2,10})\b')
        has_token_amount = bool(token_pattern.search(text))
        
        # Check for simple DeFi command patterns
        has_keyword = any(keyword in text for keyword in defi_keywords)
        
        return has_keyword or has_token_amount
    
    async def _handle_defi_command(self, command: str) -> dict[str, str]:
        """
        Process a DeFi command using the DeFi agent.
        
        Args:
            command: The DeFi command to process
            
        Returns:
            dict[str, str]: Response containing transaction result
        """
        try:
            self.logger.info("processing_defi_command", command=command)
            
            # Process the command through the DeFi agent
            result = self.defi_agent.process_natural_language_command(command)
            
            # Create a well-formatted transaction result response
            if result["success"]:
                # Transaction was successful
                response = f"✅ Successfully executed {result['action']} on {result['protocol']}.\n\n"
                
                # Add transaction hash if available
                if result.get("transaction_hash"):
                    tx_hash = result["transaction_hash"]
                    # Link to block explorer if available in settings
                    try:
                        from flare_ai_defai.config import settings
                        explorer_url = f"{settings.web3_explorer_url}/tx/{tx_hash}"
                        response += f"Transaction hash: [{tx_hash[:8]}...{tx_hash[-6:]}]({explorer_url})\n\n"
                    except ImportError:
                        response += f"Transaction hash: {tx_hash[:8]}...{tx_hash[-6:]}\n\n"
                
                # Add risk assessment if available
                if result.get("risk_assessment"):
                    risk = result["risk_assessment"]
                    risk_level = risk.get("overall_risk", {}).get("level", "UNKNOWN")
                    
                    risk_emoji = "🟢" if risk_level == "LOW" else \
                                "🟠" if risk_level == "MEDIUM" else \
                                "🔴" if risk_level == "HIGH" else "⚪"
                                
                    response += f"Risk Assessment: {risk_emoji} {risk_level}\n"
                    
                    # Add risk factors if available
                    if risk.get("risk_factors"):
                        response += "\nRisk Factors:\n"
                        for factor in risk["risk_factors"]:
                            factor_level = factor.get("level", "UNKNOWN")
                            factor_emoji = "🟢" if factor_level == "LOW" else \
                                          "🟠" if factor_level == "MEDIUM" else \
                                          "🔴" if factor_level == "HIGH" else "⚪"
                            response += f"- {factor_emoji} {factor.get('name')}: {factor.get('description')}\n"
                
                # Add warnings if available
                if result.get("warnings") and result["warnings"]:
                    response += "\n⚠️ Warnings:\n"
                    for warning in result["warnings"]:
                        response += f"- {warning}\n"
                
                # Add recommendations if available
                if result.get("recommendations") and result["recommendations"]:
                    response += "\n💡 Recommendations:\n"
                    for rec in result["recommendations"]:
                        response += f"- {rec}\n"
                        
            else:
                # Transaction failed
                response = f"❌ Failed to execute {result.get('action', 'transaction')}"                
                if result.get("protocol"):
                    response += f" on {result['protocol']}"
                response += ".\n\n"
                
                # Add errors if available
                if result.get("errors") and result["errors"]:
                    response += "Errors:\n"
                    for error in result["errors"]:
                        response += f"- {error}\n"
                        
                # Add recommendations if available
                if result.get("recommendations") and result["recommendations"]:
                    response += "\n💡 Recommendations:\n"
                    for rec in result["recommendations"]:
                        response += f"- {rec}\n"
            
            return {"response": response}
        except Exception as e:
            self.logger.exception("defi_command_processing_failed", error=str(e))
            return {"response": f"Error processing DeFi command: {str(e)}"}
