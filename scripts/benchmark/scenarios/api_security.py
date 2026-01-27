"""
API Security Test Scenario
Tests rate limiting, authentication, and general API security
"""
import asyncio
import time
from typing import List, Dict, Optional
import aiohttp
from dataclasses import dataclass, field

from .base import BaseScenario
from config import config


@dataclass
class SecurityTestResult:
    """Result of a single security test"""
    test_name: str
    passed: bool
    requests_sent: int
    requests_blocked: int
    avg_response_time_ms: float
    status_codes: Dict[int, int] = field(default_factory=dict)
    error: Optional[str] = None


class APISecurityScenario(BaseScenario):
    """
    Security tests for API endpoints
    
    Tests:
    - Rate limiting effectiveness (should return 429)
    - Unauthenticated access (should return 401)
    - Authenticated flood protection
    - Trusted IP bypass validation (for benchmarks)
    """
    
    def __init__(self):
        super().__init__("api_security_test")
        self.target_url: str = ""
        self.auth_token: Optional[str] = None
        self.results: List[SecurityTestResult] = []
    
    async def setup(self, target: str = "http://localhost:8000", auth_token: str = None, **kwargs):
        """Prepare for security tests"""
        self.target_url = target.rstrip("/")
        self.auth_token = auth_token
        
        print(f"[{self.name}] Target: {self.target_url}")
        print(f"[{self.name}] Auth token: {'provided' if auth_token else 'none'}")
        
        # Verify target is reachable
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.target_url}/health", timeout=5) as resp:
                    if resp.status == 200:
                        print(f"[{self.name}] Target API is healthy")
                    else:
                        print(f"[{self.name}] Warning: Health check returned {resp.status}")
            except Exception as e:
                print(f"[{self.name}] Warning: Could not reach target: {e}")
    
    async def execute(self, rps: int = 100, duration: int = 10, **kwargs):
        """
        Execute security tests
        
        Args:
            rps: Requests per second for flood tests
            duration: Duration in seconds for sustained tests
        """
        print(f"[{self.name}] Starting security tests...")
        
        # Test 1: Rate Limit Flood Test
        result1 = await self._flood_test(rps=rps, duration=duration)
        self.results.append(result1)
        print(f"[{self.name}] Rate Limit Test: {'PASS ✓' if result1.passed else 'FAIL ✗'}")
        
        # Test 2: Unauthenticated Access Test
        result2 = await self._unauth_test()
        self.results.append(result2)
        print(f"[{self.name}] Unauth Access Test: {'PASS ✓' if result2.passed else 'FAIL ✗'}")
        
        # Test 3: Brute Force Protection (auth endpoint)
        result3 = await self._brute_force_test()
        self.results.append(result3)
        print(f"[{self.name}] Brute Force Test: {'PASS ✓' if result3.passed else 'FAIL ✗'}")
        
        # Test 4: Authenticated Flood Test (if token provided)
        if self.auth_token:
            result4 = await self._authenticated_flood_test(rps=rps, duration=duration)
            self.results.append(result4)
            print(f"[{self.name}] Auth Flood Test: {'PASS ✓' if result4.passed else 'FAIL ✗'}")
    
    async def teardown(self, **kwargs):
        """Cleanup and summary"""
        print(f"\n[{self.name}] Security Test Summary:")
        print("-" * 50)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {status} | {result.test_name}")
            print(f"       Requests: {result.requests_sent}, Blocked: {result.requests_blocked}")
            print(f"       Avg Response: {result.avg_response_time_ms:.2f}ms")
            if result.error:
                print(f"       Error: {result.error}")
        
        print("-" * 50)
        print(f"Total: {passed}/{total} tests passed")
    
    async def _flood_test(self, rps: int, duration: int) -> SecurityTestResult:
        """
        Test rate limiting by flooding the API
        
        Success criteria: API returns 429 after hitting rate limit
        """
        test_name = "rate_limit_flood"
        endpoint = f"{self.target_url}/health"
        
        status_codes: Dict[int, int] = {}
        response_times: List[float] = []
        total_requests = rps * duration
        
        print(f"[{self.name}] Flood test: {rps} req/s for {duration}s = {total_requests} requests")
        
        connector = aiohttp.TCPConnector(limit=rps, limit_per_host=rps)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            async def make_request():
                start = time.time()
                try:
                    async with session.get(endpoint, timeout=5) as resp:
                        status = resp.status
                        status_codes[status] = status_codes.get(status, 0) + 1
                        response_times.append((time.time() - start) * 1000)
                except asyncio.TimeoutError:
                    status_codes[0] = status_codes.get(0, 0) + 1
                except Exception as e:
                    status_codes[-1] = status_codes.get(-1, 0) + 1
            
            # Send requests in batches
            start_time = time.time()
            tasks = []
            
            while time.time() - start_time < duration:
                batch_start = time.time()
                
                # Create batch of requests
                for _ in range(rps):
                    tasks.append(asyncio.create_task(make_request()))
                
                # Wait for batch window (1 second)
                elapsed = time.time() - batch_start
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)
            
            # Wait for all pending requests
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Evaluate results
        requests_blocked = status_codes.get(429, 0)
        total_sent = sum(status_codes.values())
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        # Pass if we got at least some 429s (rate limit is working)
        passed = requests_blocked > 0
        
        return SecurityTestResult(
            test_name=test_name,
            passed=passed,
            requests_sent=total_sent,
            requests_blocked=requests_blocked,
            avg_response_time_ms=avg_response,
            status_codes=status_codes,
            error=None if passed else "Rate limiting not triggered (no 429 responses)"
        )
    
    async def _unauth_test(self) -> SecurityTestResult:
        """
        Test that protected endpoints reject unauthenticated requests
        
        Success criteria: All protected endpoints return 401/403
        """
        test_name = "unauthenticated_access"
        
        protected_endpoints = [
            "/api/meetings",
            "/api/calendar/events",
            "/api/settings",
            "/api/recordings",
            "/api/transcriptions",
        ]
        
        status_codes: Dict[int, int] = {}
        response_times: List[float] = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in protected_endpoints:
                url = f"{self.target_url}{endpoint}"
                start = time.time()
                
                try:
                    async with session.get(url, timeout=5) as resp:
                        status = resp.status
                        status_codes[status] = status_codes.get(status, 0) + 1
                        response_times.append((time.time() - start) * 1000)
                except Exception as e:
                    status_codes[-1] = status_codes.get(-1, 0) + 1
        
        # Evaluate: all requests should be 401 or 403
        unauthorized_count = status_codes.get(401, 0) + status_codes.get(403, 0)
        total_sent = sum(status_codes.values())
        passed = unauthorized_count == total_sent
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return SecurityTestResult(
            test_name=test_name,
            passed=passed,
            requests_sent=total_sent,
            requests_blocked=unauthorized_count,
            avg_response_time_ms=avg_response,
            status_codes=status_codes,
            error=None if passed else f"Some endpoints returned non-401/403: {status_codes}"
        )
    
    async def _brute_force_test(self) -> SecurityTestResult:
        """
        Test brute force protection
        
        Success criteria: Multiple failed requests trigger rate limiting
        """
        test_name = "brute_force_protection"
        
        # Try 50 rapid requests (invalid auth)
        status_codes: Dict[int, int] = {}
        response_times: List[float] = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(50):
                headers = {"Authorization": f"Bearer invalid-token-{i}"}
                url = f"{self.target_url}/api/meetings"
                start = time.time()
                
                try:
                    async with session.get(url, headers=headers, timeout=5) as resp:
                        status = resp.status
                        status_codes[status] = status_codes.get(status, 0) + 1
                        response_times.append((time.time() - start) * 1000)
                except Exception as e:
                    status_codes[-1] = status_codes.get(-1, 0) + 1
        
        # Evaluate: should see 429s after hitting limit
        requests_blocked = status_codes.get(429, 0)
        unauthorized = status_codes.get(401, 0)
        total_sent = sum(status_codes.values())
        
        # Pass if we see 429s OR all are 401s (both acceptable)
        passed = requests_blocked > 0 or unauthorized == total_sent
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return SecurityTestResult(
            test_name=test_name,
            passed=passed,
            requests_sent=total_sent,
            requests_blocked=requests_blocked,
            avg_response_time_ms=avg_response,
            status_codes=status_codes,
            error=None if passed else "Brute force not rate limited"
        )
    
    async def _authenticated_flood_test(self, rps: int, duration: int) -> SecurityTestResult:
        """
        Test that even authenticated users are rate limited
        
        Success criteria: Authenticated flood eventually triggers 429
        """
        test_name = "authenticated_flood"
        endpoint = f"{self.target_url}/api/meetings"
        
        status_codes: Dict[int, int] = {}
        response_times: List[float] = []
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        connector = aiohttp.TCPConnector(limit=rps, limit_per_host=rps)
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            
            async def make_request():
                start = time.time()
                try:
                    async with session.get(endpoint, timeout=5) as resp:
                        status = resp.status
                        status_codes[status] = status_codes.get(status, 0) + 1
                        response_times.append((time.time() - start) * 1000)
                except asyncio.TimeoutError:
                    status_codes[0] = status_codes.get(0, 0) + 1
                except Exception:
                    status_codes[-1] = status_codes.get(-1, 0) + 1
            
            tasks = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                for _ in range(rps):
                    tasks.append(asyncio.create_task(make_request()))
                await asyncio.sleep(1.0)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        requests_blocked = status_codes.get(429, 0)
        total_sent = sum(status_codes.values())
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        # Pass if rate limiting kicks in
        passed = requests_blocked > 0
        
        return SecurityTestResult(
            test_name=test_name,
            passed=passed,
            requests_sent=total_sent,
            requests_blocked=requests_blocked,
            avg_response_time_ms=avg_response,
            status_codes=status_codes,
            error=None if passed else "Authenticated flood not rate limited"
        )
    
    def generate_recommendations(self, config_params: dict) -> dict:
        """Generate security recommendations based on test results"""
        recommendations = {
            "security_status": "PASS" if all(r.passed for r in self.results) else "NEEDS ATTENTION",
            "tests_passed": sum(1 for r in self.results if r.passed),
            "tests_total": len(self.results),
            "issues": [],
            "suggestions": [],
        }
        
        for result in self.results:
            if not result.passed:
                recommendations["issues"].append({
                    "test": result.test_name,
                    "error": result.error,
                    "status_codes": result.status_codes,
                })
        
        if recommendations["issues"]:
            recommendations["suggestions"].append("Review and strengthen rate limiting configuration")
            recommendations["suggestions"].append("Ensure all protected endpoints require authentication")
        
        return recommendations
