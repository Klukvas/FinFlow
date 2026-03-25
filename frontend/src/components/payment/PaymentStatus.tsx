import React from "react";
import { useTranslation } from "react-i18next";
import { PaymentStatus as PaymentStatusEnum } from "@/types/payment";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertTriangle,
  Undo2,
} from "lucide-react";

interface PaymentStatusProps {
  status: PaymentStatusEnum;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const PaymentStatusBadge: React.FC<PaymentStatusProps> = ({
  status,
  showLabel = true,
  size = "md",
  className = "",
}) => {
  const { t } = useTranslation();

  const statusConfig = {
    [PaymentStatusEnum.CREATED]: {
      icon: Clock,
      color: "text-content-secondary",
      bg: "bg-surface-alt",
      label: t("payment.status.created"),
    },
    [PaymentStatusEnum.PENDING]: {
      icon: Loader2,
      color: "text-accent-base",
      bg: "bg-[var(--accent-dim)]",
      label: t("payment.status.pending"),
      animate: true,
    },
    [PaymentStatusEnum.PAID]: {
      icon: CheckCircle2,
      color: "text-success-base",
      bg: "bg-[var(--success-dim)]",
      label: t("payment.status.paid"),
    },
    [PaymentStatusEnum.FAILED]: {
      icon: XCircle,
      color: "text-danger-base",
      bg: "bg-[var(--danger-dim)]",
      label: t("payment.status.failed"),
    },
    [PaymentStatusEnum.EXPIRED]: {
      icon: AlertTriangle,
      color: "text-warning-base",
      bg: "bg-[var(--warning-dim)]",
      label: t("payment.status.expired"),
    },
    [PaymentStatusEnum.REFUNDED]: {
      icon: Undo2,
      color: "text-[var(--purple)]",
      bg: "bg-[var(--purple-dim)]",
      label: t("payment.status.refunded"),
    },
    [PaymentStatusEnum.PARTIALLY_REFUNDED]: {
      icon: Undo2,
      color: "text-[var(--purple)]",
      bg: "bg-[var(--purple-dim)]",
      label: t("payment.status.partiallyRefunded"),
    },
    [PaymentStatusEnum.CANCELED]: {
      icon: XCircle,
      color: "text-content-secondary",
      bg: "bg-surface-alt",
      label: t("payment.status.canceled"),
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "px-2 py-1 text-xs",
    md: "px-3 py-1.5 text-sm",
    lg: "px-4 py-2 text-base",
  };

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full font-medium ${config.bg} ${config.color} ${sizeClasses[size]} ${className}`}
    >
      <Icon
        className={`${iconSizes[size]} ${"animate" in config && config.animate ? "animate-spin" : ""}`}
      />
      {showLabel && <span>{config.label}</span>}
    </div>
  );
};
