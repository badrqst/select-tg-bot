"""Conversation states for the bot."""
from enum import IntEnum


class ConversationState(IntEnum):
    """States for conversation handler."""
    # KYC flow
    KYC_EMAIL = 1
    KYC_FIRST_NAME = 2
    KYC_LAST_NAME = 3

    # Wallet management
    WALLET_TYPE_SELECTION = 10
    WALLET_NETWORK_SELECTION = 11
    WALLET_ADDRESS_INPUT = 12

    # Bank account management
    BANK_IBAN_INPUT = 20
    BANK_LABEL_INPUT = 21

    # Buy flow
    BUY_AMOUNT_INPUT = 30
    BUY_WALLET_SELECTION = 31
    BUY_BANK_SELECTION = 32
    BUY_CONFIRMATION = 33

    # Sell flow
    SELL_AMOUNT_INPUT = 40
    SELL_WALLET_SELECTION = 41
    SELL_BANK_SELECTION = 42
    SELL_CONFIRMATION = 43


# Temporary storage for conversation data
# In production, consider using Redis or similar
conversation_data: dict[int, dict] = {}


def get_user_data(telegram_id: int) -> dict:
    """Get or create conversation data for user."""
    if telegram_id not in conversation_data:
        conversation_data[telegram_id] = {}
    return conversation_data[telegram_id]


def clear_user_data(telegram_id: int):
    """Clear conversation data for user."""
    if telegram_id in conversation_data:
        del conversation_data[telegram_id]
