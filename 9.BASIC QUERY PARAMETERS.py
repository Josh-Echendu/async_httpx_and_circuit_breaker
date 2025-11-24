import httpx
import asyncio

async def basic_query_params():
    max_retry=3
    retry_delay=2.5
    retry_count=0

    """Simple query parameters for product search"""
    async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=2, max_keepalive_connections=2)) as client:
            try:
                # Build URL with query parameters
                base_url = "https://httpbin.org/get"
                params = {
                    "category": "electronics",
                    "price_min": "100",
                    "price_max": "1000", 
                    "sort": "price_desc",
                    "limit": "50"
                }

                resp = await client.get(
                    base_url,
                    params=params,
                    headers={
                        "User-Agent": "QueryClient/1.0",
                        "Accept": "application/json"
                    }
                )

                if resp.status_code == 200:
                    data = resp.json()
                    print("✅ Query Parameters Successful!")
                    print(f"data: {data}")
                    print(f"text: {resp.text}")
                    return data
                else:
                    print("❌ Query Parameters Failed!")
                    print(f"Status Code: {resp.status_code}")
                    print(f"text: {resp.text}")
                    retry_count = retry_count + 1
                    print(f"🔄 Retrying... ({retry_count}/{max_retry})")
                    await asyncio.sleep(retry_delay * (2 ** retry_count))

            except httpx.RequestError as e:
                print(f"🔥 Network error: {type(e).__name__} - {e}")
                retry_count += 1
                if retry_count <= max_retry:
                    print(f"🔄 Retrying... ({retry_count}/{max_retry})")
                    await asyncio.sleep(retry_delay * (2 ** retry_count))

# Run it
if __name__ == "__main__":
    asyncio.run(basic_query_params())
