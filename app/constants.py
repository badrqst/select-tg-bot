"""Constants and enums for the application."""
from enum import Enum


class KYCStatus(str, Enum):
    """KYC verification status (from Iron API)."""
    NOT_STARTED = "not_started"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class TransactionStatus(str, Enum):
    """Transaction status (from Iron API)."""
    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class WalletType(str, Enum):
    """Crypto wallet type (from Iron API)."""
    SELF_HOSTED = "SelfHosted"
    HOSTED = "Hosted"


class CryptoNetwork(str, Enum):
    """Supported crypto networks (from Iron API - must match exactly with capital letter)."""
    ETHEREUM = "Ethereum"
    POLYGON = "Polygon"
    SOLANA = "Solana"
    ARBITRUM = "Arbitrum"
    BASE = "Base"
    STELLAR = "Stellar"


class Currency(str, Enum):
    """Supported currencies."""
    USDT = "USDT"
    EUR = "EUR"


# Callback data prefixes
class CallbackPrefix(str, Enum):
    """Callback query data prefixes."""
    WALLET_TYPE = "wt_"
    WALLET_NETWORK = "wn_"
    WALLET_SELECT = "ws_"
    BANK_SELECT = "bs_"
    BUY_CONFIRM = "buy_confirm_"
    SELL_CONFIRM = "sell_confirm_"
    CANCEL = "cancel"
    BACK = "back"
