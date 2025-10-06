FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies first (better cache)
COPY package.json yarn.lock ./
# Use Corepack to ensure Yarn 4 per packageManager field
RUN corepack enable && corepack prepare yarn@4.0.0 --activate \
    && yarn install --immutable

# Copy source and build
COPY . .
RUN yarn build

FROM nginx:alpine

# Copy built frontend assets from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


