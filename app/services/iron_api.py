"""Iron API service for crypto/fiat operations."""
import logging
import uuid
from typing import Any, Optional

import httpx

from app.config import settings
from app.constants import WalletType, CryptoNetwork

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

        # Add Idempotency-Key for POST/PUT/PATCH requests
        if method.upper() in ["POST", "PUT", "PATCH"]:
            headers["Idempotency-Key"] = str(uuid.uuid4())

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
                raise IronAPIError(f"API error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Iron API request error: {str(e)}")
                raise IronAPIError(f"Request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise IronAPIError(f"Unexpected error: {str(e)}")

    # Customer Management
    async def onboard_customer(
        self,
        telegram_id: int,
        email: str,
        first_name: str,
        last_name: str,
    ) -> dict[str, Any]:
        """
        Onboard a new customer to Iron.

        Returns customer data including customer_id.
        """
        data = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "externalId": str(telegram_id),  # Use telegram_id as external reference
        }

        result = await self._request("POST", "/customer/onboard", data=data)
        logger.info(f"Customer onboarded: {result.get('customerId')}")
        return result

    async def get_customer_kyc_status(self, customer_id: str) -> dict[str, Any]:
        """Get KYC status for a customer."""
        result = await self._request("GET", f"/customer/{customer_id}")
        return result

    # Crypto Wallet Management
    async def register_self_hosted_wallet(
        self,
        customer_id: str,
        network: CryptoNetwork,
        address: str,
        label: Optional[str] = None,
    ) -> dict[str, Any]:
        """Register a self-hosted (external) crypto wallet."""
        data = {
            "customerId": customer_id,
            "network": network.value,
            "address": address,
            "label": label or f"{network.value.upper()} Wallet",
        }

        result = await self._request("POST", "/addresses/crypto/self-hosted", data=data)
        logger.info(f"Self-hosted wallet registered: {address}")
        return result

    async def create_hosted_wallet(
        self,
        customer_id: str,
        network: CryptoNetwork,
        label: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a hosted wallet (managed by Iron)."""
        data = {
            "customerId": customer_id,
            "network": network.value,
            "label": label or f"Hosted {network.value.upper()} Wallet",
        }

        result = await self._request("POST", "/addresses/crypto/hosted", data=data)
        logger.info(f"Hosted wallet created for customer {customer_id}")
        return result

    async def get_crypto_wallets(self, customer_id: str) -> list[dict[str, Any]]:
        """Get all crypto wallets for a customer."""
        params = {"customer_id": customer_id}
        result = await self._request("GET", "/addresses/crypto", params=params)
        return result.get("addresses", [])

    # Fiat Bank Account Management
    async def register_bank_account(
        self,
        customer_id: str,
        iban: str,
        label: Optional[str] = None,
    ) -> dict[str, Any]:
        """Register a bank account (IBAN) for fiat operations."""
        data = {
            "customerId": customer_id,
            "iban": iban,
            "label": label or "EUR Bank Account",
        }

        result = await self._request("POST", "/addresses/fiat", data=data)
        logger.info(f"Bank account registered: {iban}")
        return result

    async def get_bank_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        """Get all bank accounts for a customer."""
        params = {"customer_id": customer_id}
        result = await self._request("GET", "/addresses/fiat", params=params)
        return result.get("accounts", [])

    # Quotes
    async def get_quote(
        self,
        source_currency: str,
        destination_currency: str,
        amount: float,
    ) -> dict[str, Any]:
        """
        Get a quote for currency exchange.

        Args:
            source_currency: e.g., "EUR" or "USDT"
            destination_currency: e.g., "USDT" or "EUR"
            amount: Amount in source currency
        """
        data = {
            "sourceCurrency": source_currency,
            "destinationCurrency": destination_currency,
            "amount": amount,
        }

        result = await self._request("POST", "/quotes", data=data)
        logger.info(f"Quote: {amount} {source_currency} = {result.get('destinationAmount')} {destination_currency}")
        return result

    # Onramp (Buy Crypto with Fiat)
    async def create_onramp_order(
        self,
        customer_id: str,
        quote_id: str,
        source_account_id: str,  # Bank account ID
        destination_address_id: str,  # Crypto wallet ID
    ) -> dict[str, Any]:
        """
        Create an onramp order (buy crypto with fiat).

        Returns order details including payment instructions.
        """
        data = {
            "customerId": customer_id,
            "quoteId": quote_id,
            "sourceAccountId": source_account_id,
            "destinationAddressId": destination_address_id,
        }

        result = await self._request("POST", "/onramp/create", data=data)
        logger.info(f"Onramp order created: {result.get('orderId')}")
        return result

    # Offramp (Sell Crypto for Fiat)
    async def create_offramp_order(
        self,
        customer_id: str,
        quote_id: str,
        source_address_id: str,  # Crypto wallet ID
        destination_account_id: str,  # Bank account ID
    ) -> dict[str, Any]:
        """
        Create an offramp order (sell crypto for fiat).

        Returns order details including crypto deposit address.
        """
        data = {
            "customerId": customer_id,
            "quoteId": quote_id,
            "sourceAddressId": source_address_id,
            "destinationAccountId": destination_account_id,
        }

        result = await self._request("POST", "/offramp/create", data=data)
        logger.info(f"Offramp order created: {result.get('orderId')}")
        return result

    # Transactions
    async def get_transactions(
        self,
        customer_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get transaction history for a customer."""
        params = {
            "customer_id": customer_id,
            "limit": limit,
            "offset": offset,
        }

        result = await self._request("GET", "/transactions", params=params)
        return result.get("transactions", [])

    async def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        """Get details of a specific transaction."""
        result = await self._request("GET", f"/transactions/{transaction_id}")
        return result


# Global instance
iron_api = IronAPIService()
