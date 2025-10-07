import React, { useState } from "react";
import { FaLock, FaEye, FaEyeSlash } from "react-icons/fa";
import { FormField } from "../forms/FormField";
import { Input } from "../forms/Input";

interface PasswordInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: () => void;
  error?: string;
  label?: string;
  required?: boolean;
}

export const PasswordInput: React.FC<PasswordInputProps> = ({ 
  value, 
  onChange, 
  onBlur,
  error,
  label = "Пароль",
  required = true 
}) => {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <FormField
      label={label}
      error={error || undefined}
      required={required}
      className="mb-4"
    >
      <div className="relative">
        <Input
          type={showPassword ? "text" : "password"}
          name="password"
          placeholder="Введите пароль"
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          error={!!error}
          icon={<FaLock className="w-4 h-4 text-gray-400" />}
          required={required}
          data-testid="password-input"
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          data-testid="password-toggle"
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
        >
          {showPassword ? (
            <FaEyeSlash className="w-4 h-4" />
          ) : (
            <FaEye className="w-4 h-4" />
          )}
        </button>
      </div>
    </FormField>
  );
};