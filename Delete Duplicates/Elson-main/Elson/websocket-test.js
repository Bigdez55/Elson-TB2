// Elson WebSocket Test Script
// Run with Node.js: node websocket-test.js

const WebSocket = require('ws');

// Configuration
const SERVER_URL = 'ws://localhost:8000/ws/market/feed';
const TOKEN = null; // Optional JWT token
const SYMBOLS = ['AAPL', 'MSFT', 'GOOGL'];
const TIMEOUT = 30000; // 30 seconds

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

console.log(`${colors.cyan}Elson WebSocket Market Data Test${colors.reset}`);
console.log(`${colors.yellow}Server URL:${colors.reset} ${SERVER_URL}`);
console.log(`${colors.yellow}Auth:${colors.reset} ${TOKEN ? 'Using token' : 'No token'}`);
console.log(`${colors.yellow}Test symbols:${colors.reset} ${SYMBOLS.join(', ')}`);
console.log(`${colors.yellow}Timeout:${colors.reset} ${TIMEOUT / 1000} seconds\n`);

// Create connection URL
const url = TOKEN ? `${SERVER_URL}?token=${encodeURIComponent(TOKEN)}` : SERVER_URL;

// Connect to WebSocket
console.log(`${colors.blue}Connecting to server...${colors.reset}`);
const ws = new WebSocket(url);

// Set timeout
const timeoutId = setTimeout(() => {
    console.log(`${colors.red}Test timed out after ${TIMEOUT / 1000} seconds${colors.reset}`);
    ws.close();
    process.exit(1);
}, TIMEOUT);

// Message count tracking
let messagesSent = 0;
let messagesReceived = 0;

// Track test stages
const stages = [
    { name: 'Connect', completed: false },
    { name: 'Subscribe', completed: false },
    { name: 'Receive Data', completed: false, required: 3 }, // Need at least 3 data points
    { name: 'Ping/Pong', completed: false },
    { name: 'Unsubscribe', completed: false },
    { name: 'Disconnect', completed: false }
];

// Track subscription data
let dataReceived = {};
SYMBOLS.forEach(symbol => {
    dataReceived[symbol] = 0;
});

// Log a message with timestamp
function log(message, color = colors.reset) {
    const timestamp = new Date().toISOString();
    console.log(`${colors.yellow}[${timestamp}]${colors.reset} ${color}${message}${colors.reset}`);
}

// Send a message to the server
function sendMessage(message) {
    if (ws.readyState !== WebSocket.OPEN) {
        log(`Cannot send message, connection not open`, colors.red);
        return;
    }
    
    const messageStr = JSON.stringify(message);
    ws.send(messageStr);
    messagesSent++;
    log(`SENT: ${messageStr}`, colors.blue);
}

// Update test stage
function updateStage(stageName, completed = true) {
    const stage = stages.find(s => s.name === stageName);
    if (stage) {
        stage.completed = completed;
        log(`Test stage ${completed ? 'COMPLETED' : 'STARTED'}: ${stageName}`, colors.green);
    }
}

// Check if all test stages are completed
function checkAllStagesCompleted() {
    const allCompleted = stages.every(stage => stage.completed);
    if (allCompleted) {
        clearTimeout(timeoutId);
        log(`All test stages completed successfully!`, colors.green);
        log(`Messages sent: ${messagesSent}, received: ${messagesReceived}`, colors.green);
        
        // Print data received per symbol
        log(`Data points received per symbol:`, colors.green);
        Object.keys(dataReceived).forEach(symbol => {
            log(`  ${symbol}: ${dataReceived[symbol]} data points`, colors.green);
        });
        
        ws.close();
        process.exit(0);
    }
}

// Check data received stage
function checkDataReceivedStage() {
    const dataPointsReceived = Object.values(dataReceived).reduce((a, b) => a + b, 0);
    const requiredPoints = stages.find(s => s.name === 'Receive Data').required;
    
    if (dataPointsReceived >= requiredPoints && !stages.find(s => s.name === 'Receive Data').completed) {
        updateStage('Receive Data');
        
        // Move to next stage - ping
        sendMessage({ action: 'ping' });
    }
}

// Connection opened
ws.on('open', () => {
    log(`Connected to server`, colors.green);
    updateStage('Connect');
    
    // Subscribe to symbols
    log(`Subscribing to symbols: ${SYMBOLS.join(', ')}`, colors.blue);
    sendMessage({
        action: 'subscribe',
        symbols: SYMBOLS
    });
});

// Message received
ws.on('message', (data) => {
    messagesReceived++;
    
    try {
        const message = JSON.parse(data.toString());
        log(`RECEIVED: ${JSON.stringify(message, null, 2)}`, colors.cyan);
        
        // Handle subscription confirmation
        if (message.type === 'subscribed') {
            updateStage('Subscribe');
            log(`Successfully subscribed to ${message.symbols.length} symbols`, colors.green);
        }
        // Handle unsubscription confirmation
        else if (message.type === 'unsubscribed') {
            updateStage('Unsubscribe');
            
            // All done, close connection
            log(`Test completed successfully, closing connection`, colors.green);
            updateStage('Disconnect');
            checkAllStagesCompleted();
        }
        // Handle pong response
        else if (message.type === 'pong') {
            updateStage('Ping/Pong');
            
            // Move to next stage - unsubscribe
            log(`Unsubscribing from symbols: ${SYMBOLS.join(', ')}`, colors.blue);
            sendMessage({
                action: 'unsubscribe',
                symbols: SYMBOLS
            });
        }
        // Handle market data
        else if (message.symbol && SYMBOLS.includes(message.symbol)) {
            dataReceived[message.symbol]++;
            log(`Received data for ${message.symbol}: $${message.price}`, colors.cyan);
            checkDataReceivedStage();
        }
        
    } catch (error) {
        log(`Error parsing message: ${error.message}`, colors.red);
        log(`Raw message: ${data}`, colors.red);
    }
});

// Connection error
ws.on('error', (error) => {
    log(`WebSocket error: ${error.message}`, colors.red);
});

// Connection closed
ws.on('close', (code, reason) => {
    log(`Connection closed: ${reason || 'No reason provided'} (Code: ${code})`, colors.yellow);
    
    if (!stages.find(s => s.name === 'Disconnect').completed) {
        log(`Test did not complete all stages`, colors.red);
        process.exit(1);
    }
});

// Handle exit signals
process.on('SIGINT', () => {
    log(`Test interrupted by user`, colors.yellow);
    ws.close();
    process.exit(1);
});