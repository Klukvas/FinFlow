import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { FaLink, FaExternalLinkAlt } from "react-icons/fa";

interface ConnectFormProps {
 onConnect: (token: string) => Promise<void>;
 isLoading: boolean;
}

export const ConnectForm: React.FC<ConnectFormProps> = ({
 onConnect,
 isLoading,
}) => {
 const { t } = useTranslation();
 const [token, setToken] = useState("");

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault();
 if (!token.trim()) return;
 await onConnect(token.trim());
 };

 return (
 <div className="max-w-xl mx-auto">
 <div className="bg-elevated rounded-lg p-6 shadow-sm border-[var(--color-border)] border">
 <div className="text-center mb-6">
 <div className="w-16 h-16 bg-[var(--color-accent-light)] rounded-full flex items-center justify-center mx-auto mb-4">
 <FaLink className="w-8 h-8 text-accent-base" />
 </div>
 <h2 className="text-xl font-semibold text-content mb-2">
 {t("bankSync.connectTitle")}
 </h2>
 <p className="text-content-secondary text-sm">
 {t("bankSync.connectDescription")}
 </p>
 </div>

 <div className="bg-surface rounded-lg p-4 mb-6">
 <h3 className="font-medium text-content text-sm mb-3">
 {t("bankSync.howToGetToken")}
 </h3>
 <ol className="space-y-2 text-sm text-content-secondary">
 <li className="flex items-start gap-2">
 <span className="text-accent-base font-bold">1.</span>
 {t("bankSync.step1")}
 </li>
 <li className="flex items-start gap-2">
 <span className="text-accent-base font-bold">2.</span>
 {t("bankSync.step2")}
 </li>
 <li className="flex items-start gap-2">
 <span className="text-accent-base font-bold">3.</span>
 {t("bankSync.step3")}
 </li>
 </ol>
 <a
 href="https://api.monobank.ua/"
 target="_blank"
 rel="noopener noreferrer"
 className="inline-flex items-center gap-1 text-sm text-accent-base hover:underline mt-3"
 >
 api.monobank.ua <FaExternalLinkAlt className="w-3 h-3" />
 </a>
 </div>

 <form onSubmit={handleSubmit}>
 <div className="mb-4">
 <label
 htmlFor="monobank-token"
 className="block text-sm font-medium text-content mb-1"
 >
 {t("bankSync.tokenLabel")}
 </label>
 <input
 id="monobank-token"
 type="password"
 value={token}
 onChange={(e) => setToken(e.target.value)}
 placeholder={t("bankSync.tokenPlaceholder")}
 className="w-full px-3 py-2 bg-surface border-[var(--color-border)] border rounded-lg text-content text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)]"
 disabled={isLoading}
 autoComplete="off"
 />
 </div>
 <button
 type="submit"
 disabled={isLoading || !token.trim()}
 className="w-full py-2.5 px-4 rounded-lg font-medium text-sm text-white bg-accent-base hover:bg-accent-base-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
 >
 {isLoading ? t("common.loading") : t("bankSync.connectButton")}
 </button>
 </form>
 </div>
 </div>
 );
};
