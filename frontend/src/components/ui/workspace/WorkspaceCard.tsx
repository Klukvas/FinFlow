import React from 'react';
import { useTranslation } from 'react-i18next';
import { Workspace } from '@/types';
import { FaUsers, FaUser, FaCrown, FaArchive, FaEdit, FaSignOutAlt, FaTrash } from 'react-icons/fa';

interface WorkspaceCardProps {
  workspace: Workspace;
  isCurrentWorkspace: boolean;
  onSelect: (workspaceId: string) => void;
  onEdit: (workspace: Workspace) => void;
  onArchive: (workspace: Workspace) => void;
  onLeave: (workspace: Workspace) => void;
}

export const WorkspaceCard: React.FC<WorkspaceCardProps> = ({
  workspace,
  isCurrentWorkspace,
  onSelect,
  onEdit,
  onArchive,
  onLeave,
}) => {
  const { t } = useTranslation();

  const isOwner = workspace.current_user_role === 'owner';
  const isAdmin = workspace.current_user_role === 'admin';
  const canEdit = isOwner || isAdmin;
  const canLeave = !isOwner && workspace.type !== 'personal';
  const canArchive = isOwner && workspace.type !== 'personal';

  const getRoleBadge = () => {
    const roleColors: Record<string, string> = {
      owner: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
      admin: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      member: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      viewer: 'bg-gray-100 text-gray-800 dark:bg-gray-700/30 dark:text-gray-400',
    };

    const role = workspace.current_user_role || 'member';
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${roleColors[role]}`}>
        {role === 'owner' && <FaCrown className="inline w-3 h-3 mr-1" />}
        {t(`workspace.roles.${role}`, role)}
      </span>
    );
  };

  return (
    <div 
      className={`relative p-4 rounded-xl theme-surface theme-border border theme-transition hover:shadow-md ${
        isCurrentWorkspace ? 'ring-2 ring-offset-2 theme-accent ring-current' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className={`p-2.5 rounded-lg ${
            workspace.type === 'personal' 
              ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' 
              : 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
          }`}>
            {workspace.type === 'personal' ? (
              <FaUser className="w-5 h-5" />
            ) : (
              <FaUsers className="w-5 h-5" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold theme-text-primary truncate">{workspace.name}</h3>
            <p className="text-sm theme-text-tertiary">
              {workspace.type === 'personal' 
                ? t('workspace.personal', 'Personal') 
                : t('workspace.shared', 'Shared')}
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
            <span>{workspace.member_count} {t('workspace.members', 'members')}</span>
          </div>
        )}
        <div className="text-xs theme-text-tertiary">
          {t('workspace.created', 'Created')} {new Date(workspace.created_at).toLocaleDateString()}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t theme-border">
        {!isCurrentWorkspace && (
          <button
            onClick={() => onSelect(workspace.id)}
            className="flex-1 px-3 py-2 text-sm font-medium theme-accent theme-accent-light rounded-lg hover:opacity-80 theme-transition"
          >
            {t('workspace.select', 'Select')}
          </button>
        )}
        {isCurrentWorkspace && (
          <span className="flex-1 px-3 py-2 text-sm font-medium text-center theme-text-tertiary">
            {t('workspace.current', 'Current')}
          </span>
        )}
        
        {canEdit && (
          <button
            onClick={() => onEdit(workspace)}
            className="p-2 rounded-lg hover:theme-surface-hover theme-text-secondary theme-transition"
            title={t('common.edit', 'Edit')}
          >
            <FaEdit className="w-4 h-4" />
          </button>
        )}
        
        {canLeave && (
          <button
            onClick={() => onLeave(workspace)}
            className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 theme-transition"
            title={t('workspace.leave', 'Leave')}
          >
            <FaSignOutAlt className="w-4 h-4" />
          </button>
        )}
        
        {canArchive && (
          <button
            onClick={() => onArchive(workspace)}
            className="p-2 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 text-orange-500 theme-transition"
            title={t('workspace.archive', 'Archive')}
          >
            <FaArchive className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default WorkspaceCard;

