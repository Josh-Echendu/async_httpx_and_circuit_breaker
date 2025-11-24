import httpx
import asyncio
import time
import random

async def middleware_pattern():
    """Middleware pattern for request/response modification"""

    # Custom middleware functions
    async def add_timestamp_middleware(request):
        """Add timestamp to all requests"""
        request.headers['X-Request-Timestamp'] = str(int(time.time() * 1000))
        return request

    async def add_request_id_middleware(request):
        """Add unique request ID"""
        request_id = f"req_{int(time.time())}_{random.randint(1000, 9999)}"
        request.headers['X-request-ID'] = request_id
        return request

    async def rate_limit_detection_middleware(response, request):
        """Detect rate limiting and add headers"""
        if response.status_code == 429:
            response.headers["X-RateLimit-Detected"] = "true"
            retry_after = response.headers.get("Retry-After", "unknown")
            print(f"⚠️ Rate limit detected! Retry after: {retry_after}")
        return response

    async def response_time_middleware(response, request):
        """Add response time to headers"""
        if hasattr(request, '_start_time'):
            response_time = time.time() - request._start_time
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        return response

    async def make_request_with_middleware(url, custom_headers=None):
        # prepare request
        headers = custom_headers or {}
        request = httpx.Request("GET", url, headers=headers)
        print(request.headers)

        # Apply request middleware
        request = await add_timestamp_middleware(request)

        # Make the request
        request = await add_request_id_middleware(request)

        # Store start time for response middleware
        request._start_time = time.time()

        print("Request Headers: ", request.headers)
        print("Resquest startTime: ", request._start_time)

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), follow_redirects=True, limits=httpx.Limits(max_connections=2, max_keepalive_connections=2)) as client:
            response = await client.send(request)

            # Apply response middleware
            response = await rate_limit_detection_middleware(response, request)
            print(f"Response Headers: {response.headers}")
            print(f"Response: {response}")

            response = await response_time_middleware(response, request)
            print("response time", response.headers)
            print()

            return response

    test_urls = [
        "https://httpbin.org/headers",
        "https://httpbin.org/status/429",  # Test rate limit detection
        "https://httpbin.org/delay/1"      # Test response time
    ]
    custom_headers={"X-Custom-Data": "test_value"}
    tasks = [make_request_with_middleware(url, custom_headers) for i, url in enumerate(test_urls)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print("result summary: ", results)

    for response in results:
        if response.status_code == 200:

            data = response.json() if "json" in response.headers.get("content-type", "") else response.text
            print(f"✅ Request completed!")
            print(f"   Request ID: {response.request.headers.get('X-Request-ID')}")
            print(f"   Timestamp: {response.request.headers.get('X-Request-Timestamp')}")
            print(f"   Response Time: {response.headers.get('X-Response-Time', 'N/A')}")
            print(f"   Rate Limit: {response.headers.get('X-RateLimit-Detected', 'false')}")
            print()
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Rate Limit: {response.headers.get('X-RateLimit-Detected', 'false')}")
            print()




if __name__ == '__main__':
    asyncio.run(middleware_pattern())
