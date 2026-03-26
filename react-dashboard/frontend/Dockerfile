# Build stage
FROM node:18-slim AS build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM node:18-slim

WORKDIR /app
COPY package*.json ./
RUN npm install --only=production

COPY --from=build /app/dist ./dist
COPY server.js ./

# Make port 8080 available to the world outside this container
EXPOSE 8080

CMD ["node", "server.js"]
