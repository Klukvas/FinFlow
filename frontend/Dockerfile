FROM node:25-alpine AS builder
WORKDIR /app

# Install dependencies first (better cache)
COPY frontend/package.json frontend/yarn.lock ./
# Install dependencies (regenerate lockfile if needed)
RUN yarn install

# Copy source and build
COPY frontend/ .
RUN yarn build

FROM nginx:alpine

# Copy custom nginx configuration for SPA routing
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend assets from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


