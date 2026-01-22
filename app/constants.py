"""Constants and enums for the application."""
from enum import Enum


class KYCStatus(str, Enum):
    """KYC verification status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_STARTED = "not_started"


class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WalletType(str, Enum):
    """Crypto wallet type."""
    SELF_HOSTED = "self_hosted"
    HOSTED = "hosted"


class CryptoNetwork(str, Enum):
    """Supported crypto networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    TRON = "tron"


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
