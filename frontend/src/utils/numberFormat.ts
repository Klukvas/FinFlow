/**
 * Number formatting utilities
 */

/**
 * Format a number with thousand separators using spaces
 * @param value - The number or string to format
 * @returns Formatted string with spaces as thousand separators
 * 
 * @example
 * formatNumberWithSpaces(150000000) // Returns: "150 000 000"
 * formatNumberWithSpaces("1234567.89") // Returns: "1 234 567.89"
 */
export const formatNumberWithSpaces = (value: string | number): string => {
  if (value === '' || value === null || value === undefined) {
    return '';
  }

  const numValue = typeof value === 'string' ? value : value.toString();
  
  // Split by decimal point to handle decimal numbers
  const parts = numValue.split('.');
  const integerPart = parts[0] || '';
  const decimalPart = parts[1] || '';
  
  // Add spaces as thousand separators to integer part
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  
  // Reconstruct with decimal part if it exists
  return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
};

/**
 * Remove spaces from a formatted number string
 * @param value - The formatted string
 * @returns Clean number string without spaces
 * 
 * @example
 * removeSpacesFromNumber("1 234 567.89") // Returns: "1234567.89"
 */
export const removeSpacesFromNumber = (value: string): string => {
  return value.replace(/\s/g, '');
};

/**
 * Validate and format a number input value
 * Allows digits, decimal point, and spaces
 * @param value - The input value to validate
 * @returns The cleaned value or empty string if invalid
 */
export const sanitizeNumericInput = (value: string): string => {
  // Remove spaces first, then validate
  const cleaned = removeSpacesFromNumber(value);
  
  // Allow empty, digits, and single decimal point
  if (cleaned === '' || /^\d*\.?\d*$/.test(cleaned)) {
    return cleaned;
  }
  
  // If invalid, try to extract valid numeric part
  const match = cleaned.match(/^\d*\.?\d*/);
  return match ? match[0] : '';
};

