"""Iron API service for crypto/fiat operations - corrected according to official API spec."""
import logging
import uuid
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class IronAPIError(Exception):
    """Custom exception for Iron API errors."""
    pass


class IronAPIService:
    """Service for interacting with Iron API."""

    def __init__(self):
        self.base_url = settings.iron_api_base_url
        self.api_key = settings.iron_api_key
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Iron API."""
        url = f"{self.base_url}{endpoint}"

        # Prepare headers
        headers = self.headers.copy()

        # Add IDEMPOTENCY-KEY for POST/PUT/PATCH requests (uppercase with dashes!)
        if method.upper() in ["POST", "PUT", "PATCH"]:
            headers["IDEMPOTENCY-KEY"] = str(uuid.uuid4())

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Iron API HTTP error: {e.response.status_code} - {e.response.text}")
                raise IronAPIError(f"API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Iron API request error: {str(e)}")
                raise IronAPIError(f"Request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise IronAPIError(f"Unexpected error: {str(e)}")

    # =========================================================================
    # Customer Management
    # =========================================================================

    async def onboard_customer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Onboard a new customer to Iron.

        Args:
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            metadata: Optional metadata dictionary

        Returns:
            Customer data with 'id' field (UUID)
        """
        data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        if metadata:
            data["metadata"] = metadata

        result = await self._request("POST", "/customers", data=data)
        logger.info(f"Customer created: {result.get('id')}")
        return result

    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        """
        Get customer details including KYC status.

        Returns:
            Customer data with fields: id, email, kyc_status, kyc_url, created_at
        """
        result = await self._request("GET", f"/customer/{customer_id}")
        return result

    # =========================================================================
    # Crypto Wallet Management
    # =========================================================================

    async def register_self_hosted_wallet(
        self,
        customer_id: str,
        blockchain: str,
        wallet_address: str,
        proof_message: Optional[str] = None,
        proof_signature: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Register a self-hosted (customer-controlled) crypto wallet.

        Args:
            customer_id: Customer UUID
            blockchain: Blockchain name (Ethereum, Solana, Polygon, Arbitrum, Base, Stellar)
            wallet_address: Wallet address
            proof_message: Optional proof message for wallet ownership
            proof_signature: Optional signature proving wallet ownership

        Returns:
            Wallet data with 'id', 'wallet_address', 'blockchain', 'address_type': 'SelfHosted'
        """
        data = {
            "customer_id": customer_id,
            "blockchain": blockchain,
            "wallet_address": wallet_address,
        }

        if proof_message:
            data["proof_message"] = proof_message
        if proof_signature:
            data["proof_signature"] = proof_signature

        result = await self._request("POST", "/addresses/crypto/self-hosted", data=data)
        logger.info(f"Self-hosted wallet registered: {wallet_address}")
        return result

    async def register_hosted_wallet(
        self,
        customer_id: str,
        blockchain: str,
        wallet_address: str,
        vasp_did: str,
    ) -> dict[str, Any]:
        """
        Register a hosted wallet (exchange wallet).

        Args:
            customer_id: Customer UUID
            blockchain: Blockchain name (Ethereum, Solana, Polygon, Arbitrum, Base, Stellar)
            wallet_address: Wallet address on the exchange
            vasp_did: VASP DID of the hosting exchange (get from search_vasps)

        Returns:
            Wallet data with 'id', 'wallet_address', 'blockchain', 'address_type': 'Hosted'
        """
        data = {
            "customer_id": customer_id,
            "blockchain": blockchain,
            "wallet_address": wallet_address,
            "vasp_did": vasp_did,
        }

        result = await self._request("POST", "/addresses/crypto/hosted", data=data)
        logger.info(f"Hosted wallet registered: {wallet_address}")
        return result

    async def search_vasps(self, query: str) -> list[dict[str, Any]]:
        """
        Search for VASP (exchange) providers to get their DID.

        Args:
            query: Search query (e.g., 'binance', 'coinbase')

        Returns:
            List of VASPs with 'did', 'name', 'country'
        """
        params = {"query": query}
        result = await self._request("GET", "/addresses/search-vasps", params=params)
        return result.get("results", [])

    async def get_crypto_wallets(self, customer_id: str) -> list[dict[str, Any]]:
        """
        Get all crypto wallets for a customer.

        Returns:
            List of wallet addresses with fields:
            - id (UUID)
            - address_type (Hosted/SelfHosted)
            - blockchain
            - wallet_address
            - disabled
            - created_at
        """
        params = {"customer_id": customer_id}
        result = await self._request("GET", "/addresses/crypto", params=params)
        return result.get("addresses", [])

    async def update_wallet_status(self, address_id: str, disabled: bool) -> dict[str, Any]:
        """Enable or disable a crypto wallet address."""
        data = {"disabled": disabled}
        result = await self._request("PUT", f"/addresses/crypto/{address_id}/disabled", data=data)
        return result

    # =========================================================================
    # Fiat Bank Account Management
    # =========================================================================

    async def register_bank_account(
        self,
        customer_id: str,
        account_holder_name: str,
        iban: str,
        country_code: str,
        bic: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Register a SEPA bank account for fiat operations.

        Args:
            customer_id: Customer UUID
            account_holder_name: Name on the bank account
            iban: IBAN number
            country_code: 2-letter country code (e.g., 'DE', 'FR')
            bic: Optional BIC/SWIFT code

        Returns:
            Bank account data with 'id', 'iban', 'account_holder_name', 'status'
        """
        data = {
            "customer_id": customer_id,
            "account_holder_name": account_holder_name,
            "iban": iban,
            "country_code": country_code,
        }

        if bic:
            data["bic"] = bic

        result = await self._request("POST", "/addresses/fiat", data=data)
        logger.info(f"Bank account registered: {iban}")
        return result

    async def get_bank_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        """
        Get all bank accounts for a customer.

        Returns:
            List of bank accounts with fields:
            - id (UUID)
            - iban
            - account_holder_name
            - status (pending/verified/failed)
            - created_at
        """
        params = {"customer_id": customer_id}
        result = await self._request("GET", "/addresses/fiat", params=params)
        return result.get("accounts", [])

    async def get_bank_account(self, address_id: str) -> dict[str, Any]:
        """Get specific bank account details."""
        result = await self._request("GET", f"/addresses/fiat/{address_id}")
        return result

    async def delete_bank_account(self, address_id: str) -> dict[str, Any]:
        """Delete a bank account."""
        result = await self._request("DELETE", f"/addresses/fiat/{address_id}")
        return result

    # =========================================================================
    # Quotes
    # =========================================================================

    async def get_quote(
        self,
        customer_id: str,
        source_currency: str,
        target_currency: str,
        source_amount: Optional[float] = None,
        target_amount: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Get a quote for currency exchange.

        Args:
            customer_id: Customer UUID
            source_currency: Source currency code (EUR, USD, GBP, USDT, USDC)
            target_currency: Target currency code (EUR, USD, GBP, USDT, USDC)
            source_amount: Amount to convert FROM (specify this OR target_amount)
            target_amount: Amount to receive TO (specify this OR source_amount)

        Returns:
            Quote with fields:
            - quote_id (UUID)
            - source_amount
            - target_amount
            - exchange_rate
            - fee_amount
            - expires_at
        """
        data = {
            "customer_id": customer_id,
            "source_currency": source_currency,
            "target_currency": target_currency,
        }

        if source_amount is not None:
            data["source_amount"] = source_amount
        if target_amount is not None:
            data["target_amount"] = target_amount

        result = await self._request("POST", "/quotes", data=data)
        logger.info(
            f"Quote: {result.get('source_amount')} {source_currency} = "
            f"{result.get('target_amount')} {target_currency}"
        )
        return result

    # =========================================================================
    # Onramp (Buy Crypto with Fiat)
    # =========================================================================

    async def create_onramp_order(
        self,
        customer_id: str,
        quote_id: str,
        crypto_address_id: str,
        fiat_address_id: str,
    ) -> dict[str, Any]:
        """
        Create an onramp order (buy crypto with fiat).

        Args:
            customer_id: Customer UUID
            quote_id: Quote UUID from get_quote()
            crypto_address_id: Destination wallet ID
            fiat_address_id: Source bank account ID

        Returns:
            Order data with:
            - order_id (UUID)
            - transaction_id (UUID)
            - status
            - payment_reference (use this in SEPA transfer!)
            - payment_iban (send EUR here)
            - payment_bic
            - amount_eur
            - amount_usdt
            - expires_at
        """
        data = {
            "customer_id": customer_id,
            "quote_id": quote_id,
            "crypto_address_id": crypto_address_id,
            "fiat_address_id": fiat_address_id,
        }

        result = await self._request("POST", "/onramp/create", data=data)
        logger.info(f"Onramp order created: {result.get('order_id')}")
        return result

    # =========================================================================
    # Offramp (Sell Crypto for Fiat)
    # =========================================================================

    async def create_offramp_order(
        self,
        customer_id: str,
        quote_id: str,
        crypto_address_id: str,
        fiat_address_id: str,
    ) -> dict[str, Any]:
        """
        Create an offramp order (sell crypto for fiat).

        Args:
            customer_id: Customer UUID
            quote_id: Quote UUID from get_quote()
            crypto_address_id: Source wallet ID
            fiat_address_id: Destination bank account ID

        Returns:
            Order data with:
            - order_id (UUID)
            - transaction_id (UUID)
            - status
            - deposit_address (send USDT here!)
            - deposit_network
            - amount_usdt
            - amount_eur
            - expires_at
        """
        data = {
            "customer_id": customer_id,
            "quote_id": quote_id,
            "crypto_address_id": crypto_address_id,
            "fiat_address_id": fiat_address_id,
        }

        result = await self._request("POST", "/offramp/create", data=data)
        logger.info(f"Offramp order created: {result.get('order_id')}")
        return result

    # =========================================================================
    # Transactions
    # =========================================================================

    async def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        """
        Get details of a specific transaction.

        Returns:
            Transaction with fields:
            - transaction_id
            - order_id
            - type (onramp/offramp)
            - status (created/pending/processing/completed/failed/expired)
            - source_amount
            - target_amount
            - created_at
            - updated_at
            - completed_at
        """
        result = await self._request("GET", f"/transactions/{transaction_id}")
        return result

    async def get_transactions(
        self,
        customer_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get transaction history for a customer.

        Args:
            customer_id: Customer UUID
            limit: Max results (default 50, max 100)
            offset: Pagination offset (default 0)

        Returns:
            List of transactions
        """
        params = {
            "customer_id": customer_id,
            "limit": min(limit, 100),
            "offset": offset,
        }

        result = await self._request("GET", "/transactions", params=params)
        return result.get("transactions", [])

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_country_subdivisions(self, country_code: str) -> dict[str, Any]:
        """Get list of states/provinces for a country."""
        params = {"country_code": country_code}
        result = await self._request("GET", "/addresses/country-subdivisions", params=params)
        return result


# Global instance
iron_api = IronAPIService()
