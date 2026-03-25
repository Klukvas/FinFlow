import React, { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { setStoredWorkspaceId } from "@/utils/workspaceStorage";
import { ChevronDown, Users, User, Settings } from "lucide-react";
import { Link } from "react-router-dom";

interface WorkspaceSelectorProps {
  compact?: boolean;
}

export const WorkspaceSelector: React.FC<WorkspaceSelectorProps> = ({
  compact = false,
}) => {
  const { t } = useTranslation();
  const { workspaces, currentWorkspace, setCurrentWorkspace, isLoading } =
    useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (workspaceId: string) => {
    logger.info("[WorkspaceSelector] Selecting workspace:", workspaceId);
    // First, synchronously set the workspace ID in localStorage
    setStoredWorkspaceId(workspaceId);
    logger.info(
      "[WorkspaceSelector] Stored in localStorage, verifying:",
      localStorage.getItem("current_workspace_id"),
    );
    // Then update React state
    setCurrentWorkspace(workspaceId);
    setIsOpen(false);
    // Small delay to ensure localStorage is committed, then reload
    setTimeout(() => {
      logger.info(
        "[WorkspaceSelector] Before reload, localStorage:",
        localStorage.getItem("current_workspace_id"),
      );
      window.location.reload();
    }, 100);
  };

  if (isLoading) {
    return (
      <div className="px-3 py-2 rounded-lg bg-surface-alt animate-pulse">
        <div className="h-5 w-24 bg-surface-alt rounded"></div>
      </div>
    );
  }

  if (!currentWorkspace) {
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-alt transition-colors hover:bg-[var(--accent-dim)] ${
          compact ? "text-sm" : ""
        }`}
      >
        {currentWorkspace.type === "personal" ? (
          <User className="w-4 h-4 text-accent-base" />
        ) : (
          <Users className="w-4 h-4 text-accent-base" />
        )}
        <span
          className={`text-content font-medium ${compact ? "max-w-[100px]" : "max-w-[150px]"} truncate`}
        >
          {currentWorkspace.name}
        </span>
        <ChevronDown
          className={`w-3 h-3 text-content-secondary transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 py-2 bg-elevated rounded-lg shadow-lg border-[var(--border)] border z-50">
          <div className="px-3 py-2 text-xs font-semibold text-content-tertiary uppercase tracking-wider">
            {t("workspace.switchWorkspace", "Switch Workspace")}
          </div>

          <div className="max-h-64 overflow-y-auto">
            {workspaces.map((workspace) => (
              <button
                key={workspace.id}
                onClick={() => handleSelect(workspace.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 transition-colors ${
                  workspace.id === currentWorkspace.id
                    ? "bg-[var(--accent-dim)] text-accent-base"
                    : "hover:bg-surface-alt text-content"
                }`}
              >
                {workspace.type === "personal" ? (
                  <User className="w-4 h-4 flex-shrink-0" />
                ) : (
                  <Users className="w-4 h-4 flex-shrink-0" />
                )}
                <div className="flex-1 text-left min-w-0">
                  <div className="font-medium truncate">{workspace.name}</div>
                  <div className="text-xs text-content-tertiary">
                    {workspace.type === "personal"
                      ? t("workspace.personal", "Personal")
                      : t("workspace.shared", "Shared")}
                    {workspace.member_count && workspace.member_count > 1 && (
                      <span>
                        {" "}
                        · {workspace.member_count}{" "}
                        {t("workspace.members", "members")}
                      </span>
                    )}
                  </div>
                </div>
                {workspace.id === currentWorkspace.id && (
                  <span className="text-xs text-accent-base">✓</span>
                )}
              </button>
            ))}
          </div>

          <div className="border-t border-[var(--border)] mt-2 pt-2">
            <Link
              to="/workspaces"
              onClick={() => setIsOpen(false)}
              className="w-full flex items-center gap-3 px-3 py-2 hover:bg-surface-alt text-content-secondary transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span>
                {t("workspace.manageWorkspaces", "Manage Workspaces")}
              </span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkspaceSelector;
