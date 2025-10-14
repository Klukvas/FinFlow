import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '../shared/Modal';
import { EmailInput } from '../inputs/EmailInput';
import { PasswordInput } from '../inputs/PasswordInput';
import { useAuth } from '@/contexts/AuthContext';
import { useAuthForm } from '@/hooks';
import { LoginRequest } from '@/services/api/userApiClient';
import { config } from '@/config/env';
import { validateEmail } from '@/utils';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToRegister: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ 
  isOpen, 
  onClose, 
  onSwitchToRegister 
}) => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const [emailError, setEmailError] = useState<string>('');
  
  const {
    formData,
    error,
    isLoading,
    handleChange,
    handleSubmit,
    setError,
  } = useAuthForm({
    initialValues: {
      email: "",
      password: "",
    } as LoginRequest,
    validateEmail: false, // We handle email validation separately with translations
    onSubmit: async (data: LoginRequest) => {
      // Validate email before submitting
      if (!validateEmail(data.email)) {
        setEmailError(t('auth.invalidEmail'));
        throw new Error('Invalid email');
      }
      
      if (config.debug) {
      }
      
      const result = await login(data.email, data.password);
      
      if (config.debug) {
      }
      
      if (result.success) {
        if (config.debug) {
        }
        onClose();
      } else {
        if (config.debug) {
          console.error('Login error:', result.error);
        }
        setError(result.error || t('auth.loginError'));
      }
    },
  });

  const handleClose = () => {
    setError('');
    setEmailError('');
    onClose();
  };

  const handleEmailBlur = () => {
    if (formData.email && !validateEmail(formData.email)) {
      setEmailError(t('auth.invalidEmail'));
    } else {
      setEmailError('');
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e);
    // Clear error when user starts typing
    if (emailError) {
      setEmailError('');
    }
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose}
      title={t('auth.loginTitle')}
      size="md"
      data-testid="login-modal"
    >
      <div className="space-y-6">
        <p className="theme-text-secondary">
          {t('auth.loginTitle')}
        </p>

        <form onSubmit={handleSubmit} noValidate className="space-y-6">
          <EmailInput 
            value={formData.email} 
            onChange={handleEmailChange}
            onBlur={handleEmailBlur}
            error={emailError} 
          />
          
          <PasswordInput 
            value={formData.password} 
            onChange={handleChange} 
          />
          
          {error && (
            <div className="theme-error-light theme-border border rounded-lg p-4" data-testid="login-error">
              <p className="theme-error text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !!emailError}
            data-testid="submit-login-button"
            className="w-full theme-accent-bg hover:theme-accent-hover theme-text-inverse font-semibold py-3 px-4 rounded-lg theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? t('common.loading') : t('auth.loginButton')}
          </button>
        </form>

        <div className="text-center">
          <p className="theme-text-secondary">
            Нет аккаунта?{' '}
            <button
              data-testid="switch-to-register"
              onClick={onSwitchToRegister}
              className="theme-accent hover:theme-accent-hover font-medium theme-transition"
            >
              {t('navigation.register')}
            </button>
          </p>
        </div>
      </div>
    </Modal>
  );
};
