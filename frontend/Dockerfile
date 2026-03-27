FROM node:20-alpine AS builder
WORKDIR /app

# Build arguments for feature flags
ARG VITE_PAYMENTS_ENABLED=false
ARG VITE_SENTRY_DSN=""
ARG VITE_ENVIRONMENT=production

# Install dependencies first (better cache)
COPY frontend/package.json frontend/yarn.lock frontend/.npmrc ./
# Install dependencies using BuildKit secret mount for GitHub token
# The token never touches a layer — invisible to `docker history`
RUN --mount=type=secret,id=github_token \
    if [ -f /run/secrets/github_token ]; then \
      echo "//npm.pkg.github.com/:_authToken=$(cat /run/secrets/github_token)" >> .npmrc; \
    fi && \
    yarn install && \
    git_line=$(grep -n '_authToken' .npmrc | tail -1 | cut -d: -f1) && \
    if [ -n "$git_line" ]; then sed -i "${git_line}d" .npmrc; fi

# Copy source and build
COPY frontend/ .

# Set environment variables for build
ENV VITE_PAYMENTS_ENABLED=${VITE_PAYMENTS_ENABLED}
ENV VITE_SENTRY_DSN=${VITE_SENTRY_DSN}
ENV VITE_ENVIRONMENT=${VITE_ENVIRONMENT}

RUN yarn build

FROM nginx:alpine

# Copy custom nginx configuration for SPA routing
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend assets from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


