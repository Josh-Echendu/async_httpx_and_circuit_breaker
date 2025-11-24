import asyncio
import httpx

async def session_with_cookies():
    async with httpx.AsyncClient(http2=True) as client:

        response1 = await client.get("https://httpbin.org/cookies/set/session/abc123")
        print(f"✅ Cookies set: {response1.cookies}")

        response2 = await client.get("https://httpbin.org/cookies")
        print(f"✅ Cookies sent: {response2.json()}")

asyncio.run(session_with_cookies())
                  