import asyncio
import httpx


async def stealth_post():
    async with httpx.AsyncClient(http2=True, timeout=20, follow_redirects=True) as client:
        requestBody = {
            "title": "Test Post for joshua",
            "body": "This is post call for id 5",
            "userId": 5
        }

        resp = await client.post(
            "https://jsonplaceholder.typicode.com/posts/",
            json=requestBody,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",  # Mimic AJAX
                "Referer": "https://google.com"

            }
        )
        print(f"✅ Request Body: ", resp.request.content)
        print(f"✅ Response JSON: {resp.json()}")
        print(f"✅ cookies: ", resp.cookies.jar)
        print(f"✅ Status: {resp.status_code}")
        print(f"✅ Headers: {resp.headers}")
        print(f"✅ Body snippet: {resp.text[:100].replace('\n', ' ')}")
asyncio.run(stealth_post())


# 🧩 Step 5: In your 1000 logcode case

# Here’s exactly what happens:

# You start with 10 active TCP connections.

# 10 logcodes get declined at once.

# 5 of those connections are kept alive for reuse.

# Next logcodes reuse those 5.

# The client continues like this until all 1000 are done.

# Total connections opened during the whole process:
# 👉 10 opened initially, then reused repeatedly.
# 👉 5 always stay warm and ready between batches.