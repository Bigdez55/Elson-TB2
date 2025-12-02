#!/bin/bash

# Load environment variables
export $(grep -v '^#' .env.test | xargs)

# Run WebSocket server
python run_websocket.py