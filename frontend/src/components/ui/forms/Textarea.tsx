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
      className={`flex min-h-[80px] w-full rounded-md theme-border border theme-surface px-3 py-2 text-sm theme-text-primary placeholder:theme-text-tertiary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    />
  );
};
