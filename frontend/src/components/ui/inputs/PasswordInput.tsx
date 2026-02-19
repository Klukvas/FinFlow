import React, { useState } from "react";
import { useTranslation } from "react-i18next";
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
  'data-testid'?: string;
}

export const PasswordInput: React.FC<PasswordInputProps> = ({
  value,
  onChange,
  onBlur,
  error,
  label,
  required = true
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const { t } = useTranslation();

  return (
    <FormField
      label={label || t('auth.password')}
      error={error || undefined}
      required={required}
    >
      <div className="relative">
        <Input
          type={showPassword ? "text" : "password"}
          name="password"
          placeholder={t('auth.passwordPlaceholder')}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          error={!!error}
          icon={<FaLock className="w-4 h-4 theme-text-tertiary" />}
          required={required}
          autoComplete="current-password"
          data-testid="password-input"
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          data-testid="password-toggle"
          className="absolute inset-y-0 right-0 pr-3 flex items-center theme-text-tertiary hover:theme-text-secondary theme-transition opacity-70 hover:opacity-100"
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
