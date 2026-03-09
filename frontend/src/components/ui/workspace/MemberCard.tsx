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
 className: "bg-[var(--color-warning-light)] text-warning-base",
 label: t("workspace.roles.owner", "Owner"),
 },
 full: {
 icon: <FaEdit className="w-3 h-3" />,
 className: "bg-[var(--color-success-light)] text-success-base",
 label: t("workspace.roles.full", "Full Access"),
 },
 read: {
 icon: <FaEye className="w-3 h-3" />,
 className: "bg-[var(--color-accent-light)] text-accent-base",
 label: t("workspace.roles.read", "View Only"),
 },
 };

 const config = roleConfig[member.role] ?? roleConfig.read!;
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
 <div className="flex items-center justify-between p-4 rounded-lg bg-surface-alt border border-[var(--color-border)]">
 <div className="flex items-center gap-3 min-w-0 flex-1">
 {/* Avatar */}
 <div
 className={`p-2.5 rounded-full ${
 member.role === "owner"
 ? "bg-[var(--color-warning-light)] text-warning-base"
 : "bg-surface-alt text-content-secondary"
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
 <span className="font-medium text-content truncate">
 {member.email || `User #${member.user_id}`}
 </span>
 {isCurrentUser && (
 <span className="text-xs text-content-tertiary">
 ({t("common.you", "You")})
 </span>
 )}
 </div>
 <div className="flex items-center gap-2 text-sm text-content-tertiary mt-0.5">
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
 className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-surface-alt transition-colors"
 disabled={isLoading}
 >
 {getRoleBadge()}
 <FaChevronDown className="w-3 h-3 text-content-tertiary ml-1" />
 </button>

 {showRoleMenu && (
 <>
 <div
 className="fixed inset-0 z-10"
 onClick={() => setShowRoleMenu(false)}
 />
 <div className="absolute right-0 top-full mt-1 z-20 w-48 py-1 rounded-lg bg-elevated border border-[var(--color-border)] shadow-lg">
 <button
 onClick={() => handleRoleChange("read")}
 className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-surface-alt transition-colors ${
 member.role === "read" ? "bg-[var(--color-accent-light)]" : ""
 }`}
 >
 <FaEye className="w-4 h-4 text-accent-base" />
 <div>
 <div className="font-medium text-content">
 {t("workspace.roles.read", "View Only")}
 </div>
 <div className="text-xs text-content-tertiary">
 {t("workspace.roles.readDesc", "Can view all data")}
 </div>
 </div>
 </button>
 <button
 onClick={() => handleRoleChange("full")}
 className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-surface-alt transition-colors ${
 member.role === "full" ? "bg-[var(--color-success-light)]" : ""
 }`}
 >
 <FaEdit className="w-4 h-4 text-success-base" />
 <div>
 <div className="font-medium text-content">
 {t("workspace.roles.full", "Full Access")}
 </div>
 <div className="text-xs text-content-tertiary">
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
 className="p-2 rounded-lg hover:bg-surface-alt text-danger-base transition-colors"
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
