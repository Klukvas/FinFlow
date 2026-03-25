import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useApiClients } from "@/hooks/useApiClients";
import { Category, ExpenseResponse, CategoryExpenseStatistics } from "@/types";
import { IncomeOut, CategoryIncomeStatistics } from "@/types/income";
import { Button } from "@/components/ui/shared/Button";
import { Modal } from "@/components/ui/shared/Modal";
import { ArrowLeft, Pencil, Trash2, Plus } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/utils/logger";

export const CategoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { category, expense, income } = useApiClients();

  const [categoryData, setCategoryData] = useState<Category | null>(null);
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [incomes, setIncomes] = useState<IncomeOut[]>([]);
  const [expenseStatistics, setExpenseStatistics] =
    useState<CategoryExpenseStatistics | null>(null);
  const [incomeStatistics, setIncomeStatistics] =
    useState<CategoryIncomeStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const fetchCategoryData = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      const [categoryResponse, expensesResponse, incomesResponse] =
        await Promise.all([
          category.getCategory(parseInt(id)),
          expense.getExpensesByCategory(parseInt(id)),
          income.getIncomesByCategory(parseInt(id)),
        ]);

      if ("error" in categoryResponse) {
        setError(categoryResponse.error);
        return;
      }

      setCategoryData(categoryResponse);

      // Обрабатываем расходы
      if ("error" in expensesResponse) {
        logger.error("Error fetching expenses:", expensesResponse.error);
        setExpenses([]);
        setExpenseStatistics(null);
      } else {
        setExpenses(expensesResponse.expenses);
        setExpenseStatistics(expensesResponse.statistics);
      }

      // Обрабатываем доходы
      if ("error" in incomesResponse) {
        logger.warn(
          "Error fetching incomes (endpoint may not be available yet):",
          incomesResponse.error,
        );
        setIncomes([]);
        setIncomeStatistics(null);
      } else {
        setIncomes(incomesResponse.incomes);
        setIncomeStatistics(incomesResponse.statistics);
      }
    } catch (err) {
      setError("Ошибка при загрузке данных категории");
      logger.error("Error fetching category data:", err);
    } finally {
      setLoading(false);
    }
  }, [id, category, expense, income]);

  useEffect(() => {
    fetchCategoryData();
  }, [fetchCategoryData]);

  const handleDeleteCategory = async () => {
    if (!categoryData) return;

    try {
      const response = await category.deleteCategory(categoryData.id);
      if (response && "error" in response) {
        toast.error(response.error);
      } else {
        toast.success("Категория успешно удалена");
        navigate("/category");
      }
    } catch (err) {
      toast.error("Ошибка при удалении категории");
      logger.error("Error deleting category:", err);
    }
  };

  const handleEditCategory = () => {
    if (categoryData) {
      navigate(`/category/${categoryData.id}/edit`);
    }
  };

  // Получаем данные в зависимости от типа категории
  const isIncomeCategory = categoryData?.type === "INCOME";
  const items = (isIncomeCategory ? incomes : expenses) || [];

  // Use backend statistics for both expenses and incomes
  const totalAmount = isIncomeCategory
    ? incomeStatistics?.total_amount || 0
    : expenseStatistics?.total_amount || 0;
  const itemsCount = items.length;
  const averageAmount = isIncomeCategory
    ? incomeStatistics?.average_amount || 0
    : expenseStatistics?.average_amount || 0;
  const currency = isIncomeCategory
    ? incomeStatistics?.currency || "₴"
    : expenseStatistics?.currency || "₴";

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 text-accent-base"></div>
      </div>
    );
  }

  if (error || !categoryData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate("/category")}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад к категориям
          </Button>
        </div>
        <div className="bg-[var(--danger-dim)] text-danger-base-border border-[var(--border)] border rounded-lg p-6">
          <p className="text-danger-base">{error || "Категория не найдена"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate("/category")}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-content">
              {categoryData.name}
            </h1>
            <p className="text-content-secondary mt-1">
              Детали категории и связанные расходы
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={handleEditCategory}
            className="flex items-center gap-2"
          >
            <Pencil className="w-4 h-4" />
            Редактировать
          </Button>
          <Button
            variant="danger"
            onClick={() => setShowDeleteModal(true)}
            className="flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Удалить
          </Button>
        </div>
      </div>

      {/* Category Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border p-6">
          <h3 className="text-lg font-semibold text-content mb-4">
            Информация о категории
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-content-secondary">Название:</span>
              <span className="text-content font-medium">
                {categoryData.name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-content-secondary">Тип:</span>
              <span
                className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  categoryData.type === "INCOME"
                    ? "bg-[var(--success-dim)] text-success-base"
                    : "bg-[var(--danger-dim)] text-danger-base"
                }`}
              >
                {categoryData.type === "INCOME" ? "Доходы" : "Расходы"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-content-secondary">ID:</span>
              <span className="text-content">#{categoryData.id}</span>
            </div>
            {categoryData.parent_id && (
              <div className="flex justify-between">
                <span className="text-content-secondary">
                  Родительская категория:
                </span>
                <span className="text-content">
                  ID: {categoryData.parent_id}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border p-6">
          <h3 className="text-lg font-semibold text-content mb-4">
            {isIncomeCategory ? "Статистика доходов" : "Статистика расходов"}
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-content-secondary">
                Всего {isIncomeCategory ? "доходов" : "расходов"}:
              </span>
              <span className="text-content font-medium">{itemsCount}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-content-secondary">Общая сумма:</span>
              <span className="text-content font-medium">
                {totalAmount.toFixed(2)} {currency}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-content-secondary">Средняя сумма:</span>
              <span className="text-content font-medium">
                {averageAmount.toFixed(2)} {currency}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border p-6">
          <h3 className="text-lg font-semibold text-content mb-4">
            Быстрые действия
          </h3>
          <div className="space-y-3">
            <Button
              variant="primary"
              onClick={() =>
                navigate(isIncomeCategory ? "/income" : "/expense")
              }
              className="w-full flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              {isIncomeCategory ? "Добавить доход" : "Добавить расход"}
            </Button>
            <Button
              variant="secondary"
              onClick={() =>
                navigate(
                  `${isIncomeCategory ? "/income" : "/expense"}?category=${categoryData.id}`,
                )
              }
              className="w-full"
            >
              Просмотреть все {isIncomeCategory ? "доходы" : "расходы"}
            </Button>
          </div>
        </div>
      </div>

      {/* Recent Items */}
      {items.length > 0 && (
        <div className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border">
          <div className="bg-accent-base px-6 py-4">
            <h3 className="text-lg font-semibold text-content-inverse">
              Последние {isIncomeCategory ? "доходы" : "расходы"}
            </h3>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="min-w-full border-[var(--border)] divide-y">
                <thead className="bg-elevated-secondary">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-content-tertiary uppercase tracking-wider">
                      Дата
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-content-tertiary uppercase tracking-wider">
                      Описание
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-content-tertiary uppercase tracking-wider">
                      Сумма
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-elevated divide-y border-[var(--border)]">
                  {items.slice(0, 10).map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-surface-alt transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-content">
                          {item.date
                            ? new Date(item.date).toLocaleDateString()
                            : "—"}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-content">
                          {item.description || "Без описания"}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm font-medium text-content">
                          {item.amount.toFixed(2)} {currency}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {items.length > 10 && (
              <div className="mt-4 text-center">
                <Button
                  variant="secondary"
                  onClick={() =>
                    navigate(
                      `${isIncomeCategory ? "/income" : "/expense"}?category=${categoryData.id}`,
                    )
                  }
                >
                  Показать все {isIncomeCategory ? "доходы" : "расходы"} (
                  {items.length})
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Подтверждение удаления"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-content">
            Вы уверены, что хотите удалить категорию{" "}
            <strong>{categoryData.name}</strong>?
          </p>
          <p className="text-content-secondary text-sm">
            Это действие нельзя отменить. Все связанные расходы будут перемещены
            в категорию "Без категории".
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => setShowDeleteModal(false)}
            >
              Отмена
            </Button>
            <Button variant="danger" onClick={handleDeleteCategory}>
              Удалить
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default CategoryDetail;
