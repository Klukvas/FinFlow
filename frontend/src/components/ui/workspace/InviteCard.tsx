import React from 'react';
import { useTranslation } from 'react-i18next';
import { WorkspaceInvite, InviteStatus } from '@/types';
import { FaEnvelope, FaClock, FaTimes, FaCheck, FaBan, FaHourglass, FaEye, FaEdit } from 'react-icons/fa';

interface InviteCardProps {
  invite: WorkspaceInvite;
  onCancel?: (inviteId: string) => void;
  isLoading?: boolean;
}

export const InviteCard: React.FC<InviteCardProps> = ({
  invite,
  onCancel,
  isLoading = false,
}) => {
  const { t } = useTranslation();

  const getStatusBadge = (status: InviteStatus, isExpired: boolean) => {
    // Check if actually expired (time-based)
    const effectiveStatus = status === 'pending' && isExpired ? 'expired' : status;
    
    const statusConfig: Record<string, { icon: React.ReactNode; className: string; label: string }> = {
      pending: {
        icon: <FaHourglass className="w-3 h-3" />,
        className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
        label: t('workspace.invite.status.pending', 'Pending'),
      },
      accepted: {
        icon: <FaCheck className="w-3 h-3" />,
        className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
        label: t('workspace.invite.status.accepted', 'Accepted'),
      },
      rejected: {
        icon: <FaBan className="w-3 h-3" />,
        className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        label: t('workspace.invite.status.rejected', 'Rejected'),
      },
      expired: {
        icon: <FaClock className="w-3 h-3" />,
        className: 'bg-gray-100 text-gray-800 dark:bg-gray-700/30 dark:text-gray-400',
        label: t('workspace.invite.status.expired', 'Expired'),
      },
      canceled: {
        icon: <FaTimes className="w-3 h-3" />,
        className: 'bg-gray-100 text-gray-800 dark:bg-gray-700/30 dark:text-gray-400',
        label: t('workspace.invite.status.canceled', 'Canceled'),
      },
    };

    const config = statusConfig[effectiveStatus] || statusConfig.pending;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
        {config.icon}
        {config.label}
      </span>
    );
  };

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
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
        {config.icon}
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const canCancel = invite.status === 'pending' && !invite.is_expired;

  return (
    <div className="flex items-center justify-between p-4 rounded-lg theme-surface-hover border theme-border">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 theme-text-secondary">
          <FaEnvelope className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium theme-text-primary truncate">
              {invite.invitee_email}
            </span>
            {getRoleBadge()}
          </div>
          <div className="flex items-center gap-2 text-sm theme-text-tertiary mt-0.5">
            <span>{t('workspace.invite.sentAt', 'Sent')} {formatDate(invite.created_at)}</span>
            {invite.status === 'pending' && (
              <>
                <span>•</span>
                <span className={invite.is_expired ? 'text-red-500' : ''}>
                  {invite.is_expired 
                    ? t('workspace.invite.expired', 'Expired')
                    : t('workspace.invite.expiresAt', 'Expires') + ' ' + formatDate(invite.expires_at)
                  }
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {getStatusBadge(invite.status, invite.is_expired)}
        
        {canCancel && onCancel && (
          <button
            onClick={() => onCancel(invite.id)}
            className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 theme-transition"
            title={t('workspace.invite.cancel', 'Cancel Invite')}
            disabled={isLoading}
          >
            <FaTimes className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default InviteCard;
