import React from "react";
import { useTranslation } from "react-i18next";
import { WorkspaceInvite, InviteStatus } from "@/types";
import {
  FaEnvelope,
  FaClock,
  FaTimes,
  FaCheck,
  FaBan,
  FaHourglass,
  FaEye,
  FaEdit,
} from "react-icons/fa";

interface InviteCardProps {
  invite: WorkspaceInvite;
  onCancel?: (inviteId: string) => void;
  isLoading?: boolean;
}

export const InviteCard: React.FC<InviteCardProps> = ({
  invite,
  onCancel,
  isLoading = false,
}) => {
  const { t } = useTranslation();

  const getStatusBadge = (status: InviteStatus, isExpired: boolean) => {
    // Check if actually expired (time-based)
    const effectiveStatus =
      status === "pending" && isExpired ? "expired" : status;

    const statusConfig: Record<
      string,
      { icon: React.ReactNode; className: string; label: string }
    > = {
      pending: {
        icon: <FaHourglass className="w-3 h-3" />,
        className: "theme-warning-light theme-warning",
        label: t("workspace.invite.status.pending", "Pending"),
      },
      accepted: {
        icon: <FaCheck className="w-3 h-3" />,
        className: "theme-success-light theme-success",
        label: t("workspace.invite.status.accepted", "Accepted"),
      },
      rejected: {
        icon: <FaBan className="w-3 h-3" />,
        className: "theme-error-light theme-error",
        label: t("workspace.invite.status.rejected", "Rejected"),
      },
      expired: {
        icon: <FaClock className="w-3 h-3" />,
        className: "theme-bg-secondary theme-text-secondary",
        label: t("workspace.invite.status.expired", "Expired"),
      },
      canceled: {
        icon: <FaTimes className="w-3 h-3" />,
        className: "theme-bg-secondary theme-text-secondary",
        label: t("workspace.invite.status.canceled", "Canceled"),
      },
    };

    const config = statusConfig[effectiveStatus] || statusConfig.pending;
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
      >
        {config.icon}
        {config.label}
      </span>
    );
  };

  const getRoleBadge = () => {
    const roleConfig = {
      read: {
        icon: <FaEye className="w-3 h-3" />,
        className: "theme-accent-light theme-accent",
        label: t("workspace.roles.read", "View Only"),
      },
      full: {
        icon: <FaEdit className="w-3 h-3" />,
        className: "theme-success-light theme-success",
        label: t("workspace.roles.full", "Full Access"),
      },
    };

    const config = roleConfig[invite.role] || roleConfig.read;
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
      >
        {config.icon}
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const canCancel = invite.status === "pending" && !invite.is_expired;

  return (
    <div className="flex items-center justify-between p-4 rounded-lg theme-surface-hover border theme-border">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div className="p-2 rounded-lg theme-bg-secondary theme-text-secondary">
          <FaEnvelope className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium theme-text-primary truncate">
              {invite.invitee_email}
            </span>
            {getRoleBadge()}
          </div>
          <div className="flex items-center gap-2 text-sm theme-text-tertiary mt-0.5">
            <span>
              {t("workspace.invite.sentAt", "Sent")}{" "}
              {formatDate(invite.created_at)}
            </span>
            {invite.status === "pending" && (
              <>
                <span>•</span>
                <span className={invite.is_expired ? "text-red-500" : ""}>
                  {invite.is_expired
                    ? t("workspace.invite.expired", "Expired")
                    : t("workspace.invite.expiresAt", "Expires") +
                      " " +
                      formatDate(invite.expires_at)}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {getStatusBadge(invite.status, invite.is_expired)}

        {canCancel && onCancel && (
          <button
            onClick={() => onCancel(invite.id)}
            className="p-2 rounded-lg hover:theme-surface-hover text-red-500 theme-transition"
            title={t("workspace.invite.cancel", "Cancel Invite")}
            disabled={isLoading}
          >
            <FaTimes className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default InviteCard;
