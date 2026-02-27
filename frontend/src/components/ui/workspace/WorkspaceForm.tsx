import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Workspace,
  WorkspaceCreate,
  WorkspaceUpdate,
  WorkspaceType,
} from "@/types";
import { FaUsers, FaUser } from "react-icons/fa";

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
        <label className="block text-sm font-medium theme-text-primary mb-2">
          {t("workspace.form.name", "Workspace Name")}{" "}
          <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t(
            "workspace.form.namePlaceholder",
            "e.g., Family Budget, Business Expenses",
          )}
          className="w-full px-4 py-3 rounded-lg theme-surface theme-border border theme-text-primary placeholder:theme-text-tertiary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
          disabled={isLoading}
          autoFocus
        />
      </div>

      {/* Type selection (only for new workspaces) */}
      {!isEditing && (
        <div>
          <label className="block text-sm font-medium theme-text-primary mb-3">
            {t("workspace.form.type", "Workspace Type")}
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setType("personal")}
              className={`flex items-center gap-3 p-4 rounded-xl border theme-transition ${
                type === "personal"
                  ? "border-emerald-500 theme-success-light"
                  : "theme-border hover:theme-surface-hover"
              }`}
              disabled={isLoading}
            >
              <div
                className={`p-2 rounded-lg ${
                  type === "personal"
                    ? "theme-success-light theme-success"
                    : "theme-surface-hover theme-text-secondary"
                }`}
              >
                <FaUser className="w-5 h-5" />
              </div>
              <div className="text-left">
                <div
                  className={`font-medium ${type === "personal" ? "theme-success" : "theme-text-primary"}`}
                >
                  {t("workspace.types.personal", "Personal")}
                </div>
                <div className="text-xs theme-text-tertiary">
                  {t("workspace.types.personalDesc", "Just for you")}
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setType("shared")}
              className={`flex items-center gap-3 p-4 rounded-xl border theme-transition ${
                type === "shared"
                  ? "border-blue-500 theme-accent-light"
                  : "theme-border hover:theme-surface-hover"
              }`}
              disabled={isLoading}
            >
              <div
                className={`p-2 rounded-lg ${
                  type === "shared"
                    ? "theme-accent-light theme-accent"
                    : "theme-surface-hover theme-text-secondary"
                }`}
              >
                <FaUsers className="w-5 h-5" />
              </div>
              <div className="text-left">
                <div
                  className={`font-medium ${type === "shared" ? "theme-accent" : "theme-text-primary"}`}
                >
                  {t("workspace.types.shared", "Shared")}
                </div>
                <div className="text-xs theme-text-tertiary">
                  {t("workspace.types.sharedDesc", "Collaborate with others")}
                </div>
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-3 rounded-lg theme-error-light theme-error text-sm">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t theme-border">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg theme-text-secondary hover:theme-surface-hover theme-transition"
          disabled={isLoading}
        >
          {t("common.cancel", "Cancel")}
        </button>
        <button
          type="submit"
          className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed theme-transition"
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
