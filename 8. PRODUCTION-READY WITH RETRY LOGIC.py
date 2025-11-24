import httpx
import asyncio
import time


async def make_authenticated_request_with_retry(endpoint: str, api_key: str, max_retries: int = 3, method: str = "GET", data=None):
    """Production-ready function with retry logic"""

    base_url = "https://httpbin.org"
    retry_count = 0

    while retry_count <= max_retries:
        try:
            async with httpx.AsyncClient(http2=True, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5), timeout=httpx.Timeout(10.0)) as client:
                headers = {
                    "X-API-Key": api_key,
                    "User-Agent": "RobustClient/1.0",
                    "Accept": "application/json",
                    "X-Request": f"req_{int(time.time())}_{retry_count}"
                }
                url = f"{base_url}/{endpoint}"

                if method == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(url, headers=headers, json=data)

                if response.status_code == 200:
                    print(f"✅ Request successful on attempt {retry_count + 1}")
                    return response.json()  

                elif response.status_code in {429, 503}:
                    print("⚠️ Rate limited, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    retry_count = retry_count + 1
                
                elif response.status_code in {401}:
                    print("❌ Authentication failed - check API key")
                    return None

                else:
                    print(f"❌ HTTP error {response.status_code}")
                    retry_count = retry_count + 1
                    await asyncio.sleep(2 ** retry_count) # # Exponential backoff

        except httpx.RequestError as e:
            print(f"🔥 Network error: {type(e).__name__} - {e}")
            retry_count += 1
            if retry_count <= max_retries:
                wait_time = 2 ** retry_count
                print(f"🔄 Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

async def production_ready_demo():
    """Demo the production-ready function"""

    # Test with different endpoints
    api_key = "prod_api_key_456"

    print("🚀 Testing production-ready authentication...")

    result = await make_authenticated_request_with_retry("headers", api_key)
    if result:
        print("✅ Production-ready request succeeded:", result)

    result2 = await make_authenticated_request_with_retry(
        "post",
        api_key,
        method="POST",
        data={"order": "test_order_123"}
    )
    if result2:
        print("✅ Production-ready POST request succeeded:", result2)

    result3 = await make_authenticated_request_with_retry("status/429", api_key)

    if not result3:
        print("✅ Rate limit handling worked correctly.")


if __name__ == "__main__":
    asyncio.run(production_ready_demo())




