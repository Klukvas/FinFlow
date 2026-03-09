import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { Modal } from "../shared/Modal";
import { EmailInput } from "../inputs/EmailInput";
import { PasswordInput } from "../inputs/PasswordInput";
import { useAuth } from "@/contexts/AuthContext";
import { useAuthForm } from "@/hooks";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { LoginRequest } from "@/services/api/userApiClient";
import { config } from "@/config/env";
import { validateEmail } from "@/utils";
import { FaShieldAlt } from "react-icons/fa";

interface LoginModalProps {
 isOpen: boolean;
 onClose: () => void;
 onSwitchToRegister: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({
 isOpen,
 onClose,
 onSwitchToRegister,
}) => {
 const { t } = useTranslation();
 const navigate = useNavigate();
 const { login } = useAuth();
 const { handleUserError } = useErrorHandler();
 const [emailError, setEmailError] = useState<string>("");

 const { formData, error, isLoading, handleChange, handleSubmit, setError } =
 useAuthForm({
 initialValues: {
 email: "",
 password: "",
 } as LoginRequest,
 validateEmail: false,
 onSubmit: async (data: LoginRequest) => {
 if (!validateEmail(data.email)) {
 setEmailError(t("auth.invalidEmail"));
 throw new Error("Invalid email");
 }

 if (config.debug) {
 }

 const result = await login(data.email, data.password);

 if (config.debug) {
 }

 if (result.success) {
 if (config.debug) {
 }
 onClose();
 navigate("/dashboard", { replace: true });
 } else {
 if (config.debug) {
 logger.error("Login error:", result.error);
 }
 const mockErrorResponse = {
 error: result.error || t("auth.loginError"),
 errorCode: "INVALID_CREDENTIALS",
 };
 handleUserError(mockErrorResponse);
 setError(result.error || t("auth.loginError"));
 }
 },
 });

 const handleClose = () => {
 setError("");
 setEmailError("");
 onClose();
 };

 const handleEmailBlur = () => {
 if (formData.email && !validateEmail(formData.email)) {
 setEmailError(t("auth.invalidEmail"));
 } else {
 setEmailError("");
 }
 };

 const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
 handleChange(e);
 if (emailError) {
 setEmailError("");
 }
 };

 const isFormValid = formData.email && formData.password && !emailError;

 return (
 <Modal
 isOpen={isOpen}
 onClose={handleClose}
 title={t("auth.loginTitle")}
 showHeader={false}
 size="md"
 data-testid="login-modal"
 >
 <div className="space-y-6">
 {/* Title */}
 <div>
 <h2 className="text-2xl font-semibold text-content">
 {t("auth.loginTitle")}
 </h2>
 <p className="text-sm text-content-secondary mt-1.5">
 {t("auth.loginSubtitle")}
 </p>
 </div>

 {/* Form */}
 <form onSubmit={handleSubmit} noValidate className="space-y-5">
 <EmailInput
 value={formData.email}
 onChange={handleEmailChange}
 onBlur={handleEmailBlur}
 error={emailError}
 autoFocus
 />

 <PasswordInput value={formData.password} onChange={handleChange} />

 {/* Error */}
 {error && (
 <div
 className="rounded-lg border border-[var(--color-danger-light)] bg-[var(--color-danger-light)] px-4 py-3"
 data-testid="login-error"
 >
 <p className="text-danger-base text-sm">{error}</p>
 </div>
 )}

 {/* Submit */}
 <button
 type="submit"
 disabled={isLoading || !isFormValid}
 data-testid="submit-login-button"
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
 t("auth.loginButton")
 )}
 </button>
 </form>

 {/* Security line */}
 <div className="flex items-center justify-center gap-1.5">
 <FaShieldAlt className="w-3 h-3 text-content-tertiary" />
 <span className="text-xs text-content-tertiary">
 {t("auth.securityNote")}
 </span>
 </div>

 {/* Switch to register */}
 <div className="text-center pt-2 border-t border-[var(--color-border)]">
 <p className="text-sm text-content-secondary pt-4">
 {t("auth.noAccount")}{" "}
 <button
 data-testid="switch-to-register"
 onClick={onSwitchToRegister}
 className="text-accent-base hover:underline font-medium transition-colors"
 >
 {t("auth.registerButton")}
 </button>
 </p>
 </div>
 </div>
 </Modal>
 );
};
