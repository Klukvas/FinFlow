import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useApiClients } from "@/hooks/useApiClients";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { IncomeCreate, AccountResponse } from "@/types";
import { Button } from "@/components/ui/shared/Button";
import { FormattedNumberInput } from "@/components/ui/forms/FormattedNumberInput";
import { CurrencySelect, CategorySelect } from "@/components/ui/forms";
import { removeSpacesFromNumber } from "@/utils/numberFormat";
// removed unused icon and config imports

interface CreateIncomeProps {
  onIncomeCreated: () => void;
}

export const CreateIncome: React.FC<CreateIncomeProps> = ({
  onIncomeCreated,
}) => {
  const { t } = useTranslation();
  const { income, account } = useApiClients();
  const { handleIncomeError } = useErrorHandler();
  const [formData, setFormData] = useState<IncomeCreate>({
    amount: 0,
    category_id: null,
    description: "",
    date: new Date().toISOString().split("T")[0] as string,
    account_id: null,
    currency: "USD",
  });
  const [amountDisplay, setAmountDisplay] = useState("");
  const [accounts, setAccounts] = useState<AccountResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await account.getAccounts();
        if ("error" in response) {
          logger.error("Failed to fetch accounts:", response.error);
        } else {
          setAccounts(response);
        }
      } catch (err) {
        logger.error("Error fetching accounts:", err);
      }
    };

    fetchAccounts();
  }, [account]);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >,
  ) => {
    const { name, value } = e.target;

    if (name === "account_id") {
      setFormData((prev) => ({
        ...prev,
        [name]: value ? parseInt(value) : null,
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleCategoryChange = (categoryId: number | null) => {
    setFormData((prev) => ({
      ...prev,
      category_id: categoryId,
    }));
  };

  const handleAmountChange = (value: string) => {
    setAmountDisplay(value);
    const cleanedValue = removeSpacesFromNumber(value);
    setFormData((prev) => ({ ...prev, amount: parseFloat(cleanedValue) || 0 }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (formData.amount <= 0) {
        setError(t("income.form.amountMustBePositive"));
        return;
      }

      const response = await income.createIncome(formData);

      if ("error" in response && "errorCode" in response) {
        // Handle API error with errorCode
        handleIncomeError(response as any);
        return;
      } else {
        onIncomeCreated();
        setFormData({
          amount: 0,
          category_id: null,
          description: "",
          date: new Date().toISOString().split("T")[0],
          account_id: null,
          currency: "USD",
        });
        setAmountDisplay("");
      }
    } catch (err) {
      // Handle network or other errors
      handleIncomeError(err as Error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
      <div className="space-y-4 sm:space-y-6">
        {/* Amount */}
        <FormattedNumberInput
          label={t("income.form.amount")}
          value={amountDisplay}
          onChange={handleAmountChange}
          placeholder="0"
          required
          error={
            formData.amount <= 0 ? t("income.form.amountMustBePositive") : ""
          }
          className="w-full"
        />

        {/* Currency */}
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold theme-text-primary"
            htmlFor="currency"
          >
            {t("income.form.currency")}
          </label>
          <CurrencySelect
            value={formData.currency || "USD"}
            onChange={(value) =>
              handleInputChange({ target: { name: "currency", value } } as any)
            }
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            showFlags={true}
          />
        </div>

        {/* Category */}
        <CategorySelect
          value={formData.category_id || null}
          onChange={handleCategoryChange}
          categoryType="INCOME"
          optional={true}
          showEmptyOption={true}
        />

        {/* Account */}
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold theme-text-primary"
            htmlFor="account_id"
          >
            {t("income.form.account")}
            <span className="theme-text-tertiary font-normal ml-1">
              {t("income.form.optional")}
            </span>
          </label>
          <select
            id="account_id"
            name="account_id"
            value={formData.account_id || ""}
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
          >
            <option value="">{t("income.form.noAccount")}</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.currency})
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold theme-text-primary"
            htmlFor="description"
          >
            {t("income.form.description")}
            <span className="theme-text-tertiary font-normal ml-1">
              {t("income.form.optional")}
            </span>
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description || ""}
            onChange={handleInputChange}
            placeholder={t("income.form.descriptionPlaceholder")}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg resize-none text-sm sm:text-base min-h-[88px]"
            rows={3}
            maxLength={500}
          />
        </div>

        {/* Date */}
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold theme-text-primary"
            htmlFor="date"
          >
            {t("income.form.date")}
            <span className="text-red-500 ml-1">*</span>
          </label>
          <input
            type="date"
            id="date"
            name="date"
            value={formData.date || ""}
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            required
          />
        </div>

        {error && (
          <div className="theme-error-light theme-border border rounded-lg sm:rounded-xl p-3 sm:p-4">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-4 h-4 sm:w-5 sm:h-5 theme-error flex-shrink-0">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <p className="theme-error text-xs sm:text-sm font-medium">
                {error}
              </p>
            </div>
          </div>
        )}
      </div>

      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        loading={isLoading}
      >
        {t("income.form.createIncome")}
      </Button>
    </form>
  );
};
