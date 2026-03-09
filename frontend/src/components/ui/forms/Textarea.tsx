import React from "react";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
 className?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
 className = "",
 ...props
}) => {
 return (
 <textarea
 className={`flex min-h-[80px] w-full rounded-md border-[var(--color-border)] border bg-elevated px-3 py-2 text-sm text-content placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
 {...props}
 />
 );
};
