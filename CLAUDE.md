# CLAUDE.md - AI Assistant Guide for select-tg-bot

**Last Updated**: 2026-01-22
**Repository**: badrqst/select-tg-bot
**Project Type**: Telegram Bot

---

## Project Overview

This is a Telegram bot project designed for selection-based interactions. The bot likely handles user selections, polls, or interactive menus through Telegram's API.

### Technology Stack

Based on the project name and common Telegram bot architectures, expect:
- **Language**: Likely Node.js/TypeScript or Python
- **Bot Framework**: node-telegram-bot-api, telegraf, python-telegram-bot, or similar
- **Database**: To be determined (commonly PostgreSQL, MongoDB, or SQLite)
- **Deployment**: To be determined

---

## Repository Structure

```
select-tg-bot/
├── src/              # Source code
│   ├── bot/          # Bot logic and handlers
│   ├── commands/     # Command handlers
│   ├── services/     # Business logic services
│   ├── models/       # Data models
│   └── utils/        # Utility functions
├── config/           # Configuration files
├── tests/            # Test files
├── scripts/          # Build and deployment scripts
├── docs/             # Documentation
├── .env.example      # Environment variables template
├── package.json      # Node.js dependencies (if applicable)
├── requirements.txt  # Python dependencies (if applicable)
└── README.md         # Project documentation
```

**Note**: This structure will evolve as the project develops. Always verify actual structure before making assumptions.

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

### General Guidelines

1. **Read Before Writing**: Always read existing files before modifying them. Understand the current implementation before suggesting changes.

2. **Minimal Changes**: Only make changes that are directly requested or clearly necessary. Avoid over-engineering or adding unrequested features.

3. **Security First**: Be vigilant about:
   - Never commit sensitive data (API tokens, credentials)
   - Validate and sanitize user inputs
   - Use environment variables for configuration
   - Implement rate limiting for bot commands
   - Handle errors gracefully without exposing internal details

4. **Testing**: Write tests for new features and bug fixes. Run existing tests before committing.

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

### Basic Bot Structure

**Node.js/TypeScript Example**:
```javascript
// bot/index.ts
import { Telegraf } from 'telegraf';

const bot = new Telegraf(process.env.BOT_TOKEN);

// Middleware
bot.use(async (ctx, next) => {
  // Logging, auth, etc.
  await next();
});

// Command handlers
bot.command('start', (ctx) => ctx.reply('Welcome!'));

// Callback query handlers
bot.on('callback_query', handleCallbackQuery);

bot.launch();
```

**Python Example**:
```python
# bot/main.py
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

async def start(update, context):
    await update.message.reply_text('Welcome!')

def main():
    app = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()
```

### Selection/Poll Patterns

```javascript
// Example: Creating an inline keyboard for selections
const keyboard = {
  inline_keyboard: [
    [{ text: 'Option 1', callback_data: 'opt_1' }],
    [{ text: 'Option 2', callback_data: 'opt_2' }],
    [{ text: 'Option 3', callback_data: 'opt_3' }]
  ]
};

await ctx.reply('Please select an option:', {
  reply_markup: keyboard
});
```

### Callback Query Handling

```javascript
bot.on('callback_query', async (ctx) => {
  const data = ctx.callbackQuery.data;

  // Handle selection
  await handleSelection(ctx, data);

  // Answer callback query to remove loading state
  await ctx.answerCbQuery();
});
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
