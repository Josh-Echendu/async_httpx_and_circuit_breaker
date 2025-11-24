import httpx
import asyncio
import time
from datetime import datetime, timedelta


async def advanced_parameter_building():
    """Advanced parameter building for financial data APIs"""

    async with httpx.AsyncClient(http2=True, limits=httpx.Limits(max_connections=5, max_keepalive_connections=5), timeout=httpx.Timeout(30.0)) as client:
        
        end_date = datetime.now()

        """current time now - 30 days later"""
        start_date = end_date - timedelta(days=30)

        symbols = ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN"]

        for symbol in symbols:
            params = {
                "symbol": symbol,
                "interval": "1d",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "indicators": "sma,ema,rsi",
                "period": "30",
                "format": "json",
                "apikey": "demo_key"  # In real use, this would be your actual API key
            }

            params = {k: v for k, v in params.items() if v is not None and v != ""}
            try:
                response = await client.get(
                    "https://httpbin.org/get",
                    params=params,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {symbol} data fetched successfully")
                    print(f"   Parameters: {data['args']}")

            except Exception as e:
                print(f"❌ Error fetching {symbol}: {e}")

# Run it
asyncio.run(advanced_parameter_building())


