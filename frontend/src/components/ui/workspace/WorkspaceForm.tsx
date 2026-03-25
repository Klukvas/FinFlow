import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Workspace,
  WorkspaceCreate,
  WorkspaceUpdate,
  WorkspaceType,
} from "@/types";
import { Users, User } from "lucide-react";

interface WorkspaceFormProps {
  workspace?: Workspace | null;
  onSubmit: (data: WorkspaceCreate | WorkspaceUpdate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const WorkspaceForm: React.FC<WorkspaceFormProps> = ({
  workspace,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const { t } = useTranslation();
  const isEditing = !!workspace;

  const [name, setName] = useState(workspace?.name || "");
  const [type, setType] = useState<WorkspaceType>(workspace?.type || "shared");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (workspace) {
      setName(workspace.name);
      setType(workspace.type);
    }
  }, [workspace]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError(t("workspace.form.nameRequired", "Workspace name is required"));
      return;
    }

    try {
      if (isEditing) {
        await onSubmit({ name: name.trim() } as WorkspaceUpdate);
      } else {
        await onSubmit({ name: name.trim(), type } as WorkspaceCreate);
      }
    } catch (err) {
      setError(t("workspace.form.submitError", "Failed to save workspace"));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name field */}
      <div>
        <label className="block text-sm font-medium text-content mb-2">
          {t("workspace.form.name", "Workspace Name")}{" "}
          <span className="text-danger-base">*</span>
        </label>
        <input
          type="text"
          data-testid="workspace-name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t(
            "workspace.form.namePlaceholder",
            "e.g., Family Budget, Business Expenses",
          )}
          className="w-full px-4 py-3 rounded-lg bg-elevated border-[var(--border)] border text-content placeholder:text-content-tertiary focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors"
          disabled={isLoading}
          autoFocus
        />
      </div>

      {/* Type selection (only for new workspaces) */}
      {!isEditing && (
        <div>
          <label className="block text-sm font-medium text-content mb-3">
            {t("workspace.form.type", "Workspace Type")}
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setType("personal")}
              className={`flex items-center gap-3 p-4 rounded-xl border transition-colors ${
                type === "personal"
                  ? "border-success-base bg-[var(--success-dim)]"
                  : "border-[var(--border)] hover:bg-surface-alt"
              }`}
              disabled={isLoading}
            >
              <div
                className={`p-2 rounded-lg ${
                  type === "personal"
                    ? "bg-[var(--success-dim)] text-success-base"
                    : "bg-surface-alt text-content-secondary"
                }`}
              >
                <User className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <div className="text-left">
                <div
                  className={`font-medium ${type === "personal" ? "text-success-base" : "text-content"}`}
                >
                  {t("workspace.types.personal", "Personal")}
                </div>
                <div className="text-xs text-content-tertiary">
                  {t("workspace.types.personalDesc", "Just for you")}
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setType("shared")}
              className={`flex items-center gap-3 p-4 rounded-xl border transition-colors ${
                type === "shared"
                  ? "border-accent-base bg-[var(--accent-dim)]"
                  : "border-[var(--border)] hover:bg-surface-alt"
              }`}
              disabled={isLoading}
            >
              <div
                className={`p-2 rounded-lg ${
                  type === "shared"
                    ? "bg-[var(--accent-dim)] text-accent-base"
                    : "bg-surface-alt text-content-secondary"
                }`}
              >
                <Users className="w-5 h-5" />
              </div>
              <div className="text-left">
                <div
                  className={`font-medium ${type === "shared" ? "text-accent-base" : "text-content"}`}
                >
                  {t("workspace.types.shared", "Shared")}
                </div>
                <div className="text-xs text-content-tertiary">
                  {t("workspace.types.sharedDesc", "Collaborate with others")}
                </div>
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-3 rounded-lg bg-[var(--danger-dim)] text-danger-base text-sm">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border)]">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg text-content-secondary hover:bg-surface-alt transition-colors"
          disabled={isLoading}
        >
          {t("common.cancel", "Cancel")}
        </button>
        <button
          type="submit"
          data-testid="workspace-form-submit"
          className="px-6 py-2 rounded-lg bg-accent-base text-white font-medium hover:bg-accent-base-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          disabled={isLoading || !name.trim()}
        >
          {isLoading
            ? t("common.saving", "Saving...")
            : isEditing
              ? t("common.save", "Save")
              : t("workspace.form.create", "Create Workspace")}
        </button>
      </div>
    </form>
  );
};

export default WorkspaceForm;
