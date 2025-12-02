#!/bin/bash
#
# Elson Wealth Trading Platform - External Access Setup Script
#
# This script sets up external access to the local beta environment using ngrok
# It provides a public URL that beta testers can use to access the application
#

set -e

echo "================================================================================"
echo "           ELSON WEALTH TRADING PLATFORM - EXTERNAL ACCESS SETUP               "
echo "================================================================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok is required but not installed."
    echo "    Please install ngrok first: https://ngrok.com/download"
    echo "    On Mac, you can use: brew install ngrok"
    exit 1
fi

# Check if the beta environment is running
if ! docker ps | grep -q "elson_nginx_beta"; then
    echo "❌ Error: Beta environment doesn't appear to be running."
    echo "    Please start the beta environment first using:"
    echo "    ./launch-beta.sh (select option 1)"
    exit 1
fi

# Create ngrok configuration if it doesn't exist
NGROK_CONFIG_DIR="$HOME/.ngrok2"
NGROK_CONFIG="$NGROK_CONFIG_DIR/ngrok.yml"

if [ ! -f "$NGROK_CONFIG" ]; then
    mkdir -p "$NGROK_CONFIG_DIR"
    echo "Creating ngrok configuration file at $NGROK_CONFIG"
    cat > "$NGROK_CONFIG" << EOF
version: "2"
web_addr: 127.0.0.1:4040
tunnels:
  elson-beta:
    proto: http
    addr: 443
    bind_tls: true
EOF
    echo "✅ Ngrok configuration created."
fi

# Check if we need to add authtoken
if ! grep -q "authtoken:" "$NGROK_CONFIG"; then
    echo ""
    echo "Ngrok requires authentication for longer sessions."
    echo "Sign up at https://ngrok.com/ and get your authtoken."
    echo ""
    read -p "Enter your ngrok authtoken (leave empty to skip): " authtoken
    
    if [ ! -z "$authtoken" ]; then
        echo "authtoken: $authtoken" >> "$NGROK_CONFIG"
        echo "✅ Authtoken added to configuration."
    else
        echo "⚠️ No authtoken provided. The tunnel may expire after a few hours."
    fi
fi

# Start ngrok tunnel
echo ""
echo "Starting ngrok tunnel..."
echo "This will provide an external URL for accessing your local beta environment."
echo ""

# Get IP address for informational purposes
IP_ADDRESS=$(curl -s https://ipinfo.io/ip)
echo "Your public IP address: $IP_ADDRESS"
echo ""

# Start ngrok in the background
ngrok start --config="$NGROK_CONFIG" --all > /dev/null &
NGROK_PID=$!

# Wait for ngrok to start
sleep 5

# Get tunnel information
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https:[^"]*' | grep -o 'https:[^"]*')

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ Error: Failed to retrieve ngrok tunnel URL."
    echo "    Check if ngrok is running correctly with: ngrok start --config=$NGROK_CONFIG --all"
    exit 1
fi

echo "================================================================================"
echo "✅ External access setup successfully!"
echo ""
echo "🚀 External beta access URL: $TUNNEL_URL"
echo ""
echo "📋 Instructions for beta testers:"
echo "1. Visit $TUNNEL_URL in your browser"
echo "2. Ignore any SSL certificate warnings (this is expected)"
echo "3. Proceed to use the beta application as normal"
echo ""
echo "📱 Web dashboard: http://localhost:4040"
echo ""
echo "⚠️ IMPORTANT: Keep this terminal window open to maintain the tunnel"
echo "   Press Ctrl+C to stop the tunnel when you're done"
echo "================================================================================"

# Write access info to a file for reference
ACCESS_INFO_FILE="beta_external_access.txt"
cat > "$ACCESS_INFO_FILE" << EOF
ELSON WEALTH BETA - EXTERNAL ACCESS INFORMATION
===============================================

External URL: $TUNNEL_URL
Created: $(date)
Public IP: $IP_ADDRESS

Instructions for beta testers:
1. Visit the URL above in your browser
2. Ignore any SSL certificate warnings (this is expected with ngrok)
3. Proceed to use the beta application as normal

Note: This URL is temporary and will change each time ngrok is restarted.
EOF

echo "Access information saved to $ACCESS_INFO_FILE"

# Wait for user to press Ctrl+C
trap "echo 'Stopping ngrok tunnel...'; kill $NGROK_PID; exit" INT TERM
wait $NGROK_PID