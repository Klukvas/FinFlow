import React from "react";
import { useTranslation } from "react-i18next";
import { Mail } from "lucide-react";
import { FormField } from "../forms/FormField";
import { Input } from "../forms/Input";

interface EmailInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: () => void;
  error?: string | undefined;
  label?: string;
  required?: boolean;
  autoFocus?: boolean;
  "data-testid"?: string;
}

export const EmailInput: React.FC<EmailInputProps> = ({
  value,
  onChange,
  onBlur,
  error,
  label,
  required = true,
  autoFocus = false,
}) => {
  const { t } = useTranslation();

  return (
    <FormField
      label={label || t("auth.email")}
      error={error || ""}
      required={required}
    >
      <Input
        type="email"
        name="email"
        placeholder={t("auth.emailPlaceholder")}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        error={!!error}
        icon={<Mail className="w-4 h-4 text-content-tertiary" />}
        required={required}
        autoFocus={autoFocus}
        autoComplete="email"
        data-testid="email-input"
      />
    </FormField>
  );
};
