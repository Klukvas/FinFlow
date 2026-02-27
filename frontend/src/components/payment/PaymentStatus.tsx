import React from "react";
import { useTranslation } from "react-i18next";
import { PaymentStatus as PaymentStatusEnum } from "@/types/payment";
import {
  FaCheckCircle,
  FaTimesCircle,
  FaClock,
  FaSpinner,
  FaExclamationTriangle,
  FaUndo,
} from "react-icons/fa";

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
      icon: FaClock,
      color: "theme-text-secondary",
      bg: "theme-bg-secondary",
      label: t("payment.status.created"),
    },
    [PaymentStatusEnum.PENDING]: {
      icon: FaSpinner,
      color: "text-blue-500",
      bg: "bg-blue-100",
      label: t("payment.status.pending"),
      animate: true,
    },
    [PaymentStatusEnum.PAID]: {
      icon: FaCheckCircle,
      color: "text-green-500",
      bg: "bg-green-100",
      label: t("payment.status.paid"),
    },
    [PaymentStatusEnum.FAILED]: {
      icon: FaTimesCircle,
      color: "text-red-500",
      bg: "bg-red-100",
      label: t("payment.status.failed"),
    },
    [PaymentStatusEnum.EXPIRED]: {
      icon: FaExclamationTriangle,
      color: "text-orange-500",
      bg: "bg-orange-100",
      label: t("payment.status.expired"),
    },
    [PaymentStatusEnum.REFUNDED]: {
      icon: FaUndo,
      color: "text-purple-500",
      bg: "bg-purple-100",
      label: t("payment.status.refunded"),
    },
    [PaymentStatusEnum.PARTIALLY_REFUNDED]: {
      icon: FaUndo,
      color: "text-purple-400",
      bg: "bg-purple-50",
      label: t("payment.status.partiallyRefunded"),
    },
    [PaymentStatusEnum.CANCELED]: {
      icon: FaTimesCircle,
      color: "theme-text-secondary",
      bg: "theme-bg-secondary",
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
        className={`${iconSizes[size]} ${config.animate ? "animate-spin" : ""}`}
      />
      {showLabel && <span>{config.label}</span>}
    </div>
  );
};
