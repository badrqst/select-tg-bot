# Select Bot - USDT/EUR Exchange via Iron API

Telegram bot for easy USDT/EUR exchange using Iron API infrastructure. Buy and sell USDT directly through Telegram with simple commands.

## Features

- **Buy USDT**: Purchase USDT with EUR via SEPA transfer
- **Sell USDT**: Convert USDT to EUR and receive funds in your bank account
- **Wallet Management**: Add and manage crypto wallets (self-hosted or Iron-hosted)
- **Bank Accounts**: Link your bank accounts for fiat transactions
- **Real-time Quotes**: Get instant exchange rates
- **KYC Integration**: Automated customer onboarding through Iron API
- **Transaction History**: Track your exchange history

## Architecture

The bot follows a minimal database approach:
- **Local storage**: Only `telegram_id ↔ iron_customer_id` mapping
- **Iron API**: All wallets, banks, transactions, and KYC data

This ensures data consistency and reduces local storage requirements.

## Tech Stack

- **Python 3.11**
- **python-telegram-bot 20.7** - Telegram Bot API
- **httpx** - Async HTTP client for Iron API
- **SQLAlchemy** - Async database ORM
- **Pydantic Settings** - Configuration management
- **Docker** - Containerization

## Project Structure

```
select-tg-bot/
├── app/
│   ├── main.py              # Bot entry point
│   ├── config.py            # Pydantic settings
│   ├── constants.py         # Enums and constants
│   ├── models/
│   │   ├── database.py      # SQLAlchemy base
│   │   └── user.py          # User model (single table)
│   ├── services/
│   │   └── iron_api.py      # Iron API client
│   └── bot/
│       ├── handlers.py      # Command handlers
│       └── states.py        # Conversation states
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Iron API Key (from [Iron Dashboard](https://dashboard.iron.xyz))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/badrqst/select-tg-bot.git
   cd select-tg-bot
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   IRON_API_KEY=your_iron_api_key
   IRON_API_BASE_URL=https://api.sandbox.iron.xyz/api
   DATABASE_URL=sqlite+aiosqlite:///./data/select.db
   ```

3. **Run with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Check logs**
   ```bash
   docker-compose logs -f bot
   ```

### Local Development

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the bot**
   ```bash
   python -m app.main
   ```

## Usage

### User Flow

1. **Start the bot**
   ```
   /start
   ```
   New users will go through KYC onboarding (email, name).

2. **Add wallet**
   - Navigate to "💼 Wallets & Banks"
   - Choose "Add Crypto Wallet"
   - Select wallet type (self-hosted or Iron-hosted)
   - Select network (Ethereum, Polygon, Tron)
   - Provide address (for self-hosted) or get auto-generated (for hosted)

3. **Add bank account**
   - Navigate to "💼 Wallets & Banks"
   - Choose "Add Bank Account"
   - Enter your IBAN

4. **Buy USDT**
   - Select "💰 Buy USDT"
   - Enter EUR amount
   - Review quote
   - Select destination wallet
   - Select source bank account
   - Receive SEPA payment instructions
   - Transfer EUR to provided IBAN with reference
   - Receive USDT automatically

5. **Sell USDT**
   - Select "💸 Sell USDT"
   - Enter USDT amount
   - Review quote
   - Select source wallet
   - Select destination bank account
   - Receive deposit address
   - Send USDT to provided address
   - Receive EUR in bank account

## Bot Commands

- `/start` - Start bot and create account
- `/profile` - View profile and KYC status
- `/cancel` - Cancel current operation

## Menu Options

- **💰 Buy USDT** - Purchase USDT with EUR
- **💸 Sell USDT** - Sell USDT for EUR
- **👤 Profile** - View account information
- **💼 Wallets & Banks** - Manage wallets and bank accounts

## Iron API Integration

The bot integrates with Iron API for all financial operations:

### Endpoints Used

- `POST /customer/onboard` - Customer KYC onboarding
- `POST /addresses/crypto/self-hosted` - Register external wallet
- `POST /addresses/crypto/hosted` - Create Iron-managed wallet
- `POST /addresses/fiat` - Register bank account
- `GET /addresses/crypto` - List crypto wallets
- `GET /addresses/fiat` - List bank accounts
- `POST /quotes` - Get exchange quote
- `POST /onramp/create` - Create buy order (EUR → USDT)
- `POST /offramp/create` - Create sell order (USDT → EUR)
- `GET /transactions` - Get transaction history
- `GET /customer/{id}` - Get customer KYC status

### API Documentation

Full Iron API documentation: https://docs.iron.xyz/reference-sandbox

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    iron_customer_id VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

All other data (wallets, banks, transactions) is retrieved from Iron API.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather | Required |
| `IRON_API_KEY` | Iron API key | Required |
| `IRON_API_BASE_URL` | Iron API base URL | `https://api.sandbox.iron.xyz/api` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./select.db` |

### Supported Networks

- **Ethereum** - ERC-20 USDT
- **Polygon** - Polygon USDT
- **Tron** - TRC-20 USDT

## Security

- Never commit `.env` file
- Rotate API keys regularly
- Use environment-specific API keys (sandbox for dev, production for prod)
- Implement rate limiting for production
- Enable KYC verification for compliance
- Validate all user inputs
- Log security events

## Deployment

### Production Checklist

- [ ] Use production Iron API credentials
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure proper logging
- [ ] Set up monitoring and alerts
- [ ] Enable HTTPS for webhooks (if using)
- [ ] Implement rate limiting
- [ ] Set up backup strategy
- [ ] Configure error tracking (Sentry, etc.)
- [ ] Test KYC flow
- [ ] Test buy/sell flows with small amounts

### PostgreSQL Setup

Uncomment PostgreSQL service in `docker-compose.yml` and update `DATABASE_URL`:

```env
DATABASE_URL=postgresql+asyncpg://selectbot:selectbot@db:5432/selectbot
```

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check bot token is correct
   - Verify bot is running: `docker-compose ps`
   - Check logs: `docker-compose logs bot`

2. **Iron API errors**
   - Verify API key is correct
   - Check API endpoint URL
   - Review Iron API logs in dashboard
   - Ensure sandbox vs production environment match

3. **Database errors**
   - Check database file permissions
   - Verify DATABASE_URL is correct
   - Delete database file and restart to reset

4. **Transaction not completing**
   - Check Iron dashboard for transaction status
   - Verify payment reference is included (for buy)
   - Verify correct amount sent (for sell)
   - Check KYC status

## Development

### Adding New Features

1. Update `constants.py` if new enums needed
2. Add API methods to `iron_api.py`
3. Create handlers in `handlers.py`
4. Add conversation states to `states.py`
5. Register handlers in `main.py`
6. Test thoroughly

### Code Style

- Use type hints
- Follow PEP 8
- Use async/await consistently
- Add docstrings to functions
- Log important events

## Testing

### Manual Testing

1. Start bot in sandbox mode
2. Complete KYC flow
3. Add test wallet and bank account
4. Test buy flow with small amount
5. Test sell flow with small amount
6. Verify transactions in Iron dashboard

### Iron Sandbox

Use Iron's sandbox environment for testing:
- Sandbox URL: `https://api.sandbox.iron.xyz/api`
- Test without real money
- Simulate KYC approvals
- Test all flows safely

## Monitoring

### Logs

View logs in real-time:
```bash
docker-compose logs -f bot
```

### Metrics to Track

- User registrations
- KYC completion rate
- Successful transactions
- Failed transactions
- API errors
- Response times

## Support

For issues and questions:
- Check Iron API documentation: https://docs.iron.xyz
- Review bot logs
- Contact Iron support for API issues
- Open GitHub issue for bot issues

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Iron API](https://iron.xyz)

---

**Note**: This is a demo bot. For production use, implement proper security measures, error handling, and compliance checks.
