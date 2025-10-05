import React from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from './Modal';
import { EmailInput, PasswordInput } from '../';
import { useAuth } from '@/contexts/AuthContext';
import { useAuthForm } from '@/hooks';
import { LoginRequest } from '@/services/api/userApiClient';
import { config } from '@/config/env';

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
    onSubmit: async (data: LoginRequest) => {
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
    onClose();
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

        <form onSubmit={handleSubmit} className="space-y-6">
          <EmailInput 
            value={formData.email} 
            onChange={handleChange} 
            error={error === "Введите корректный email." ? error : undefined} 
          />
          
          <PasswordInput 
            value={formData.password} 
            onChange={handleChange} 
          />
          
          {error && error !== "Введите корректный email." && (
            <div className="theme-error-light theme-border border rounded-lg p-4" data-testid="login-error">
              <p className="theme-error text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
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
