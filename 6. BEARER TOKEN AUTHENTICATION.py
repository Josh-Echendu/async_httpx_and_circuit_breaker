import httpx
import asyncio
import time




current_token = None
token_expiry = 0


async def get_bearer_token(client):
    """Get a fresh bearer token"""
    global current_token, token_expiry

    # Return existing token if still valid
    if current_token and time.time() < token_expiry: # if current time is less than expiry token time
        return current_token

    # Simulate token endpoint - in real world, this would be real auth
    print("🔄 Getting new bearer token...")

    data = {
        "username": "demo_user",
        "password": "demo_pass",
        "grant_type": "password"
    }

    response = await client.post("https://httpbin.org/post", json=data)

    if response.status_code == 200:
        print("response:", response.json())
        # Simulate extracting token from response
        current_token = "fake_jwt_token_abc123xyz"
        token_expiry = time.time() + 3500 # Token valid for 1 hour
        return current_token
    else:
        raise Exception("Failed to obtain token, status code: {}".format(response.status_code))

async def bearer_token_auth():
    """Bearer Token Authentication with token refresh"""

    async with httpx.AsyncClient(
        http2=True,
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1)
    ) as client:
        try:
            token = await get_bearer_token(client)
        except Exception as e:
            print("❌ Failed to obtain bearer token:", str(e))
            return None

        # --------------- Bearer Token is always in headers ----------------
        response = await client.get(
            "https://httpbin.org/bearer",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Bearer Token Auth Successful!")
            print("Response Headers:", data)
            print("Response Body:", response.text)
            return data
        else:
            print("❌ Bearer Token Auth Failed with status code:", response.status_code)
            return None


asyncio.run(bearer_token_auth())