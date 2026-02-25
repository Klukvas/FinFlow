import React from "react";
import { FaTimes, FaExclamationTriangle } from "react-icons/fa";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning";
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
  onConfirm,
  onCancel,
}) => {
  const confirmStyles =
    variant === "danger"
      ? "bg-red-500 hover:bg-red-400 text-white"
      : "bg-amber-500 hover:bg-amber-400 text-white";

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-sm">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                variant === "danger"
                  ? "bg-red-500/10"
                  : "bg-amber-500/10"
              }`}
            >
              <FaExclamationTriangle
                className={`w-5 h-5 ${
                  variant === "danger" ? "text-red-400" : "text-amber-400"
                }`}
              />
            </div>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
          </div>
          <button
            onClick={onCancel}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6">
          <p className="text-slate-300">{message}</p>
        </div>

        <div className="flex gap-3 p-6 border-t border-slate-700">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`flex-1 py-2.5 rounded-xl transition-colors disabled:opacity-50 ${confirmStyles}`}
          >
            {isLoading ? "..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
