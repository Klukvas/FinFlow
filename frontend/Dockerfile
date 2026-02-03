FROM node:20-alpine AS builder
WORKDIR /app

# Build arguments for feature flags
ARG VITE_PAYMENTS_ENABLED=false

# Install dependencies first (better cache)
COPY frontend/package.json frontend/yarn.lock ./
# Install dependencies (regenerate lockfile if needed)
RUN yarn install

# Copy source and build
COPY frontend/ .

# Set environment variables for build
ENV VITE_PAYMENTS_ENABLED=${VITE_PAYMENTS_ENABLED}

RUN yarn build

FROM nginx:alpine

# Copy custom nginx configuration for SPA routing
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend assets from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


