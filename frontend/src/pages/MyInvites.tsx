import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { WorkspaceApiClient } from "@/services/api/workspaceApiClient";
import { MyInvite, MyInviteListResponse } from "@/types";
import { MyInviteCard } from "@/components/ui/workspace";
import { FaEnvelope, FaSpinner, FaInbox, FaCheckCircle } from "react-icons/fa";
import { Skeleton } from "@/components/ui/shared/Skeleton";
import { logger } from "@/utils/logger";

export const MyInvites: React.FC = () => {
  const { t } = useTranslation();
  const { token, refreshAccessToken } = useAuth();
  const { refreshWorkspaces } = useWorkspace();

  const [invites, setInvites] = useState<MyInvite[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingInviteId, setLoadingInviteId] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<
    "accept" | "reject" | null
  >(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Create API client
  const workspaceApi = useMemo(() => {
    const getToken = () => token;
    const refreshTokenFn = () => refreshAccessToken();
    return new WorkspaceApiClient(getToken, refreshTokenFn);
  }, [token, refreshAccessToken]);

  // Fetch invites
  const fetchInvites = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await workspaceApi.getMyInvites(false); // Only pending

      if ("error" in response) {
        setError(response.error);
        return;
      }

      setInvites((response as MyInviteListResponse).invites);
    } catch (err) {
      logger.error("Failed to fetch invites:", err);
      setError(t("workspace.invite.fetchError", "Failed to load invitations"));
    } finally {
      setIsLoading(false);
    }
  }, [workspaceApi, t]);

  useEffect(() => {
    fetchInvites();
  }, [fetchInvites]);

  // Handle accept
  const handleAccept = async (inviteId: string) => {
    setLoadingInviteId(inviteId);
    setLoadingAction("accept");
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await workspaceApi.acceptInvite(inviteId);

      if ("error" in response) {
        setError(response.error);
        return;
      }

      // Remove from list and show success
      const acceptedInvite = invites.find((i) => i.id === inviteId);
      setInvites((prev) => prev.filter((i) => i.id !== inviteId));
      setSuccessMessage(
        t("workspace.invite.acceptSuccess", 'You have joined "{{workspace}}"', {
          workspace: acceptedInvite?.workspace_name || "the workspace",
        }),
      );

      // Refresh workspaces to show the new one
      await refreshWorkspaces();
    } catch (err) {
      logger.error("Failed to accept invite:", err);
      setError(
        t("workspace.invite.acceptError", "Failed to accept invitation"),
      );
    } finally {
      setLoadingInviteId(null);
      setLoadingAction(null);
    }
  };

  // Handle reject
  const handleReject = async (inviteId: string) => {
    setLoadingInviteId(inviteId);
    setLoadingAction("reject");
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await workspaceApi.rejectInvite(inviteId);

      if (response && "error" in response) {
        setError(response.error);
        return;
      }

      // Remove from list
      setInvites((prev) => prev.filter((i) => i.id !== inviteId));
      setSuccessMessage(
        t("workspace.invite.rejectSuccess", "Invitation declined"),
      );
    } catch (err) {
      logger.error("Failed to reject invite:", err);
      setError(
        t("workspace.invite.rejectError", "Failed to decline invitation"),
      );
    } finally {
      setLoadingInviteId(null);
      setLoadingAction(null);
    }
  };

  // Clear success message after delay
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  const pendingCount = invites.filter((i) => i.is_actionable).length;

  return (
    <div className="min-h-full">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl theme-accent-light theme-accent">
            <FaEnvelope className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold theme-text-primary">
              {t("workspace.myInvites.title", "My Invitations")}
            </h1>
            <p className="mt-1 theme-text-secondary">
              {pendingCount > 0
                ? t(
                    "workspace.myInvites.pending",
                    "You have {{count}} pending invitations",
                    { count: pendingCount },
                  )
                : t("workspace.myInvites.noPending", "No pending invitations")}
            </p>
          </div>
        </div>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="mb-6 p-4 rounded-lg theme-success-light theme-success flex items-center gap-3">
          <FaCheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 rounded-lg theme-error-light theme-error">
          {error}
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <FaSpinner className="w-8 h-8 theme-text-secondary animate-spin" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && invites.length === 0 && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full theme-bg-secondary mb-4">
            <FaInbox className="w-10 h-10 theme-text-tertiary" />
          </div>
          <h3 className="text-lg font-medium theme-text-primary mb-2">
            {t("workspace.myInvites.empty.title", "No invitations")}
          </h3>
          <p className="theme-text-secondary max-w-md mx-auto">
            {t(
              "workspace.myInvites.empty.description",
              "When someone invites you to collaborate on a workspace, it will appear here.",
            )}
          </p>
        </div>
      )}

      {/* Invites list */}
      {!isLoading && invites.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {invites.map((invite) => (
            <MyInviteCard
              key={invite.id}
              invite={invite}
              onAccept={handleAccept}
              onReject={handleReject}
              isLoading={loadingInviteId === invite.id}
              loadingAction={
                loadingInviteId === invite.id ? loadingAction : null
              }
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MyInvites;
