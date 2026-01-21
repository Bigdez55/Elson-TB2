#!/usr/bin/env python3
"""
Simple test client for the personal market streaming WebSocket service.

This script demonstrates how to connect to the WebSocket endpoint and
subscribe to real-time market data.
"""

import asyncio
import json
import logging
from typing import List

import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingTestClient:
    """Test client for market data streaming."""

    def __init__(self, ws_url: str = "ws://localhost:8000/api/v1/streaming/ws"):
        self.ws_url = ws_url
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.running = True
            logger.info(f"Connected to {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")

    async def send_message(self, message: dict):
        """Send a message to the server."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent: {message}")

    async def subscribe_to_symbols(self, symbols: List[str]):
        """Subscribe to market data for specified symbols."""
        message = {"action": "subscribe", "symbols": symbols}
        await self.send_message(message)

    async def unsubscribe_from_symbols(self, symbols: List[str]):
        """Unsubscribe from market data for specified symbols."""
        message = {"action": "unsubscribe", "symbols": symbols}
        await self.send_message(message)

    async def ping(self):
        """Send a ping message."""
        message = {"action": "ping"}
        await self.send_message(message)

    async def get_status(self):
        """Request status information."""
        message = {"action": "status"}
        await self.send_message(message)

    async def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type == "connected":
                    logger.info(f"✓ Connected: {data.get('message')}")

                elif message_type == "quote":
                    quote_data = data.get("data", {})
                    symbol = quote_data.get("symbol")
                    price = quote_data.get("price")
                    source = quote_data.get("source")
                    timestamp = quote_data.get("timestamp")
                    logger.info(
                        f"📈 {symbol}: ${price:.2f} (from {source}) at {timestamp}"
                    )

                elif message_type == "subscribed":
                    symbols = data.get("symbols", [])
                    logger.info(f"✓ Subscribed to: {', '.join(symbols)}")

                elif message_type == "unsubscribed":
                    symbols = data.get("symbols", [])
                    logger.info(f"✓ Unsubscribed from: {', '.join(symbols)}")

                elif message_type == "pong":
                    logger.info("🏓 Pong received")

                elif message_type == "status":
                    logger.info(f"📊 Status: {json.dumps(data, indent=2)}")

                elif message_type == "error":
                    logger.error(f"❌ Error: {data.get('message')}")

                else:
                    logger.info(f"📨 Received: {data}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error listening for messages: {str(e)}")

    async def run_interactive_demo(self):
        """Run an interactive demo of the streaming client."""
        if not await self.connect():
            return

        # Start listening for messages in the background
        listen_task = asyncio.create_task(self.listen_for_messages())

        try:
            logger.info("\n=== Interactive Market Streaming Demo ===")
            logger.info(
                "This demo will subscribe to some popular stocks and show real-time data"
            )

            # Wait for connection confirmation
            await asyncio.sleep(1)

            # Subscribe to some popular symbols
            demo_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
            logger.info(f"\nSubscribing to: {', '.join(demo_symbols)}")
            await self.subscribe_to_symbols(demo_symbols)

            # Wait for subscription confirmation
            await asyncio.sleep(2)

            # Get status
            logger.info("\nRequesting status...")
            await self.get_status()

            # Listen for real-time data for 30 seconds
            logger.info("\nListening for real-time market data for 30 seconds...")
            logger.info(
                "You should see price updates every 5 seconds (configured update interval)"
            )
            await asyncio.sleep(30)

            # Send a ping
            logger.info("\nSending ping...")
            await self.ping()
            await asyncio.sleep(1)

            # Unsubscribe from some symbols
            logger.info(f"\nUnsubscribing from TSLA and AMZN...")
            await self.unsubscribe_from_symbols(["TSLA", "AMZN"])
            await asyncio.sleep(2)

            # Get final status
            logger.info("\nGetting final status...")
            await self.get_status()
            await asyncio.sleep(2)

        except KeyboardInterrupt:
            logger.info("\nDemo interrupted by user")

        finally:
            listen_task.cancel()
            await self.disconnect()

    async def run_simple_test(self):
        """Run a simple test of basic functionality."""
        if not await self.connect():
            return

        # Start listening for messages in the background
        listen_task = asyncio.create_task(self.listen_for_messages())

        try:
            logger.info("\n=== Simple Streaming Test ===")

            # Wait for connection
            await asyncio.sleep(1)

            # Subscribe to AAPL
            await self.subscribe_to_symbols(["AAPL"])
            await asyncio.sleep(5)  # Listen for 5 seconds

            # Get status
            await self.get_status()
            await asyncio.sleep(1)

            # Ping test
            await self.ping()
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Test error: {str(e)}")

        finally:
            listen_task.cancel()
            await self.disconnect()


async def main():
    """Main function to run the test client."""
    import sys

    client = StreamingTestClient()

    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        await client.run_simple_test()
    else:
        await client.run_interactive_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest client interrupted by user")
    except Exception as e:
        print(f"Test client error: {str(e)}")
