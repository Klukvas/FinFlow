import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { Modal } from "../shared/Modal";
import { EmailInput } from "../inputs/EmailInput";
import { PasswordInput } from "../inputs/PasswordInput";
import { CurrencySelect } from "../forms/CurrencySelect";
import { useAuth } from "@/contexts/AuthContext";
import { useAuthForm } from "@/hooks";
import { RegisterRequest } from "@/services/api/userApiClient";
import { config } from "@/config/env";
import { FaShieldAlt } from "react-icons/fa";
import { validateEmail } from "@/utils";
import { validatePasswordStrength } from "@/utils/validation";

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

interface ValidationErrors {
  email: string;
  password: string;
  currency: string;
}

export const RegisterModal: React.FC<RegisterModalProps> = ({
  isOpen,
  onClose,
  onSwitchToLogin,
}) => {
  const { t } = useTranslation();
  const { register } = useAuth();
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({
    email: "",
    password: "",
    currency: "",
  });

  const { formData, error, isLoading, handleChange, handleSubmit, setError } =
    useAuthForm({
      initialValues: {
        email: "",
        password: "",
        base_currency: "USD",
      } as RegisterRequest,
      validateEmail: false,
      onSubmit: async (data: RegisterRequest) => {
        const errors: ValidationErrors = {
          email: "",
          password: "",
          currency: "",
        };

        if (!validateEmail(data.email)) {
          errors.email = t("auth.invalidEmail");
        }

        const passwordValidation = validatePasswordStrength(data.password);
        if (!passwordValidation.isValid) {
          errors.password = passwordValidation.errors[0] || "Invalid password";
        }

        if (!data.base_currency) {
          errors.currency = t("profile.baseCurrency") || "Currency is required";
        }

        if (errors.email || errors.password || errors.currency) {
          setValidationErrors(errors);
          throw new Error("Validation failed");
        }

        if (config.debug) {
        }

        const result = await register(
          data.email,
          data.password,
          data.base_currency || "USD",
        );

        if (config.debug) {
        }

        if (result.success) {
          if (config.debug) {
          }
          onClose();
        } else {
          if (config.debug) {
            logger.error("Registration error:", result.error);
          }
          setError(result.error || t("auth.registerError"));
        }
      },
    });

  const handleClose = () => {
    setError("");
    setValidationErrors({ email: "", password: "", currency: "" });
    onClose();
  };

  const handleEmailBlur = () => {
    if (formData.email && !validateEmail(formData.email)) {
      setValidationErrors((prev) => ({
        ...prev,
        email: t("auth.invalidEmail"),
      }));
    } else {
      setValidationErrors((prev) => ({ ...prev, email: "" }));
    }
  };

  const handlePasswordBlur = () => {
    if (formData.password) {
      const validation = validatePasswordStrength(formData.password);
      setValidationErrors((prev) => ({
        ...prev,
        password: validation.isValid
          ? ""
          : validation.errors[0] || "Invalid password",
      }));
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e);
    if (validationErrors.email) {
      setValidationErrors((prev) => ({ ...prev, email: "" }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e);
    if (validationErrors.password) {
      setValidationErrors((prev) => ({ ...prev, password: "" }));
    }
  };

  const handleCurrencyChange = (value: string) => {
    handleChange({
      target: { name: "base_currency", value },
    } as React.ChangeEvent<HTMLInputElement>);
    if (validationErrors.currency) {
      setValidationErrors((prev) => ({ ...prev, currency: "" }));
    }
  };

  const handleCurrencyBlur = () => {
    if (!formData.base_currency) {
      setValidationErrors((prev) => ({
        ...prev,
        currency: t("profile.baseCurrency") || "Currency is required",
      }));
    } else {
      setValidationErrors((prev) => ({ ...prev, currency: "" }));
    }
  };

  const hasValidationErrors = !!(
    validationErrors.email ||
    validationErrors.password ||
    validationErrors.currency
  );
  const isFormValid =
    formData.email && formData.password && !hasValidationErrors;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t("auth.registerTitle")}
      showHeader={false}
      size="md"
      data-testid="register-modal"
    >
      <div className="space-y-6">
        {/* Title */}
        <div>
          <h2 className="text-2xl font-semibold theme-text-primary">
            {t("auth.registerTitle")}
          </h2>
          <p className="text-sm theme-text-secondary mt-1.5">
            {t("auth.registerSubtitle")}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          <EmailInput
            value={formData.email}
            onChange={handleEmailChange}
            onBlur={handleEmailBlur}
            error={validationErrors.email}
          />

          <PasswordInput
            value={formData.password}
            onChange={handlePasswordChange}
            onBlur={handlePasswordBlur}
            error={validationErrors.password}
          />

          {/* Currency */}
          <div className="space-y-2">
            <label className="block text-sm font-medium theme-text-primary">
              {t("profile.baseCurrency")}{" "}
              <span className="text-red-400">*</span>
            </label>
            <CurrencySelect
              value={formData.base_currency || "USD"}
              onChange={handleCurrencyChange}
              onBlur={handleCurrencyBlur}
              showFlags={true}
              dataTestId="currency-select"
            />
            {validationErrors.currency && (
              <p className="text-red-400 text-sm flex items-center gap-1.5 mt-1">
                <svg
                  className="w-3.5 h-3.5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                {validationErrors.currency}
              </p>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !isFormValid}
            data-testid="submit-register-button"
            className="w-full theme-accent-bg hover:theme-accent-hover text-white font-medium py-3 px-4 rounded-lg theme-transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                {t("common.loading")}
              </>
            ) : (
              t("auth.registerButton")
            )}
          </button>
        </form>

        {/* Security line */}
        <div className="flex items-center justify-center gap-1.5">
          <FaShieldAlt className="w-3 h-3 theme-text-tertiary" />
          <span className="text-xs theme-text-tertiary">
            {t("auth.securityNote")}
          </span>
        </div>

        {/* Switch to login */}
        <div className="text-center pt-2 border-t theme-border">
          <p className="text-sm theme-text-secondary pt-4">
            {t("auth.hasAccount")}{" "}
            <button
              onClick={onSwitchToLogin}
              className="theme-accent hover:underline font-medium theme-transition"
            >
              {t("auth.loginButton")}
            </button>
          </p>
        </div>
      </div>
    </Modal>
  );
};
