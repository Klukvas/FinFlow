import React from "react";
import { FaEnvelope } from "react-icons/fa";
import { FormField } from "../forms/FormField";
import { Input } from "../forms/Input";

interface EmailInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string | undefined;
  label?: string;
  required?: boolean;
}

export const EmailInput: React.FC<EmailInputProps> = ({ 
  value, 
  onChange, 
  error, 
  label = "Email",
  required = true 
}) => {
  return (
    <FormField
      label={label}
      error={error || ''}
      required={required}
      className="mb-4"
    >
      <Input
        type="email"
        name="email"
        placeholder="Введите email"
        value={value}
        onChange={onChange}
        error={!!error}
        icon={<FaEnvelope className="w-4 h-4 text-gray-400" />}
        required={required}
        data-testid="email-input"
      />
    </FormField>
  );
};