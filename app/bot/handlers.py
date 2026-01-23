"""Bot handlers for commands and conversations."""
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AsyncSessionLocal
from app.models.user import User
from app.services.iron_api import iron_api, IronAPIError
from app.constants import CryptoNetwork, CallbackPrefix, KYCStatus
from app.bot.states import ConversationState, get_user_data, clear_user_data

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get user from database by telegram_id."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def create_user(telegram_id: int, iron_customer_id: str) -> User:
    """Create new user in database."""
    async with AsyncSessionLocal() as session:
        user = User(telegram_id=telegram_id, iron_customer_id=iron_customer_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def get_main_menu_keyboard():
    """Get main menu keyboard."""
    keyboard = [
        ["💰 Buy USDT", "💸 Sell USDT"],
        ["👤 Profile", "💼 Wallets & Banks"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ============================================================================
# Start Command & KYC Flow
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command."""
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if user:
        # User exists, check KYC status
        try:
            customer_data = await iron_api.get_customer(user.iron_customer_id)
            kyc_status = customer_data.get("kyc_status", "not_started")

            if kyc_status == KYCStatus.APPROVED:
                await update.message.reply_text(
                    f"Welcome back, {update.effective_user.first_name}! 👋\n\n"
                    "Choose an option from the menu below:",
                    reply_markup=get_main_menu_keyboard(),
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    f"Your KYC status: {kyc_status}\n\n"
                    "Please complete KYC verification to continue.",
                )
                return ConversationHandler.END
        except IronAPIError as e:
            logger.error(f"Error checking KYC status: {e}")
            await update.message.reply_text(
                "Error checking your account status. Please try again later."
            )
            return ConversationHandler.END

    # New user - start KYC
    await update.message.reply_text(
        f"Welcome to Select Bot! 👋\n\n"
        f"I'll help you exchange USDT/EUR easily.\n\n"
        f"First, let's set up your account.\n\n"
        f"Please provide your email address:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationState.KYC_EMAIL


async def kyc_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle email input for KYC."""
    email = update.message.text.strip()

    # Basic email validation
    if "@" not in email or "." not in email:
        await update.message.reply_text(
            "Please provide a valid email address:"
        )
        return ConversationState.KYC_EMAIL

    user_data = get_user_data(update.effective_user.id)
    user_data["email"] = email

    await update.message.reply_text(
        "Great! Now please provide your full name:"
    )
    return ConversationState.KYC_FIRST_NAME


async def kyc_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle name input and complete KYC onboarding."""
    name = update.message.text.strip()
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)

    await update.message.reply_text(
        "Creating your account... ⏳"
    )

    try:
        # Onboard customer to Iron
        result = await iron_api.onboard_customer(
            email=user_data["email"],
            name=name,
        )

        iron_customer_id = result.get("id")
        if not iron_customer_id:
            raise IronAPIError("No customer ID returned from Iron API")

        # Save to database
        await create_user(telegram_id, iron_customer_id)

        clear_user_data(telegram_id)

        await update.message.reply_text(
            "✅ Account created successfully!\n\n"
            "Note: KYC verification may be required for larger transactions.\n\n"
            "Choose an option from the menu:",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    except IronAPIError as e:
        logger.error(f"Error creating customer: {e}")
        await update.message.reply_text(
            "❌ Error creating account. Please try again later or contact support."
        )
        clear_user_data(telegram_id)
        return ConversationHandler.END


# ============================================================================
# Profile
# ============================================================================

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile."""
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text(
            "Please use /start first to create an account."
        )
        return

    try:
        customer_data = await iron_api.get_customer(user.iron_customer_id)
        transactions = await iron_api.get_transactions(user.iron_customer_id, limit=5)

        profile_text = (
            f"👤 Profile\n\n"
            f"Customer ID: {user.iron_customer_id[:8]}...\n"
            f"KYC Status: {customer_data.get('kyc_status', 'N/A')}\n"
            f"Recent Transactions: {len(transactions)}\n"
        )

        await update.message.reply_text(profile_text)

    except IronAPIError as e:
        logger.error(f"Error fetching profile: {e}")
        await update.message.reply_text(
            "Error loading profile. Please try again."
        )


# ============================================================================
# Wallets & Banks Management
# ============================================================================

async def wallets_banks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallets and banks management menu."""
    keyboard = [
        [InlineKeyboardButton("💳 Add Crypto Wallet", callback_data="add_wallet")],
        [InlineKeyboardButton("🏦 Add Bank Account", callback_data="add_bank")],
        [InlineKeyboardButton("📋 View Wallets", callback_data="view_wallets")],
        [InlineKeyboardButton("📋 View Banks", callback_data="view_banks")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = "💼 Wallets & Banks\n\nManage your crypto wallets and bank accounts:"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
        )


async def add_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start wallet addition flow."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🏠 Self-Hosted (Your Wallet)", callback_data=f"{CallbackPrefix.WALLET_TYPE}self")],
        [InlineKeyboardButton("☁️ Hosted (Iron Wallet)", callback_data=f"{CallbackPrefix.WALLET_TYPE}hosted")],
        [InlineKeyboardButton("« Back", callback_data=CallbackPrefix.BACK)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Choose wallet type:\n\n"
        "🏠 Self-Hosted: Use your own wallet address\n"
        "☁️ Hosted: Iron creates and manages wallet for you",
        reply_markup=reply_markup,
    )
    return ConversationState.WALLET_TYPE_SELECTION


async def wallet_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet type selection."""
    query = update.callback_query
    await query.answer()

    wallet_type = query.data.replace(CallbackPrefix.WALLET_TYPE, "")
    user_data = get_user_data(update.effective_user.id)
    user_data["wallet_type"] = wallet_type

    keyboard = [
        [InlineKeyboardButton("Ethereum", callback_data=f"{CallbackPrefix.WALLET_NETWORK}ethereum")],
        [InlineKeyboardButton("Polygon", callback_data=f"{CallbackPrefix.WALLET_NETWORK}polygon")],
        [InlineKeyboardButton("Tron", callback_data=f"{CallbackPrefix.WALLET_NETWORK}tron")],
        [InlineKeyboardButton("« Cancel", callback_data=CallbackPrefix.CANCEL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Choose network:",
        reply_markup=reply_markup,
    )
    return ConversationState.WALLET_NETWORK_SELECTION


async def wallet_network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle network selection."""
    query = update.callback_query
    await query.answer()

    network = query.data.replace(CallbackPrefix.WALLET_NETWORK, "")
    user_data = get_user_data(update.effective_user.id)
    user_data["wallet_network"] = network

    if user_data["wallet_type"] == "self":
        await query.edit_message_text(
            f"Please send your {network.upper()} wallet address:"
        )
        return ConversationState.WALLET_ADDRESS_INPUT
    else:
        # Create hosted wallet immediately
        return await create_hosted_wallet_finish(update, context)


async def wallet_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet address input."""
    address = update.message.text.strip()
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Error: User not found. Please use /start")
        return ConversationHandler.END

    await update.message.reply_text("Adding wallet... ⏳")

    try:
        network = CryptoNetwork(user_data["wallet_network"])
        result = await iron_api.register_self_hosted_wallet(
            customer_id=user.iron_customer_id,
            network=network,
            address=address,
        )

        clear_user_data(telegram_id)

        await update.message.reply_text(
            f"✅ Wallet added successfully!\n\n"
            f"Network: {network.value.upper()}\n"
            f"Address: {address[:10]}...{address[-8:]}",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    except IronAPIError as e:
        logger.error(f"Error adding wallet: {e}")
        await update.message.reply_text(
            "❌ Error adding wallet. Please check the address and try again."
        )
        clear_user_data(telegram_id)
        return ConversationHandler.END


async def create_hosted_wallet_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create hosted wallet and finish."""
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.callback_query.edit_message_text("Error: User not found. Please use /start")
        return ConversationHandler.END

    query = update.callback_query

    # Hosted wallets require exchange integration (vasp_did + wallet_address)
    clear_user_data(telegram_id)
    await query.edit_message_text(
        "❌ Hosted wallets are not yet supported.\n\n"
        "Hosted wallets require exchange integration with VASP credentials.\n\n"
        "Please use 'Self-Hosted' option to add your own wallet address."
    )
    return ConversationHandler.END


async def add_bank_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start bank account addition flow."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🏦 Add Bank Account\n\n"
        "Please send your IBAN (e.g., DE89370400440532013000):"
    )
    return ConversationState.BANK_IBAN_INPUT


async def bank_iban_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle IBAN input."""
    iban = update.message.text.strip().upper().replace(" ", "")
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Error: User not found. Please use /start")
        return ConversationHandler.END

    # Basic IBAN validation (length check)
    if len(iban) < 15 or len(iban) > 34:
        await update.message.reply_text(
            "Invalid IBAN format. Please try again:"
        )
        return ConversationState.BANK_IBAN_INPUT

    await update.message.reply_text("Adding bank account... ⏳")

    try:
        # Get customer data for account holder name
        customer_data = await iron_api.get_customer(user.iron_customer_id)
        first_name = customer_data.get("first_name", "")
        last_name = customer_data.get("last_name", "")
        account_holder_name = f"{first_name} {last_name}".strip()

        # Extract country code from IBAN (first 2 letters)
        country_code = iban[:2]

        result = await iron_api.register_bank_account(
            customer_id=user.iron_customer_id,
            account_holder_name=account_holder_name,
            iban=iban,
            country_code=country_code,
        )

        await update.message.reply_text(
            f"✅ Bank account added successfully!\n\n"
            f"IBAN: {iban[:4]}...{iban[-4:]}",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    except IronAPIError as e:
        logger.error(f"Error adding bank account: {e}")
        await update.message.reply_text(
            "❌ Error adding bank account. Please check the IBAN and try again."
        )
        return ConversationHandler.END


async def view_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all crypto wallets."""
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await query.edit_message_text("Error: User not found. Please use /start")
        return

    try:
        wallets = await iron_api.get_crypto_wallets(user.iron_customer_id)

        if not wallets:
            await query.edit_message_text(
                "You don't have any wallets yet.\n\n"
                "Use 'Add Crypto Wallet' to add one."
            )
            return

        wallet_text = "💳 Your Crypto Wallets:\n\n"
        for idx, wallet in enumerate(wallets, 1):
            address = wallet.get("wallet_address", "N/A")
            network = wallet.get("blockchain", "N/A")
            wallet_type = wallet.get("type", "N/A")
            wallet_text += f"{idx}. {network.upper()} ({wallet_type})\n"
            wallet_text += f"   {address[:10]}...{address[-8:]}\n\n"

        await query.edit_message_text(wallet_text)

    except IronAPIError as e:
        logger.error(f"Error fetching wallets: {e}")
        await query.edit_message_text("Error loading wallets. Please try again.")


async def view_banks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all bank accounts."""
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await query.edit_message_text("Error: User not found. Please use /start")
        return

    try:
        banks = await iron_api.get_bank_accounts(user.iron_customer_id)

        if not banks:
            await query.edit_message_text(
                "You don't have any bank accounts yet.\n\n"
                "Use 'Add Bank Account' to add one."
            )
            return

        bank_text = "🏦 Your Bank Accounts:\n\n"
        for idx, bank in enumerate(banks, 1):
            iban = bank.get("iban", "N/A")
            account_holder_name = bank.get("account_holder_name", "N/A")
            label = bank.get("label", "EUR Account")
            bank_text += f"{idx}. {label}\n"
            bank_text += f"   {account_holder_name}\n"
            bank_text += f"   {iban[:4]}...{iban[-4:]}\n\n"

        await query.edit_message_text(bank_text)

    except IronAPIError as e:
        logger.error(f"Error fetching bank accounts: {e}")
        await query.edit_message_text("Error loading bank accounts. Please try again.")


# ============================================================================
# Buy USDT Flow
# ============================================================================

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start buy USDT flow."""
    await update.message.reply_text(
        "💰 Buy USDT\n\n"
        "How much EUR do you want to spend?\n\n"
        "Example: 100",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationState.BUY_AMOUNT_INPUT


async def buy_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle EUR amount input for buying."""
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (e.g., 100):"
        )
        return ConversationState.BUY_AMOUNT_INPUT

    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user_data["buy_amount"] = amount
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Error: User not found. Please use /start")
        return ConversationHandler.END

    await update.message.reply_text("Getting quote... ⏳")

    try:
        quote = await iron_api.get_quote(
            customer_id=user.iron_customer_id,
            source_currency="EUR",
            target_currency="USDT",
            source_amount=amount,
        )

        user_data["quote_id"] = quote.get("quote_id")
        user_data["usdt_amount"] = quote.get("target_amount")
        user_data["rate"] = quote.get("exchange_rate")
        user_data["fee"] = quote.get("fee_amount", 0)

        await update.message.reply_text(
            f"💱 Quote:\n\n"
            f"You pay: {amount} EUR\n"
            f"You get: ~{user_data['usdt_amount']} USDT\n"
            f"Rate: {user_data['rate']}\n"
            f"Fee: {user_data['fee']} EUR\n\n"
            f"Select destination wallet:",
        )

        # Show wallet selection
        return await show_wallet_selection_for_buy(update, context)

    except IronAPIError as e:
        logger.error(f"Error getting quote: {e}")
        await update.message.reply_text(
            "❌ Error getting quote. Please try again.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END


async def show_wallet_selection_for_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show wallet selection for buy."""
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    try:
        wallets = await iron_api.get_crypto_wallets(user.iron_customer_id)

        if not wallets:
            await update.message.reply_text(
                "❌ You don't have any wallets.\n\n"
                "Please add a wallet first using '💼 Wallets & Banks'.",
                reply_markup=get_main_menu_keyboard(),
            )
            return ConversationHandler.END

        keyboard = []
        for wallet in wallets:
            address = wallet.get("wallet_address", "")
            network = wallet.get("blockchain", "")
            wallet_id = wallet.get("id", "")
            button_text = f"{network.upper()} - {address[:6]}...{address[-4:]}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{CallbackPrefix.WALLET_SELECT}{wallet_id}")])

        keyboard.append([InlineKeyboardButton("« Cancel", callback_data=CallbackPrefix.CANCEL)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Choose wallet to receive USDT:",
            reply_markup=reply_markup,
        )
        return ConversationState.BUY_WALLET_SELECTION

    except IronAPIError as e:
        logger.error(f"Error fetching wallets: {e}")
        await update.message.reply_text(
            "❌ Error loading wallets.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END


async def buy_wallet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet selection for buy."""
    query = update.callback_query
    await query.answer()

    wallet_id = query.data.replace(CallbackPrefix.WALLET_SELECT, "")
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user_data["destination_wallet_id"] = wallet_id

    user = await get_user_by_telegram_id(telegram_id)

    try:
        banks = await iron_api.get_bank_accounts(user.iron_customer_id)

        if not banks:
            await query.edit_message_text(
                "❌ You don't have any bank accounts.\n\n"
                "Please add a bank account first using '💼 Wallets & Banks'."
            )
            return ConversationHandler.END

        keyboard = []
        for bank in banks:
            iban = bank.get("iban", "")
            bank_id = bank.get("id", "")
            label = bank.get("label", "EUR Account")
            button_text = f"{label} - {iban[:4]}...{iban[-4:]}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{CallbackPrefix.BANK_SELECT}{bank_id}")])

        keyboard.append([InlineKeyboardButton("« Cancel", callback_data=CallbackPrefix.CANCEL)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Choose bank account to pay from:",
            reply_markup=reply_markup,
        )
        return ConversationState.BUY_BANK_SELECTION

    except IronAPIError as e:
        logger.error(f"Error fetching banks: {e}")
        await query.edit_message_text("❌ Error loading bank accounts.")
        return ConversationHandler.END


async def buy_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank selection and create order."""
    query = update.callback_query
    await query.answer()

    bank_id = query.data.replace(CallbackPrefix.BANK_SELECT, "")
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user = await get_user_by_telegram_id(telegram_id)

    await query.edit_message_text("Creating order... ⏳")

    try:
        order = await iron_api.create_onramp_order(
            customer_id=user.iron_customer_id,
            quote_id=user_data["quote_id"],
            crypto_address_id=user_data["destination_wallet_id"],
            fiat_address_id=bank_id,
        )

        order_id = order.get("order_id")
        payment_reference = order.get("payment_reference", "N/A")
        payment_iban = order.get("payment_iban", "N/A")
        payment_bic = order.get("payment_bic", "N/A")
        amount_eur = order.get("amount_eur", user_data["buy_amount"])
        amount_usdt = order.get("amount_usdt", user_data["usdt_amount"])

        clear_user_data(telegram_id)

        await query.edit_message_text(
            f"✅ Order created!\n\n"
            f"Order ID: {order_id}\n\n"
            f"📤 Payment Instructions:\n"
            f"Amount: {amount_eur} EUR\n"
            f"IBAN: {payment_iban}\n"
            f"BIC: {payment_bic}\n"
            f"Reference: {payment_reference}\n\n"
            f"⚠️ Important: Include the reference in your transfer!\n\n"
            f"You will receive: {amount_usdt} USDT\n\n"
            f"Once we receive your payment, USDT will be sent to your wallet.",
        )
        return ConversationHandler.END

    except IronAPIError as e:
        logger.error(f"Error creating order: {e}")
        await query.edit_message_text("❌ Error creating order. Please try again.")
        clear_user_data(telegram_id)
        return ConversationHandler.END


# ============================================================================
# Sell USDT Flow
# ============================================================================

async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start sell USDT flow."""
    await update.message.reply_text(
        "💸 Sell USDT\n\n"
        "How much USDT do you want to sell?\n\n"
        "Example: 100",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationState.SELL_AMOUNT_INPUT


async def sell_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle USDT amount input for selling."""
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (e.g., 100):"
        )
        return ConversationState.SELL_AMOUNT_INPUT

    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user_data["sell_amount"] = amount
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Error: User not found. Please use /start")
        return ConversationHandler.END

    await update.message.reply_text("Getting quote... ⏳")

    try:
        quote = await iron_api.get_quote(
            customer_id=user.iron_customer_id,
            source_currency="USDT",
            target_currency="EUR",
            source_amount=amount,
        )

        user_data["quote_id"] = quote.get("quote_id")
        user_data["eur_amount"] = quote.get("target_amount")
        user_data["rate"] = quote.get("exchange_rate")
        user_data["fee"] = quote.get("fee_amount", 0)

        await update.message.reply_text(
            f"💱 Quote:\n\n"
            f"You send: {amount} USDT\n"
            f"You get: ~{user_data['eur_amount']} EUR\n"
            f"Rate: {user_data['rate']}\n"
            f"Fee: {user_data['fee']} EUR\n\n"
            f"Select source wallet:",
        )

        # Show wallet selection
        return await show_wallet_selection_for_sell(update, context)

    except IronAPIError as e:
        logger.error(f"Error getting quote: {e}")
        await update.message.reply_text(
            "❌ Error getting quote. Please try again.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END


async def show_wallet_selection_for_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show wallet selection for sell."""
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    try:
        wallets = await iron_api.get_crypto_wallets(user.iron_customer_id)

        if not wallets:
            await update.message.reply_text(
                "❌ You don't have any wallets.\n\n"
                "Please add a wallet first using '💼 Wallets & Banks'.",
                reply_markup=get_main_menu_keyboard(),
            )
            return ConversationHandler.END

        keyboard = []
        for wallet in wallets:
            address = wallet.get("wallet_address", "")
            network = wallet.get("blockchain", "")
            wallet_id = wallet.get("id", "")
            button_text = f"{network.upper()} - {address[:6]}...{address[-4:]}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{CallbackPrefix.WALLET_SELECT}{wallet_id}")])

        keyboard.append([InlineKeyboardButton("« Cancel", callback_data=CallbackPrefix.CANCEL)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Choose wallet to send USDT from:",
            reply_markup=reply_markup,
        )
        return ConversationState.SELL_WALLET_SELECTION

    except IronAPIError as e:
        logger.error(f"Error fetching wallets: {e}")
        await update.message.reply_text(
            "❌ Error loading wallets.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END


async def sell_wallet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet selection for sell."""
    query = update.callback_query
    await query.answer()

    wallet_id = query.data.replace(CallbackPrefix.WALLET_SELECT, "")
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user_data["source_wallet_id"] = wallet_id

    user = await get_user_by_telegram_id(telegram_id)

    try:
        banks = await iron_api.get_bank_accounts(user.iron_customer_id)

        if not banks:
            await query.edit_message_text(
                "❌ You don't have any bank accounts.\n\n"
                "Please add a bank account first using '💼 Wallets & Banks'."
            )
            return ConversationHandler.END

        keyboard = []
        for bank in banks:
            iban = bank.get("iban", "")
            bank_id = bank.get("id", "")
            label = bank.get("label", "EUR Account")
            button_text = f"{label} - {iban[:4]}...{iban[-4:]}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{CallbackPrefix.BANK_SELECT}{bank_id}")])

        keyboard.append([InlineKeyboardButton("« Cancel", callback_data=CallbackPrefix.CANCEL)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Choose bank account to receive EUR:",
            reply_markup=reply_markup,
        )
        return ConversationState.SELL_BANK_SELECTION

    except IronAPIError as e:
        logger.error(f"Error fetching banks: {e}")
        await query.edit_message_text("❌ Error loading bank accounts.")
        return ConversationHandler.END


async def sell_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank selection and create offramp order."""
    query = update.callback_query
    await query.answer()

    bank_id = query.data.replace(CallbackPrefix.BANK_SELECT, "")
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    user = await get_user_by_telegram_id(telegram_id)

    await query.edit_message_text("Creating order... ⏳")

    try:
        order = await iron_api.create_offramp_order(
            customer_id=user.iron_customer_id,
            quote_id=user_data["quote_id"],
            crypto_address_id=user_data["source_wallet_id"],
            fiat_address_id=bank_id,
        )

        order_id = order.get("order_id")
        deposit_address = order.get("deposit_address", "N/A")
        deposit_network = order.get("deposit_network", "N/A")
        amount_usdt = order.get("amount_usdt", user_data["sell_amount"])
        amount_eur = order.get("amount_eur", user_data["eur_amount"])

        clear_user_data(telegram_id)

        await query.edit_message_text(
            f"✅ Order created!\n\n"
            f"Order ID: {order_id}\n\n"
            f"📤 Deposit Instructions:\n"
            f"Amount: {amount_usdt} USDT\n"
            f"Network: {deposit_network.upper()}\n"
            f"Address: {deposit_address}\n\n"
            f"⚠️ Important: Send exactly {amount_usdt} USDT to the address above!\n\n"
            f"You will receive: {amount_eur} EUR\n\n"
            f"Once we receive your USDT, EUR will be sent to your bank account.",
        )
        return ConversationHandler.END

    except IronAPIError as e:
        logger.error(f"Error creating order: {e}")
        await query.edit_message_text("❌ Error creating order. Please try again.")
        clear_user_data(telegram_id)
        return ConversationHandler.END


# ============================================================================
# Common Handlers
# ============================================================================

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current conversation."""
    telegram_id = update.effective_user.id
    clear_user_data(telegram_id)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Operation cancelled.",
        )
    else:
        await update.message.reply_text(
            "Operation cancelled.",
            reply_markup=get_main_menu_keyboard(),
        )
    return ConversationHandler.END


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button."""
    await wallets_banks_menu(update, context)
