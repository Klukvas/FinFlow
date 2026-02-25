// Validation rules matching backend validation
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Password validation settings (matching backend config)
const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;

export const validatePasswordStrength = (
  password: string,
): ValidationResult => {
  const errors: string[] = [];

  if (password.length < MIN_PASSWORD_LENGTH) {
    errors.push(
      `Password must be at least ${MIN_PASSWORD_LENGTH} characters long`,
    );
  }

  if (password.length > MAX_PASSWORD_LENGTH) {
    errors.push(
      `Password must be no more than ${MAX_PASSWORD_LENGTH} characters long`,
    );
  }

  if (!/[a-zA-Z]/.test(password)) {
    errors.push("Password must contain at least one letter");
  }

  if (!/\d/.test(password)) {
    errors.push("Password must contain at least one number");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

export const validateEmailDomain = (email: string): ValidationResult => {
  const errors: string[] = [];

  if (!email.includes("@")) {
    errors.push("Invalid email format");
    return { isValid: false, errors };
  }

  const domain = email.split("@")[1]?.toLowerCase();

  if (!domain) {
    errors.push("Invalid email format");
    return { isValid: false, errors };
  }

  // List of common disposable email domains
  const disposableDomains = [
    "10minutemail.com",
    "tempmail.org",
    "guerrillamail.com",
    "mailinator.com",
    "throwaway.email",
    "temp-mail.org",
  ];

  if (disposableDomains.includes(domain)) {
    errors.push("Disposable email addresses are not allowed");
  }

  return {
    isValid: errors.length === 0,
    errors,
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
    errors,
  };
};
