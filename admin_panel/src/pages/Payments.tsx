import React, { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { PaymentService } from "@/services/paymentService";
import { AdminPayment } from "@/types";
import {
  FaSearch,
  FaChevronLeft,
  FaChevronRight,
  FaChevronDown,
  FaChevronUp,
} from "react-icons/fa";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "PAID", label: "Paid" },
  { value: "PENDING", label: "Pending" },
  { value: "CREATED", label: "Created" },
  { value: "FAILED", label: "Failed" },
  { value: "EXPIRED", label: "Expired" },
  { value: "REFUNDED", label: "Refunded" },
  { value: "CANCELED", label: "Canceled" },
];

export const Payments: React.FC = () => {
  const { token, logout, refreshToken } = useAuth();

  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const pageSize = 15;

  const paymentService = React.useMemo(
    () => new PaymentService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-payments", statusFilter, search, page, pageSize],
    queryFn: async () => {
      const result = await paymentService.listPayments({
        status: statusFilter || undefined,
        userId: search || undefined,
        page,
        pageSize,
      });
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

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const statusStyle = (status: string) => {
    const styles: Record<string, string> = {
      PAID: "bg-green-500/10 text-green-400 border border-green-500/20",
      PENDING: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
      CREATED: "bg-slate-600/30 text-slate-300 border border-slate-600/30",
      FAILED: "bg-red-500/10 text-red-400 border border-red-500/20",
      EXPIRED: "bg-slate-600/30 text-slate-400 border border-slate-600/30",
      REFUNDED: "bg-purple-500/10 text-purple-400 border border-purple-500/20",
      PARTIALLY_REFUNDED:
        "bg-purple-500/10 text-purple-400 border border-purple-500/20",
      CANCELED: "bg-slate-600/30 text-slate-400 border border-slate-600/30",
    };
    return `inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.CREATED}`;
  };

  const renderExpandedRow = (payment: AdminPayment) => (
    <tr>
      <td colSpan={8} className="px-6 py-4 bg-slate-900/50">
        <div className="space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-slate-500">Order Reference</p>
              <p className="text-white font-mono text-xs">
                {payment.order_reference}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Provider</p>
              <p className="text-white">{payment.provider}</p>
            </div>
            <div>
              <p className="text-slate-500">Paid At</p>
              <p className="text-white">
                {payment.paid_at
                  ? new Date(payment.paid_at).toLocaleString()
                  : "-"}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Failure Reason</p>
              <p className="text-white">{payment.failure_reason || "-"}</p>
            </div>
          </div>

          {payment.events.length > 0 && (
            <div>
              <p className="text-sm text-slate-400 mb-2">Events</p>
              <div className="space-y-1">
                {payment.events.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center gap-4 py-1.5 px-3 bg-slate-800 rounded text-xs"
                  >
                    <span className="text-slate-500">
                      {new Date(event.created_at).toLocaleString()}
                    </span>
                    <span className="text-cyan-400 font-mono">
                      {event.event_type}
                    </span>
                    {event.status_before && event.status_after && (
                      <span className="text-slate-400">
                        {event.status_before} &rarr; {event.status_after}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </td>
    </tr>
  );

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Payments</h1>
        <p className="text-slate-400">View all payment transactions</p>
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
                  <th className="w-10 px-4 py-4"></th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    User ID
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Amount
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Status
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Plan
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Provider
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Purpose
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((payment) => (
                  <React.Fragment key={payment.id}>
                    <tr
                      onClick={() => toggleExpand(payment.id)}
                      className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors cursor-pointer"
                    >
                      <td className="px-4 py-4 text-slate-500">
                        {expandedId === payment.id ? (
                          <FaChevronUp className="w-3 h-3" />
                        ) : (
                          <FaChevronDown className="w-3 h-3" />
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        {payment.user_id}
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-semibold">
                        {payment.amount} {payment.currency}
                      </td>
                      <td className="px-6 py-4">
                        <span className={statusStyle(payment.status)}>
                          {payment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {payment.plan_code || "-"}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {payment.provider}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {payment.purpose}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                    {expandedId === payment.id && renderExpandedRow(payment)}
                  </React.Fragment>
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                No payments found
              </div>
            )}
          </div>

          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, data.total)} of {data.total} payments
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
