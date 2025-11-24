import asyncio
import httpx
import statistics
import time



# Enterprise circuit breaker with multiple services
enterprise_circuits = {}

# 👉 “Give me the latest status record for that service — create one if it doesn’t exist.”
def get_circuit_for_service(service_name):
    """Get or create circuit for a service"""

    if service_name not in enterprise_circuits:
        enterprise_circuits[service_name] = {

            # "closed" or "open" or "half_open"
            "state": "closed", 

            # Total number of failed requests since start.
            "failure_count": 0, 

            # Total number of successful requests.
            "success_count": 0, 

            # How many failures in a row — used to trigger “open”.
            "consecutive_failures": 0, # consecutive_failures → helps decide if circuit should open right now (short-term stability)

            # When the last failure happened (in seconds since epoch).
            "last_failure_time": 0,

            # When to try again after being open (used for the 60s wait).
            "next_retry_time": 0, 
            
            # List of response durations for calculating averages.
            "response_times": [],
            
            # Keeps a count of which errors occurred most often (timeout, 500, etc.).
            "error_types": {}, ####

            # Total number of requests made overall.
            "total_requests": 0, 

            # When the circuit last changed from open → closed or vice versa.
            "last_state_change": time.time(),
            
            # The overall “service health” percentage (0–100). Starts healthy at 100.
            "health_score": 100, # 0-100 scale

            'retry': False
        }

    return enterprise_circuits[service_name]

async def enterprise_circuit_breaker(service_name, request_func, *args, config=None):
    """Enterprise-grade circuit breaker for any service"""

    default_config = {
        # How many times a request can fail before the circuit “opens” (stops sending requests temporarily).
        "max_failures": 5,

        # How long (in seconds) the circuit should stay open before testing again.
        "reset_timeout": 30,

        # Number of successful requests required to close the circuit again after reopening.
        "success_threshold": 3,

        # If a response takes longer than this (in seconds), it counts as a “slow” request.
        "slow_response_threshold": 3.0,

        # A health score (0–100). If it drops below this, the service is considered unhealthy.
        "health_threshold": 30, 

        # A “warning” level — below this, service is degraded but not yet broken.
        "degraded_threshold": 70,  

        # How many past requests are tracked to calculate the health score.
        "window_size": 100,  # Requests to consider for health

        # When the circuit is half-open (testing state), only allow this many trial requests.
        "half_open_max_requests": 5  
    }

    config = default_config or config

    # 👉 “Give me the latest status record for that service — create one if it doesn’t exist.”
    circuit = get_circuit_for_service(service_name)
    current_time = time.time()

    # Circuit state machine
    if circuit["state"] == "open":

        if current_time < circuit["next_retry_time"]:

            if not circuit['retry']:
                print(f"🚫 [{service_name}] Circuit OPEN - failing fast")
                circuit['retry'] = True
                # circuit["total_requests"] += 1
                
                return {
                    "error": f"Circuit breaker open for {service_name}",
                    "status": "fail_fast", 
                    "circuit_state": "open",
                    'health_score': circuit['health_score'],
                }
            return 
        else:
            # update the state from open to half-open
            print(f"🟡 [{service_name}] Circuit transitioning to HALF-OPEN")
            circuit.update({
                "state": "half_open",
                "consecutive_failures": 0,
                "last_state_change": current_time,
                "retry": False
            })

    # Track requests in half-open state
    if circuit["state"] == "half_open":
        half_open_requests = circuit.get("half_open_requests", 0) + 1
        circuit["half_open_requests"] = half_open_requests
        
        if half_open_requests > config["half_open_max_requests"]:
            print(f"🔴 [{service_name}] Too many failed half-open requests - reopening circuit")
            circuit.update({
                "state": "open",
                "next_retry_time": current_time + config["reset_timeout"],
                "last_state_change": current_time

            })
            return {
                "error": f"Too many half-open requests for {service_name}",
                "status": "fail_fast",
                "circuit_state": "open",
            }

    start_time = time.time()
    circuit['total_requests'] = circuit['total_requests'] + 1

    try:
        result = await request_func(*args)
        response_time = time.time() - start_time
        
        # Track successful request
        circuit['success_count'] = circuit['success_count'] + 1
        circuit['response_times'].append(response_time)

        # Keep only recent response times(we wanna focus on only 100 request)
        if len(circuit['response_times']) > config['window_size']:
            circuit['response_times'].pop(0)

        # Reset consecutive failures on success
        circuit['consecutive_failures'] = 0

        health_score = calculate_health_score(circuit, config)
        circuit['health_score'] = health_score

        # State transitions on success
        if circuit['state'] == "half_open":

            # Success in half-open state - check if we should close
            half_open_successes = circuit.get("half_open_successes", 0) + 1
            circuit['half_open_successes'] = half_open_successes

            if half_open_successes >= config['success_threshold']:
                print(f"✅ [{service_name}] Service recovered - circuit CLOSED")
    
                circuit.update({
                   "state": "closed",
                   "last_state_change": current_time,
                   "half_open_requests": 0,
                   "half_open_successes": 0 
                })

        print(f"✅ [{service_name}] Request succeeded | Health: {health_score} | Time: {response_time:.2f}s")
        return {
            "data": result,
            "status": "success",
            "response_time": response_time,
            "circuit_state": circuit['state'],
            "health_score": health_score
            }

    except Exception as e:
        # Request failed
        response_time = time.time() - start_time
        error_type = type(e).__name__
        error_count = circuit['error_types'].get(error_type, 0) + 1

        # Track failure
        # This counts all-time total failures for the service.
        circuit['failure_count'] = circuit['failure_count'] + 1

        # This counts how many times in a row it has failed.
        circuit['consecutive_failures'] = circuit['consecutive_failures'] + 1
        
        # current time of failure
        circuit['last_failure_time'] = current_time

        # For example: { "TimeoutError": 3, "HTTPStatusError": 5, "ConnectionRefusedError": 2}
        circuit['error_types'][error_type] = error_count

        # Calculate health score
        health_score = calculate_health_score(circuit, config)
        circuit['health_score'] = health_score
        print(f"❌ [{service_name}] Request failed: {error_type} | Health: {health_score} 🔋 | Time: {response_time:.2f}s")

        # Check if we should open circuit
        if (circuit['consecutive_failures'] >= config['max_failures'] or health_score < config['health_threshold']):
            if circuit['state'] != 'open':
                print(f"🪫 [{service_name}] Opening circuit - health too low or too many failures")
                circuit.update({
                    "state": "open",
                    "next_retry_time": current_time + config['reset_timeout'],
                    "last_state_change": current_time
                })
        
        return {
            "error": str(e), # error string
            "status": "failure",
            "response_time": response_time, 
            "circuit_state": circuit['state'],
            'health_score': health_score,
            "error_type": error_type
        }
    
"""⚙️ What You Just Understood (and You’re Right)

    ✅ failure_count = long-term memory (historical record)
    ✅ success_count = long-term wins
    ✅ consecutive_failures = short-term warning meter — “yo, I’m failing now repeatedly”
    ✅ Health score = a constantly updated “mood” of the service
    ✅ Health isn’t checked once — it’s recalculated after every single request
    ✅ Every time a request succeeds or fails → we recalculate health
    ✅ Every time we recalc → we decide: “Should I stay CLOSED, go HALF-OPEN, or fully OPEN?”
 """

def calculate_health_score(circuit, config):
    """Calculate health score 0-100 based on recent performance"""
    if circuit['total_requests'] == 0:
        return 100

    # Base score from success rate, Example: 8 successes / 10 requests → success_rate = 0.8
    success_rate = circuit['success_count'] / circuit['total_requests'] # thats good so if 90 passes out of 100 its has a success rate of 0.9/1.0
    base_score = success_rate * 80 # 80% weight to success rate
    
    # penalty for recent failures
    failure_penalty = min(circuit['consecutive_failures'] * 10, 20) # Max 20 point penalty

    time_penalty = 0

    if circuit['response_times']:
        avg_time = statistics.mean(circuit['response_times'])
        if avg_time > config['slow_response_threshold']: # if avg_time > 3
            # Penalize slow response
            time_penalty = min((avg_time - config["slow_response_threshold"]) * 10, 10)

    health_score = max(0, base_score - failure_penalty - time_penalty)
    return round(health_score)

async def mock_api_request(url, should_fail=False, delay=0):
    """Mock API request for testing"""
    if delay > 0:
        await asyncio.sleep(delay)

    if should_fail:
        raise httpx.HTTPStatusError(f"Mock error for {url}", request=None, response=None)

    async with httpx.AsyncClient(http2=True) as client:
        return await client.get(url)


async def test_enterprise_circuit_breaker():
    """Test enterprise circuit breaker with multiple services"""
    services = {
        "payment_api": {
            "config": {
                "max_failures": 3,
                "reset_timeout": 15,
                "slow_response_threshold": 2.0,
                "health_threshold": 40
            },
            "scenarios": [
                {"url": "https://httpbin.org/status/200", "fail": False, "delay": 0},
                {"url": "https://httpbin.org/status/500", "fail": True, "delay": 0},
                {"url": "https://httpbin.org/status/500", "fail": True, "delay": 0},
                {"url": "https://httpbin.org/status/500", "fail": True, "delay": 0},  # Should open circuit
                {"url": "https://httpbin.org/status/200", "fail": False, "delay": 0},  # Fail fast
            ]
        },
        "user_service": {
            "config": {
                "max_failures": 2, 
                "reset_timeout": 10,
                "slow_response_threshold": 1.5
            },
            "scenarios": [
                {"url": "https://httpbin.org/delay/1", "fail": False, "delay": 1},
                {"url": "https://httpbin.org/delay/3", "fail": False, "delay": 3},  # Slow
                {"url": "https://httpbin.org/status/500", "fail": True, "delay": 0},
                {"url": "https://httpbin.org/status/500", "fail": True, "delay": 0},  # Should open
                {"url": "https://httpbin.org/status/200", "fail": False, "delay": 0},
            ]
        }
    }

    print("🚀 Starting Enterprise Circuit Breaker Test...")

    for service_name, service_config in services.items():
        print(f"\n🔧 Testing Service: {service_name}")

        for i, scenario in enumerate(service_config['scenarios']):
            print(f"\n🎯 Request {i+1} to {service_name}: {scenario['url']}")

            result = await enterprise_circuit_breaker(
                service_name,
                mock_api_request,
                scenario['url'],
                scenario['fail'],
                scenario['delay'],
                config=service_config['config']
            )

            if result is None:
                continue
            print(f"   Status: {result['status']} | Circuit: {result['circuit_state']} | Health: {result.get('health_score', 'N/A')}")
            
        # Print final status
        print(f"\n📊 ENTERPRISE CIRCUIT BREAKER SUMMARY:")
        for service_name, circuit in enterprise_circuits.items():
            print(f"   🔌 {service_name}: {circuit['state']} | Health: {circuit['health_score']} | Total Requests: {circuit['total_requests']}")


if __name__ == "__main__":
    asyncio.run(test_enterprise_circuit_breaker())

# Simple version (your words)

# Bro, success rate gives the main energy (80 points),
# failures can drain up to 20 points,
# slowness can drain up to 10 points,
# so in total, you can lose up to 30 points if your connection misbehaves —
# but you can never gain more than your success gave you.


# | Config                           | Meaning (in your own words)                     |
# | -------------------------------- | ----------------------------------------------- |
# | **slow_response_threshold = 3s** | If it takes >3s, we mark it slow.               |
# | **window_size = 100**            | We track the last 100 requests.                 |
# | **health_threshold = 30**        | If health < 30 → open (pause).                  |
# | **degraded_threshold = 70**      | If 30 < health < 70 → warn “weak service”.      |
# | **max_failures = 5**             | If 5 requests fail in a row → open immediately. |
# | **reset_timeout = 60**           | After opening, wait 60s before testing again.   |
# | **half_open_max_requests = 5**   | During test, only allow 5 trial requests.       |
# | **success_threshold = 3**        | If 3 of them succeed → close circuit again.     |


# Circuit Breaker Logic (in plain English)

# Normal phase (Closed)

# Everything’s working fine.

# You keep sending requests normally.

# Fail phase (Open)

# Suddenly, 5 requests fail in a row → (max_failures = 5)

# The breaker says “whoa, something’s wrong!”

# It opens the circuit and pauses all API calls.

# It waits for 60 seconds → (reset_timeout = 60)

# Testing phase (Half-Open)

# After 60 s, breaker gives the API another chance.

# It sends only 5 test requests → (half_open_max_requests = 5)

# Recovery check

# If at least 3 of those succeed → (success_threshold = 3)
# → breaker says “service looks fine again” → closes back to normal.

# If they still fail → breaker re-opens and waits another 60 s.



# | Step | Event     | consecutive_failures | health_score | State             |
# | ---- | --------- | -------------------- | ------------ | ----------------- |
# | 1    | ✅ success | 0                    | 100         | closed            |
# | 2    | ❌ fail    | 1                    | 85           | closed            |
# | 3    | ❌ fail    | 2                    | 70           | ⚠️ degraded       |
# | 4    | ❌ fail    | 3                    | 55           | ⚠️ degraded       |
# | 5    | ❌ fail    | 4                    | 35           | ⚠️ nearly open    |
# | 6    | ❌ fail    | 5                    | 25           | 🔴 open (tripped) |

# So before the process even “ends,” the circuit has already detected danger and cut off traffic to prevent further overload.
# Circuit breakers are live monitors, not end-reporters.
# Health score changes in real-time — just like a heartbeat monitor.
# Once health drops below the limit(30) → circuit trips instantly to open, no need to “wait till the end.”


# 4️⃣ Finally — the min(..., 10) part

# That means:

# “Never penalize more than 10 points, no matter how slow it gets.”

# | Avg Time | Over Limit | Raw Penalty | Final Penalty |
# | -------- | ---------- | ----------- | ------------- |
# | 3.0s     | 0s         | 0           | 0             |
# | 3.5s     | 0.5s       | 5           | 5             |
# | 4.0s     | 1s         | 10          | 10            |
# | 6.0s     | 3s         | 30          | **10 (max)**  |




# | Situation            | Success Rate               | Base Score (×80) | Failure Penalty  | Slow Penalty | Final Health               |
# | -------------------- | -------------------------- | ---------------- | ---------------- | ------------ | -------------------------- |
# | **Normal (perfect)** | 1.0 → (100% good requests) | 1.0 × 80 = 80    | 0 (no failures)  | 0 (not slow) | 80 + 20 = **100% HEALTHY** |
# | **Few fails (1)**    | 0.9 (90% success)          | 0.9 × 80 = 72    | 10               | 0            | 72 - 10 = **62**           |
# | **2 fails**          | 0.8 (80% success)          | 0.8 × 80 = 64    | 20               | 0            | 64 - 20 = **44**           |
# | **5 fails**          | 0.5 (50% success)          | 0.5 × 80 = 40    | 20 (max penalty) | 0            | 40 - 20 = **20 (BAD)**     |
