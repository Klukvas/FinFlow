import React from 'react';
import { RecurringPayment } from '@/services/api/recurringApi';
import { DeleteButton } from '@/components/ui';
import { FaPlay, FaPause, FaEdit } from 'react-icons/fa';

interface RecurringPaymentCardProps {
  payment: RecurringPayment;
  onEdit: (payment: RecurringPayment) => void;
  onDelete: (paymentId: string) => void;
  onPause: (paymentId: string) => void;
  onResume: (paymentId: string) => void;
}

export const RecurringPaymentCard: React.FC<RecurringPaymentCardProps> = ({
  payment,
  onEdit,
  onDelete,
  onPause,
  onResume,
}) => {
  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'theme-success-light theme-success';
      case 'paused':
        return 'theme-warning-light theme-warning';
      case 'completed':
        return 'theme-accent-light theme-accent';
      case 'cancelled':
        return 'theme-error-light theme-error';
      default:
        return 'theme-bg-tertiary theme-text-primary';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Активен';
      case 'paused':
        return 'Приостановлен';
      case 'completed':
        return 'Завершен';
      case 'cancelled':
        return 'Отменен';
      default:
        return status;
    }
  };

  const getScheduleText = () => {
    switch (payment.schedule_type) {
      case 'daily':
        return 'Ежедневно';
      case 'weekly':
        const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
        return `Еженедельно (${days[payment.schedule_config.day_of_week || 0]})`;
      case 'monthly':
        return `Ежемесячно (${payment.schedule_config.day_of_month || 1} число)`;
      case 'yearly':
        const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                       'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        return `Ежегодно (${payment.schedule_config.day || 1} ${months[(payment.schedule_config.month || 1) - 1]})`;
      default:
        return payment.schedule_type;
    }
  };

  return (
    <div className="theme-surface rounded-lg theme-shadow p-6 theme-border border">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold theme-text-primary mb-1">
            {payment.name}
          </h3>
          {payment.description && (
            <p className="theme-text-secondary text-sm mb-2">{payment.description}</p>
          )}
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(payment.status)}`}>
          {getStatusText(payment.status)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm theme-text-tertiary">Сумма</p>
          <p className="text-lg font-semibold theme-text-primary">
            {formatAmount(payment.amount, payment.currency)}
          </p>
        </div>
        <div>
          <p className="text-sm theme-text-tertiary">Тип</p>
          <p className="text-sm font-medium theme-text-primary">
            {payment.payment_type === 'expense' ? 'Расход' : 'Доход'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">

        <div>
          <p className="text-sm theme-text-tertiary mb-1">Расписание</p>
          <p className="text-sm font-medium theme-text-primary">{getScheduleText()}</p>
        </div>

        <div>
          <p className="text-sm theme-text-tertiary">Последнее выполнение</p>
          <p className="text-sm font-medium theme-text-primary">{payment.last_executed ? formatDate(payment.last_executed) : 'Нет выполнений'}</p>
        </div>
      </div>


      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm theme-text-tertiary">Дата начала</p>
          <p className="text-sm font-medium theme-text-primary">
            {formatDate(payment.start_date)}
          </p>
        </div>
        <div>
          <p className="text-sm theme-text-tertiary">Следующее выполнение</p>
          <p className="text-sm font-medium theme-text-primary">
            {formatDate(payment.next_execution)}
          </p>
        </div>
      </div>

      {payment.end_date && (
        <div className="mb-4">
          <p className="text-sm theme-text-tertiary">Дата окончания</p>
          <p className="text-sm font-medium theme-text-primary">
            {formatDate(payment.end_date)}
          </p>
        </div>
      )}

      {payment.last_executed && (
        <div className="mb-4">
          <p className="text-sm theme-text-tertiary">Последнее выполнение</p>
          <p className="text-sm font-medium theme-text-primary">
            {formatDate(payment.last_executed)}
          </p>
        </div>
      )}

      <div className="flex justify-end space-x-2">
        {payment.status === 'active' && (
          <button
            onClick={() => onPause(payment.id)}
            className="p-2 theme-warning hover:theme-warning-light rounded-md theme-transition"
            title="Приостановить"
          >
            <FaPause className="w-4 h-4" />
          </button>
        )}
        
        {payment.status === 'paused' && (
          <button
            onClick={() => onResume(payment.id)}
            className="p-2 theme-success hover:theme-success-light rounded-md theme-transition"
            title="Возобновить"
          >
            <FaPlay className="w-4 h-4" />
          </button>
        )}

        <button
          onClick={() => onEdit(payment)}
          className="p-2 theme-accent hover:theme-accent-light rounded-md theme-transition"
          title="Редактировать"
        >
          <FaEdit className="w-4 h-4" />
        </button>

        <DeleteButton
          onDelete={() => onDelete(payment.id)}
          variant="icon"
          size="md"
        />
      </div>
    </div>
  );
};
