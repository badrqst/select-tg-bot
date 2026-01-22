# CLAUDE.md - AI Assistant Guide for select-tg-bot

**Last Updated**: 2026-01-22
**Repository**: badrqst/select-tg-bot
**Project Type**: Telegram Bot

---

## Project Overview

This is a Telegram bot for USDT/EUR exchange through Iron API. The bot enables users to buy and sell USDT directly via Telegram, with fiat payments handled through SEPA bank transfers.

### Core Principle

**Minimal Local Storage**: Store ONLY `telegram_id ↔ iron_customer_id` mapping locally. Everything else (wallets, banks, transactions, KYC status) is queried from Iron API in real-time.

### Technology Stack

- **Language**: Python 3.11
- **Bot Framework**: python-telegram-bot 20.7
- **HTTP Client**: httpx (for Iron API)
- **Database**: SQLAlchemy with async support (SQLite/PostgreSQL)
- **Configuration**: pydantic-settings
- **Deployment**: Docker & Docker Compose

---

## Repository Structure

```
select-tg-bot/
├── app/
│   ├── main.py              # Bot entry point, polling, handlers registration
│   ├── config.py            # Pydantic Settings from .env
│   ├── constants.py         # Enums: KYCStatus, TransactionStatus, WalletType, etc.
│   ├── models/
│   │   ├── database.py      # SQLAlchemy async Base
│   │   └── user.py          # User(telegram_id, iron_customer_id) - SINGLE table
│   ├── services/
│   │   └── iron_api.py      # httpx client for Iron API operations
│   └── bot/
│       ├── handlers.py      # All command handlers and conversation flows
│       └── states.py        # ConversationState enum and user data management
├── data/                    # Database storage (gitignored)
├── Dockerfile               # Python 3.11 container
├── docker-compose.yml       # Docker orchestration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
├── README.md                # User documentation
└── CLAUDE.md                # This file - AI assistant guide
```

---

## Iron API Integration

This bot is tightly integrated with Iron API (https://docs.iron.xyz/reference-sandbox).

### Key Endpoints

**Base URL**: `https://api.sandbox.iron.xyz/api` (sandbox) or `https://api.iron.xyz/api` (production)

#### Customer Management
- `POST /customer/onboard` - Onboard new customer with KYC
  - Body: `{email, first_name, last_name, metadata?}`
  - Returns: `{id, email, kyc_status, kyc_url, created_at}`
- `GET /customer/{customerId}` - Get customer details and KYC status

#### Wallet Management
- `POST /addresses/crypto/self-hosted` - Register user's self-hosted wallet
  - Body: `{customer_id, blockchain, wallet_address, proof_message?, proof_signature?}`
  - Blockchain: "Ethereum", "Polygon", "Solana", "Arbitrum", "Base", "Stellar"
- `POST /addresses/crypto/hosted` - Register hosted wallet (exchange wallet)
  - Body: `{customer_id, blockchain, wallet_address, vasp_did}`
  - Requires VASP DID from `/addresses/search-vasps`
- `GET /addresses/crypto?customer_id=` - List all crypto wallets
  - Returns: `{addresses: [{id, address_type, blockchain, wallet_address, disabled}]}`
- `GET /addresses/search-vasps?query=` - Search for exchange VASP DIDs

#### Bank Account Management
- `POST /addresses/fiat` - Register bank account (IBAN)
  - Body: `{customer_id, account_holder_name, iban, country_code, bic?}`
  - Returns: `{id, iban, account_holder_name, status, created_at}`
- `GET /addresses/fiat?customer_id=` - List all bank accounts
- `DELETE /addresses/fiat/{addressId}` - Delete bank account

#### Trading Operations
- `POST /quotes` - Get exchange rate quote
  - Body: `{customer_id, source_currency, target_currency, source_amount? OR target_amount?}`
  - Returns: `{quote_id, source_amount, target_amount, exchange_rate, fee_amount, expires_at}`
- `POST /onramp/create` - Create buy order (EUR → USDT)
  - Body: `{customer_id, quote_id, crypto_address_id, fiat_address_id}`
  - Returns: `{order_id, transaction_id, payment_reference, payment_iban, amount_eur, amount_usdt}`
- `POST /offramp/create` - Create sell order (USDT → EUR)
  - Body: `{customer_id, quote_id, crypto_address_id, fiat_address_id}`
  - Returns: `{order_id, transaction_id, deposit_address, deposit_network, amount_usdt, amount_eur}`

#### Transaction History
- `GET /transactions/{transactionId}` - Get specific transaction
- `GET /transactions?customer_id=&limit=&offset=` - Get customer transactions
  - Returns: `{transactions: [{transaction_id, order_id, type, status, source_amount, target_amount}]}`

### Important API Notes

- **Authentication**: API key is passed in `X-API-Key` header (NOT Authorization Bearer)
- **Idempotency**: All POST/PUT/PATCH requests require `IDEMPOTENCY-KEY` header (UUID)
- **Field naming**: All request and response fields use snake_case (first_name, wallet_address, etc.)
- **Blockchain names**: Must use capital first letter ("Ethereum", "Polygon", not "ethereum")
- **Error handling**: Always handle `IronAPIError` exceptions
- **Data freshness**: Never cache wallet/bank/transaction data - always fetch fresh from API
- **Environments**: Sandbox for testing, production for real transactions

---

## Development Workflows

### Branch Strategy

- **Feature branches**: `feature/<feature-name>`
- **Bug fixes**: `bugfix/<bug-description>`
- **Claude branches**: `claude/claude-md-<session-id>` (for AI assistant work)
- **Main branch**: Default branch for production-ready code

### Git Workflow

1. **Create feature branch** from main/default branch
2. **Develop and test** changes locally
3. **Commit** with clear, descriptive messages
4. **Push** to remote branch
5. **Create Pull Request** for review

### Commit Message Conventions

Follow conventional commits format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Build process or auxiliary tool changes
- `style`: Code style changes (formatting, missing semicolons, etc.)

**Examples**:
```
feat(bot): add poll creation command
fix(handlers): resolve callback query timeout issue
docs(readme): update installation instructions
refactor(services): extract selection logic to separate service
```

---

## Key Conventions for AI Assistants

### Project-Specific Rules

1. **Minimal Database Storage**:
   - ONLY store `telegram_id ↔ iron_customer_id` in local database
   - NEVER cache wallets, banks, or transactions locally
   - Always fetch fresh data from Iron API
   - This ensures data consistency and reduces storage

2. **Iron API Integration**:
   - All financial operations MUST go through Iron API
   - Handle `IronAPIError` exceptions in all handlers
   - Log API errors but don't expose details to users
   - Use async/await for all API calls (httpx AsyncClient)

3. **Conversation Flow Management**:
   - Use `ConversationHandler` for multi-step flows
   - Store temporary data in `conversation_data` dict (app/bot/states.py)
   - Always clear user data with `clear_user_data()` after flow completion
   - Handle cancellation gracefully

4. **Security for Financial Bot**:
   - Validate all numeric inputs (amounts, IBANs)
   - Never log sensitive data (API keys, IBANs, wallet addresses)
   - Use environment variables for ALL credentials
   - Implement proper error messages without exposing internals

### General Guidelines

1. **Read Before Writing**: Always read existing files before modifying them. Understand the current implementation before suggesting changes.

2. **Minimal Changes**: Only make changes that are directly requested or clearly necessary. Avoid over-engineering or adding unrequested features.

3. **Security First**: Be vigilant about:
   - Never commit sensitive data (API tokens, credentials)
   - Validate and sanitize user inputs
   - Use environment variables for configuration
   - Implement rate limiting for bot commands
   - Handle errors gracefully without exposing internal details

4. **Testing**: Test all flows manually with Iron sandbox before production.

5. **Documentation**: Update relevant documentation when making changes, but don't create documentation files unless explicitly requested.

### Telegram Bot Specific Conventions

1. **Command Handlers**: Keep command handlers focused and delegate business logic to services
2. **Error Handling**: Always wrap bot interactions in try-catch blocks
3. **User Privacy**: Follow Telegram's privacy guidelines and GDPR compliance
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Logging**: Log important events but avoid logging sensitive user data

### Code Style

- **Consistent Formatting**: Follow existing code style in the repository
- **Naming Conventions**:
  - Use descriptive variable and function names
  - Follow language-specific conventions (camelCase for JS/TS, snake_case for Python)
- **Comments**: Write comments for complex logic, not obvious code
- **Type Safety**: Use TypeScript or type hints where applicable

### Environment Variables

Always use environment variables for:
- Bot tokens and API keys
- Database connection strings
- Service URLs
- Feature flags
- Environment-specific configuration

Create `.env.example` with placeholder values, never commit actual `.env` files.

---

## Common Telegram Bot Patterns

### Bot Structure (This Project)

This project uses python-telegram-bot 20.7 with async/await:

```python
# app/main.py - Entry point
from telegram.ext import Application, ConversationHandler

def main():
    # Initialize database
    asyncio.run(init_db())

    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()

    # Add conversation handlers
    application.add_handler(kyc_conversation)
    application.add_handler(buy_conversation)

    # Run polling
    application.run_polling(allowed_updates=["message", "callback_query"])
```

### Conversation Handler Pattern

All multi-step flows use ConversationHandler:

```python
conversation = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^💰 Buy USDT$"), buy_start),
    ],
    states={
        ConversationState.BUY_AMOUNT_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, buy_amount_input),
        ],
        ConversationState.BUY_WALLET_SELECTION: [
            CallbackQueryHandler(buy_wallet_selected, pattern=f"^{CallbackPrefix.WALLET_SELECT}"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_conversation),
    ],
)
```

### Main Menu Pattern

This bot uses ReplyKeyboardMarkup for main menu:

```python
def get_main_menu_keyboard():
    keyboard = [
        ["💰 Buy USDT", "💸 Sell USDT"],
        ["👤 Profile", "💼 Wallets & Banks"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
```

### Inline Keyboard for Selections

Used for wallet/bank selection, confirmations:

```python
keyboard = []
for wallet in wallets:
    address = wallet.get("address", "")
    wallet_id = wallet.get("id", "")
    button_text = f"{network.upper()} - {address[:6]}...{address[-4:]}"
    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"ws_{wallet_id}")])

reply_markup = InlineKeyboardMarkup(keyboard)
await update.message.reply_text("Choose wallet:", reply_markup=reply_markup)
```

### Callback Query Handling

Always answer callback queries to remove loading state:

```python
async def wallet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Important: answer first!

    wallet_id = query.data.replace("ws_", "")
    # Process selection...

    await query.edit_message_text("Wallet selected!")
```

### Iron API Call Pattern

All Iron API calls follow this pattern:

```python
async def some_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Please use /start first")
        return

    try:
        # Call Iron API
        result = await iron_api.some_method(
            customer_id=user.iron_customer_id,
            param=value,
        )

        # Process result
        await update.message.reply_text("Success!")

    except IronAPIError as e:
        logger.error(f"Iron API error: {e}")
        await update.message.reply_text("Error occurred. Please try again.")
```

---

## Testing Guidelines

### Unit Tests

- Test individual functions and methods in isolation
- Mock external dependencies (Telegram API, database, etc.)
- Aim for high code coverage on business logic

### Integration Tests

- Test command flows end-to-end
- Test callback query handling
- Test database interactions

### Test Structure

```
tests/
├── unit/
│   ├── services/
│   └── utils/
└── integration/
    ├── commands/
    └── handlers/
```

### Running Tests

```bash
# Node.js
npm test
npm run test:coverage

# Python
pytest
pytest --cov=src
```

---

## Deployment Guidelines

### Pre-deployment Checklist

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Error logging configured
- [ ] Rate limiting enabled
- [ ] Bot commands registered with BotFather
- [ ] Webhook configured (if using webhooks instead of polling)

### Environment Setup

1. **Development**: Use polling, verbose logging, test database
2. **Staging**: Mirror production setup, use test bot token
3. **Production**: Use webhooks, minimal logging, production database

---

## Common Tasks for AI Assistants

### Adding a New Command

1. Create command handler in `src/commands/` or appropriate location
2. Register command with bot instance
3. Add tests for the command
4. Update bot commands in BotFather if needed
5. Document the command

### Adding Selection Options

1. Define option data structure
2. Create inline keyboard markup
3. Implement callback query handler
4. Add validation and error handling
5. Test the selection flow

### Database Changes

1. Create migration file (if using migrations)
2. Update model definitions
3. Update related services
4. Test migrations in development
5. Document schema changes

### Bug Fixes

1. Identify root cause through logs and reproduction
2. Write test that reproduces the bug
3. Fix the bug
4. Verify test passes
5. Check for similar issues in codebase

---

## Debugging Tips

### Telegram Bot API

- Use Telegram's official API documentation: https://core.telegram.org/bots/api
- Test with BotFather commands for bot configuration
- Use Telegram's test environment for development

### Common Issues

1. **Callback Query Timeout**: Always call `answerCbQuery()` within 30 seconds
2. **Message Edit Errors**: Can only edit messages within 48 hours
3. **Rate Limiting**: Respect Telegram's rate limits (30 messages/second)
4. **Inline Keyboard Size**: Maximum 8 bytes per callback_data

### Logging

- Log all incoming updates in development
- Log errors with stack traces
- Log user actions for analytics (without PII)
- Use structured logging (JSON format)

---

## Dependencies Management

### Node.js

```bash
# Install dependencies
npm install

# Add new dependency
npm install <package-name>

# Add dev dependency
npm install --save-dev <package-name>

# Update dependencies
npm update

# Audit for vulnerabilities
npm audit
```

### Python

```bash
# Install dependencies
pip install -r requirements.txt

# Add new dependency
pip install <package-name>
pip freeze > requirements.txt

# Update dependencies
pip install --upgrade -r requirements.txt
```

---

## Security Best Practices

### API Token Protection

- Never hardcode bot tokens
- Use environment variables
- Rotate tokens if compromised
- Use different tokens for dev/staging/prod

### User Input Validation

- Sanitize all user inputs
- Validate callback_data format
- Implement input length limits
- Check for injection attacks

### Data Protection

- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement user data deletion on request
- Follow GDPR/privacy regulations

### Access Control

- Implement admin-only commands
- Use user ID whitelists where appropriate
- Rate limit all bot interactions
- Log suspicious activities

---

## Performance Optimization

### Bot Responsiveness

- Acknowledge callback queries immediately
- Use async/await for non-blocking operations
- Implement command queues for heavy operations
- Cache frequently accessed data

### Database Optimization

- Use indexes for frequently queried fields
- Implement connection pooling
- Optimize queries with EXPLAIN
- Use database transactions appropriately

### Resource Management

- Implement graceful shutdown
- Clean up event listeners
- Close database connections properly
- Monitor memory usage

---

## Monitoring and Maintenance

### Metrics to Track

- Message processing time
- Error rates
- Active users count
- Command usage statistics
- Database query performance

### Health Checks

- Bot connectivity to Telegram API
- Database connection status
- External service availability
- Disk space and memory usage

### Logging Strategy

**Development**: Verbose logging, all events
**Production**: Error and warning logs, critical events

---

## Resources

### Official Documentation

- Telegram Bot API: https://core.telegram.org/bots/api
- BotFather Commands: https://core.telegram.org/bots#botfather

### Popular Libraries

**Node.js**:
- Telegraf: https://telegraf.js.org/
- node-telegram-bot-api: https://github.com/yagop/node-telegram-bot-api

**Python**:
- python-telegram-bot: https://python-telegram-bot.org/
- aiogram: https://docs.aiogram.dev/

### Tools

- ngrok: For testing webhooks locally
- Postman: For testing API endpoints
- Redis: For caching and rate limiting

---

## AI Assistant Specific Notes

### When Working on This Repository

1. **Always check current structure**: This repository may have evolved since this document was created
2. **Read package.json/requirements.txt**: To understand the actual tech stack in use
3. **Look for existing patterns**: Follow the established code style and architecture
4. **Ask for clarification**: When requirements are ambiguous or multiple approaches are valid
5. **Test thoroughly**: Always run tests before committing
6. **Commit incrementally**: Make small, focused commits rather than large omnibus commits

### Before Making Changes

- [ ] Read the files you're about to modify
- [ ] Understand the current implementation
- [ ] Identify the minimal change needed
- [ ] Consider security implications
- [ ] Plan for error handling
- [ ] Think about edge cases

### After Making Changes

- [ ] Run tests and verify they pass
- [ ] Check for unintended side effects
- [ ] Update relevant documentation
- [ ] Review your changes (self-code-review)
- [ ] Commit with descriptive message
- [ ] Push to appropriate branch

---

## Project Evolution

As this project grows, update this document with:
- Actual technology stack and dependencies
- Real directory structure
- Established patterns and conventions
- Deployment procedures
- Team-specific guidelines
- Lessons learned

**Note**: This document is a living guide. Keep it updated as the project evolves!

---

## Contact and Support

For questions or clarifications about this project:
- Check existing documentation
- Review closed issues and PRs
- Consult the project owner: badrqst

---

**Remember**: This guide is here to help you understand the project quickly and work effectively. When in doubt, prioritize code clarity, security, and user experience.
