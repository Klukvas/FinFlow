import React from 'react';
import { PaymentStatistics } from '@/services/api/recurringApi';
import { FaChartBar, FaPlay, FaPause, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

interface RecurringPaymentStatsProps {
  stats: PaymentStatistics;
}

export const RecurringPaymentStats: React.FC<RecurringPaymentStatsProps> = ({ stats }) => {
  const statCards = [
    {
      title: 'Всего платежей',
      value: stats.total_payments,
      icon: FaChartBar,
      color: 'theme-accent-bg',
      textColor: 'theme-accent',
    },
    {
      title: 'Активные',
      value: stats.active_payments,
      icon: FaPlay,
      color: 'theme-success-bg',
      textColor: 'theme-success',
    },
    {
      title: 'Приостановленные',
      value: stats.paused_payments,
      icon: FaPause,
      color: 'theme-warning-bg',
      textColor: 'theme-warning',
    },
    {
      title: 'Выполнено за месяц',
      value: stats.executed_this_month,
      icon: FaCheckCircle,
      color: 'theme-success-bg',
      textColor: 'theme-success',
    },
    {
      title: 'Ошибок за месяц',
      value: stats.failed_this_month,
      icon: FaTimesCircle,
      color: 'theme-error-bg',
      textColor: 'theme-error',
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div key={index} className="theme-surface rounded-lg theme-shadow p-4 theme-border border">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg ${stat.color} mr-3`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm theme-text-tertiary">{stat.title}</p>
                <p className={`text-2xl font-bold ${stat.textColor}`}>
                  {stat.value}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
