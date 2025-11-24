import httpx
import asyncio


async def basic_api_key_auth():
    """Simple API key in headers - e-commerce style"""
    async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=100, max_keepalive_connections=30)) as client:
        response = await client.get(
            "https://httpbin.org/headers",  # Using httpbin for testing
            headers={

                # API Key for e-commerce style authentication
                "X-API-KEY": 'fake_ecommerce_key_12345',

                # User-Agent for e-commerce style authentication
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                
                # Accept files type for e-commerce style authentication
                "Accept": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ API Key Auth Successful!")
            print("Response Headers:", data)
            print("Response Body:", response.text)
            return data
        else:
            print("❌ API Key Auth Failed with status code:", response.status_code)
            return None

if __name__ == "__main__":
    """Simple API key in headers - e-commerce style"""
    asyncio.run(basic_api_key_auth())


