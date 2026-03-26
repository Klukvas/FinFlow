import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
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
import { Shield } from "lucide-react";
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
  const navigate = useNavigate();
  const { register } = useAuth();
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({
    email: "",
    password: "",
    currency: "",
  });
  const [touched, setTouched] = useState<Record<string, boolean>>({
    email: false,
    password: false,
    currency: false,
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
          setTouched({ email: true, password: true, currency: true });
          setValidationErrors(errors);
          throw new Error("Validation failed");
        }

        const result = await register(
          data.email,
          data.password,
          data.base_currency || "USD",
        );

        if (result.success) {
          onClose();
          navigate("/dashboard", { replace: true });
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
    setTouched({ email: false, password: false, currency: false });
    onClose();
  };

  const handleEmailBlur = () => {
    setTouched((prev) => ({ ...prev, email: true }));
    if (!formData.email) {
      setValidationErrors((prev) => ({
        ...prev,
        email: t("auth.emailRequired", { defaultValue: "Email is required" }),
      }));
    } else if (!validateEmail(formData.email)) {
      setValidationErrors((prev) => ({
        ...prev,
        email: t("auth.invalidEmail"),
      }));
    } else {
      setValidationErrors((prev) => ({ ...prev, email: "" }));
    }
  };

  const handlePasswordBlur = () => {
    setTouched((prev) => ({ ...prev, password: true }));
    const validation = validatePasswordStrength(formData.password);
    setValidationErrors((prev) => ({
      ...prev,
      password: validation.isValid
        ? ""
        : validation.errors[0] || "Invalid password",
    }));
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
    setTouched((prev) => ({ ...prev, currency: true }));
    if (!formData.base_currency) {
      setValidationErrors((prev) => ({
        ...prev,
        currency: t("profile.baseCurrency") || "Currency is required",
      }));
    } else {
      setValidationErrors((prev) => ({ ...prev, currency: "" }));
    }
  };

  const isFormValid =
    validateEmail(formData.email) &&
    validatePasswordStrength(formData.password).isValid &&
    !!formData.base_currency;

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
          <h2 className="text-2xl font-semibold text-content">
            {t("auth.registerTitle")}
          </h2>
          <p className="text-sm text-content-secondary mt-1.5">
            {t("auth.registerSubtitle")}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          <EmailInput
            value={formData.email}
            onChange={handleEmailChange}
            onBlur={handleEmailBlur}
            error={touched.email ? validationErrors.email : ""}
          />

          <PasswordInput
            value={formData.password}
            onChange={handlePasswordChange}
            onBlur={handlePasswordBlur}
            error={touched.password ? validationErrors.password : ""}
          />

          {/* Currency */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-content">
              {t("profile.baseCurrency")}{" "}
              <span className="text-danger-base">*</span>
            </label>
            <CurrencySelect
              value={formData.base_currency || "USD"}
              onChange={handleCurrencyChange}
              onBlur={handleCurrencyBlur}
              showFlags={true}
              dataTestId="currency-select"
            />
            {touched.currency && validationErrors.currency && (
              <p className="text-danger-base text-sm flex items-center gap-1.5 mt-1">
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
            <div className="rounded-lg border border-[var(--danger-dim)] bg-[var(--danger-dim)] px-4 py-3">
              <p className="text-danger-base text-sm">{error}</p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !isFormValid}
            data-testid="submit-register-button"
            className="w-full bg-accent-base hover:bg-accent-base-hover text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
          <Shield className="w-3 h-3 text-content-tertiary" strokeWidth={1.5} />
          <span className="text-xs text-content-tertiary">
            {t("auth.securityNote")}
          </span>
        </div>

        {/* Switch to login */}
        <div className="text-center pt-2 border-t border-[var(--border)]">
          <p className="text-sm text-content-secondary pt-4">
            {t("auth.hasAccount")}{" "}
            <button
              onClick={onSwitchToLogin}
              className="text-accent-base hover:underline font-medium transition-colors"
            >
              {t("auth.loginButton")}
            </button>
          </p>
        </div>
      </div>
    </Modal>
  );
};
