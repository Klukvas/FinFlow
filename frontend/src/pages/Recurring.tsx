import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { recurringApiService, RecurringPayment, PaymentStatistics } from '@/services/api/recurringApi';
import { CreateRecurringPayment, RecurringPaymentCard, RecurringPaymentStats } from '@/components/ui/recurring';
import { FaPlus, FaSearch } from 'react-icons/fa';
import { toast } from 'sonner';

export const Recurring: React.FC = () => {
  const { user } = useAuth();
  const [payments, setPayments] = useState<RecurringPayment[]>([]);
  const [stats, setStats] = useState<PaymentStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    payment_type: '',
    search: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchPayments = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await recurringApiService.getRecurringPayments(user.id, {
        status: filters?.status,
        payment_type: filters?.payment_type,
        page: currentPage,
        size: 10,
      });
      
      setPayments(response.items);
      setTotalPages(response.pages);
    } catch (error) {
      console.error('Failed to fetch recurring payments:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!user?.id) return;

    try {
      const response = await recurringApiService.getPaymentStatistics(user.id);
      setStats(response);
    } catch (error) {
      console.error('Failed to fetch payment statistics:', error);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchPayments();
      fetchStats();
    }
  }, [user?.id, filters, currentPage]);

  const handleCreateSuccess = () => {
    setShowCreateModal(false);
    fetchPayments();
    fetchStats();
  };

  const handleDelete = async (paymentId: string) => {
    if (!user?.id) return;
    
    try {
      await recurringApiService.deleteRecurringPayment(user.id, paymentId);
      fetchPayments();
      fetchStats();
      toast.success('Повторяющийся платеж успешно удален');
    } catch (error) {
      console.error('Failed to delete recurring payment:', error);
      toast.error('Ошибка при удалении повторяющегося платежа');
    }
  };

  const handlePause = async (paymentId: string) => {
    if (!user?.id) return;

    try {
      await recurringApiService.pauseRecurringPayment(user.id, paymentId);
      fetchPayments();
      toast.success('Повторяющийся платеж приостановлен');
    } catch (error) {
      console.error('Failed to pause recurring payment:', error);
      toast.error('Ошибка при приостановке повторяющегося платежа');
    }
  };

  const handleResume = async (paymentId: string) => {
    if (!user?.id) return;

    try {
      await recurringApiService.resumeRecurringPayment(user.id, paymentId);
      fetchPayments();
      toast.success('Повторяющийся платеж возобновлен');
    } catch (error) {
      console.error('Failed to resume recurring payment:', error);
      toast.error('Ошибка при возобновлении повторяющегося платежа');
    }
  };

  const handleEdit = (payment: RecurringPayment) => {
    // TODO: Implement edit functionality
    console.log('Edit payment:', payment);
  };

  const filteredPayments = payments.filter(payment => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        payment.name.toLowerCase().includes(searchLower) ||
        (payment.description && payment.description.toLowerCase().includes(searchLower))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">Повторяющиеся платежи</h1>
          <p className="theme-text-secondary">Управление автоматическими платежами</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center px-4 py-2 theme-accent-bg theme-text-inverse rounded-lg hover:theme-accent-hover theme-transition"
        >
          <FaPlus className="w-4 h-4 mr-2" />
          Создать платеж
        </button>
      </div>

      {/* Statistics */}
      {stats && <RecurringPaymentStats stats={stats} />}

      {/* Filters */}
      <div className="theme-surface theme-shadow rounded-lg p-4 border theme-border">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium theme-text-secondary mb-2">
              Поиск
            </label>
            <div className="relative">
              <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 theme-text-tertiary w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск по названию..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full pl-10 pr-3 py-2 theme-surface theme-border border rounded-md theme-text-primary placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium theme-text-secondary mb-2">
              Статус
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 theme-surface theme-border border rounded-md theme-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
            >
              <option value="">Все статусы</option>
              <option value="active">Активные</option>
              <option value="paused">Приостановленные</option>
              <option value="completed">Завершенные</option>
              <option value="cancelled">Отмененные</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-secondary mb-2">
              Тип платежа
            </label>
            <select
              value={filters.payment_type}
              onChange={(e) => setFilters(prev => ({ ...prev, payment_type: e.target.value }))}
              className="w-full px-3 py-2 theme-surface theme-border border rounded-md theme-text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
            >
              <option value="">Все типы</option>
              <option value="EXPENSE">Расходы</option>
              <option value="INCOME">Доходы</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => setFilters({ status: '', payment_type: '', search: '' })}
              className="w-full px-4 py-2 theme-text-secondary theme-bg-tertiary theme-border border rounded-md hover:theme-surface-hover theme-transition"
            >
              Сбросить фильтры
            </button>
          </div>
        </div>
      </div>

      {/* Payments List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 theme-accent"></div>
          </div>
        ) : filteredPayments.length === 0 ? (
          <div className="text-center py-8">
            <p className="theme-text-secondary text-lg">Нет повторяющихся платежей</p>
            <p className="theme-text-tertiary">Создайте первый повторяющийся платеж</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredPayments.map((payment) => (
              <RecurringPaymentCard
                key={payment.id}
                payment={payment}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onPause={handlePause}
                onResume={handleResume}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 theme-text-secondary theme-surface theme-border border rounded-md hover:theme-surface-hover disabled:opacity-50 disabled:cursor-not-allowed theme-transition"
          >
            Предыдущая
          </button>
          
          <span className="px-3 py-2 theme-text-secondary">
            Страница {currentPage} из {totalPages}
          </span>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 theme-text-secondary theme-surface theme-border border rounded-md hover:theme-surface-hover disabled:opacity-50 disabled:cursor-not-allowed theme-transition"
          >
            Следующая
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateRecurringPayment
          onSuccess={handleCreateSuccess}
          onCancel={() => setShowCreateModal(false)}
        />
      )}
    </div>
  );
};
