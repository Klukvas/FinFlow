// Validation rules matching backend validation
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Password validation settings (matching backend config)
const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;
const REQUIRE_UPPERCASE = true;
const REQUIRE_LOWERCASE = true;
const REQUIRE_NUMBERS = true;
const REQUIRE_SPECIAL_CHARS = true;

// Username validation settings (matching backend config)
const MIN_USERNAME_LENGTH = 3;
const MAX_USERNAME_LENGTH = 50;

export const validatePasswordStrength = (password: string): ValidationResult => {
  const errors: string[] = [];

  if (password.length < MIN_PASSWORD_LENGTH) {
    errors.push(`Password must be at least ${MIN_PASSWORD_LENGTH} characters long`);
  }

  if (password.length > MAX_PASSWORD_LENGTH) {
    errors.push(`Password must be no more than ${MAX_PASSWORD_LENGTH} characters long`);
  }

  if (REQUIRE_UPPERCASE && !/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  }

  if (REQUIRE_LOWERCASE && !/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  }

  if (REQUIRE_NUMBERS && !/\d/.test(password)) {
    errors.push("Password must contain at least one number");
  }

  if (REQUIRE_SPECIAL_CHARS && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push("Password must contain at least one special character");
  }

  // Check for common weak patterns
  if (/(.)\1{2,}/.test(password)) {
    errors.push("Password cannot contain more than 2 consecutive identical characters");
  }

  if (/(123|abc|qwe|asd|zxc)/i.test(password)) {
    errors.push("Password cannot contain common sequences");
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateUsername = (username: string): ValidationResult => {
  const errors: string[] = [];

  if (username.length < MIN_USERNAME_LENGTH) {
    errors.push(`Username must be at least ${MIN_USERNAME_LENGTH} characters long`);
  }

  if (username.length > MAX_USERNAME_LENGTH) {
    errors.push(`Username must be no more than ${MAX_USERNAME_LENGTH} characters long`);
  }

  // Username should only contain alphanumeric characters, underscores, and hyphens
  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    errors.push("Username can only contain letters, numbers, underscores, and hyphens");
  }

  // Username should start with a letter or number
  if (username.length > 0 && !/^[a-zA-Z0-9]/.test(username)) {
    errors.push("Username must start with a letter or number");
  }

  // Username should not end with underscore or hyphen
  if (username.endsWith('_') || username.endsWith('-')) {
    errors.push("Username cannot end with underscore or hyphen");
  }

  // Check for reserved usernames
  const reservedUsernames = ['admin', 'root', 'administrator', 'user', 'test', 'api', 'www', 'mail', 'ftp'];
  if (reservedUsernames.includes(username.toLowerCase())) {
    errors.push("This username is reserved and cannot be used");
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateEmailDomain = (email: string): ValidationResult => {
  const errors: string[] = [];

  if (!email.includes('@')) {
    errors.push("Invalid email format");
    return { isValid: false, errors };
  }

  const domain = email.split('@')[1]?.toLowerCase();
  
  if (!domain) {
    errors.push("Invalid email format");
    return { isValid: false, errors };
  }

  // List of common disposable email domains
  const disposableDomains = [
    '10minutemail.com',
    'tempmail.org',
    'guerrillamail.com',
    'mailinator.com',
    'throwaway.email',
    'temp-mail.org'
  ];

  if (disposableDomains.includes(domain)) {
    errors.push("Disposable email addresses are not allowed");
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateEmail = (email: string): ValidationResult => {
  const errors: string[] = [];

  // Basic email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    errors.push("Please enter a valid email address");
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

