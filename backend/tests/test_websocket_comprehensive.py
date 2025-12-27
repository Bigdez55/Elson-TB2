#!/usr/bin/env python3
"""
Comprehensive WebSocket Streaming Functionality Test Suite

This test suite performs thorough testing of:
1. WebSocket connection establishment and termination
2. Market data streaming functionality
3. Connection management and persistence
4. Performance testing and metrics
5. Trading updates streaming
6. Error handling and recovery mechanisms
"""

import asyncio
import json
import logging
import time
import statistics
import websockets
import httpx
import psutil
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketTestMetrics:
    """Metrics collection for WebSocket testing."""
    
    def __init__(self):
        self.connection_times = []
        self.message_latencies = []
        self.reconnection_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.message_counts = {}
        self.error_counts = {}
        self.test_start_time = None
        self.test_end_time = None
        
    def record_connection_time(self, time_taken: float):
        """Record connection establishment time."""
        self.connection_times.append(time_taken)
        
    def record_message_latency(self, latency: float):
        """Record message round-trip latency."""
        self.message_latencies.append(latency)
        
    def record_reconnection_time(self, time_taken: float):
        """Record reconnection time."""
        self.reconnection_times.append(time_taken)
        
    def record_system_metrics(self):
        """Record current system metrics."""
        process = psutil.Process()
        self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
        self.cpu_usage.append(process.cpu_percent())
        
    def increment_message_count(self, message_type: str):
        """Increment message count for a type."""
        self.message_counts[message_type] = self.message_counts.get(message_type, 0) + 1
        
    def increment_error_count(self, error_type: str):
        """Increment error count for a type."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
    def start_test(self):
        """Mark test start time."""
        self.test_start_time = time.time()
        
    def end_test(self):
        """Mark test end time."""
        self.test_end_time = time.time()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        test_duration = (self.test_end_time - self.test_start_time) if self.test_end_time and self.test_start_time else 0
        
        return {
            "test_duration_seconds": test_duration,
            "connection_metrics": {
                "count": len(self.connection_times),
                "avg_time_ms": statistics.mean(self.connection_times) * 1000 if self.connection_times else 0,
                "min_time_ms": min(self.connection_times) * 1000 if self.connection_times else 0,
                "max_time_ms": max(self.connection_times) * 1000 if self.connection_times else 0,
            },
            "message_latency_metrics": {
                "count": len(self.message_latencies),
                "avg_latency_ms": statistics.mean(self.message_latencies) * 1000 if self.message_latencies else 0,
                "min_latency_ms": min(self.message_latencies) * 1000 if self.message_latencies else 0,
                "max_latency_ms": max(self.message_latencies) * 1000 if self.message_latencies else 0,
                "p95_latency_ms": statistics.quantiles(self.message_latencies, n=20)[18] * 1000 if len(self.message_latencies) > 20 else 0,
            },
            "reconnection_metrics": {
                "count": len(self.reconnection_times),
                "avg_time_ms": statistics.mean(self.reconnection_times) * 1000 if self.reconnection_times else 0,
            },
            "system_metrics": {
                "avg_memory_mb": statistics.mean(self.memory_usage) if self.memory_usage else 0,
                "max_memory_mb": max(self.memory_usage) if self.memory_usage else 0,
                "avg_cpu_percent": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                "max_cpu_percent": max(self.cpu_usage) if self.cpu_usage else 0,
            },
            "message_counts": self.message_counts,
            "error_counts": self.error_counts,
        }


class ComprehensiveWebSocketTester:
    """Comprehensive WebSocket functionality tester."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = f"ws://localhost:8000/api/v1/streaming/ws"
        self.rest_url = f"{base_url}/api/v1/streaming"
        self.metrics = WebSocketTestMetrics()
        self.active_connections = []
        
    async def test_rest_endpoints(self) -> Dict[str, Any]:
        """Test REST endpoints for streaming service."""
        logger.info("Testing REST endpoints...")
        results = {}
        
        async with httpx.AsyncClient() as client:
            try:
                # Test status endpoint
                response = await client.get(f"{self.rest_url}/status")
                results["status_endpoint"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                }
                logger.info(f"Status endpoint: {response.status_code}")
                
                # Test subscriptions endpoint
                response = await client.get(f"{self.rest_url}/subscriptions")
                results["subscriptions_endpoint"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                }
                logger.info(f"Subscriptions endpoint: {response.status_code}")
                
                # Test quote endpoint
                response = await client.get(f"{self.rest_url}/quote/AAPL")
                results["quote_endpoint"] = {
                    "success": response.status_code in [200, 404],  # 404 is acceptable if no data
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                }
                logger.info(f"Quote endpoint: {response.status_code}")
                
            except Exception as e:
                logger.error(f"REST endpoint test error: {str(e)}")
                results["error"] = str(e)
                
        return results
    
    async def test_basic_connection(self) -> Dict[str, Any]:
        """Test basic WebSocket connection establishment and termination."""
        logger.info("Testing basic WebSocket connection...")
        
        results = {
            "connection_successful": False,
            "connection_time_ms": 0,
            "welcome_message_received": False,
            "disconnection_clean": False,
            "error": None
        }
        
        try:
            start_time = time.time()
            websocket = await websockets.connect(self.ws_url)
            connection_time = time.time() - start_time
            
            self.metrics.record_connection_time(connection_time)
            results["connection_successful"] = True
            results["connection_time_ms"] = connection_time * 1000
            
            # Wait for welcome message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                if data.get("type") == "connected":
                    results["welcome_message_received"] = True
                    self.metrics.increment_message_count("connected")
                    logger.info("Welcome message received")
                    
            except asyncio.TimeoutError:
                logger.warning("No welcome message received within timeout")
                
            # Clean disconnection
            await websocket.close()
            results["disconnection_clean"] = True
            logger.info("Basic connection test successful")
            
        except Exception as e:
            logger.error(f"Basic connection test failed: {str(e)}")
            results["error"] = str(e)
            self.metrics.increment_error_count("connection_failed")
            
        return results
    
    async def test_subscription_functionality(self) -> Dict[str, Any]:
        """Test symbol subscription and unsubscription."""
        logger.info("Testing subscription functionality...")
        
        results = {
            "subscription_successful": False,
            "unsubscription_successful": False,
            "quote_data_received": False,
            "subscription_time_ms": 0,
            "quotes_received": 0,
            "error": None
        }
        
        try:
            websocket = await websockets.connect(self.ws_url)
            
            # Wait for connection
            await websocket.recv()  # Welcome message
            
            # Test subscription
            test_symbols = ["AAPL", "GOOGL", "MSFT"]
            subscription_message = {
                "action": "subscribe",
                "symbols": test_symbols
            }
            
            start_time = time.time()
            await websocket.send(json.dumps(subscription_message))
            
            # Wait for subscription confirmation
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "subscribed":
                        subscription_time = time.time() - start_time
                        results["subscription_successful"] = True
                        results["subscription_time_ms"] = subscription_time * 1000
                        self.metrics.increment_message_count("subscribed")
                        logger.info(f"Subscription confirmed for: {data.get('symbols', [])}")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("Subscription confirmation timeout")
                    break
                    
            # Listen for quote data
            quote_start_time = time.time()
            while time.time() - quote_start_time < 15:  # Listen for 15 seconds
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "quote":
                        results["quote_data_received"] = True
                        results["quotes_received"] += 1
                        self.metrics.increment_message_count("quote")
                        
                        quote_data = data.get("data", {})
                        symbol = quote_data.get("symbol")
                        price = quote_data.get("price")
                        logger.info(f"Quote received: {symbol} @ ${price}")
                        
                except asyncio.TimeoutError:
                    continue
                    
            # Test unsubscription
            unsubscription_message = {
                "action": "unsubscribe",
                "symbols": ["AAPL"]
            }
            
            await websocket.send(json.dumps(unsubscription_message))
            
            # Wait for unsubscription confirmation
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                if data.get("type") == "unsubscribed":
                    results["unsubscription_successful"] = True
                    self.metrics.increment_message_count("unsubscribed")
                    logger.info("Unsubscription confirmed")
                    
            except asyncio.TimeoutError:
                logger.warning("Unsubscription confirmation timeout")
                
            await websocket.close()
            
        except Exception as e:
            logger.error(f"Subscription test failed: {str(e)}")
            results["error"] = str(e)
            self.metrics.increment_error_count("subscription_failed")
            
        return results
    
    async def test_ping_pong(self) -> Dict[str, Any]:
        """Test ping/pong functionality and measure latency."""
        logger.info("Testing ping/pong functionality...")
        
        results = {
            "ping_successful": False,
            "avg_latency_ms": 0,
            "min_latency_ms": 0,
            "max_latency_ms": 0,
            "pings_sent": 0,
            "pongs_received": 0,
            "error": None
        }
        
        try:
            websocket = await websockets.connect(self.ws_url)
            await websocket.recv()  # Welcome message
            
            latencies = []
            pings_sent = 0
            pongs_received = 0
            
            # Send multiple pings
            for i in range(10):
                ping_start = time.time()
                ping_message = {"action": "ping"}
                await websocket.send(json.dumps(ping_message))
                pings_sent += 1
                
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "pong":
                        latency = time.time() - ping_start
                        latencies.append(latency)
                        pongs_received += 1
                        self.metrics.record_message_latency(latency)
                        self.metrics.increment_message_count("pong")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Ping {i+1} timeout")
                    
                await asyncio.sleep(0.5)  # Wait between pings
                
            if latencies:
                results["ping_successful"] = True
                results["avg_latency_ms"] = statistics.mean(latencies) * 1000
                results["min_latency_ms"] = min(latencies) * 1000
                results["max_latency_ms"] = max(latencies) * 1000
                
            results["pings_sent"] = pings_sent
            results["pongs_received"] = pongs_received
            
            await websocket.close()
            logger.info(f"Ping/pong test: {pongs_received}/{pings_sent} successful")
            
        except Exception as e:
            logger.error(f"Ping/pong test failed: {str(e)}")
            results["error"] = str(e)
            self.metrics.increment_error_count("ping_pong_failed")
            
        return results
    
    async def test_multiple_connections(self, num_connections: int = 5) -> Dict[str, Any]:
        """Test multiple concurrent WebSocket connections."""
        logger.info(f"Testing {num_connections} concurrent connections...")
        
        results = {
            "target_connections": num_connections,
            "successful_connections": 0,
            "failed_connections": 0,
            "all_received_welcome": False,
            "concurrent_quotes_working": False,
            "connection_times": [],
            "error": None
        }
        
        try:
            connections = []
            tasks = []
            
            # Establish multiple connections
            for i in range(num_connections):
                try:
                    start_time = time.time()
                    websocket = await websockets.connect(self.ws_url)
                    connection_time = time.time() - start_time
                    
                    connections.append(websocket)
                    results["successful_connections"] += 1
                    results["connection_times"].append(connection_time * 1000)
                    self.metrics.record_connection_time(connection_time)
                    
                    logger.info(f"Connection {i+1} established")
                    
                except Exception as e:
                    logger.error(f"Connection {i+1} failed: {str(e)}")
                    results["failed_connections"] += 1
                    self.metrics.increment_error_count("concurrent_connection_failed")
                    
            # Check welcome messages
            welcome_count = 0
            for i, websocket in enumerate(connections):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    if data.get("type") == "connected":
                        welcome_count += 1
                        
                except Exception as e:
                    logger.warning(f"No welcome message from connection {i+1}")
                    
            results["all_received_welcome"] = welcome_count == len(connections)
            
            # Subscribe each connection to different symbols
            symbols_list = [["AAPL"], ["GOOGL"], ["MSFT"], ["TSLA"], ["AMZN"]]
            for i, websocket in enumerate(connections):
                if i < len(symbols_list):
                    subscription_message = {
                        "action": "subscribe",
                        "symbols": symbols_list[i]
                    }
                    await websocket.send(json.dumps(subscription_message))
                    
            # Listen for quotes on all connections
            async def listen_for_quotes(websocket, connection_id):
                quotes_received = 0
                try:
                    for _ in range(10):  # Listen for up to 10 messages
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        if data.get("type") == "quote":
                            quotes_received += 1
                except:
                    pass
                return quotes_received
                
            # Start listening tasks
            listen_tasks = []
            for i, websocket in enumerate(connections):
                task = asyncio.create_task(listen_for_quotes(websocket, i))
                listen_tasks.append(task)
                
            # Wait for listening to complete
            quote_results = await asyncio.gather(*listen_tasks, return_exceptions=True)
            total_quotes = sum(r for r in quote_results if isinstance(r, int))
            results["concurrent_quotes_working"] = total_quotes > 0
            
            # Clean up connections
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass
                    
            logger.info(f"Multiple connections test: {results['successful_connections']}/{num_connections} successful")
            
        except Exception as e:
            logger.error(f"Multiple connections test failed: {str(e)}")
            results["error"] = str(e)
            self.metrics.increment_error_count("multiple_connections_failed")
            
        return results
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and malformed message processing."""
        logger.info("Testing error handling...")
        
        results = {
            "invalid_json_handled": False,
            "invalid_action_handled": False,
            "invalid_symbols_handled": False,
            "connection_survives_errors": False,
            "error_messages_received": 0,
            "error": None
        }
        
        try:
            websocket = await websockets.connect(self.ws_url)
            await websocket.recv()  # Welcome message
            
            # Test 1: Invalid JSON
            try:
                await websocket.send("invalid json {")
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                if data.get("type") == "error" and "Invalid JSON" in data.get("message", ""):
                    results["invalid_json_handled"] = True
                    results["error_messages_received"] += 1
                    self.metrics.increment_message_count("error")
                    
            except Exception as e:
                logger.warning(f"Invalid JSON test failed: {str(e)}")
                
            # Test 2: Invalid action
            try:
                invalid_action_message = {"action": "invalid_action"}
                await websocket.send(json.dumps(invalid_action_message))
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                if data.get("type") == "error" and "Unknown action" in data.get("message", ""):
                    results["invalid_action_handled"] = True
                    results["error_messages_received"] += 1
                    self.metrics.increment_message_count("error")
                    
            except Exception as e:
                logger.warning(f"Invalid action test failed: {str(e)}")
                
            # Test 3: Invalid symbols format
            try:
                invalid_symbols_message = {"action": "subscribe", "symbols": "not_a_list"}
                await websocket.send(json.dumps(invalid_symbols_message))
                # This might not generate an error response, but shouldn't crash
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Invalid symbols test failed: {str(e)}")
                
            # Test 4: Check if connection is still alive after errors
            try:
                ping_message = {"action": "ping"}
                await websocket.send(json.dumps(ping_message))
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                if data.get("type") == "pong":
                    results["connection_survives_errors"] = True
                    
            except Exception as e:
                logger.warning(f"Connection survival test failed: {str(e)}")
                
            await websocket.close()
            logger.info("Error handling test completed")
            
        except Exception as e:
            logger.error(f"Error handling test failed: {str(e)}")
            results["error"] = str(e)
            self.metrics.increment_error_count("error_handling_failed")
            
        return results
    
    async def test_performance_under_load(self) -> Dict[str, Any]:
        """Test performance under load conditions."""
        logger.info("Testing performance under load...")
        
        results = {
            "test_duration_seconds": 30,
            "messages_sent": 0,
            "messages_received": 0,
            "avg_latency_ms": 0,
            "max_memory_mb": 0,
            "avg_cpu_percent": 0,
            "errors_encountered": 0,
            "error": None
        }
        
        try:
            websocket = await websockets.connect(self.ws_url)
            await websocket.recv()  # Welcome message
            
            # Subscribe to multiple symbols
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
            subscription_message = {"action": "subscribe", "symbols": symbols}
            await websocket.send(json.dumps(subscription_message))
            
            # Wait for subscription confirmation
            await websocket.recv()
            
            test_duration = 30  # 30 seconds
            start_time = time.time()
            messages_sent = 0
            messages_received = 0
            latencies = []
            
            # Performance monitoring task
            async def monitor_performance():
                while time.time() - start_time < test_duration:
                    self.metrics.record_system_metrics()
                    await asyncio.sleep(1)
                    
            monitor_task = asyncio.create_task(monitor_performance())
            
            # Message handling task
            async def handle_messages():
                nonlocal messages_received
                try:
                    while time.time() - start_time < test_duration:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        messages_received += 1
                        self.metrics.increment_message_count(data.get("type", "unknown"))
                        
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    results["errors_encountered"] += 1
                    self.metrics.increment_error_count("performance_test_error")
                    
            message_task = asyncio.create_task(handle_messages())
            
            # Send periodic status requests to generate load
            while time.time() - start_time < test_duration:
                try:
                    ping_start = time.time()
                    status_message = {"action": "status"}
                    await websocket.send(json.dumps(status_message))
                    messages_sent += 1
                    
                    # Don't wait for specific response in load test
                    await asyncio.sleep(2)  # Send every 2 seconds
                    
                except Exception as e:
                    results["errors_encountered"] += 1
                    self.metrics.increment_error_count("performance_test_error")
                    
            # Wait for tasks to complete
            monitor_task.cancel()
            message_task.cancel()
            
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
                
            try:
                await message_task
            except asyncio.CancelledError:
                pass
            
            # Calculate results
            results["messages_sent"] = messages_sent
            results["messages_received"] = messages_received
            
            if self.metrics.memory_usage:
                results["max_memory_mb"] = max(self.metrics.memory_usage)
                results["avg_cpu_percent"] = statistics.mean(self.metrics.cpu_usage) if self.metrics.cpu_usage else 0
                
            if self.metrics.message_latencies:
                results["avg_latency_ms"] = statistics.mean(self.metrics.message_latencies) * 1000
                
            await websocket.close()
            logger.info("Performance test completed")
            
        except Exception as e:
            logger.error(f"Performance test failed: {str(e)}")
            results["error"] = str(e)
            self.metrics.increment_error_count("performance_test_failed")
            
        return results
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all WebSocket tests and return comprehensive results."""
        logger.info("Starting comprehensive WebSocket test suite...")
        
        self.metrics.start_test()
        
        test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "websocket_url": self.ws_url,
            "tests": {}
        }
        
        # Test REST endpoints first
        test_results["tests"]["rest_endpoints"] = await self.test_rest_endpoints()
        
        # Basic connection test
        test_results["tests"]["basic_connection"] = await self.test_basic_connection()
        
        # Subscription functionality
        test_results["tests"]["subscription_functionality"] = await self.test_subscription_functionality()
        
        # Ping/pong functionality
        test_results["tests"]["ping_pong"] = await self.test_ping_pong()
        
        # Multiple connections
        test_results["tests"]["multiple_connections"] = await self.test_multiple_connections(5)
        
        # Error handling
        test_results["tests"]["error_handling"] = await self.test_error_handling()
        
        # Performance under load
        test_results["tests"]["performance_under_load"] = await self.test_performance_under_load()
        
        self.metrics.end_test()
        
        # Add comprehensive metrics
        test_results["metrics"] = self.metrics.get_summary()
        
        # Calculate overall health score
        test_results["overall_health_score"] = self._calculate_health_score(test_results)
        
        return test_results
    
    def _calculate_health_score(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate an overall health score based on test results."""
        scores = {}
        total_score = 0
        max_score = 0
        
        tests = test_results.get("tests", {})
        
        # Basic connection (20 points)
        basic = tests.get("basic_connection", {})
        if basic.get("connection_successful") and basic.get("welcome_message_received"):
            scores["connection"] = 20
        elif basic.get("connection_successful"):
            scores["connection"] = 15
        else:
            scores["connection"] = 0
        max_score += 20
        
        # Subscription functionality (25 points)
        subscription = tests.get("subscription_functionality", {})
        sub_score = 0
        if subscription.get("subscription_successful"):
            sub_score += 10
        if subscription.get("quote_data_received"):
            sub_score += 10
        if subscription.get("unsubscription_successful"):
            sub_score += 5
        scores["subscription"] = sub_score
        max_score += 25
        
        # Ping/pong (15 points)
        ping_pong = tests.get("ping_pong", {})
        if ping_pong.get("ping_successful") and ping_pong.get("pongs_received", 0) >= 8:
            scores["ping_pong"] = 15
        elif ping_pong.get("ping_successful"):
            scores["ping_pong"] = 10
        else:
            scores["ping_pong"] = 0
        max_score += 15
        
        # Multiple connections (15 points)
        multi = tests.get("multiple_connections", {})
        if multi.get("successful_connections", 0) >= 4:
            scores["multiple_connections"] = 15
        elif multi.get("successful_connections", 0) >= 2:
            scores["multiple_connections"] = 10
        else:
            scores["multiple_connections"] = 0
        max_score += 15
        
        # Error handling (10 points)
        error_handling = tests.get("error_handling", {})
        error_score = 0
        if error_handling.get("invalid_json_handled"):
            error_score += 3
        if error_handling.get("invalid_action_handled"):
            error_score += 3
        if error_handling.get("connection_survives_errors"):
            error_score += 4
        scores["error_handling"] = error_score
        max_score += 10
        
        # Performance (15 points)
        performance = tests.get("performance_under_load", {})
        perf_score = 0
        if performance.get("messages_received", 0) > 0:
            perf_score += 5
        if performance.get("avg_latency_ms", 1000) < 100:
            perf_score += 5
        elif performance.get("avg_latency_ms", 1000) < 500:
            perf_score += 3
        if performance.get("errors_encountered", 100) < 5:
            perf_score += 5
        scores["performance"] = perf_score
        max_score += 15
        
        total_score = sum(scores.values())
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Determine health status
        if percentage >= 90:
            status = "EXCELLENT"
        elif percentage >= 75:
            status = "GOOD"
        elif percentage >= 60:
            status = "FAIR"
        elif percentage >= 40:
            status = "POOR"
        else:
            status = "CRITICAL"
            
        return {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "status": status,
            "category_scores": scores
        }


async def main():
    """Main function to run comprehensive WebSocket tests."""
    logger.info("=" * 60)
    logger.info("COMPREHENSIVE WEBSOCKET STREAMING FUNCTIONALITY TESTS")
    logger.info("=" * 60)
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/streaming/status", timeout=5.0)
            if response.status_code != 200:
                logger.error("Server is not responding correctly. Please ensure the FastAPI server is running.")
                return
    except Exception as e:
        logger.error(f"Cannot connect to server: {str(e)}")
        logger.error("Please ensure the FastAPI server is running on localhost:8000")
        return
    
    tester = ComprehensiveWebSocketTester()
    
    try:
        # Run all tests
        results = await tester.run_comprehensive_tests()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"websocket_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        logger.info(f"Test results saved to: {results_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("WEBSOCKET STREAMING TEST RESULTS SUMMARY")
        print("=" * 80)
        
        health = results.get("overall_health_score", {})
        print(f"Overall Health Score: {health.get('total_score', 0)}/{health.get('max_score', 0)} ({health.get('percentage', 0):.1f}%)")
        print(f"Health Status: {health.get('status', 'UNKNOWN')}")
        
        print("\nTest Results:")
        for test_name, test_result in results.get("tests", {}).items():
            if isinstance(test_result, dict):
                success_indicators = [
                    test_result.get("connection_successful"),
                    test_result.get("subscription_successful"),
                    test_result.get("ping_successful"),
                    test_result.get("all_received_welcome"),
                    test_result.get("connection_survives_errors"),
                    test_result.get("messages_received", 0) > 0
                ]
                success = any(success_indicators) and not test_result.get("error")
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  {test_name}: {status}")
                if test_result.get("error"):
                    print(f"    Error: {test_result['error']}")
        
        print("\nPerformance Metrics:")
        metrics = results.get("metrics", {})
        conn_metrics = metrics.get("connection_metrics", {})
        latency_metrics = metrics.get("message_latency_metrics", {})
        system_metrics = metrics.get("system_metrics", {})
        
        print(f"  Average Connection Time: {conn_metrics.get('avg_time_ms', 0):.1f}ms")
        print(f"  Average Message Latency: {latency_metrics.get('avg_latency_ms', 0):.1f}ms")
        print(f"  Peak Memory Usage: {system_metrics.get('max_memory_mb', 0):.1f}MB")
        print(f"  Average CPU Usage: {system_metrics.get('avg_cpu_percent', 0):.1f}%")
        
        message_counts = metrics.get("message_counts", {})
        print(f"  Messages Processed: {sum(message_counts.values())}")
        
        error_counts = metrics.get("error_counts", {})
        total_errors = sum(error_counts.values())
        print(f"  Total Errors: {total_errors}")
        
        print("\n" + "=" * 80)
        
        # Return results for further processing if needed
        return results
        
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())