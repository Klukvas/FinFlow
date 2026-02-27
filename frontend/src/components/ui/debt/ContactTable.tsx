import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { ContactResponse, ContactSummary } from "../../../types/contact";
import { Button } from "../shared/Button";
import { useCurrencyConversion } from "../../../hooks/useCurrencyConversion";

interface ContactTableProps {
  contacts: ContactResponse[];
  contactSummaries: ContactSummary[];
  loading: boolean;
  onEdit: (contact: ContactResponse) => void;
  onDelete: (contact: ContactResponse) => void;
  onCreateClick: () => void;
}

export const ContactTable: React.FC<ContactTableProps> = ({
  contacts,
  contactSummaries,
  loading,
  onEdit,
  onDelete,
  onCreateClick,
}) => {
  const { t } = useTranslation();
  const { formatCurrency, userCurrency } = useCurrencyConversion();

  // Merge contacts with their summaries
  const enrichedContacts = useMemo(() => {
    const summaryMap = new Map(contactSummaries.map((s) => [s.id, s]));
    return contacts.map((c) => ({
      ...c,
      debts_count: summaryMap.get(c.id)?.debts_count ?? 0,
      total_debt_amount: summaryMap.get(c.id)?.total_debt_amount ?? 0,
    }));
  }, [contacts, contactSummaries]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-6 w-6 border-2 border-[var(--color-accent)] border-t-transparent" />
        <span className="ml-3 theme-text-secondary text-sm">
          {t("debtPage.contactsTable.loading")}
        </span>
      </div>
    );
  }

  if (contacts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 theme-bg-tertiary rounded-xl flex items-center justify-center">
          <svg
            className="w-8 h-8 theme-text-tertiary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold theme-text-primary mb-1">
          {t("debtPage.contactsTable.noContactsAtAll")}
        </h3>
        <p className="theme-text-secondary text-sm max-w-md mx-auto mb-4">
          {t("debtPage.contactsTable.noContactsSubtitle")}
        </p>
        <Button variant="primary" size="sm" onClick={onCreateClick}>
          {t("debtPage.addContact")}
        </Button>
      </div>
    );
  }

  const thClasses =
    "px-4 py-3 text-xs font-semibold theme-text-secondary uppercase tracking-wider";

  return (
    <div className="w-full">
      {/* Mobile Cards View */}
      <div className="block lg:hidden space-y-2 p-4">
        {enrichedContacts.map((contact) => (
          <div
            key={contact.id}
            className="theme-bg-secondary rounded-lg border theme-border p-3 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium theme-text-primary">
                  {contact.name}
                </p>
                {contact.company && (
                  <p className="text-xs theme-text-tertiary mt-0.5">
                    {contact.company}
                  </p>
                )}
                {contact.email && (
                  <a
                    href={`mailto:${contact.email}`}
                    className="text-xs theme-accent hover:underline mt-0.5 block"
                  >
                    {contact.email}
                  </a>
                )}
                <div className="flex items-center gap-3 mt-1.5">
                  <span className="text-xs theme-text-secondary">
                    {contact.debts_count}{" "}
                    {t("debtPage.contactsTable.debtCount").toLowerCase()}
                  </span>
                  {contact.total_debt_amount > 0 && (
                    <span className="text-xs text-red-500/80 tabular-nums">
                      {formatCurrency(contact.total_debt_amount, userCurrency)}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(contact)}
                  className="theme-text-secondary hover:theme-text-primary !p-1.5 !min-h-0"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(contact)}
                  className="text-red-500 hover:text-red-600 !p-1.5 !min-h-0"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop Table View */}
      <div className="hidden lg:block">
        <div className="overflow-hidden">
          <table className="w-full">
            <thead className="theme-bg-secondary sticky top-0 z-10">
              <tr>
                <th className={`${thClasses} text-left`}>
                  {t("debtPage.contactsTable.name")}
                </th>
                <th className={`${thClasses} text-left`}>
                  {t("debtPage.contactsTable.company")}
                </th>
                <th className={`${thClasses} text-left`}>
                  {t("debtPage.contactsTable.email")}
                </th>
                <th className={`${thClasses} text-right`}>
                  {t("debtPage.contactsTable.debtCount")}
                </th>
                <th className={`${thClasses} text-right`}>
                  {t("debtPage.contactsTable.totalDebt")}
                </th>
                <th className={`${thClasses} text-right`}>
                  {t("debtPage.contactsTable.actions")}
                </th>
              </tr>
            </thead>
            <tbody className="theme-surface divide-y theme-border">
              {enrichedContacts.map((contact) => (
                <tr
                  key={contact.id}
                  className="hover:theme-surface-hover transition-colors group"
                >
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium theme-text-primary">
                      {contact.name}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm theme-text-secondary">
                      {contact.company || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {contact.email ? (
                      <a
                        href={`mailto:${contact.email}`}
                        className="text-sm theme-accent hover:underline"
                      >
                        {contact.email}
                      </a>
                    ) : (
                      <span className="text-sm theme-text-tertiary">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm theme-text-secondary tabular-nums">
                      {contact.debts_count}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-red-500/80 tabular-nums">
                      {contact.total_debt_amount > 0
                        ? formatCurrency(
                            contact.total_debt_amount,
                            userCurrency,
                          )
                        : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(contact)}
                        className="theme-text-secondary hover:theme-text-primary !p-1.5 !min-h-0"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                          />
                        </svg>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(contact)}
                        className="text-red-500 hover:text-red-600 !p-1.5 !min-h-0"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
