import httpx
import asyncio

async def fetch_url(product_id, client):
    url = f"https://httpbin.org/json"  # Simulating product API
    response = await client.get(url, params={"product_id": product_id}, timeout=30.0)
    return response

async def basic_concurrent_requests():
    """Basic concurrent requests for product data"""

    # List of product IDs to fetch
    product_ids = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)) as client:
        tasks = [fetch_url(product_id, client) for product_id in product_ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # prints out a list of all API responses
        print("Results Summary:", responses)

        successful_responses = 0

        # iterate through the responses list
        for i, response in enumerate(responses):
            if response.status_code == 200:
                successful_responses += 1
                data = response.json()
                print(f"✅ Product ID {product_ids[i]} data fetched successfully")

            else:
                print(f"❌ Error fetching Product ID {product_ids[i]}: {response}")

        print(f"🎯 Results: {successful_responses}/{len(product_ids)} successful")

# Run it
asyncio.run(basic_concurrent_requests())

