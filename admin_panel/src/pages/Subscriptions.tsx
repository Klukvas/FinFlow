import React, { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate, useSearchParams } from "react-router-dom";
import { SubscriptionService } from "@/services/subscriptionService";
import {
  FaSearch,
  FaCheck,
  FaBan,
  FaExclamationTriangle,
  FaPause,
  FaChevronLeft,
  FaChevronRight,
} from "react-icons/fa";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "active", label: "Active" },
  { value: "past_due", label: "Past Due" },
  { value: "canceled", label: "Canceled" },
  { value: "paused", label: "Paused" },
];

export const Subscriptions: React.FC = () => {
  const { token, logout, refreshToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [statusFilter, setStatusFilter] = useState(
    searchParams.get("status") || "",
  );
  const [planFilter, setPlanFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const subscriptionService = React.useMemo(
    () => new SubscriptionService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const { data, isLoading, error } = useQuery({
    queryKey: [
      "admin-subscriptions",
      statusFilter,
      planFilter,
      search,
      page,
      pageSize,
    ],
    queryFn: async () => {
      const result = await subscriptionService.listSubscriptions({
        status: statusFilter || undefined,
        planCode: planFilter || undefined,
        userId: search || undefined,
        page,
        pageSize,
      });
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const { data: plansData } = useQuery({
    queryKey: ["admin-plans-filter"],
    queryFn: async () => {
      const result = await subscriptionService.listPlans();
      if ("error" in result) throw new Error(result.error);
      return result;
    },
  });

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setSearch(searchInput);
      setPage(1);
    },
    [searchInput],
  );

  const statusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <FaCheck className="w-3 h-3" />;
      case "past_due":
        return <FaExclamationTriangle className="w-3 h-3" />;
      case "canceled":
        return <FaBan className="w-3 h-3" />;
      case "paused":
        return <FaPause className="w-3 h-3" />;
      default:
        return null;
    }
  };

  const statusStyle = (status: string) => {
    const styles: Record<string, string> = {
      active: "bg-green-500/10 text-green-400 border border-green-500/20",
      past_due: "bg-red-500/10 text-red-400 border border-red-500/20",
      canceled: "bg-slate-600/30 text-slate-300 border border-slate-600/30",
      paused: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
    };
    return `inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${styles[status] || styles.canceled}`;
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Subscriptions</h1>
        <p className="text-slate-400">View all user subscriptions</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <form onSubmit={handleSearch} className="relative">
          <FaSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by user ID..."
            className="pl-11 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors w-64"
          />
        </form>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-cyan-500 transition-colors"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={planFilter}
          onChange={(e) => {
            setPlanFilter(e.target.value);
            setPage(1);
          }}
          className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-cyan-500 transition-colors"
        >
          <option value="">All Plans</option>
          {plansData?.items.map((plan) => (
            <option key={plan.code} value={plan.code}>
              {plan.name}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          {error.message}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      ) : (
        <>
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden mb-6">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    User ID
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Plan
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Status
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Started
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Expires
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Auto-Renew
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Provider
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((sub) => (
                  <tr
                    key={sub.id}
                    onClick={() => navigate(`/users/${sub.user_id}`)}
                    className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors cursor-pointer"
                  >
                    <td className="px-6 py-4 text-sm text-white font-mono">
                      {sub.user_id}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {sub.plan_code}
                    </td>
                    <td className="px-6 py-4">
                      <span className={statusStyle(sub.status)}>
                        {statusIcon(sub.status)}
                        {sub.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {new Date(sub.started_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {sub.expires_at
                        ? new Date(sub.expires_at).toLocaleDateString()
                        : "-"}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {sub.auto_renew ? (
                        <FaCheck className="w-3 h-3 text-green-400" />
                      ) : (
                        <FaBan className="w-3 h-3 text-slate-500" />
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {sub.payment_provider || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                No subscriptions found
              </div>
            )}
          </div>

          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, data.total)} of {data.total}{" "}
                subscriptions
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FaChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-4 py-2 text-sm text-slate-300">
                  Page {page} of {data.total_pages}
                </span>
                <button
                  onClick={() =>
                    setPage((p) => Math.min(data.total_pages, p + 1))
                  }
                  disabled={page === data.total_pages}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FaChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
