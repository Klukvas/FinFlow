import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '../shared/Modal';
import { EmailInput } from '../inputs/EmailInput';
import { PasswordInput } from '../inputs/PasswordInput';
import { useAuth } from '@/contexts/AuthContext';
import { useAuthForm } from '@/hooks';
import { RegisterRequest } from '@/services/api/userApiClient';
import { config } from '@/config/env';
import { MdOutlineDriveFileRenameOutline } from "react-icons/md";
import { validateEmail } from '@/utils';
import { validateUsername, validatePasswordStrength } from '@/utils/validation';

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

interface ValidationErrors {
  username: string;
  email: string;
  password: string;
}

export const RegisterModal: React.FC<RegisterModalProps> = ({ 
  isOpen, 
  onClose, 
  onSwitchToLogin 
}) => {
  const { t } = useTranslation();
  const { register } = useAuth();
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({
    username: '',
    email: '',
    password: ''
  });
  
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
      username: "",
    } as RegisterRequest,
    validateEmail: false, // We handle validation separately with translations
    onSubmit: async (data: RegisterRequest) => {
      // Validate all fields before submitting
      const errors: ValidationErrors = {
        username: '',
        email: '',
        password: ''
      };

      // Validate username
      const usernameValidation = validateUsername(data.username);
      if (!usernameValidation.isValid) {
        errors.username = usernameValidation.errors[0] || 'Invalid username';
      }

      // Validate email
      if (!validateEmail(data.email)) {
        errors.email = t('auth.invalidEmail');
      }

      // Validate password
      const passwordValidation = validatePasswordStrength(data.password);
      if (!passwordValidation.isValid) {
        errors.password = passwordValidation.errors[0] || 'Invalid password';
      }

      // If any errors, show them and stop submission
      if (errors.username || errors.email || errors.password) {
        setValidationErrors(errors);
        throw new Error('Validation failed');
      }
      
      if (config.debug) {
      }
      
      const result = await register(data.email, data.password, data.username);
      
      if (config.debug) {
      }
      
      if (result.success) {
        if (config.debug) {
        }
        onClose();
      } else {
        if (config.debug) {
          console.error('Registration error:', result.error);
        }
        setError(result.error || t('auth.registerError'));
      }
    },
  });

  const handleClose = () => {
    setError('');
    setValidationErrors({ username: '', email: '', password: '' });
    onClose();
  };

  // Validate username on blur
  const handleUsernameBlur = () => {
    if (formData.username) {
      const validation = validateUsername(formData.username);
      setValidationErrors(prev => ({
        ...prev,
        username: validation.isValid ? '' : (validation.errors[0] || 'Invalid username')
      }));
    }
  };

  // Validate email on blur
  const handleEmailBlur = () => {
    if (formData.email && !validateEmail(formData.email)) {
      setValidationErrors(prev => ({
        ...prev,
        email: t('auth.invalidEmail')
      }));
    } else {
      setValidationErrors(prev => ({ ...prev, email: '' }));
    }
  };

  // Validate password on blur
  const handlePasswordBlur = () => {
    if (formData.password) {
      const validation = validatePasswordStrength(formData.password);
      setValidationErrors(prev => ({
        ...prev,
        password: validation.isValid ? '' : (validation.errors[0] || 'Invalid password')
      }));
    }
  };

  // Clear validation error when user starts typing
  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e);
    if (validationErrors.username) {
      setValidationErrors(prev => ({ ...prev, username: '' }));
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e);
    if (validationErrors.email) {
      setValidationErrors(prev => ({ ...prev, email: '' }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e);
    if (validationErrors.password) {
      setValidationErrors(prev => ({ ...prev, password: '' }));
    }
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose}
      title={t('auth.registerTitle')}
      size="md"
      data-testid="register-modal"
    >
      <div className="space-y-6">
        <p className="theme-text-secondary">
          {t('auth.registerTitle')}
        </p>

        <form onSubmit={handleSubmit} noValidate className="space-y-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium theme-text-primary">
              {t('auth.username')} <span className="theme-error">*</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MdOutlineDriveFileRenameOutline className="w-4 h-4 theme-text-tertiary" />
              </div>
              <input
                type="text"
                name="username"
                data-testid="username-input"
                placeholder={t('auth.username')}
                value={formData.username}
                onChange={handleUsernameChange}
                onBlur={handleUsernameBlur}
                className={`w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary ${
                  validationErrors.username ? 'border-red-500' : 'theme-border'
                }`}
                required
              />
            </div>
            {validationErrors.username && (
              <p className="text-red-500 text-sm mt-1">{validationErrors.username}</p>
            )}
          </div>

          <EmailInput 
            data-testid="email-input"
            value={formData.email} 
            onChange={handleEmailChange}
            onBlur={handleEmailBlur}
            error={validationErrors.email} 
          />
          
          <PasswordInput 
            data-testid="password-input"
            value={formData.password} 
            onChange={handlePasswordChange}
            onBlur={handlePasswordBlur}
            error={validationErrors.password}
          />
          
          {error && (
            <div className="theme-error-light theme-border border rounded-lg p-4">
              <p className="theme-error text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !!validationErrors.username || !!validationErrors.email || !!validationErrors.password}
            data-testid="submit-register-button"
            className="w-full theme-accent-bg hover:theme-accent-hover theme-text-inverse font-semibold py-3 px-4 rounded-lg theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? t('common.loading') : t('auth.registerButton')}
          </button>
        </form>

        <div className="text-center">
          <p className="theme-text-secondary">
            Уже есть аккаунт?{' '}
            <button
              onClick={onSwitchToLogin}
              className="theme-accent hover:theme-accent-hover font-medium theme-transition"
            >
              {t('navigation.login')}
            </button>
          </p>
        </div>
      </div>
    </Modal>
  );
};
