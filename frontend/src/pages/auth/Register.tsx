import { EmailInput, PasswordInput } from "../../components";
import { CurrencySelect } from "../../components/ui/forms/CurrencySelect";
import { Link, useNavigate } from "react-router-dom";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { RegisterRequest } from "../../services/api/userApiClient";
import { useAuth } from "../../contexts/AuthContext";
import { useAuthForm } from "../../hooks";
import { config } from "@/config/env";
import { logger } from "@/utils/logger";
import {
 validatePasswordStrength,
 validateEmail,
 validateEmailDomain,
} from "../../utils/validation";

export default function Register() {
 const { t } = useTranslation();
 const navigate = useNavigate();
 const { register } = useAuth();

 const [validationErrors, setValidationErrors] = useState<{
 email: string[];
 password: string[];
 currency: string;
 }>({
 email: [],
 password: [],
 currency: "",
 });

 const [touched, setTouched] = useState<{
 email: boolean;
 password: boolean;
 currency: boolean;
 }>({
 email: false,
 password: false,
 currency: false,
 });

 const {
 formData,
 error,
 isLoading,
 handleChange: originalHandleChange,
 handleSubmit: originalHandleSubmit,
 setError,
 } = useAuthForm({
 initialValues: {
 email: "",
 password: "",
 base_currency: "USD",
 } as RegisterRequest,
 onSubmit: async (data: RegisterRequest) => {
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
 navigate("/dashboard", { replace: true });
 } else {
 if (config.debug) {
 logger.error("Registration error:", result.error);
 }
 setError(result.error || t("authPage.register.error"));
 }
 },
 });

 const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
 const { name, value } = e.target;
 originalHandleChange(e);

 // Validate on change
 if (name === "email") {
 const emailResult = validateEmail(value);
 const domainResult = value.includes("@")
 ? validateEmailDomain(value)
 : { isValid: true, errors: [] };
 setValidationErrors((prev) => ({
 ...prev,
 email: [...emailResult.errors, ...domainResult.errors],
 }));
 } else if (name === "password") {
 const result = validatePasswordStrength(value);
 setValidationErrors((prev) => ({ ...prev, password: result.errors }));
 }
 };

 const handleBlur = (fieldName: "email" | "password" | "currency") => {
 setTouched((prev) => ({ ...prev, [fieldName]: true }));
 };

 const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
 e.preventDefault();

 // Mark all fields as touched
 setTouched({ email: true, password: true, currency: true });

 // Validate all fields
 const emailResult = validateEmail(formData.email);
 const emailDomainResult = formData.email.includes("@")
 ? validateEmailDomain(formData.email)
 : { isValid: true, errors: [] };
 const passwordResult = validatePasswordStrength(formData.password);
 const currencyError = !formData.base_currency
 ? t("profile.baseCurrency") || "Currency is required"
 : "";

 setValidationErrors({
 email: [...emailResult.errors, ...emailDomainResult.errors],
 password: passwordResult.errors,
 currency: currencyError,
 });

 // If any validation fails, don't submit
 if (
 !emailResult.isValid ||
 !emailDomainResult.isValid ||
 !passwordResult.isValid ||
 currencyError
 ) {
 return;
 }

 // Call original submit handler
 originalHandleSubmit(e);
 };

 return (
 <div className="flex items-center justify-center px-4 py-12">
 <div className="w-full max-w-md">
 <div className="bg-elevated border-[var(--border)] border rounded-lg theme-shadow p-6 md:p-8 transition-colors">
 <div className="text-center mb-8">
 <h2 className="text-2xl font-bold text-content mb-2">
 {t("authPage.register.title")}
 </h2>
 <p className="text-content-secondary">
 {t("authPage.register.subtitle")}
 </p>
 </div>

 <form onSubmit={handleSubmit} className="space-y-6">
 <div className="space-y-2">
 <EmailInput
 value={formData.email}
 onChange={handleChange}
 onBlur={() => handleBlur("email")}
 error={
 touched.email && validationErrors.email.length > 0
 ? validationErrors.email[0]
 : ""
 }
 />
 {touched.email && validationErrors.email.length > 1 && (
 <div className="mt-1 space-y-1">
 {validationErrors.email.slice(1).map((err, idx) => (
 <p key={idx} className="text-danger-base text-xs">
 {err}
 </p>
 ))}
 </div>
 )}
 </div>

 <div className="space-y-2">
 <PasswordInput
 value={formData.password}
 onChange={handleChange}
 onBlur={() => handleBlur("password")}
 />
 {touched.password && validationErrors.password.length > 0 && (
 <div className="mt-1 space-y-1">
 {validationErrors.password.map((err, idx) => (
 <p key={idx} className="text-danger-base text-xs">
 {err}
 </p>
 ))}
 </div>
 )}
 </div>

 <div className="space-y-2">
 <label className="block text-sm font-medium text-content">
 {t("profile.baseCurrency")}{" "}
 <span className="text-danger-base">*</span>
 </label>
 <CurrencySelect
 value={formData.base_currency || "USD"}
 onChange={(value) => {
 handleChange({
 target: { name: "base_currency", value },
 } as React.ChangeEvent<HTMLInputElement>);
 if (validationErrors.currency) {
 setValidationErrors((prev) => ({ ...prev, currency: "" }));
 }
 }}
 onBlur={() => {
 handleBlur("currency");
 if (!formData.base_currency) {
 setValidationErrors((prev) => ({
 ...prev,
 currency:
 t("profile.baseCurrency") || "Currency is required",
 }));
 }
 }}
 showFlags={true}
 />
 {touched.currency && validationErrors.currency && (
 <p className="text-danger-base text-xs">
 {validationErrors.currency}
 </p>
 )}
 </div>

 {error && (
 <div className="bg-[var(--danger-dim)] border-[var(--border)] border rounded-lg p-4">
 <p className="text-danger-base text-sm">{error}</p>
 </div>
 )}

 <button
 type="submit"
 disabled={isLoading}
 className="w-full bg-accent-base hover:bg-accent-base-hover text-content-inverse font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
 >
 {isLoading
 ? t("authPage.register.loading")
 : t("authPage.register.submit")}
 </button>
 </form>

 <div className="mt-6 text-center">
 <p className="text-content-secondary">
 {t("authPage.register.hasAccount")}{" "}
 <Link
 to="/login"
 className="text-accent-base hover:bg-accent-base-hover font-medium transition-colors"
 >
 {t("authPage.register.loginLink")}
 </Link>
 </p>
 </div>
 </div>
 </div>
 </div>
 );
}
