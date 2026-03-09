import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { setStoredWorkspaceId } from "@/utils/workspaceStorage";
import { Workspace, WorkspaceCreate, WorkspaceUpdate } from "@/types";
import {
 WorkspaceCard,
 WorkspaceForm,
 WorkspaceMembers,
} from "@/components/ui/workspace";
import { FaPlus, FaUsers, FaSpinner } from "react-icons/fa";

// Modal Component
interface ModalProps {
 isOpen: boolean;
 onClose: () => void;
 title: string;
 children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
 if (!isOpen) return null;

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center">
 <div className="fixed inset-0 bg-black/50" onClick={onClose} />
 <div className="relative w-full max-w-lg mx-4 bg-elevated rounded-2xl shadow-2xl">
 <div className="p-6 border-b border-[var(--color-border)]">
 <h2 className="text-xl font-semibold text-content">{title}</h2>
 </div>
 <div className="p-6">{children}</div>
 </div>
 </div>
 );
};

// Confirmation Dialog
interface ConfirmDialogProps {
 isOpen: boolean;
 onClose: () => void;
 onConfirm: () => void;
 title: string;
 message: string;
 confirmText?: string;
 confirmVariant?: "danger" | "warning";
 isLoading?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
 isOpen,
 onClose,
 onConfirm,
 title,
 message,
 confirmText = "Confirm",
 confirmVariant = "danger",
 isLoading = false,
}) => {
 if (!isOpen) return null;

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center">
 <div className="fixed inset-0 bg-black/50" onClick={onClose} />
 <div className="relative w-full max-w-md mx-4 bg-elevated rounded-2xl shadow-2xl p-6">
 <h3 className="text-lg font-semibold text-content mb-2">
 {title}
 </h3>
 <p className="text-content-secondary mb-6">{message}</p>
 <div className="flex justify-end gap-3">
 <button
 onClick={onClose}
 className="px-4 py-2 rounded-lg text-content-secondary hover:bg-surface-alt transition-colors"
 disabled={isLoading}
 >
 Cancel
 </button>
 <button
 onClick={onConfirm}
 className={`px-4 py-2 rounded-lg text-white font-medium transition-colors disabled:opacity-50 ${
 confirmVariant === "danger"
 ? "bg-danger-base hover:bg-danger-base-hover"
 : "bg-warning-base hover:bg-warning-base"
 }`}
 disabled={isLoading}
 >
 {isLoading ? (
 <FaSpinner className="animate-spin w-4 h-4" />
 ) : (
 confirmText
 )}
 </button>
 </div>
 </div>
 </div>
 );
};

export const Workspaces: React.FC = () => {
 const { t } = useTranslation();
 const {
 workspaces,
 currentWorkspaceId,
 isLoading,
 error,
 setCurrentWorkspace,
 createWorkspace,
 updateWorkspace,
 archiveWorkspace,
 leaveWorkspace,
 } = useWorkspace();

 // Modal states
 const [showCreateModal, setShowCreateModal] = useState(false);
 const [editingWorkspace, setEditingWorkspace] = useState<Workspace | null>(
 null,
 );
 const [archivingWorkspace, setArchivingWorkspace] =
 useState<Workspace | null>(null);
 const [leavingWorkspace, setLeavingWorkspace] = useState<Workspace | null>(
 null,
 );
 const [managingWorkspace, setManagingWorkspace] = useState<Workspace | null>(
 null,
 );
 const [isSubmitting, setIsSubmitting] = useState(false);

 const handleCreateWorkspace = async (
 data: WorkspaceCreate | WorkspaceUpdate,
 ) => {
 setIsSubmitting(true);
 try {
 const result = await createWorkspace(data as WorkspaceCreate);
 if (result) {
 setShowCreateModal(false);
 }
 } finally {
 setIsSubmitting(false);
 }
 };

 const handleUpdateWorkspace = async (
 data: WorkspaceCreate | WorkspaceUpdate,
 ) => {
 if (!editingWorkspace) return;
 setIsSubmitting(true);
 try {
 const result = await updateWorkspace(
 editingWorkspace.id,
 data as WorkspaceUpdate,
 );
 if (result) {
 setEditingWorkspace(null);
 }
 } finally {
 setIsSubmitting(false);
 }
 };

 const handleArchiveWorkspace = async () => {
 if (!archivingWorkspace) return;
 setIsSubmitting(true);
 try {
 const success = await archiveWorkspace(archivingWorkspace.id);
 if (success) {
 setArchivingWorkspace(null);
 }
 } finally {
 setIsSubmitting(false);
 }
 };

 const handleLeaveWorkspace = async () => {
 if (!leavingWorkspace) return;
 setIsSubmitting(true);
 try {
 const success = await leaveWorkspace(leavingWorkspace.id);
 if (success) {
 setLeavingWorkspace(null);
 }
 } finally {
 setIsSubmitting(false);
 }
 };

 const handleSelectWorkspace = (workspaceId: string) => {
 // First, synchronously set the workspace ID in localStorage
 setStoredWorkspaceId(workspaceId);
 // Then update React state
 setCurrentWorkspace(workspaceId);
 // Small delay to ensure localStorage is committed, then reload
 setTimeout(() => {
 window.location.reload();
 }, 50);
 };

 return (
 <div className="min-h-full">
 {/* Header */}
 <div className="mb-8">
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-2xl font-bold text-content">
 {t("workspace.title", "Workspaces")}
 </h1>
 <p className="mt-1 text-content-secondary">
 {t(
 "workspace.subtitle",
 "Manage your workspaces and collaborate with others",
 )}
 </p>
 </div>
 <button
 onClick={() => setShowCreateModal(true)}
 className="flex items-center gap-2 px-4 py-2.5 bg-accent-base text-white rounded-lg font-medium hover:bg-accent-base-hover transition-colors shadow-sm"
 >
 <FaPlus className="w-4 h-4" />
 <span>{t("workspace.createButton", "Create Workspace")}</span>
 </button>
 </div>
 </div>

 {/* Error message */}
 {error && (
 <div className="mb-6 p-4 rounded-lg bg-[var(--color-danger-light)] text-danger-base">
 {error}
 </div>
 )}

 {/* Loading state */}
 {isLoading && (
 <div className="flex items-center justify-center py-12">
 <FaSpinner className="w-8 h-8 text-content-secondary animate-spin" />
 </div>
 )}

 {/* Workspaces grid */}
 {!isLoading && workspaces.length === 0 && (
 <div className="text-center py-16">
 <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-alt mb-4">
 <FaUsers className="w-8 h-8 text-content-tertiary" />
 </div>
 <h3 className="text-lg font-medium text-content mb-2">
 {t("workspace.empty.title", "No workspaces yet")}
 </h3>
 <p className="text-content-secondary mb-6">
 {t(
 "workspace.empty.description",
 "Create your first workspace to get started",
 )}
 </p>
 <button
 onClick={() => setShowCreateModal(true)}
 className="inline-flex items-center gap-2 px-4 py-2.5 bg-accent-base text-white rounded-lg font-medium hover:bg-accent-base-hover transition-colors"
 >
 <FaPlus className="w-4 h-4" />
 <span>{t("workspace.createButton", "Create Workspace")}</span>
 </button>
 </div>
 )}

 {!isLoading && workspaces.length > 0 && (
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
 {workspaces.map((workspace) => (
 <WorkspaceCard
 key={workspace.id}
 workspace={workspace}
 isCurrentWorkspace={workspace.id === currentWorkspaceId}
 onSelect={handleSelectWorkspace}
 onEdit={setEditingWorkspace}
 onArchive={setArchivingWorkspace}
 onLeave={setLeavingWorkspace}
 onManageMembers={setManagingWorkspace}
 />
 ))}
 </div>
 )}

 {/* Create Modal */}
 <Modal
 isOpen={showCreateModal}
 onClose={() => setShowCreateModal(false)}
 title={t("workspace.createModal.title", "Create New Workspace")}
 >
 <WorkspaceForm
 onSubmit={handleCreateWorkspace}
 onCancel={() => setShowCreateModal(false)}
 isLoading={isSubmitting}
 />
 </Modal>

 {/* Edit Modal */}
 <Modal
 isOpen={!!editingWorkspace}
 onClose={() => setEditingWorkspace(null)}
 title={t("workspace.editModal.title", "Edit Workspace")}
 >
 <WorkspaceForm
 workspace={editingWorkspace}
 onSubmit={handleUpdateWorkspace}
 onCancel={() => setEditingWorkspace(null)}
 isLoading={isSubmitting}
 />
 </Modal>

 {/* Archive Confirmation */}
 <ConfirmDialog
 isOpen={!!archivingWorkspace}
 onClose={() => setArchivingWorkspace(null)}
 onConfirm={handleArchiveWorkspace}
 title={t("workspace.archiveConfirm.title", "Archive Workspace")}
 message={t(
 "workspace.archiveConfirm.message",
 `Are you sure you want to archive "${archivingWorkspace?.name}"? This will hide it from your workspace list but data will be preserved.`,
 )}
 confirmText={t("workspace.archive", "Archive")}
 confirmVariant="warning"
 isLoading={isSubmitting}
 />

 {/* Leave Confirmation */}
 <ConfirmDialog
 isOpen={!!leavingWorkspace}
 onClose={() => setLeavingWorkspace(null)}
 onConfirm={handleLeaveWorkspace}
 title={t("workspace.leaveConfirm.title", "Leave Workspace")}
 message={t(
 "workspace.leaveConfirm.message",
 `Are you sure you want to leave "${leavingWorkspace?.name}"? You will lose access to all data in this workspace.`,
 )}
 confirmText={t("workspace.leave", "Leave")}
 confirmVariant="danger"
 isLoading={isSubmitting}
 />

 {/* Manage Members Modal */}
 {managingWorkspace && (
 <WorkspaceMembers
 workspace={managingWorkspace}
 onClose={() => setManagingWorkspace(null)}
 />
 )}
 </div>
 );
};

export default Workspaces;
