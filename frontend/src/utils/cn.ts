/**
 * Utility for conditionally joining class names.
 * Lightweight replacement for clsx + tailwind-merge.
 */
export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(' ');
}
