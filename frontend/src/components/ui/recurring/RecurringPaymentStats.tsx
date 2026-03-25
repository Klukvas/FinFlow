import React from "react";
import { PaymentStatistics } from "@/services/api/recurringApi";
import { BarChart3, Play, Pause, CheckCircle2, XCircle } from "lucide-react";

interface RecurringPaymentStatsProps {
  stats: PaymentStatistics;
}

export const RecurringPaymentStats: React.FC<RecurringPaymentStatsProps> = ({
  stats,
}) => {
  const statCards = [
    {
      title: "Всего платежей",
      value: stats.total_payments,
      icon: BarChart3,
      color: "bg-accent-base",
      textColor: "text-accent-base",
    },
    {
      title: "Активные",
      value: stats.active_payments,
      icon: Play,
      color: "bg-success-base",
      textColor: "text-success-base",
    },
    {
      title: "Приостановленные",
      value: stats.paused_payments,
      icon: Pause,
      color: "bg-warning-base",
      textColor: "text-warning-base",
    },
    {
      title: "Выполнено за месяц",
      value: stats.executed_this_month,
      icon: CheckCircle2,
      color: "bg-success-base",
      textColor: "text-success-base",
    },
    {
      title: "Ошибок за месяц",
      value: stats.failed_this_month,
      icon: XCircle,
      color: "bg-danger-base",
      textColor: "text-danger-base",
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div
            key={index}
            className="bg-elevated rounded-lg theme-shadow p-4 border-[var(--border)] border"
          >
            <div className="flex items-center">
              <div className={`p-2 rounded-lg ${stat.color} mr-3`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm text-content-tertiary">{stat.title}</p>
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
