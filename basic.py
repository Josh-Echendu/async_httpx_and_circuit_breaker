# it’s what lets Python send HTTP requests (like visiting a website or calling an API).
import httpx 

import asyncio


async def stealth_get():

    # Create an asynchronous HTTP client using 'httpx.AsyncClient'
    async with httpx.AsyncClient(http2=True, timeout=20, follow_redirects=True) as client: # 'http2=True' enables the modern HTTP/2 protocol for faster and more efficient requests

        response = await client.get(
            "https://1xbet.whoscored.com/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                
                # It means: “I accept JSON, plain text, or anything (*/*).”
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

                # 👉 This says your browser prefers English (US).
                "Accept-Language": "en-US,en;q=0.9",

                # 👉 This tells the server which page you came from.
                "Referer": "https://google.com"
            }

        )

        # show cookies set by server (if any)
        print("✅ cookies: ", response.cookies.jar, "\n")
        print(f"✅ Status: {response.status_code} \n")
        print(f"✅ headers: ", response.headers, "\n")

        # print a safe excerpt of the body for diagnosis
        print("✅ body snippet: ", response.text[:100].replace("\n", " "), "\n")

        [print(f"  {k}: {v}") for k,v in response.headers.items()]

if __name__ == "__main__":
    asyncio.run(stealth_get())



# import httpx
# import asyncio

# async def debug_request():
#     async with httpx.AsyncClient(http2=True, follow_redirects=True, timeout=10.0) as client:
#         resp = await client.get("https://1xbet.whoscored.com/", headers={
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#             "Accept-Language": "en-US,en;q=0.9",
#             "Referer": "https://google.com"
#         })

#         print("status:", resp.status_code)
#         print("response headers:", resp.headers)
#         for k,v in resp.headers.items():
#             print(f"  {k}: {v}")

#         # show cookies set by server (if any)
#         print("cookies:", client.cookies.jar)

#         # print a safe excerpt of the body for diagnosis
#         body_snippet = resp.text[:800].replace("\n", " ")
#         print("body snippet:", body_snippet)

# asyncio.run(debug_request())
