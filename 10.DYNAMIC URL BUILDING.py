import httpx
import asyncio

async def dynamic_url_building():
    """Build URLs dynamically for e-commerce scraping"""

    retry_count=0
    max_retry=3
    retry_delay=2.5

    async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=2, max_keepalive_connections=2)) as client:
            try:
                search_scenarios = [
                    {"query": "gaming laptop", "page": 1, "sort": "relevance"},
                    {"query": "wireless headphones", "page": 2, "sort": "price_low"},
                    {"query": "smartphone", "page": 1, "sort": "rating"}
                ]

                for scenario in search_scenarios:

                    while retry_count <= max_retry:
                        base_url = "https://httpbin.org/get"
                        params = {
                            "q": scenario["query"],
                            "page": scenario["page"],
                            "sort": scenario["sort"],
                            "in_stock": "true",
                            "free_shipping": "true"
                        }

                        resp = await client.get(
                            base_url,
                            params=params,
                            headers={
                                "User-Agent": "DynamicURLClient/1.0",
                                "Accept": "application/json"
                            }
                        )

                        if resp.status_code == 200:
                            data = resp.json()
                            print("✅ Dynamic URL Building Successful!")
                            print(f"data: {data}")
                            print(f"✅ Search '{scenario['query']}' - Page {scenario['page']}")
                            print(f"   URL: {data['url']}")
                            break

                        else:
                            print(f"❌ Search failed: {resp.status_code}")
                            print(f"   Response: {resp.text}")
                            retry_count = retry_count + 1
                            print(f"🔄 Retrying... ({retry_count}/{max_retry + 1})")
                            await asyncio.sleep(retry_delay * (2 ** retry_count))
                    
            except httpx.RequestError as e:
                print(f"🔥 Network error: {type(e).__name__} - {e}")
                retry_count += 1
                if retry_count <= max_retry:
                    print(f"🔄 Retrying... ({retry_count}/{max_retry + 1})")
                    await asyncio.sleep(retry_delay * (2 ** retry_count))
                

if __name__ == "__main__":
    asyncio.run(dynamic_url_building())