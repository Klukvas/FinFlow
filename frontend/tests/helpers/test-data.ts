// Define interfaces locally
interface UserCredentials {
  email: string;
  password: string;
}

interface CategoryData {
  name: string;
  description?: string;
  type: 'expense' | 'income';
  color?: string;
}

interface ExpenseData {
  amount: number;
  description: string;
  category: string;
  date: string;
  account?: string;
  tags?: string[];
}

// Test user credentials
export const TEST_USERS = {
  valid: {
    email: 'test@example.com',
    password: 'password123'
  } as UserCredentials,
  
  invalid: {
    email: 'invalid@example.com',
    password: 'wrongpassword'
  } as UserCredentials,
  
  admin: {
    email: 'admin@example.com',
    password: 'admin123'
  } as UserCredentials
};

// Test categories
export const TEST_CATEGORIES = {
  expense: {
    name: 'Test Expense Category',
    description: 'A test category for expenses',
    type: 'expense' as const,
    color: '#FF5733'
  } as CategoryData,
  
  income: {
    name: 'Test Income Category',
    description: 'A test category for income',
    type: 'income' as const,
    color: '#33FF57'
  } as CategoryData,
  
  food: {
    name: 'Food & Dining',
    description: 'Restaurants, groceries, and food expenses',
    type: 'expense' as const,
    color: '#FF6B6B'
  } as CategoryData,
  
  salary: {
    name: 'Salary',
    description: 'Monthly salary income',
    type: 'income' as const,
    color: '#4ECDC4'
  } as CategoryData
};

// Test expenses
export const TEST_EXPENSES = {
  small: {
    amount: 25.50,
    description: 'Small Test Expense',
    category: 'Test Expense Category',
    date: '2024-01-15',
    tags: ['test', 'small']
  } as ExpenseData,
  
  medium: {
    amount: 150.75,
    description: 'Medium Test Expense',
    category: 'Test Expense Category',
    date: '2024-01-16',
    tags: ['test', 'medium']
  } as ExpenseData,
  
  large: {
    amount: 999.99,
    description: 'Large Test Expense',
    category: 'Test Expense Category',
    date: '2024-01-17',
    tags: ['test', 'large']
  } as ExpenseData,
  
  food: {
    amount: 45.20,
    description: 'Lunch at Restaurant',
    category: 'Food & Dining',
    date: '2024-01-18',
    tags: ['food', 'restaurant']
  } as ExpenseData
};

// Test income
export const TEST_INCOME = {
  salary: {
    amount: 5000.00,
    description: 'Monthly Salary',
    category: 'Salary',
    date: '2024-01-01',
    tags: ['salary', 'monthly']
  } as ExpenseData
};

// Special characters test data
export const SPECIAL_CHARS_DATA = {
  category: {
    name: 'Category with Special Ch@rs! & Symbols',
    description: 'Description with émojis 🎉 and spëcial chars',
    type: 'expense' as const,
    color: '#FF5733'
  } as CategoryData,
  
  expense: {
    amount: 99.99,
    description: 'Expense with Special Ch@rs! & Symbols',
    category: 'Category with Special Ch@rs! & Symbols',
    date: '2024-01-15',
    tags: ['tëst', 'émojis 🎉']
  } as ExpenseData
};

// Validation test data
export const VALIDATION_DATA = {
  invalidEmails: [
    'invalid-email',
    '@example.com',
    'test@',
    'test.example.com',
    'test@.com',
    'test@example.',
    ''
  ],
  
  weakPasswords: [
    '123',
    'password',
    '12345678',
    'abc',
    'qwerty',
    ''
  ],
  
  invalidAmounts: [
    'abc',
    '-50',
    '0',
    '100.999',
    '',
    '100.1234'
  ],
  
  longStrings: {
    name: 'A'.repeat(256),
    description: 'B'.repeat(1001),
    tags: Array(101).fill('tag')
  }
};

// Date test data
export const DATE_DATA = {
  valid: [
    '2024-01-01',
    '2024-12-31',
    '2023-06-15'
  ],
  
  invalid: [
    '2024-13-01', // Invalid month
    '2024-01-32', // Invalid day
    '2024-02-30', // Invalid day for February
    '2024/01/01', // Wrong format
    '01-01-2024', // Wrong format
    '2024-1-1',   // Missing leading zeros
    ''
  ],
  
  future: '2030-01-01',
  past: '2020-01-01',
  today: new Date().toISOString().split('T')[0]
};

// Currency test data
export const CURRENCY_DATA = {
  valid: [
    '100.00',
    '100',
    '1000.50',
    '0.01',
    '999999.99'
  ],
  
  invalid: [
    'abc',
    '-100',
    '100.999',
    '100.1234',
    '',
    '0',
    '1000000.00' // Too large
  ]
};

// Helper functions for generating test data
export const generateRandomEmail = (): string => {
  const timestamp = Date.now();
  return `test-${timestamp}@example.com`;
};

export const generateRandomUsername = (): string => {
  const timestamp = Date.now();
  return `testuser${timestamp}`;
};

export const generateRandomCategoryName = (): string => {
  const timestamp = Date.now();
  return `Test Category ${timestamp}`;
};

export const generateRandomExpenseDescription = (): string => {
  const timestamp = Date.now();
  return `Test Expense ${timestamp}`;
};

// Test data cleanup helpers
export const cleanupTestData = {
  categories: [
    'Test Expense Category',
    'Test Income Category',
    'Food & Dining',
    'Salary',
    'Category with Special Ch@rs! & Symbols'
  ],
  
  expenses: [
    'Small Test Expense',
    'Medium Test Expense',
    'Large Test Expense',
    'Lunch at Restaurant',
    'Monthly Salary',
    'Expense with Special Ch@rs! & Symbols'
  ]
};

