#!/usr/bin/env python
"""
Run the WebSocket server for market data streaming.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.websocket_server:app", host="0.0.0.0", port=8001, reload=True)