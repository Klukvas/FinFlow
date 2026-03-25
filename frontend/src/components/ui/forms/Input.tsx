import React from "react";

interface InputProps extends Omit<
 React.InputHTMLAttributes<HTMLInputElement>,
 "size"
> {
 error?: boolean;
 icon?: React.ReactNode;
 size?: "sm" | "md" | "lg";
 "data-testid"?: string;
}

export const Input: React.FC<InputProps> = ({
 error = false,
 icon,
 size = "md",
 className = "",
 "data-testid": testId,
 ...props
}) => {
 const sizeClasses = {
 sm: "h-10 px-3 py-2 text-sm",
 md: "h-12 px-4 py-3 text-base",
 lg: "h-14 px-4 py-4 text-lg",
 };

 const baseClasses = `w-full ${sizeClasses[size]} bg-surface border border-[var(--border)] rounded-lg text-content placeholder:text-content-tertiary hover:border-[var(--border-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 transition-colors`;
 const errorClasses = error
 ? "border-danger-base/70 focus-visible:border-danger-base/70 focus-visible:ring-[var(--danger)]/40"
 : "";
 const iconClasses = icon ? "pl-10" : "";

 return (
 <div
 className="relative w-full"
 data-testid={testId ? `${testId}-container` : "input-container"}
 >
 {icon && (
 <div
 className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none opacity-60 z-10"
 data-testid={testId ? `${testId}-icon` : "input-icon"}
 >
 {icon}
 </div>
 )}
 <input
 className={`${baseClasses} ${errorClasses} ${iconClasses} ${className}`.trim()}
 data-testid={testId || "input"}
 {...props}
 />
 </div>
 );
};
