import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { WorkspaceInviteCreate, AssignableRole } from '@/types';
import { FaEnvelope, FaEye, FaEdit, FaSpinner } from 'react-icons/fa';

interface InviteFormProps {
  onSubmit: (data: WorkspaceInviteCreate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export const InviteForm: React.FC<InviteFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  error: externalError,
}) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<AssignableRole>('read');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim().toLowerCase();
    
    if (!trimmedEmail) {
      setError(t('workspace.invite.emailRequired', 'Email is required'));
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setError(t('workspace.invite.invalidEmail', 'Please enter a valid email address'));
      return;
    }

    try {
      await onSubmit({ email: trimmedEmail, role });
    } catch (err) {
      // Error will be handled externally
    }
  };

  const displayError = externalError || error;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Email field */}
      <div>
        <label className="block text-sm font-medium theme-text-primary mb-2">
          {t('workspace.invite.email', 'Email Address')} <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <FaEnvelope className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 theme-text-tertiary" />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('workspace.invite.emailPlaceholder', 'colleague@example.com')}
            className="w-full pl-11 pr-4 py-3 rounded-lg theme-surface theme-border border theme-text-primary placeholder:theme-text-tertiary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition"
            disabled={isLoading}
            autoFocus
          />
        </div>
        <p className="mt-1.5 text-sm theme-text-tertiary">
          {t('workspace.invite.emailHint', 'The user must have an existing account')}
        </p>
      </div>

      {/* Role selection */}
      <div>
        <label className="block text-sm font-medium theme-text-primary mb-3">
          {t('workspace.invite.role', 'Permission Level')}
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setRole('read')}
            className={`flex items-center gap-3 p-4 rounded-xl border theme-transition ${
              role === 'read'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'theme-border hover:theme-surface-hover'
            }`}
            disabled={isLoading}
          >
            <div className={`p-2 rounded-lg ${
              role === 'read'
                ? 'bg-blue-100 text-blue-600 dark:bg-blue-800/50 dark:text-blue-400'
                : 'theme-surface-hover theme-text-secondary'
            }`}>
              <FaEye className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className={`font-medium ${role === 'read' ? 'text-blue-700 dark:text-blue-400' : 'theme-text-primary'}`}>
                {t('workspace.roles.read', 'View Only')}
              </div>
              <div className="text-xs theme-text-tertiary">
                {t('workspace.roles.readDesc', 'Can view all data')}
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setRole('full')}
            className={`flex items-center gap-3 p-4 rounded-xl border theme-transition ${
              role === 'full'
                ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                : 'theme-border hover:theme-surface-hover'
            }`}
            disabled={isLoading}
          >
            <div className={`p-2 rounded-lg ${
              role === 'full'
                ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-800/50 dark:text-emerald-400'
                : 'theme-surface-hover theme-text-secondary'
            }`}>
              <FaEdit className="w-5 h-5" />
            </div>
            <div className="text-left">
              <div className={`font-medium ${role === 'full' ? 'text-emerald-700 dark:text-emerald-400' : 'theme-text-primary'}`}>
                {t('workspace.roles.full', 'Full Access')}
              </div>
              <div className="text-xs theme-text-tertiary">
                {t('workspace.roles.fullDesc', 'Can view and edit')}
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Error message */}
      {displayError && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {displayError}
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
          {t('common.cancel', 'Cancel')}
        </button>
        <button
          type="submit"
          className="flex items-center gap-2 px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed theme-transition"
          disabled={isLoading || !email.trim()}
        >
          {isLoading && <FaSpinner className="w-4 h-4 animate-spin" />}
          {isLoading 
            ? t('workspace.invite.sending', 'Sending...') 
            : t('workspace.invite.send', 'Send Invite')
          }
        </button>
      </div>
    </form>
  );
};

export default InviteForm;
