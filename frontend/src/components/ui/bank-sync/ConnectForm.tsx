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
      <div className="theme-surface rounded-lg p-6 shadow-sm theme-border border">
        <div className="text-center mb-6">
          <div className="w-16 h-16 theme-accent-light rounded-full flex items-center justify-center mx-auto mb-4">
            <FaLink className="w-8 h-8 theme-accent" />
          </div>
          <h2 className="text-xl font-semibold theme-text-primary mb-2">
            {t("bankSync.connectTitle")}
          </h2>
          <p className="theme-text-secondary text-sm">
            {t("bankSync.connectDescription")}
          </p>
        </div>

        <div className="theme-bg rounded-lg p-4 mb-6">
          <h3 className="font-medium theme-text-primary text-sm mb-3">
            {t("bankSync.howToGetToken")}
          </h3>
          <ol className="space-y-2 text-sm theme-text-secondary">
            <li className="flex items-start gap-2">
              <span className="theme-accent font-bold">1.</span>
              {t("bankSync.step1")}
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-accent font-bold">2.</span>
              {t("bankSync.step2")}
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-accent font-bold">3.</span>
              {t("bankSync.step3")}
            </li>
          </ol>
          <a
            href="https://api.monobank.ua/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm theme-accent hover:underline mt-3"
          >
            api.monobank.ua <FaExternalLinkAlt className="w-3 h-3" />
          </a>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label
              htmlFor="monobank-token"
              className="block text-sm font-medium theme-text-primary mb-1"
            >
              {t("bankSync.tokenLabel")}
            </label>
            <input
              id="monobank-token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder={t("bankSync.tokenPlaceholder")}
              className="w-full px-3 py-2 theme-bg theme-border border rounded-lg theme-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
              autoComplete="off"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !token.trim()}
            className="w-full py-2.5 px-4 rounded-lg font-medium text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed theme-transition"
          >
            {isLoading ? t("common.loading") : t("bankSync.connectButton")}
          </button>
        </form>
      </div>
    </div>
  );
};
