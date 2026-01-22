# Railway Deployment Guide

## Quick Setup

### 1. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

Or manually:
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `badrqst/select-tg-bot` repository
4. Railway will auto-detect Dockerfile and deploy

### 2. Configure Environment Variables

In Railway dashboard, add these variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
IRON_API_KEY=your_iron_api_key_here
IRON_API_BASE_URL=https://api.sandbox.iron.xyz/api
DATABASE_URL=sqlite+aiosqlite:///./data/select.db
```

### 3. Add Volume for Database (IMPORTANT!)

Railway requires volumes to be configured separately:

1. In your Railway project, go to your service
2. Click **"Variables"** tab
3. Scroll down to **"Volumes"**
4. Click **"+ New Volume"**
5. Configure:
   - **Mount Path**: `/app/data`
   - This will persist your SQLite database

**Without volume, database will be lost on each deployment!**

### 4. Deploy

Railway will automatically deploy after you:
- Push to GitHub
- Change environment variables
- Or click "Deploy" manually

### 5. Check Logs

In Railway dashboard:
- Click on your service
- Go to "Deployments" tab
- Click on latest deployment
- View logs to verify bot started

Look for: `Starting bot...` and `Database initialized`

---

## Alternative: Use PostgreSQL on Railway

For production, PostgreSQL is recommended:

### 1. Add PostgreSQL Service

1. In Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create PostgreSQL instance

### 2. Update Environment Variable

Railway automatically creates `DATABASE_URL` for PostgreSQL.

You need to modify it for async SQLAlchemy:

1. Get the `DATABASE_URL` from PostgreSQL service
2. In your bot service, add new variable:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   ```

   Replace `postgresql://` with `postgresql+asyncpg://` from Railway's DATABASE_URL

### 3. Update Dependencies

Railway will need `asyncpg` driver. Already included in requirements.txt:
```
sqlalchemy[asyncio]==2.0.25
```

This includes asyncpg for PostgreSQL.

---

## Troubleshooting

### Bot not starting?

Check logs for errors:
- Invalid bot token
- Missing environment variables
- Iron API connection issues

### Database errors?

- Ensure volume is mounted at `/app/data`
- Or use PostgreSQL instead of SQLite

### Iron API errors?

- Verify `IRON_API_KEY` is correct
- Check `IRON_API_BASE_URL` (sandbox vs production)
- Review Iron API dashboard for API errors

---

## Cost Estimate

**Hobby Plan (Free tier):**
- $5 credit/month included
- Should be enough for small bot (100-1000 users)

**Paid Plan:**
- ~$5-10/month for bot service
- ~$5/month if using PostgreSQL
- Total: ~$10-15/month

---

## Production Checklist

- [ ] Use production Iron API credentials (not sandbox)
- [ ] Set up PostgreSQL instead of SQLite
- [ ] Configure proper logging
- [ ] Set up monitoring/alerts
- [ ] Test all flows (KYC, buy, sell)
- [ ] Verify volume persistence

---

## Migration to VPS later

If you need to migrate to VPS:

1. Export database:
   ```bash
   # For SQLite: Download from Railway volume
   # For PostgreSQL: pg_dump
   ```

2. Deploy to VPS using docker-compose.yml

3. Import database

4. Update bot (no code changes needed)

---

## Support

Railway docs: https://docs.railway.com
Railway Discord: https://discord.gg/railway
