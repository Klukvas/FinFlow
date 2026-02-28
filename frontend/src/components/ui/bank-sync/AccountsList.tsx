import React from "react";
import { useTranslation } from "react-i18next";
import { FaToggleOn, FaToggleOff, FaCreditCard } from "react-icons/fa";
import { LinkedAccount } from "@/types/bankSync";
import { AccountResponse } from "@/types";

interface AccountsListProps {
  accounts: LinkedAccount[];
  finflowAccounts: AccountResponse[];
  onLinkAccount: (linkedAccountId: number, finflowAccountId: number) => void;
  onToggleSync: (linkedAccountId: number) => void;
}

export const AccountsList: React.FC<AccountsListProps> = ({
  accounts,
  finflowAccounts,
  onLinkAccount,
  onToggleSync,
}) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-3">
      <h3 className="font-medium theme-text-primary">
        {t("bankSync.linkedAccounts")}
      </h3>
      {accounts.map((account) => (
        <div
          key={account.id}
          className="theme-surface rounded-lg p-4 theme-border border"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 theme-accent-light rounded-lg flex items-center justify-center">
                <FaCreditCard className="w-5 h-5 theme-accent" />
              </div>
              <div>
                <p className="font-medium theme-text-primary text-sm">
                  {account.account_name || t("bankSync.unknownAccount")}
                </p>
                <p className="text-xs theme-text-secondary">
                  {account.masked_pan && <span>{account.masked_pan}</span>}
                  {account.iban && (
                    <span className="ml-2">{account.iban}</span>
                  )}
                  {!account.masked_pan && !account.iban && (
                    <span>{account.currency || "—"}</span>
                  )}
                </p>
              </div>
            </div>
            <button
              onClick={() => onToggleSync(account.id)}
              className="theme-transition"
              title={
                account.is_synced
                  ? t("bankSync.disableSync")
                  : t("bankSync.enableSync")
              }
            >
              {account.is_synced ? (
                <FaToggleOn className="w-6 h-6 text-green-500" />
              ) : (
                <FaToggleOff className="w-6 h-6 theme-text-secondary" />
              )}
            </button>
          </div>

          <div>
            <label className="block text-xs theme-text-secondary mb-1">
              {t("bankSync.mapToAccount")}
            </label>
            <select
              value={account.finflow_account_id || ""}
              onChange={(e) => {
                const val = e.target.value;
                if (val) onLinkAccount(account.id, parseInt(val, 10));
              }}
              className="w-full px-3 py-1.5 theme-bg theme-border border rounded-md text-sm theme-text-primary"
            >
              <option value="">{t("bankSync.selectAccount")}</option>
              {finflowAccounts.map((fa) => (
                <option key={fa.id} value={fa.id}>
                  {fa.name} ({fa.currency})
                </option>
              ))}
            </select>
          </div>
        </div>
      ))}
    </div>
  );
};
