import httpx
import asyncio


async def fetch_url(client, url):
    resp = await client.get(url)
    print(f"✅ {url} → {resp.status_code}")
    return resp


async def persistent_session():
    async with httpx.AsyncClient(
        http2=True, 
        timeout=httpx.Timeout(10.0), 
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
        ) as client:

        urls = [
            "https://httpbin.org/json",
            "https://httpbin.org/uuid", 
            "https://httpbin.org/headers"
        ]

        await asyncio.gather(*[fetch_url(client, url) for url in urls])

if __name__ == "__main__":
    asyncio.run(persistent_session())