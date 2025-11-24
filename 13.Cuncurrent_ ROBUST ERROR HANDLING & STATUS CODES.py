import httpx
import asyncio

async def robust_error_handling():
    """Production-ready error handling for financial data"""
    
    # Simulate different API endpoints with various responses
    endpoints = [
        "https://httpbin.org/status/200",    # Success
        "https://httpbin.org/status/404",    # Not Found
        "https://httpbin.org/status/500",    # Server Error
        "https://httpbin.org/status/429",    # Rate Limited
        "https://httpbin.org/status/200",    # Success
        "https://httpbin.org/delay/2",       # Slow endpoint
        "https://invalid-domain-xyz.com",    # Network error
        "https://httpbin.org/status/403",    # Forbidden
    ]


    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)) as client:
        tasks = [client.get(url, timeout=30.0) for url in endpoints]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        print("Results Summary:", responses)

        # Analyze each response
        results = {
            "success": 0,
            "client_errors": 0,  # 4xx
            "server_errors": 0,  # 5xx
            "timeouts": 0,
            "network_errors": 0,
            "other_errors": 0
        }

        for i, response in enumerate(responses):
            print(f"\n🔍 Endpoint: {endpoints[i]}")

            if isinstance(response, Exception):
                if isinstance(response, httpx.TimeoutException):
                    print("   ⏰ Timeout - Request took too long")
                    resuls['timeouts'] += 1
                if isinstance(response, httpx.ConnectError):
                    print("   🌐 Network Error - Unable to connect")
                    results['network_errors'] += 1
                else:
                    print(f"   ❌ Other Error: {type(response).__name__}")
                    results['other_errors'] += 1

            elif isinstance(response, httpx.Response):
                # Handle HTTP responses
                status_code = response.status_code
                if status_code == 200:
                    print("   ✅ Success - Data fetched successfully")
                    results['success'] += 1

                elif status_code >= 400 and status_code < 500:
                    print(f"   🚫 Client Error {status_code}")
                    results['client_errors'] += 1
                    
                elif status_code >= 500 and status_code < 600:
                    print(f"   ⚠️ Server Error {status_code}")
                    results['server_errors'] += 1
                else:
                    print(f"   ❓ Unexpected Status Code {status_code}")
                    results["success"] += 1  # Treat as success


        # Print summary
        print(f"\n📊 FINAL RESULTS:")
        print(f"   ✅ Success: {results['success']}")
        print(f"   🚫 Client Errors (4xx): {results['client_errors']}")
        print(f"   🔥 Server Errors (5xx): {results['server_errors']}")
        print(f"   ⏰ Timeouts: {results['timeouts']}")
        print(f"   🌐 Network Errors: {results['network_errors']}")
        print(f"   ❓ Other Errors: {results['other_errors']}")

# Run it
asyncio.run(robust_error_handling())


# fetch("https://api.emailjs.com/api/v1.0/email/send", {
#   method: "POST",
#   headers: { "Content-Type": "application/json" },
#   body: JSON.stringify({
#     service_id: "gmail_service_123",
#     template_id: "welcome_email",
#     user_id: "YOUR_PUBLIC_KEY",
#     template_params: {
#       user_email: "someone@gmail.com",
#       message: "Thanks for creating an account with our company! We’re excited to have you onboard."
#     }
#   })
# })
# .then(response => {
#   if (response.ok) {
#     alert("✅ Account created! Confirmation email sent to your inbox.");
#   } else {
#     alert("❌ Something went wrong while sending your confirmation email.");
#   }
# })
# .catch(error => alert("⚠️ Network error: " + error));






            
                



