import React from 'react';
import { useTranslation } from 'react-i18next';
import { MyInvite } from '@/types';
import { FaUsers, FaCheck, FaTimes, FaClock, FaEye, FaEdit, FaUser, FaSpinner } from 'react-icons/fa';

interface MyInviteCardProps {
  invite: MyInvite;
  onAccept: (inviteId: string) => void;
  onReject: (inviteId: string) => void;
  isLoading?: boolean;
  loadingAction?: 'accept' | 'reject' | null;
}

export const MyInviteCard: React.FC<MyInviteCardProps> = ({
  invite,
  onAccept,
  onReject,
  isLoading = false,
  loadingAction = null,
}) => {
  const { t } = useTranslation();

  const getRoleBadge = () => {
    const roleConfig = {
      read: {
        icon: <FaEye className="w-3 h-3" />,
        className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
        label: t('workspace.roles.read', 'View Only'),
      },
      full: {
        icon: <FaEdit className="w-3 h-3" />,
        className: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
        label: t('workspace.roles.full', 'Full Access'),
      },
    };

    const config = roleConfig[invite.role] || roleConfig.read;
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${config.className}`}>
        {config.icon}
        {config.label}
      </span>
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
      return t('common.timeAgo.minutes', '{{count}} min ago', { count: diffMins });
    } else if (diffHours < 24) {
      return t('common.timeAgo.hours', '{{count}}h ago', { count: diffHours });
    } else {
      return t('common.timeAgo.days', '{{count}}d ago', { count: diffDays });
    }
  };

  const formatExpiresIn = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    
    if (diffMs <= 0) {
      return t('workspace.invite.expired', 'Expired');
    }

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays > 0) {
      return t('workspace.invite.expiresInDays', 'Expires in {{count}} days', { count: diffDays });
    } else if (diffHours > 0) {
      return t('workspace.invite.expiresInHours', 'Expires in {{count}} hours', { count: diffHours });
    } else {
      return t('workspace.invite.expiresSoon', 'Expires soon');
    }
  };

  const isExpired = invite.is_expired || new Date(invite.expires_at) <= new Date();
  const canRespond = invite.is_actionable && !isExpired;

  return (
    <div className="p-5 rounded-xl theme-surface border theme-border shadow-sm hover:shadow-md theme-transition">
      {/* Header - Workspace Info */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
            <FaUsers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold theme-text-primary text-lg">
              {invite.workspace_name}
            </h3>
            <div className="flex items-center gap-2 text-sm theme-text-secondary mt-0.5">
              <FaUser className="w-3 h-3" />
              <span>
                {t('workspace.invite.from', 'From')} <span className="font-medium">{invite.inviter_username}</span>
              </span>
            </div>
          </div>
        </div>
        {getRoleBadge()}
      </div>

      {/* Inviter info */}
      <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 mb-4">
        <p className="text-sm theme-text-secondary">
          <span className="font-medium theme-text-primary">{invite.inviter_email}</span>
          {' '}
          {t('workspace.invite.invitedYou', 'invited you to collaborate')}
        </p>
      </div>

      {/* Time info */}
      <div className="flex items-center justify-between text-sm theme-text-tertiary mb-4">
        <div className="flex items-center gap-1">
          <FaClock className="w-3 h-3" />
          <span>{formatTimeAgo(invite.created_at)}</span>
        </div>
        <span className={isExpired ? 'text-red-500 font-medium' : ''}>
          {isExpired ? t('workspace.invite.expired', 'Expired') : formatExpiresIn(invite.expires_at)}
        </span>
      </div>

      {/* Actions */}
      {canRespond ? (
        <div className="flex items-center gap-3">
          <button
            onClick={() => onReject(invite.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border theme-border theme-text-secondary hover:bg-red-50 hover:border-red-200 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:border-red-800 dark:hover:text-red-400 font-medium theme-transition disabled:opacity-50"
            disabled={isLoading}
          >
            {loadingAction === 'reject' ? (
              <FaSpinner className="w-4 h-4 animate-spin" />
            ) : (
              <FaTimes className="w-4 h-4" />
            )}
            {t('workspace.invite.reject', 'Decline')}
          </button>
          <button
            onClick={() => onAccept(invite.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 theme-transition disabled:opacity-50"
            disabled={isLoading}
          >
            {loadingAction === 'accept' ? (
              <FaSpinner className="w-4 h-4 animate-spin" />
            ) : (
              <FaCheck className="w-4 h-4" />
            )}
            {t('workspace.invite.accept', 'Accept')}
          </button>
        </div>
      ) : (
        <div className="text-center py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm theme-text-tertiary">
          {isExpired 
            ? t('workspace.invite.expiredMessage', 'This invitation has expired')
            : t('workspace.invite.alreadyResponded', 'You have already responded to this invitation')
          }
        </div>
      )}
    </div>
  );
};

export default MyInviteCard;
