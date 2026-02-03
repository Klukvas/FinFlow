import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClients } from '@/hooks/useApiClients';
import { RecurringPayment, PaymentStatistics } from '@/services/api/recurringApi';
import { CreateRecurringPayment, RecurringPaymentCard, RecurringPaymentStats } from '@/components/ui/recurring';
import { FaPlus } from 'react-icons/fa';
import { toast } from 'sonner';

export const Recurring: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { recurring } = useApiClients();
  const [payments, setPayments] = useState<RecurringPayment[]>([]);
  const [stats, setStats] = useState<PaymentStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchPayments = useCallback(async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await recurring.getRecurringPayments({
        page: currentPage,
        size: 10,
      });
      
      if ('error' in response) {
        console.error('Failed to fetch recurring payments:', response.error);
        return;
      }
      
      setPayments(response.items);
      setTotalPages(response.pages);
    } catch (error) {
      console.error('Failed to fetch recurring payments:', error);
    } finally {
      setLoading(false);
    }
  }, [user?.id, currentPage, recurring]);

  const fetchStats = useCallback(async () => {
    if (!user?.id) return;

    try {
      const response = await recurring.getPaymentStatistics();
      if ('error' in response) {
        console.error('Failed to fetch payment statistics:', response.error);
        return;
      }
      setStats(response);
    } catch (error) {
      console.error('Failed to fetch payment statistics:', error);
    }
  }, [user?.id, recurring]);

  useEffect(() => {
    if (user?.id) {
      Promise.all([fetchPayments(), fetchStats()]);
    }
  }, [user?.id, currentPage, fetchPayments, fetchStats]);

  const handleCreateSuccess = () => {
    setShowCreateModal(false);
    Promise.all([fetchPayments(), fetchStats()]);
  };

  const handleDelete = async (paymentId: string) => {
    if (!user?.id) return;
    
    try {
      const response = await recurring.deleteRecurringPayment(paymentId);
      if (response && 'error' in response) {
        toast.error(response.error);
        return;
      }
      Promise.all([fetchPayments(), fetchStats()]);
      toast.success(t('recurring.messages.paymentDeleted'));
    } catch (error) {
      console.error('Failed to delete recurring payment:', error);
      toast.error(t('recurring.messages.deleteFailed'));
    }
  };

  const handlePause = async (paymentId: string) => {
    if (!user?.id) return;

    try {
      const response = await recurring.pauseRecurringPayment(paymentId);
      if (response && 'error' in response) {
        toast.error(response.error);
        return;
      }
      fetchPayments();
      toast.success(t('recurring.messages.paymentPaused'));
    } catch (error) {
      console.error('Failed to pause recurring payment:', error);
      toast.error(t('recurring.messages.pauseFailed'));
    }
  };

  const handleResume = async (paymentId: string) => {
    if (!user?.id) return;

    try {
      const response = await recurring.resumeRecurringPayment(paymentId);
      if (response && 'error' in response) {
        toast.error(response.error);
        return;
      }
      fetchPayments();
      toast.success(t('recurring.messages.paymentResumed'));
    } catch (error) {
      console.error('Failed to resume recurring payment:', error);
      toast.error(t('recurring.messages.resumeFailed'));
    }
  };

  const handleEdit = (payment: RecurringPayment) => {
    // TODO: Implement edit functionality
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">{t('recurring.title')}</h1>
          <p className="theme-text-secondary">{t('recurring.subtitle')}</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center px-4 py-2 theme-accent-bg theme-text-inverse rounded-lg hover:theme-accent-hover theme-transition"
        >
          <FaPlus className="w-4 h-4 mr-2" />
          {t('recurring.createButton')}
        </button>
      </div>

      {/* Statistics */}
      {stats && <RecurringPaymentStats stats={stats} />}

      {/* Payments List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 theme-accent"></div>
          </div>
        ) : payments.length === 0 ? (
          <div className="text-center py-8">
            <p className="theme-text-secondary text-lg">{t('recurring.emptyState.title')}</p>
            <p className="theme-text-tertiary">{t('recurring.emptyState.description')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {payments.map((payment) => (
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
            {t('recurring.pagination.previous')}
          </button>
          
          <span className="px-3 py-2 theme-text-secondary">
            {t('recurring.pagination.page')} {currentPage} {t('recurring.pagination.of')} {totalPages}
          </span>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 theme-text-secondary theme-surface theme-border border rounded-md hover:theme-surface-hover disabled:opacity-50 disabled:cursor-not-allowed theme-transition"
          >
            {t('recurring.pagination.next')}
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
