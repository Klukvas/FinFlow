# Accounting App Frontend

A modern React TypeScript application for financial accounting with category and expense management.

## Features

- 🔐 **Authentication** - User login and registration
- 📊 **Dashboard** - Financial overview with charts and analytics
- 📁 **Category Management** - Hierarchical category organization
- 💰 **Expense Tracking** - Record and manage expenses
- 🎨 **Modern UI** - Built with Tailwind CSS and React Icons
- 🛡️ **Type Safety** - Full TypeScript support
- ⚡ **Performance** - Optimized with Vite and code splitting

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Client-side routing
- **React Icons** - Icon library
- **Recharts** - Data visualization

## Prerequisites

- Node.js >= 18.0.0
- Yarn >= 1.22.0

## Getting Started

1. **Install dependencies:**
   ```bash
   yarn install
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   VITE_API_BASE_URL=http://localhost:8001
   VITE_CATEGORY_SERVICE_URL=http://localhost:8002
   VITE_EXPENSE_SERVICE_URL=http://localhost:8003
   VITE_APP_NAME=Financial Accounting
   VITE_DEBUG=true
   ```

3. **Start development server:**
   ```bash
   yarn dev
   ```

4. **Build for production:**
   ```bash
   yarn build
   ```

5. **Preview production build:**
   ```bash
   yarn preview
   ```

## Available Scripts

- `yarn dev` - Start development server
- `yarn build` - Build for production
- `yarn preview` - Preview production build
- `yarn lint` - Run ESLint
- `yarn lint:fix` - Fix ESLint issues
- `yarn type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI components
│   └── ErrorBoundary.tsx
├── config/             # Configuration files
├── hooks/              # Custom React hooks
├── pages/              # Page components
├── services/           # API services
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

## Code Quality

This project follows modern React and TypeScript best practices:

- **TypeScript** - Strict type checking enabled
- **ESLint** - Code linting with React-specific rules
- **Error Boundaries** - Graceful error handling
- **Custom Hooks** - Reusable logic extraction
- **Environment Configuration** - Centralized config management
- **Code Splitting** - Optimized bundle sizes

## Contributing

1. Follow the existing code style
2. Add TypeScript types for all new code
3. Write meaningful commit messages
4. Test your changes thoroughly
5. Update documentation as needed