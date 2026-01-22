# Iron API Troubleshooting Guide

## Current Issue: 404 Not Found on Customer Onboarding

### Error Details
```
HTTP Request: POST https://api.sandbox.iron.xyz/api/customer/onboard
Response: HTTP/1.1 404 Not Found
```

This means the endpoint doesn't exist or the URL is incorrect.

---

## Step 1: Verify Your Iron API Access

1. Log into Iron Dashboard: https://app.sandbox.iron.xyz/
2. Check your API documentation section
3. Look for "API Reference" or "Endpoints"
4. Find the exact base URL and customer creation endpoint

---

## Step 2: Common Base URL Variants

Try these base URLs in Railway environment variables:

### Option 1 (Current):
```
IRON_API_BASE_URL=https://api.sandbox.iron.xyz/api
```

### Option 2 (Without /api):
```
IRON_API_BASE_URL=https://api.sandbox.iron.xyz
```

### Option 3 (Different subdomain):
```
IRON_API_BASE_URL=https://sandbox.iron.xyz/api
```

### Option 4 (With version):
```
IRON_API_BASE_URL=https://api.sandbox.iron.xyz/v1
```

---

## Step 3: Find Correct Endpoints

You need to find the actual endpoint paths from Iron documentation.

### Expected Endpoints (to verify):

| Operation | Expected Path | Method |
|-----------|--------------|---------|
| Customer Onboard | `/customer/onboard` OR `/customers` | POST |
| Register Wallet | `/addresses/crypto/self-hosted` | POST |
| Create Hosted Wallet | `/addresses/crypto/hosted` | POST |
| Register Bank | `/addresses/fiat` | POST |
| Get Quote | `/quotes` | POST |
| Create Onramp | `/onramp/create` | POST |
| Create Offramp | `/offramp/create` | POST |
| Get Wallets | `/addresses/crypto` | GET |
| Get Banks | `/addresses/fiat` | GET |
| Get Transactions | `/transactions` | GET |

---

## Step 4: Test with curl

Test your API key and endpoints directly:

```bash
# Test 1: Try different base URLs with health/status endpoint (if available)
curl -H "X-API-Key: YOUR_API_KEY" \
  https://api.sandbox.iron.xyz/api/health

# Test 2: Try customer creation with different endpoints
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User"
  }' \
  https://api.sandbox.iron.xyz/api/customers

# Test 3: Try without /api
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User"
  }' \
  https://api.sandbox.iron.xyz/customers
```

---

## Step 5: Contact Iron Support

If you can't find the correct endpoints:

1. Email: **support@iron.xyz**
2. Ask for:
   - Sandbox API base URL
   - Complete list of endpoints
   - API documentation access
   - Example curl commands

---

## Step 6: Update Bot Configuration

Once you find the correct base URL and endpoints:

### Update Railway Environment Variable:
```
IRON_API_BASE_URL=<correct_base_url>
```

### If Endpoints Are Different:

You'll need to update `app/services/iron_api.py`:

```python
# Example: if customer endpoint is /customers instead of /customer/onboard
async def onboard_customer(...):
    result = await self._request("POST", "/customers", data=data)
    # Change from "/customer/onboard" to "/customers"
```

---

## Step 7: Check for API Version Changes

Iron.xyz was acquired by MoonPay in 2025. It's possible:
- API structure changed
- Endpoints were renamed
- Version prefix added (e.g., `/v1/`)

Check if there's a migration guide or updated documentation.

---

## Quick Debug

Add this to see full request/response in Railway logs:

In Railway, set environment variable:
```
LOG_LEVEL=DEBUG
```

This will show full HTTP requests/responses including URLs.

---

## Alternative: Use Iron Dashboard Manually

While troubleshooting API:
1. You can create customers manually in Iron dashboard
2. Then test wallet/bank/order endpoints
3. Once those work, go back to customer creation

---

## Need Help?

Share with me:
1. Screenshot of Iron dashboard showing API docs
2. Example curl command from Iron documentation
3. Response from any successful API call

I'll update the bot code accordingly!
