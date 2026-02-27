import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { WorkspaceMember, AssignableRole } from "@/types";
import {
  FaUser,
  FaCrown,
  FaEye,
  FaEdit,
  FaTrash,
  FaSpinner,
  FaChevronDown,
} from "react-icons/fa";

interface MemberCardProps {
  member: WorkspaceMember;
  isOwner: boolean; // Is current user the owner?
  isCurrentUser: boolean; // Is this the current user's card?
  onChangeRole?: (userId: number, role: AssignableRole) => void;
  onRemove?: (userId: number) => void;
  isLoading?: boolean;
}

export const MemberCard: React.FC<MemberCardProps> = ({
  member,
  isOwner,
  isCurrentUser,
  onChangeRole,
  onRemove,
  isLoading = false,
}) => {
  const { t } = useTranslation();
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const canManage = isOwner && !isCurrentUser && member.role !== "owner";

  const getRoleBadge = () => {
    const roleConfig: Record<
      string,
      { icon: React.ReactNode; className: string; label: string }
    > = {
      owner: {
        icon: <FaCrown className="w-3 h-3" />,
        className: "theme-warning-light theme-warning",
        label: t("workspace.roles.owner", "Owner"),
      },
      full: {
        icon: <FaEdit className="w-3 h-3" />,
        className: "theme-success-light theme-success",
        label: t("workspace.roles.full", "Full Access"),
      },
      read: {
        icon: <FaEye className="w-3 h-3" />,
        className: "theme-accent-light theme-accent",
        label: t("workspace.roles.read", "View Only"),
      },
    };

    const config = roleConfig[member.role] || roleConfig.read;
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
      >
        {config.icon}
        {config.label}
      </span>
    );
  };

  const handleRoleChange = (newRole: AssignableRole) => {
    if (onChangeRole && newRole !== member.role) {
      onChangeRole(member.user_id, newRole);
    }
    setShowRoleMenu(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="flex items-center justify-between p-4 rounded-lg theme-surface-hover border theme-border">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        {/* Avatar */}
        <div
          className={`p-2.5 rounded-full ${
            member.role === "owner"
              ? "theme-warning-light theme-warning"
              : "theme-bg-secondary theme-text-secondary"
          }`}
        >
          {member.role === "owner" ? (
            <FaCrown className="w-4 h-4" />
          ) : (
            <FaUser className="w-4 h-4" />
          )}
        </div>

        {/* Member info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium theme-text-primary truncate">
              {member.email || `User #${member.user_id}`}
            </span>
            {isCurrentUser && (
              <span className="text-xs theme-text-tertiary">
                ({t("common.you", "You")})
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm theme-text-tertiary mt-0.5">
            {member.email && <span className="truncate">{member.email}</span>}
            <span>•</span>
            <span>
              {t("workspace.member.joined", "Joined")}{" "}
              {formatDate(member.joined_at)}
            </span>
          </div>
        </div>
      </div>

      {/* Right side: Role + Actions */}
      <div className="flex items-center gap-3">
        {/* Role badge or dropdown */}
        {canManage && onChangeRole ? (
          <div className="relative">
            <button
              onClick={() => setShowRoleMenu(!showRoleMenu)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:theme-surface-hover theme-transition"
              disabled={isLoading}
            >
              {getRoleBadge()}
              <FaChevronDown className="w-3 h-3 theme-text-tertiary ml-1" />
            </button>

            {showRoleMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowRoleMenu(false)}
                />
                <div className="absolute right-0 top-full mt-1 z-20 w-48 py-1 rounded-lg theme-surface border theme-border shadow-lg">
                  <button
                    onClick={() => handleRoleChange("read")}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:theme-surface-hover theme-transition ${
                      member.role === "read" ? "theme-accent-light" : ""
                    }`}
                  >
                    <FaEye className="w-4 h-4 theme-accent" />
                    <div>
                      <div className="font-medium theme-text-primary">
                        {t("workspace.roles.read", "View Only")}
                      </div>
                      <div className="text-xs theme-text-tertiary">
                        {t("workspace.roles.readDesc", "Can view all data")}
                      </div>
                    </div>
                  </button>
                  <button
                    onClick={() => handleRoleChange("full")}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:theme-surface-hover theme-transition ${
                      member.role === "full" ? "theme-success-light" : ""
                    }`}
                  >
                    <FaEdit className="w-4 h-4 theme-success" />
                    <div>
                      <div className="font-medium theme-text-primary">
                        {t("workspace.roles.full", "Full Access")}
                      </div>
                      <div className="text-xs theme-text-tertiary">
                        {t("workspace.roles.fullDesc", "Can view and edit")}
                      </div>
                    </div>
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          getRoleBadge()
        )}

        {/* Remove button */}
        {canManage && onRemove && (
          <button
            onClick={() => onRemove(member.user_id)}
            className="p-2 rounded-lg hover:theme-surface-hover text-red-500 theme-transition"
            title={t("workspace.member.remove", "Remove member")}
            disabled={isLoading}
          >
            {isLoading ? (
              <FaSpinner className="w-4 h-4 animate-spin" />
            ) : (
              <FaTrash className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default MemberCard;
