import React from "react";
import { useTranslation } from "react-i18next";
import { MyInvite } from "@/types";
import {
  Users,
  Check,
  X,
  Clock,
  Eye,
  Pencil,
  User,
  Loader2,
} from "lucide-react";

interface MyInviteCardProps {
  invite: MyInvite;
  onAccept: (inviteId: string) => void;
  onReject: (inviteId: string) => void;
  isLoading?: boolean;
  loadingAction?: "accept" | "reject" | null;
}

export const MyInviteCard: React.FC<MyInviteCardProps> = ({
  invite,
  onAccept,
  onReject,
  isLoading = false,
  loadingAction = null,
}) => {
  const { t } = useTranslation();

  const getRoleBadge = () => {
    const roleConfig = {
      read: {
        icon: <Eye className="w-3 h-3" />,
        className: "bg-[var(--accent-dim)] text-accent-base",
        label: t("workspace.roles.read", "View Only"),
      },
      full: {
        icon: <Pencil className="w-3 h-3" />,
        className: "bg-[var(--success-dim)] text-success-base",
        label: t("workspace.roles.full", "Full Access"),
      },
    };

    const config = roleConfig[invite.role] || roleConfig.read;
    return (
      <span
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${config.className}`}
      >
        {config.icon}
        {config.label}
      </span>
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
      return t("common.timeAgo.minutes", "{{count}} min ago", {
        count: diffMins,
      });
    } else if (diffHours < 24) {
      return t("common.timeAgo.hours", "{{count}}h ago", { count: diffHours });
    } else {
      return t("common.timeAgo.days", "{{count}}d ago", { count: diffDays });
    }
  };

  const formatExpiresIn = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();

    if (diffMs <= 0) {
      return t("workspace.invite.expired", "Expired");
    }

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays > 0) {
      return t("workspace.invite.expiresInDays", "Expires in {{count}} days", {
        count: diffDays,
      });
    } else if (diffHours > 0) {
      return t(
        "workspace.invite.expiresInHours",
        "Expires in {{count}} hours",
        { count: diffHours },
      );
    } else {
      return t("workspace.invite.expiresSoon", "Expires soon");
    }
  };

  const isExpired =
    invite.is_expired || new Date(invite.expires_at) <= new Date();
  const canRespond = invite.is_actionable && !isExpired;

  return (
    <div className="p-5 rounded-xl bg-elevated border border-[var(--border)] shadow-sm hover:shadow-md transition-colors">
      {/* Header - Workspace Info */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-[var(--accent-dim)] text-accent-base">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-content text-lg">
              {invite.workspace_name}
            </h3>
            <div className="flex items-center gap-2 text-sm text-content-secondary mt-0.5">
              <User className="w-3 h-3" />
              <span>
                {t("workspace.invite.from", "From")}{" "}
                <span className="font-medium">{invite.inviter_email}</span>
              </span>
            </div>
          </div>
        </div>
        {getRoleBadge()}
      </div>

      {/* Inviter info */}
      <div className="p-3 rounded-lg bg-surface-alt mb-4">
        <p className="text-sm text-content-secondary">
          <span className="font-medium text-content">
            {invite.inviter_email}
          </span>{" "}
          {t("workspace.invite.invitedYou", "invited you to collaborate")}
        </p>
      </div>

      {/* Time info */}
      <div className="flex items-center justify-between text-sm text-content-tertiary mb-4">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{formatTimeAgo(invite.created_at)}</span>
        </div>
        <span className={isExpired ? "text-danger-base font-medium" : ""}>
          {isExpired
            ? t("workspace.invite.expired", "Expired")
            : formatExpiresIn(invite.expires_at)}
        </span>
      </div>

      {/* Actions */}
      {canRespond ? (
        <div className="flex items-center gap-3">
          <button
            onClick={() => onReject(invite.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-[var(--border)] text-content-secondary hover:bg-surface-alt hover:text-danger-base font-medium transition-colors disabled:opacity-50"
            disabled={isLoading}
          >
            {loadingAction === "reject" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <X className="w-4 h-4" />
            )}
            {t("workspace.invite.reject", "Decline")}
          </button>
          <button
            onClick={() => onAccept(invite.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-accent-base text-white font-medium hover:bg-accent-base-hover transition-colors disabled:opacity-50"
            disabled={isLoading}
          >
            {loadingAction === "accept" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            {t("workspace.invite.accept", "Accept")}
          </button>
        </div>
      ) : (
        <div className="text-center py-2 rounded-lg bg-surface-alt text-sm text-content-tertiary">
          {isExpired
            ? t(
                "workspace.invite.expiredMessage",
                "This invitation has expired",
              )
            : t(
                "workspace.invite.alreadyResponded",
                "You have already responded to this invitation",
              )}
        </div>
      )}
    </div>
  );
};

export default MyInviteCard;
