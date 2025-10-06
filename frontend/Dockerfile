FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies first (better cache)
COPY package.json yarn.lock ./
# Use Yarn Classic with frozen lockfile for deterministic installs
RUN yarn --version \
    && yarn install --frozen-lockfile

# Copy source and build
COPY . .
RUN yarn build

FROM nginx:alpine

# Copy built frontend assets from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


