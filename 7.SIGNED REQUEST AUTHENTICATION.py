import httpx
import asyncio
import hashlib
import hmac
import time

async def signed_request_auth():
    """HMAC signed request - crypto exchange style"""
    
    api_key = "fake_api_key_789"
    secret_key = "fake_secret_key_xyz123"
    timestamp = str(int(time.time() * 1000))  # milliseconds
    
    # Create message to sign (method + endpoint + timestamp)
    message = f"GET\n/api/data\ntimestamp={timestamp}"
    
    # Generate HMAC signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.get(
            "https://httpbin.org/headers",
            headers={
                "X-API-Key": api_key,
                "X-Signature": signature,
                "X-Timestamp": timestamp,
                "User-Agent": "TradingBot/1.0",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Signed Request Auth Successful!")
            print(f"Signature: {signature}")
            print(f"Timestamp: {timestamp}")
            return data
        else:
            print(f"❌ Signed auth failed: {response.status_code}")
            return None

# Run it
asyncio.run(signed_request_auth())