import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { UserService } from "@/services/userService";
import { SubscriptionService } from "@/services/subscriptionService";
import { PaymentService } from "@/services/paymentService";
import {
  FaArrowLeft,
  FaUserShield,
  FaUser,
  FaCheck,
  FaBan,
  FaExclamationTriangle,
} from "react-icons/fa";

export const UserDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { token, logout, refreshToken } = useAuth();

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

  const numericUserId = Number(userId);

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ["admin-user-detail", numericUserId],
    queryFn: async () => {
      const result = await userService.getUser(numericUserId);
      if ("error" in result) throw new Error(result.error);
      return result;
    },
    enabled: !isNaN(numericUserId),
  });

  const { data: subscription } = useQuery({
    queryKey: ["admin-user-subscription", userId],
    queryFn: async () => {
      if (!userId) return null;
      const result = await subscriptionService.getSubscription(userId);
      if ("error" in result) return null;
      return result;
    },
    enabled: !!userId,
  });

  const { data: payments } = useQuery({
    queryKey: ["admin-user-payments", userId],
    queryFn: async () => {
      if (!userId) return null;
      const result = await paymentService.listPayments({
        userId,
        page: 1,
        pageSize: 10,
      });
      if ("error" in result) return null;
      return result;
    },
    enabled: !!userId,
  });

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: "bg-green-500/10 text-green-400 border border-green-500/20",
      past_due: "bg-red-500/10 text-red-400 border border-red-500/20",
      canceled: "bg-slate-600/30 text-slate-300 border border-slate-600/30",
      paused: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
      disabled: "bg-red-500/10 text-red-400 border border-red-500/20",
      PAID: "bg-green-500/10 text-green-400 border border-green-500/20",
      PENDING: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
      FAILED: "bg-red-500/10 text-red-400 border border-red-500/20",
      CREATED: "bg-slate-600/30 text-slate-300 border border-slate-600/30",
      REFUNDED:
        "bg-purple-500/10 text-purple-400 border border-purple-500/20",
    };
    return `inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.CREATED}`;
  };

  if (userLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <FaArrowLeft className="w-4 h-4" />
        <span>Back</span>
      </button>

      {/* User Header */}
      {user && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-slate-700 rounded-full flex items-center justify-center">
              <span className="text-2xl text-white font-semibold">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white">{user.username}</h1>
              <p className="text-slate-400">{user.email}</p>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                  user.role === "admin"
                    ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                    : "bg-slate-600/30 text-slate-300 border border-slate-600/30"
                }`}
              >
                {user.role === "admin" ? (
                  <FaUserShield className="w-3 h-3" />
                ) : (
                  <FaUser className="w-3 h-3" />
                )}
                {user.role}
              </span>
              <span className={statusBadge(user.status)}>
                {user.status === "active" ? (
                  <FaCheck className="w-3 h-3 mr-1" />
                ) : (
                  <FaBan className="w-3 h-3 mr-1" />
                )}
                {user.status}
              </span>
            </div>
          </div>
          {user.created_at && (
            <p className="text-xs text-slate-500 mt-3">
              Registered: {new Date(user.created_at).toLocaleDateString()}
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscription */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-slate-700">
            <h2 className="text-lg font-semibold text-white">Subscription</h2>
          </div>
          <div className="p-6">
            {subscription ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Plan</span>
                  <span className="text-sm text-white font-mono">
                    {subscription.plan_code}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Status</span>
                  <span className={statusBadge(subscription.status)}>
                    {subscription.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Started</span>
                  <span className="text-sm text-white">
                    {new Date(subscription.started_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Expires</span>
                  <span className="text-sm text-white">
                    {subscription.expires_at
                      ? new Date(
                          subscription.expires_at,
                        ).toLocaleDateString()
                      : "-"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Auto-Renew</span>
                  <span className="text-sm">
                    {subscription.auto_renew ? (
                      <FaCheck className="w-3 h-3 text-green-400" />
                    ) : (
                      <FaBan className="w-3 h-3 text-slate-500" />
                    )}
                  </span>
                </div>
                {subscription.paddle_subscription_id && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">
                      Paddle Sub ID
                    </span>
                    <span className="text-xs text-slate-300 font-mono">
                      {subscription.paddle_subscription_id}
                    </span>
                  </div>
                )}
                {subscription.cancellation_reason && (
                  <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <FaExclamationTriangle className="w-3 h-3 text-red-400" />
                      <span className="text-sm text-red-400 font-medium">
                        Cancellation
                      </span>
                    </div>
                    <p className="text-xs text-slate-300">
                      Reason: {subscription.cancellation_reason}
                    </p>
                    {subscription.cancellation_comment && (
                      <p className="text-xs text-slate-400 mt-1">
                        {subscription.cancellation_comment}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">
                No active subscription
              </p>
            )}
          </div>
        </div>

        {/* Payment History */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-slate-700">
            <h2 className="text-lg font-semibold text-white">
              Payment History
            </h2>
          </div>
          <div className="p-6">
            {payments && payments.items.length > 0 ? (
              <div className="space-y-3">
                {payments.items.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between py-3 px-4 bg-slate-900/50 rounded-lg"
                  >
                    <div>
                      <p className="text-sm text-white font-semibold">
                        {payment.amount} {payment.currency}
                      </p>
                      <p className="text-xs text-slate-400">
                        {payment.plan_code || payment.purpose} &middot;{" "}
                        {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={statusBadge(payment.status)}>
                      {payment.status}
                    </span>
                  </div>
                ))}
                {payments.total > 10 && (
                  <button
                    onClick={() => navigate(`/payments?userId=${userId}`)}
                    className="w-full text-center text-xs text-cyan-400 hover:text-cyan-300 py-2"
                  >
                    View all {payments.total} payments
                  </button>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">
                No payment history
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
