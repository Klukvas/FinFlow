/**
 * Supported languages in the application
 */
export enum SupportedLanguage {
  RU = 'ru',
  UK = 'uk',
  EN = 'en'
}

// Array of supported language codes for easy checking
const SUPPORTED_LANGUAGE_CODES = Object.values(SupportedLanguage);

/**
 * Normalize language code to supported format (e.g., 'ru-RU' -> 'ru')
 * 
 * This function extracts the base language code before the dash and maps it 
 * to a supported language. It handles various locale formats like:
 * - 'ru-RU' -> 'ru'
 * - 'uk-UA' -> 'uk'
 * - 'en-US' -> 'en'
 * - 'en' -> 'en'
 * 
 * @param lang - Language code string (can be undefined, 'ru-RU', 'uk-UA', etc.)
 * @returns Normalized language code ('ru', 'uk', or 'en' as fallback)
 * 
 * @example
 * ```typescript
 * normalizeLanguageCode('ru-RU')  // Returns: 'ru'
 * normalizeLanguageCode('uk-UA')  // Returns: 'uk'
 * normalizeLanguageCode('en-US')  // Returns: 'en'
 * normalizeLanguageCode('fr-FR')  // Returns: 'en' (fallback)
 * normalizeLanguageCode(undefined) // Returns: 'en' (fallback)
 * ```
 */
export const normalizeLanguageCode = (lang: string | undefined): string => {
  // If language is not provided, default to English
  if (!lang) {
    return SupportedLanguage.EN;
  }
  
  // Extract the base language code (before the dash)
  const parts = lang.split('-');
  const langCode = parts[0]?.toLowerCase();
  
  // If no valid language code extracted, default to English
  if (!langCode) {
    return SupportedLanguage.EN;
  }
  
  // Check if the language code is in our supported languages
  if (SUPPORTED_LANGUAGE_CODES.includes(langCode as SupportedLanguage)) {
    return langCode;
  }
  
  // Default fallback to English
  return SupportedLanguage.EN;
};

/**
 * Check if a language code is supported
 * 
 * @param lang - Language code to check
 * @returns true if the language is supported
 */
export const isLanguageSupported = (lang: string): boolean => {
  return SUPPORTED_LANGUAGE_CODES.includes(lang.toLowerCase() as SupportedLanguage);
};

/**
 * Get all supported language codes
 * 
 * @returns Array of supported language codes
 */
export const getSupportedLanguages = (): string[] => {
  return SUPPORTED_LANGUAGE_CODES;
};
