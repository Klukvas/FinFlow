import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useAuth } from "@/contexts/AuthContext";
import { WorkspaceApiClient } from "@/services/api/workspaceApiClient";
import {
 Workspace,
 WorkspaceMember,
 WorkspaceMemberListResponse,
 WorkspaceInvite,
 WorkspaceInviteListResponse,
 WorkspaceInviteCreate,
 AssignableRole,
} from "@/types";
import { MemberCard } from "./MemberCard";
import { InviteCard } from "./InviteCard";
import { InviteForm } from "./InviteForm";
import { Users, Mail, X, UserPlus } from "lucide-react";
import { Skeleton } from "@/components/ui/shared/Skeleton";

interface WorkspaceMembersProps {
 workspace: Workspace;
 onClose: () => void;
}

type TabType = "members" | "invites";

export const WorkspaceMembers: React.FC<WorkspaceMembersProps> = ({
 workspace,
 onClose,
}) => {
 const { t } = useTranslation();
 const { token, refreshAccessToken, user } = useAuth();

 const [activeTab, setActiveTab] = useState<TabType>("members");
 const [members, setMembers] = useState<WorkspaceMember[]>([]);
 const [invites, setInvites] = useState<WorkspaceInvite[]>([]);
 const [isLoading, setIsLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);
 const [showInviteForm, setShowInviteForm] = useState(false);
 const [isSubmitting, setIsSubmitting] = useState(false);
 const [inviteError, setInviteError] = useState<string | null>(null);

 // Create API client
 const workspaceApi = useMemo(() => {
 const getToken = () => token;
 const refreshTokenFn = () => refreshAccessToken();
 return new WorkspaceApiClient(getToken, refreshTokenFn);
 }, [token, refreshAccessToken]);

 const isOwner = workspace.current_user_role === "owner";

 // Fetch members
 const fetchMembers = useCallback(async () => {
 try {
 const response = await workspaceApi.getMembers(workspace.id);
 if ("error" in response) {
 setError(response.error);
 return;
 }
 setMembers((response as WorkspaceMemberListResponse).members);
 } catch (err) {
 logger.error("Failed to fetch members:", err);
 setError(t("workspace.members.fetchError", "Failed to load members"));
 }
 }, [workspaceApi, workspace.id, t]);

 // Fetch invites
 const fetchInvites = useCallback(async () => {
 if (!isOwner) return;

 try {
 const response = await workspaceApi.getWorkspaceInvites(workspace.id);
 if ("error" in response) {
 setError(response.error);
 return;
 }
 setInvites((response as WorkspaceInviteListResponse).invites);
 } catch (err) {
 logger.error("Failed to fetch invites:", err);
 }
 }, [workspaceApi, workspace.id, isOwner]);

 // Initial load
 useEffect(() => {
 const loadData = async () => {
 setIsLoading(true);
 setError(null);
 await Promise.all([fetchMembers(), fetchInvites()]);
 setIsLoading(false);
 };
 loadData();
 }, [fetchMembers, fetchInvites]);

 // Handle invite creation
 const handleCreateInvite = async (data: WorkspaceInviteCreate) => {
 setIsSubmitting(true);
 setInviteError(null);

 try {
 const response = await workspaceApi.createInvite(workspace.id, data);

 if ("error" in response) {
 setInviteError(response.error);
 return;
 }

 // Add to invites list
 setInvites((prev) => [response as WorkspaceInvite, ...prev]);
 setShowInviteForm(false);
 } catch (err) {
 logger.error("Failed to create invite:", err);
 setInviteError(
 t("workspace.invite.createError", "Failed to send invitation"),
 );
 } finally {
 setIsSubmitting(false);
 }
 };

 // Handle cancel invite
 const handleCancelInvite = async (inviteId: string) => {
 try {
 const response = await workspaceApi.cancelInvite(workspace.id, inviteId);
 if (response && "error" in response) {
 setError(response.error);
 return;
 }
 setInvites((prev) => prev.filter((i) => i.id !== inviteId));
 } catch (err) {
 logger.error("Failed to cancel invite:", err);
 setError(
 t("workspace.invite.cancelError", "Failed to cancel invitation"),
 );
 }
 };

 // Handle role change
 const handleRoleChange = async (userId: number, newRole: AssignableRole) => {
 try {
 const response = await workspaceApi.updateMemberRole(
 workspace.id,
 userId,
 { role: newRole },
 );
 if ("error" in response) {
 setError(response.error);
 return;
 }
 setMembers((prev) =>
 prev.map((m) => (m.user_id === userId ? { ...m, role: newRole } : m)),
 );
 } catch (err) {
 logger.error("Failed to update role:", err);
 setError(t("workspace.member.roleUpdateError", "Failed to update role"));
 }
 };

 // Handle remove member
 const handleRemoveMember = async (userId: number) => {
 if (
 !confirm(
 t(
 "workspace.member.removeConfirm",
 "Are you sure you want to remove this member?",
 ),
 )
 ) {
 return;
 }

 try {
 const response = await workspaceApi.removeMember(workspace.id, userId);
 if (response && "error" in response) {
 setError(response.error);
 return;
 }
 setMembers((prev) => prev.filter((m) => m.user_id !== userId));
 } catch (err) {
 logger.error("Failed to remove member:", err);
 setError(t("workspace.member.removeError", "Failed to remove member"));
 }
 };

 const pendingInvitesCount = invites.filter(
 (i) => i.status === "pending" && !i.is_expired,
 ).length;

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center">
 <div className="fixed inset-0 bg-black/50" onClick={onClose} />
 <div className="relative w-full max-w-2xl max-h-[90vh] mx-4 bg-elevated rounded-2xl shadow-2xl flex flex-col">
 {/* Header */}
 <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
 <div>
 <h2 className="text-xl font-semibold text-content">
 {workspace.name}
 </h2>
 <p className="text-sm text-content-secondary mt-1">
 {t(
 "workspace.members.subtitle",
 "Manage members and invitations",
 )}
 </p>
 </div>
 <button
 onClick={onClose}
 className="p-2 rounded-lg hover:bg-surface-alt transition-colors"
 >
 <X className="w-5 h-5 text-content-secondary" />
 </button>
 </div>

 {/* Tabs */}
 <div className="flex border-b border-[var(--border)]">
 <button
 onClick={() => setActiveTab("members")}
 className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
 activeTab === "members"
 ? "border-accent-base text-accent-base"
 : "border-transparent text-content-secondary hover:text-content"
 }`}
 >
 <Users className="w-4 h-4" />
 {t("workspace.tabs.members", "Members")} ({members.length})
 </button>
 {isOwner && (
 <button
 onClick={() => setActiveTab("invites")}
 className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
 activeTab === "invites"
 ? "border-accent-base text-accent-base"
 : "border-transparent text-content-secondary hover:text-content"
 }`}
 >
 <Mail className="w-4 h-4" />
 {t("workspace.tabs.invites", "Invitations")}
 {pendingInvitesCount > 0 && (
 <span className="px-1.5 py-0.5 text-xs rounded-full bg-[var(--accent-dim)] text-accent-base">
 {pendingInvitesCount}
 </span>
 )}
 </button>
 )}
 </div>

 {/* Content */}
 <div className="flex-1 overflow-y-auto p-6">
 {/* Error message */}
 {error && (
 <div className="mb-4 p-3 rounded-lg bg-[var(--danger-dim)] text-danger-base text-sm">
 {error}
 </div>
 )}

 {/* Loading */}
 {isLoading && (
 <div className="space-y-3">
 {Array.from({ length: 4 }).map((_, i) => (
 <div
 key={i}
 className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border)]"
 >
 <Skeleton className="w-10 h-10 rounded-full" />
 <div className="space-y-2 flex-1">
 <Skeleton className="h-4 w-32" />
 <Skeleton className="h-3 w-24" />
 </div>
 <Skeleton className="h-6 w-16 rounded-full" />
 </div>
 ))}
 </div>
 )}

 {/* Members Tab */}
 {!isLoading && activeTab === "members" && (
 <div className="space-y-3">
 {members.length === 0 ? (
 <div className="text-center py-8 text-content-secondary">
 {t("workspace.members.empty", "No members yet")}
 </div>
 ) : (
 members.map((member) => (
 <MemberCard
 key={member.id}
 member={member}
 isOwner={isOwner}
 isCurrentUser={member.user_id === user?.id}
 {...(isOwner ? { onChangeRole: handleRoleChange } : {})}
 {...(isOwner ? { onRemove: handleRemoveMember } : {})}
 />
 ))
 )}
 </div>
 )}

 {/* Invites Tab */}
 {!isLoading && activeTab === "invites" && isOwner && (
 <div className="space-y-4">
 {/* Invite Form or Button */}
 {showInviteForm ? (
 <div className="p-4 rounded-xl border border-[var(--border)]">
 <h3 className="font-medium text-content mb-4">
 {t("workspace.invite.newTitle", "Invite a Team Member")}
 </h3>
 <InviteForm
 onSubmit={handleCreateInvite}
 onCancel={() => {
 setShowInviteForm(false);
 setInviteError(null);
 }}
 isLoading={isSubmitting}
 error={inviteError}
 />
 </div>
 ) : (
 <button
 onClick={() => setShowInviteForm(true)}
 className="w-full flex items-center justify-center gap-2 p-4 rounded-xl border-2 border-dashed border-[var(--border)] hover:border-accent-base hover:bg-surface-alt text-content-secondary hover:text-accent-base transition-colors"
 >
 <UserPlus className="w-5 h-5" />
 <span className="font-medium">
 {t("workspace.invite.addButton", "Invite Someone")}
 </span>
 </button>
 )}

 {/* Pending Invites */}
 {invites.length > 0 && (
 <div className="space-y-3">
 <h4 className="text-sm font-medium text-content-secondary">
 {t("workspace.invite.pendingTitle", "Pending Invitations")}
 </h4>
 {invites.map((invite) => (
 <InviteCard
 key={invite.id}
 invite={invite}
 onCancel={handleCancelInvite}
 />
 ))}
 </div>
 )}

 {/* Empty state */}
 {invites.length === 0 && !showInviteForm && (
 <div className="text-center py-8 text-content-tertiary text-sm">
 {t("workspace.invite.emptyState", "No pending invitations")}
 </div>
 )}
 </div>
 )}
 </div>
 </div>
 </div>
 );
};

export default WorkspaceMembers;
