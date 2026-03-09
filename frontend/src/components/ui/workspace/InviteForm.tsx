import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { WorkspaceInviteCreate, AssignableRole } from "@/types";
import { FaEnvelope, FaEye, FaEdit, FaSpinner } from "react-icons/fa";

interface InviteFormProps {
 onSubmit: (data: WorkspaceInviteCreate) => Promise<void>;
 onCancel: () => void;
 isLoading?: boolean;
 error?: string | null;
}

export const InviteForm: React.FC<InviteFormProps> = ({
 onSubmit,
 onCancel,
 isLoading = false,
 error: externalError,
}) => {
 const { t } = useTranslation();
 const [email, setEmail] = useState("");
 const [role, setRole] = useState<AssignableRole>("read");
 const [error, setError] = useState<string | null>(null);

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault();
 setError(null);

 const trimmedEmail = email.trim().toLowerCase();

 if (!trimmedEmail) {
 setError(t("workspace.invite.emailRequired", "Email is required"));
 return;
 }

 // Basic email validation
 const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
 if (!emailRegex.test(trimmedEmail)) {
 setError(
 t(
 "workspace.invite.invalidEmail",
 "Please enter a valid email address",
 ),
 );
 return;
 }

 try {
 await onSubmit({ email: trimmedEmail, role });
 } catch (err) {
 // Error will be handled externally
 }
 };

 const displayError = externalError || error;

 return (
 <form onSubmit={handleSubmit} className="space-y-6">
 {/* Email field */}
 <div>
 <label className="block text-sm font-medium text-content mb-2">
 {t("workspace.invite.email", "Email Address")}{" "}
 <span className="text-danger-base">*</span>
 </label>
 <div className="relative">
 <FaEnvelope className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-content-tertiary" />
 <input
 type="email"
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 placeholder={t(
 "workspace.invite.emailPlaceholder",
 "colleague@example.com",
 )}
 className="w-full pl-11 pr-4 py-3 rounded-lg bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary focus:ring-2 focus:ring-[var(--color-ring)] focus:border-transparent transition-colors"
 disabled={isLoading}
 autoFocus
 />
 </div>
 <p className="mt-1.5 text-sm text-content-tertiary">
 {t(
 "workspace.invite.emailHint",
 "The user must have an existing account",
 )}
 </p>
 </div>

 {/* Role selection */}
 <div>
 <label className="block text-sm font-medium text-content mb-3">
 {t("workspace.invite.role", "Permission Level")}
 </label>
 <div className="grid grid-cols-2 gap-3">
 <button
 type="button"
 onClick={() => setRole("read")}
 className={`flex items-center gap-3 p-4 rounded-xl border transition-colors ${
 role === "read"
 ? "border-accent-base bg-[var(--color-accent-light)]"
 : "border-[var(--color-border)] hover:bg-surface-alt"
 }`}
 disabled={isLoading}
 >
 <div
 className={`p-2 rounded-lg ${
 role === "read"
 ? "bg-[var(--color-accent-light)] text-accent-base"
 : "bg-surface-alt text-content-secondary"
 }`}
 >
 <FaEye className="w-5 h-5" />
 </div>
 <div className="text-left">
 <div
 className={`font-medium ${role === "read" ? "text-accent-base" : "text-content"}`}
 >
 {t("workspace.roles.read", "View Only")}
 </div>
 <div className="text-xs text-content-tertiary">
 {t("workspace.roles.readDesc", "Can view all data")}
 </div>
 </div>
 </button>

 <button
 type="button"
 onClick={() => setRole("full")}
 className={`flex items-center gap-3 p-4 rounded-xl border transition-colors ${
 role === "full"
 ? "border-success-base bg-[var(--color-success-light)]"
 : "border-[var(--color-border)] hover:bg-surface-alt"
 }`}
 disabled={isLoading}
 >
 <div
 className={`p-2 rounded-lg ${
 role === "full"
 ? "bg-[var(--color-success-light)] text-success-base"
 : "bg-surface-alt text-content-secondary"
 }`}
 >
 <FaEdit className="w-5 h-5" />
 </div>
 <div className="text-left">
 <div
 className={`font-medium ${role === "full" ? "text-success-base" : "text-content"}`}
 >
 {t("workspace.roles.full", "Full Access")}
 </div>
 <div className="text-xs text-content-tertiary">
 {t("workspace.roles.fullDesc", "Can view and edit")}
 </div>
 </div>
 </button>
 </div>
 </div>

 {/* Error message */}
 {displayError && (
 <div className="p-3 rounded-lg bg-[var(--color-danger-light)] text-danger-base text-sm">
 {displayError}
 </div>
 )}

 {/* Actions */}
 <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--color-border)]">
 <button
 type="button"
 onClick={onCancel}
 className="px-4 py-2 rounded-lg text-content-secondary hover:bg-surface-alt transition-colors"
 disabled={isLoading}
 >
 {t("common.cancel", "Cancel")}
 </button>
 <button
 type="submit"
 className="flex items-center gap-2 px-6 py-2 rounded-lg bg-accent-base text-white font-medium hover:bg-accent-base-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
 disabled={isLoading || !email.trim()}
 >
 {isLoading && <FaSpinner className="w-4 h-4 animate-spin" />}
 {isLoading
 ? t("workspace.invite.sending", "Sending...")
 : t("workspace.invite.send", "Send Invite")}
 </button>
 </div>
 </form>
 );
};

export default InviteForm;
