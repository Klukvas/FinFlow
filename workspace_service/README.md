# Workspace Service

Microservice for workspace and group management in the accounting application.

## Overview

The workspace_service is the single source of truth for:
- **Workspaces** (personal & shared)
- **Memberships and roles**
- **Invitations**
- **Access validation** for domain services (category, expense, account, etc.)

A workspace is a data container. A group is simply a workspace with more than one member.

## Features

- Create and manage workspaces (personal and shared)
- Member management with role-based access control
- Invite system with secure tokens
- Archive/unarchive workspaces
- Ownership transfer
- Internal API for domain services to validate access

## Roles & Permissions

| Role   | Permissions                                    |
|--------|-----------------------------------------------|
| owner  | Full access, transfer ownership, archive workspace |
| admin  | Manage members & invites                      |
| member | Read/write domain data                        |
| viewer | Read-only domain data                         |

## API Endpoints

### Public API (Frontend/BFF)

#### Workspaces
- `POST /workspaces` - Create a new workspace
- `GET /workspaces` - List user workspaces
- `GET /workspaces/{workspace_id}` - Get workspace details
- `PATCH /workspaces/{workspace_id}` - Update workspace (rename)
- `POST /workspaces/{workspace_id}:archive` - Archive workspace
- `POST /workspaces/{workspace_id}:unarchive` - Unarchive workspace
- `POST /workspaces/{workspace_id}:leave` - Leave workspace
- `POST /workspaces/{workspace_id}/owner:transfer` - Transfer ownership

#### Members
- `GET /workspaces/{workspace_id}/members` - List workspace members
- `PATCH /workspaces/{workspace_id}/members/{user_id}` - Update member role
- `DELETE /workspaces/{workspace_id}/members/{user_id}` - Remove member

#### Invites
- `POST /workspaces/{workspace_id}/invites` - Create invite
- `GET /workspaces/{workspace_id}/invites` - List pending invites
- `DELETE /workspaces/{workspace_id}/invites/{invite_id}` - Revoke invite
- `POST /invites/{token}:accept` - Accept invite
- `POST /invites/{token}:decline` - Decline invite

### Internal API (Domain Services)

- `POST /internal/workspaces/{workspace_id}/authorize` - Check user authorization
- `GET /internal/users/{user_id}/workspaces` - Get user's workspaces
- `GET /internal/users/{user_id}/default-workspace` - Get default workspace
- `POST /internal/workspaces/personal` - Create personal workspace (registration)
- `GET /internal/workspaces/{workspace_id}/role/{user_id}` - Get user role

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `INTERNAL_SECRET_TOKEN` | Token for internal service auth | Required |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,...` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `INVITE_TOKEN_EXPIRE_DAYS` | Invite expiration in days | `7` |
| `USER_SERVICE_URL` | User service URL | `http://user_service:8000` |

## Database Schema

### workspaces
- `id` (UUID, PK)
- `name` (string)
- `type` (personal | shared)
- `owner_user_id` (int)
- `created_at`, `updated_at`, `archived_at`

### workspace_members
- `id` (int, PK)
- `workspace_id` (UUID, FK)
- `user_id` (int)
- `role` (owner | admin | member | viewer)
- `status` (active | left | removed)
- `joined_at`, `created_at`, `updated_at`

### workspace_invites
- `id` (UUID, PK)
- `workspace_id` (UUID, FK)
- `inviter_user_id` (int)
- `invitee_user_id` (int, nullable)
- `invitee_email` (string, nullable)
- `token_hash` (string)
- `expires_at` (datetime)
- `status` (pending | accepted | revoked | expired)
- `created_at`, `updated_at`, `accepted_at`

## Security

- Access requires active membership
- Only owner/admin can manage members
- Owner cannot be removed without ownership transfer
- Invite tokens are:
  - Hashed (SHA-256)
  - Expirable (default 7 days)
  - Single-use

## Running Locally

```bash
# Install dependencies
poetry install

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

## Docker

The service is configured in `docker-compose.yml` and runs on port `8012`.

```bash
docker-compose up workspace_service
```

## Integration with Other Services

During user registration, `user_service` should call:
```
POST /internal/workspaces/personal
{ "user_id": "..." }
```

This creates a personal workspace and returns the `workspace_id` for storage.

Domain services can validate access using:
```
POST /internal/workspaces/{workspace_id}/authorize
{ "user_id": "...", "required_role": "member" }
```

Returns `200` with role info or `403` if unauthorized.

