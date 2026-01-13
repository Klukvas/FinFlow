# Admin Panel

React-based administration panel for managing users and subscription plans.

## Features

- **User Management**: View, search, and manage user accounts
  - Assign/revoke admin roles
  - Enable/disable user accounts
- **Subscription Management**: Manage subscription plans
  - Create/edit plans
  - Configure feature toggles per plan

## Prerequisites

- Node.js 18+
- Running backend services:
  - `user_service` (port 8001)
  - `subscription_service` (port 8011)

## Setup

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Copy environment config:
```bash
cp .env.example .env
```

3. Adjust `.env` if needed (default values point to localhost)

4. Run development server:
```bash
npm run dev
# or
yarn dev
```

5. Open http://localhost:3001

## Authentication

Only users with `role: "admin"` can access this panel. Login with admin credentials.

### Creating an Admin User

To create an admin user, first create a regular user in the main app, then update their role via database:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

Or use the API (requires existing admin):
```bash
curl -X PATCH http://localhost:8001/admin/users/{user_id}/role \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

## Tech Stack

- React 18
- TypeScript
- Vite
- TanStack Query (React Query)
- React Router v6
- Tailwind CSS

## Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── Layout.tsx     # Admin layout with sidebar
│   └── ProtectedRoute.tsx
├── config/
│   └── env.ts         # Environment configuration
├── contexts/
│   └── AuthContext.tsx # Authentication state
├── pages/
│   ├── Login.tsx      # Admin login
│   ├── Users.tsx      # User management
│   └── Subscription.tsx # Plan management
├── services/
│   ├── httpClient.ts  # Base HTTP client
│   ├── userService.ts # User API calls
│   └── subscriptionService.ts # Subscription API calls
├── types/
│   └── index.ts       # TypeScript interfaces
└── App.tsx            # Main app with routes
```

## API Endpoints Used

### User Service
- `POST /auth/login` - Admin login
- `GET /auth/me` - Get current user (with role)
- `GET /admin/users` - List users (admin only)
- `GET /admin/users/:id` - Get user details
- `PATCH /admin/users/:id/role` - Update user role
- `PATCH /admin/users/:id/status` - Update user status

### Subscription Service
- `GET /v1/admin/plans` - List all plans
- `POST /v1/admin/plans` - Create plan
- `PATCH /v1/admin/plans/:id` - Update plan
- `PATCH /v1/admin/plans/:id/features` - Update plan features
- `GET /v1/admin/features` - List all features
