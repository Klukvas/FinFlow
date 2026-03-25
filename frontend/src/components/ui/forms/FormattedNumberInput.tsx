import React, { forwardRef } from "react";
import {
 formatNumberWithSpaces,
 removeSpacesFromNumber,
} from "@/utils/numberFormat";

export interface FormattedNumberInputProps extends Omit<
 React.InputHTMLAttributes<HTMLInputElement>,
 "type" | "value" | "onChange"
> {
 value?: string | number;
 onChange?: (value: string) => void;
 onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
 placeholder?: string;
 error?: string;
 label?: string;
 required?: boolean;
 disabled?: boolean;
 className?: string;
 "data-testid"?: string;
}

const FormattedNumberInput = forwardRef<
 HTMLInputElement,
 FormattedNumberInputProps
>(
 (
 {
 value = "",
 onChange,
 onBlur,
 placeholder = "0",
 error,
 label,
 required = false,
 disabled = false,
 className,
 "data-testid": testId,
 ...props
 },
 ref,
 ) => {
 const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
 const inputValue = e.target.value;

 // Remove spaces and validate
 const cleaned = removeSpacesFromNumber(inputValue);

 // Allow empty, digits, and single decimal point
 if (cleaned === "" || /^\d*\.?\d*$/.test(cleaned)) {
 // Re-format with spaces for display
 const formatted = formatNumberWithSpaces(cleaned);

 if (onChange) {
 onChange(formatted);
 }
 }
 };

 const handleBlurEvent = (e: React.FocusEvent<HTMLInputElement>) => {
 // Format to 2 decimal places on blur if it's a valid number
 const inputValue = e.target.value;
 const cleaned = removeSpacesFromNumber(inputValue);

 if (cleaned && !isNaN(parseFloat(cleaned))) {
 const formattedValue = formatNumberWithSpaces(
 parseFloat(cleaned).toFixed(2),
 );
 if (onChange) {
 onChange(formattedValue);
 }
 }

 if (onBlur) {
 onBlur(e);
 }
 };

 // Convert number to formatted string if value is a number
 const displayValue =
 typeof value === "number"
 ? formatNumberWithSpaces(value.toString())
 : value;

 return (
 <div
 className="space-y-2"
 data-testid={
 testId ? `${testId}-container` : "formatted-number-input-container"
 }
 >
 {label && (
 <label
 className="block text-sm font-medium leading-none text-content"
 data-testid={
 testId ? `${testId}-label` : "formatted-number-input-label"
 }
 >
 {label}
 {required && <span className="text-danger-base ml-1">*</span>}
 </label>
 )}
 <input
 ref={ref}
 type="text"
 inputMode="decimal"
 value={displayValue}
 onChange={handleChange}
 onBlur={handleBlurEvent}
 placeholder={placeholder}
 disabled={disabled}
 data-testid={testId || "formatted-number-input"}
 className={`block w-full h-12 px-3 py-3 text-base border-[var(--border)] border rounded-lg shadow-sm bg-surface text-content placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors ${
 error
 ? "border-danger-base focus:ring-[var(--danger)] focus:border-danger-base"
 : ""
 } ${
 disabled
 ? "bg-surface-alt cursor-not-allowed opacity-50"
 : "hover:border-[var(--border-hover)]"
 } ${className || ""}`}
 {...props}
 />
 {error && (
 <p
 className="text-sm text-danger-base"
 data-testid={
 testId ? `${testId}-error` : "formatted-number-input-error"
 }
 >
 {error}
 </p>
 )}
 </div>
 );
 },
);

FormattedNumberInput.displayName = "FormattedNumberInput";

export { FormattedNumberInput };
