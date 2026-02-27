import React from "react";
import { useTranslation } from "react-i18next";
import { Lock } from "lucide-react";
import { Workspace } from "@/types";
import {
  FaUsers,
  FaUser,
  FaCrown,
  FaArchive,
  FaEdit,
  FaSignOutAlt,
  FaUsersCog,
} from "react-icons/fa";

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
        className: "theme-warning-light theme-warning",
        icon: true,
      },
      full: {
        className: "theme-success-light theme-success",
      },
      read: {
        className: "theme-accent-light theme-accent",
      },
    };

    const role = workspace.current_user_role || "read";
    const config = roleConfig[role] || roleConfig.read;
    return (
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
      >
        {config.icon && <FaCrown className="inline w-3 h-3 mr-1" />}
        {t(`workspace.roles.${role}`, role)}
      </span>
    );
  };

  return (
    <div
      className={`relative p-4 rounded-xl theme-surface theme-border border theme-transition hover:shadow-md ${
        isCurrentWorkspace
          ? "ring-2 ring-offset-2 theme-accent ring-current"
          : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div
            className={`p-2.5 rounded-lg ${
              workspace.type === "personal"
                ? "theme-success-light theme-success"
                : "theme-accent-light theme-accent"
            }`}
          >
            {workspace.type === "personal" ? (
              <FaUser className="w-5 h-5" />
            ) : (
              <FaUsers className="w-5 h-5" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold theme-text-primary truncate flex items-center gap-1.5">
              {workspace.name}
              {workspace.is_read_only && (
                <Lock className="w-4 h-4 text-amber-500 flex-shrink-0" />
              )}
            </h3>
            <p className="text-sm theme-text-tertiary">
              {workspace.type === "personal"
                ? t("workspace.personal", "Personal")
                : t("workspace.shared", "Shared")}
            </p>
          </div>
        </div>
        {getRoleBadge()}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 mb-4 text-sm theme-text-secondary">
        {workspace.member_count !== null && (
          <div className="flex items-center gap-1">
            <FaUsers className="w-4 h-4" />
            <span>
              {workspace.member_count} {t("workspace.members", "members")}
            </span>
          </div>
        )}
        <div className="text-xs theme-text-tertiary">
          {t("workspace.created", "Created")}{" "}
          {new Date(workspace.created_at).toLocaleDateString()}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t theme-border">
        {!isCurrentWorkspace && (
          <button
            onClick={() => onSelect(workspace.id)}
            className="flex-1 px-3 py-2 text-sm font-medium theme-accent theme-accent-light rounded-lg hover:opacity-80 theme-transition"
          >
            {t("workspace.select", "Select")}
          </button>
        )}
        {isCurrentWorkspace && (
          <span className="flex-1 px-3 py-2 text-sm font-medium text-center theme-text-tertiary">
            {t("workspace.current", "Current")}
          </span>
        )}

        {canManageMembers && onManageMembers && (
          <button
            onClick={() => onManageMembers(workspace)}
            className="p-2 rounded-lg hover:theme-surface-hover text-blue-500 theme-transition"
            title={t("workspace.manageMembers", "Manage Members")}
          >
            <FaUsersCog className="w-4 h-4" />
          </button>
        )}

        {canEdit && (
          <button
            onClick={() => onEdit(workspace)}
            disabled={workspace.is_read_only}
            className={`p-2 rounded-lg theme-transition ${
              workspace.is_read_only
                ? "opacity-50 cursor-not-allowed theme-text-tertiary"
                : "hover:theme-surface-hover theme-text-secondary"
            }`}
            title={
              workspace.is_read_only
                ? "Read-only: upgrade or delete excess records"
                : t("common.edit", "Edit")
            }
          >
            <FaEdit className="w-4 h-4" />
          </button>
        )}

        {canLeave && (
          <button
            onClick={() => onLeave(workspace)}
            className="p-2 rounded-lg hover:theme-surface-hover text-red-500 theme-transition"
            title={t("workspace.leave", "Leave")}
          >
            <FaSignOutAlt className="w-4 h-4" />
          </button>
        )}

        {canArchive && (
          <button
            onClick={() => onArchive(workspace)}
            className="p-2 rounded-lg hover:theme-surface-hover text-orange-500 theme-transition"
            title={t("workspace.archive", "Archive")}
          >
            <FaArchive className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default WorkspaceCard;
