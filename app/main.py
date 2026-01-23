"""Main entry point for the Telegram bot."""
import asyncio
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from app.config import settings
from app.models.database import init_db
from app.bot.handlers import (
    # Start & KYC
    start_command,
    kyc_email,
    kyc_name,
    # Profile
    profile_command,
    # Wallets & Banks
    wallets_banks_menu,
    add_wallet_start,
    wallet_type_selected,
    wallet_network_selected,
    wallet_address_input,
    add_bank_start,
    bank_iban_input,
    view_wallets,
    view_banks,
    handle_back,
    # Buy
    buy_start,
    buy_amount_input,
    buy_wallet_selected,
    buy_bank_selected,
    # Sell
    sell_start,
    sell_amount_input,
    sell_wallet_selected,
    sell_bank_selected,
    # Common
    cancel_conversation,
)
from app.bot.states import ConversationState
from app.constants import CallbackPrefix

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


async def post_init(application):
    """Initialize database after application is created."""
    await init_db()
    logger.info("Database initialized")


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()

    # =========================================================================
    # KYC Conversation Handler
    # =========================================================================
    kyc_conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            ConversationState.KYC_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kyc_email),
            ],
            ConversationState.KYC_FIRST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kyc_name),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
        ],
    )

    # =========================================================================
    # Wallet Management Conversation Handler
    # =========================================================================
    wallet_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_wallet_start, pattern="^add_wallet$"),
        ],
        states={
            ConversationState.WALLET_TYPE_SELECTION: [
                CallbackQueryHandler(wallet_type_selected, pattern=f"^{CallbackPrefix.WALLET_TYPE}"),
                CallbackQueryHandler(handle_back, pattern=f"^{CallbackPrefix.BACK}$"),
            ],
            ConversationState.WALLET_NETWORK_SELECTION: [
                CallbackQueryHandler(wallet_network_selected, pattern=f"^{CallbackPrefix.WALLET_NETWORK}"),
                CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
            ],
            ConversationState.WALLET_ADDRESS_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_address_input),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
        ],
    )

    # =========================================================================
    # Bank Account Conversation Handler
    # =========================================================================
    bank_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_bank_start, pattern="^add_bank$"),
        ],
        states={
            ConversationState.BANK_IBAN_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bank_iban_input),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
        ],
    )

    # =========================================================================
    # Buy USDT Conversation Handler
    # =========================================================================
    buy_conversation = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💰 Buy USDT$"), buy_start),
        ],
        states={
            ConversationState.BUY_AMOUNT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, buy_amount_input),
            ],
            ConversationState.BUY_WALLET_SELECTION: [
                CallbackQueryHandler(buy_wallet_selected, pattern=f"^{CallbackPrefix.WALLET_SELECT}"),
                CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
            ],
            ConversationState.BUY_BANK_SELECTION: [
                CallbackQueryHandler(buy_bank_selected, pattern=f"^{CallbackPrefix.BANK_SELECT}"),
                CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
        ],
    )

    # =========================================================================
    # Sell USDT Conversation Handler
    # =========================================================================
    sell_conversation = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💸 Sell USDT$"), sell_start),
        ],
        states={
            ConversationState.SELL_AMOUNT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sell_amount_input),
            ],
            ConversationState.SELL_WALLET_SELECTION: [
                CallbackQueryHandler(sell_wallet_selected, pattern=f"^{CallbackPrefix.WALLET_SELECT}"),
                CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
            ],
            ConversationState.SELL_BANK_SELECTION: [
                CallbackQueryHandler(sell_bank_selected, pattern=f"^{CallbackPrefix.BANK_SELECT}"),
                CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern=f"^{CallbackPrefix.CANCEL}$"),
        ],
    )

    # =========================================================================
    # Register Handlers
    # =========================================================================
    application.add_handler(kyc_conversation)
    application.add_handler(wallet_conversation)
    application.add_handler(bank_conversation)
    application.add_handler(buy_conversation)
    application.add_handler(sell_conversation)

    # Simple command handlers
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(MessageHandler(filters.Regex("^👤 Profile$"), profile_command))

    # Wallets & Banks menu
    application.add_handler(MessageHandler(filters.Regex("^💼 Wallets & Banks$"), wallets_banks_menu))

    # Callback query handlers for viewing
    application.add_handler(CallbackQueryHandler(view_wallets, pattern="^view_wallets$"))
    application.add_handler(CallbackQueryHandler(view_banks, pattern="^view_banks$"))

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
