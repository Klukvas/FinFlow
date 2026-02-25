import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { UserService } from "@/services/userService";
import { SubscriptionService } from "@/services/subscriptionService";
import { PaymentService } from "@/services/paymentService";
import {
  FaUsers,
  FaCreditCard,
  FaExclamationTriangle,
  FaMoneyBillWave,
  FaArrowRight,
} from "react-icons/fa";

export const Dashboard: React.FC = () => {
  const { token, logout, refreshToken } = useAuth();
  const navigate = useNavigate();

  const userService = React.useMemo(
    () => new UserService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const subscriptionService = React.useMemo(
    () => new SubscriptionService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const paymentService = React.useMemo(
    () => new PaymentService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const { data: usersData } = useQuery({
    queryKey: ["dashboard-users"],
    queryFn: async () => {
      const result = await userService.listUsers({ page: 1, pageSize: 1 });
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const { data: subStats } = useQuery({
    queryKey: ["dashboard-sub-stats"],
    queryFn: async () => {
      const result = await subscriptionService.getSubscriptionStats();
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const { data: paymentStats } = useQuery({
    queryKey: ["dashboard-payment-stats"],
    queryFn: async () => {
      const result = await paymentService.getPaymentStats();
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const { data: recentPayments } = useQuery({
    queryKey: ["dashboard-recent-payments"],
    queryFn: async () => {
      const result = await paymentService.listPayments({
        page: 1,
        pageSize: 5,
      });
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const { data: pastDueSubs } = useQuery({
    queryKey: ["dashboard-past-due"],
    queryFn: async () => {
      const result = await subscriptionService.listSubscriptions({
        status: "past_due",
        page: 1,
        pageSize: 5,
      });
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const statCards = [
    {
      label: "Total Users",
      value: usersData?.total ?? "-",
      icon: FaUsers,
      color: "cyan",
      onClick: () => navigate("/users"),
    },
    {
      label: "Active Subscriptions",
      value: subStats?.active ?? "-",
      icon: FaCreditCard,
      color: "green",
      onClick: () => navigate("/subscriptions?status=active"),
    },
    {
      label: "Past Due",
      value: subStats?.past_due ?? "-",
      icon: FaExclamationTriangle,
      color: subStats?.past_due ? "red" : "slate",
      onClick: () => navigate("/subscriptions?status=past_due"),
    },
    {
      label: "Total Revenue",
      value: paymentStats
        ? `${Number(paymentStats.total_revenue).toLocaleString()}`
        : "-",
      icon: FaMoneyBillWave,
      color: "emerald",
      onClick: () => navigate("/payments"),
    },
  ];

  const colorMap: Record<string, string> = {
    cyan: "from-cyan-500/20 to-cyan-500/5 border-cyan-500/20 text-cyan-400",
    green:
      "from-green-500/20 to-green-500/5 border-green-500/20 text-green-400",
    red: "from-red-500/20 to-red-500/5 border-red-500/20 text-red-400",
    slate:
      "from-slate-600/20 to-slate-600/5 border-slate-600/20 text-slate-400",
    emerald:
      "from-emerald-500/20 to-emerald-500/5 border-emerald-500/20 text-emerald-400",
  };

  const iconColorMap: Record<string, string> = {
    cyan: "text-cyan-400",
    green: "text-green-400",
    red: "text-red-400",
    slate: "text-slate-400",
    emerald: "text-emerald-400",
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active:
        "bg-green-500/10 text-green-400 border border-green-500/20",
      past_due:
        "bg-red-500/10 text-red-400 border border-red-500/20",
      canceled:
        "bg-slate-600/30 text-slate-300 border border-slate-600/30",
      PAID: "bg-green-500/10 text-green-400 border border-green-500/20",
      PENDING:
        "bg-amber-500/10 text-amber-400 border border-amber-500/20",
      FAILED: "bg-red-500/10 text-red-400 border border-red-500/20",
      CREATED:
        "bg-slate-600/30 text-slate-300 border border-slate-600/30",
    };
    return `inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.CREATED}`;
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Overview of your platform</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <button
              key={card.label}
              onClick={card.onClick}
              className={`bg-gradient-to-br ${colorMap[card.color]} border rounded-xl p-6 text-left transition-all hover:scale-[1.02]`}
            >
              <div className="flex items-center justify-between mb-4">
                <Icon className={`w-6 h-6 ${iconColorMap[card.color]}`} />
                <FaArrowRight className="w-3 h-3 text-slate-500" />
              </div>
              <p className="text-3xl font-bold text-white mb-1">
                {card.value}
              </p>
              <p className="text-sm text-slate-400">{card.label}</p>
            </button>
          );
        })}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Past Due Subscriptions */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="flex items-center justify-between p-6 border-b border-slate-700">
            <h2 className="text-lg font-semibold text-white">
              Needs Attention
            </h2>
            <button
              onClick={() => navigate("/subscriptions?status=past_due")}
              className="text-xs text-cyan-400 hover:text-cyan-300"
            >
              View all
            </button>
          </div>
          <div className="p-6">
            {pastDueSubs?.items.length === 0 ? (
              <p className="text-sm text-slate-500 italic">
                No past due subscriptions
              </p>
            ) : (
              <div className="space-y-3">
                {pastDueSubs?.items.map((sub) => (
                  <div
                    key={sub.id}
                    className="flex items-center justify-between py-2 px-3 bg-slate-900/50 rounded-lg"
                  >
                    <div>
                      <p className="text-sm text-white font-mono">
                        {sub.user_id}
                      </p>
                      <p className="text-xs text-slate-400">{sub.plan_code}</p>
                    </div>
                    <span className={statusBadge(sub.status)}>
                      {sub.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Payments */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="flex items-center justify-between p-6 border-b border-slate-700">
            <h2 className="text-lg font-semibold text-white">
              Recent Payments
            </h2>
            <button
              onClick={() => navigate("/payments")}
              className="text-xs text-cyan-400 hover:text-cyan-300"
            >
              View all
            </button>
          </div>
          <div className="p-6">
            {recentPayments?.items.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No payments yet</p>
            ) : (
              <div className="space-y-3">
                {recentPayments?.items.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between py-2 px-3 bg-slate-900/50 rounded-lg"
                  >
                    <div>
                      <p className="text-sm text-white">
                        {payment.amount} {payment.currency}
                      </p>
                      <p className="text-xs text-slate-400">
                        {payment.user_id} &middot;{" "}
                        {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={statusBadge(payment.status)}>
                      {payment.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
