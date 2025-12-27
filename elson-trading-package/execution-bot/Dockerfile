# Execution Bot Dockerfile
#
# This builds the TypeScript Execution Bot (Body)
# which listens to Redis signals and executes trades.

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Build TypeScript
RUN npm run build || true

# Run the bot
CMD ["npm", "start"]
