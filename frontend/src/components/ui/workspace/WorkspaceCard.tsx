import React from "react";
import { useTranslation } from "react-i18next";
import {
  Lock,
  Users,
  User,
  Crown,
  Archive,
  Pencil,
  LogOut,
  UserCog,
} from "lucide-react";
import { Workspace } from "@/types";

interface WorkspaceCardProps {
  workspace: Workspace;
  isCurrentWorkspace: boolean;
  onSelect: (workspaceId: string) => void;
  onEdit: (workspace: Workspace) => void;
  onArchive: (workspace: Workspace) => void;
  onLeave: (workspace: Workspace) => void;
  onManageMembers?: (workspace: Workspace) => void;
}

export const WorkspaceCard: React.FC<WorkspaceCardProps> = ({
  workspace,
  isCurrentWorkspace,
  onSelect,
  onEdit,
  onArchive,
  onLeave,
  onManageMembers,
}) => {
  const { t } = useTranslation();

  const isOwner = workspace.current_user_role === "owner";
  const canEdit = isOwner; // Only owner can edit workspace settings
  const canLeave = !isOwner && workspace.type !== "personal";
  const canArchive = isOwner && workspace.type !== "personal";
  const canManageMembers = workspace.type === "shared"; // Can manage members for shared workspaces

  const getRoleBadge = () => {
    const roleConfig: Record<string, { className: string; icon?: boolean }> = {
      owner: {
        className: "bg-[var(--warning-dim)] text-warning-base",
        icon: true,
      },
      full: {
        className: "bg-[var(--success-dim)] text-success-base",
      },
      read: {
        className: "bg-[var(--accent-dim)] text-accent-base",
      },
    };

    const role = workspace.current_user_role || "read";
    const config = roleConfig[role] ?? roleConfig.read!;
    return (
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
      >
        {config.icon && <Crown className="inline w-3 h-3 mr-1" />}
        {t(`workspace.roles.${role}`, role)}
      </span>
    );
  };

  return (
    <div
      data-testid={`workspace-card-${workspace.id}`}
      className={`relative p-4 rounded-xl bg-elevated border-[var(--border)] border transition-colors hover:shadow-md ${
        isCurrentWorkspace
          ? "ring-2 ring-offset-2 text-accent-base ring-current"
          : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div
            className={`p-2.5 rounded-lg ${
              workspace.type === "personal"
                ? "bg-[var(--success-dim)] text-success-base"
                : "bg-[var(--accent-dim)] text-accent-base"
            }`}
          >
            {workspace.type === "personal" ? (
              <User className="w-5 h-5" />
            ) : (
              <Users className="w-5 h-5" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <h3
              data-testid={`workspace-name-${workspace.id}`}
              className="font-semibold text-content truncate flex items-center gap-1.5"
            >
              {workspace.name}
              {workspace.is_read_only && (
                <Lock className="w-4 h-4 text-warning-base flex-shrink-0" />
              )}
            </h3>
            <p
              data-testid={`workspace-type-${workspace.id}`}
              className="text-sm text-content-tertiary"
            >
              {workspace.type === "personal"
                ? t("workspace.personal", "Personal")
                : t("workspace.shared", "Shared")}
            </p>
          </div>
        </div>
        {getRoleBadge()}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 mb-4 text-sm text-content-secondary">
        {workspace.member_count !== null && (
          <div
            data-testid={`workspace-member-count-${workspace.id}`}
            className="flex items-center gap-1"
          >
            <Users className="w-4 h-4" />
            <span>
              {workspace.member_count} {t("workspace.members", "members")}
            </span>
          </div>
        )}
        <div className="text-xs text-content-tertiary">
          {t("workspace.created", "Created")}{" "}
          {new Date(workspace.created_at).toLocaleDateString()}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t border-[var(--border)]">
        {!isCurrentWorkspace && (
          <button
            onClick={() => onSelect(workspace.id)}
            className="flex-1 px-3 py-2 text-sm font-medium text-accent-base bg-[var(--accent-dim)] rounded-lg hover:opacity-80 transition-colors"
          >
            {t("workspace.select", "Select")}
          </button>
        )}
        {isCurrentWorkspace && (
          <span className="flex-1 px-3 py-2 text-sm font-medium text-center text-content-tertiary">
            {t("workspace.current", "Current")}
          </span>
        )}

        {canManageMembers && onManageMembers && (
          <button
            data-testid={`workspace-manage-members-${workspace.id}`}
            onClick={() => onManageMembers(workspace)}
            className="p-2 rounded-lg hover:bg-surface-alt text-accent-base transition-colors"
            title={t("workspace.manageMembers", "Manage Members")}
          >
            <UsersCog className="w-4 h-4" />
          </button>
        )}

        {canEdit && (
          <button
            data-testid={`workspace-edit-${workspace.id}`}
            onClick={() => onEdit(workspace)}
            disabled={workspace.is_read_only}
            className={`p-2 rounded-lg transition-colors ${
              workspace.is_read_only
                ? "opacity-50 cursor-not-allowed text-content-tertiary"
                : "hover:bg-surface-alt text-content-secondary"
            }`}
            title={
              workspace.is_read_only
                ? "Read-only: upgrade or delete excess records"
                : t("common.edit", "Edit")
            }
          >
            <Pencil className="w-4 h-4" />
          </button>
        )}

        {canLeave && (
          <button
            onClick={() => onLeave(workspace)}
            className="p-2 rounded-lg hover:bg-surface-alt text-danger-base transition-colors"
            title={t("workspace.leave", "Leave")}
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}

        {canArchive && (
          <button
            onClick={() => onArchive(workspace)}
            className="p-2 rounded-lg hover:bg-surface-alt text-warning-base transition-colors"
            title={t("workspace.archive", "Archive")}
          >
            <Archive className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default WorkspaceCard;
