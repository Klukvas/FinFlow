import { EmailInput, PasswordInput } from '../../components';
import { Link, useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RegisterRequest } from '../../services/api/userApiClient';
import { useAuth } from '../../contexts/AuthContext';
import { useAuthForm } from '../../hooks';
import { MdOutlineDriveFileRenameOutline } from "react-icons/md";
import { config } from '@/config/env';
import { validateUsername, validatePasswordStrength, validateEmail, validateEmailDomain } from '../../utils/validation';

export default function Register() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [validationErrors, setValidationErrors] = useState<{
    username: string[];
    email: string[];
    password: string[];
  }>({
    username: [],
    email: [],
    password: []
  });

  const [touched, setTouched] = useState<{
    username: boolean;
    email: boolean;
    password: boolean;
  }>({
    username: false,
    email: false,
    password: false
  });
  
  const {
    formData,
    error,
    isLoading,
    handleChange: originalHandleChange,
    handleSubmit: originalHandleSubmit,
    setError,
  } = useAuthForm({
    initialValues: {
      email: "",
      password: "",
      username: "",
    } as RegisterRequest,
    onSubmit: async (data: RegisterRequest) => {
      if (config.debug) {
      }
      
      const result = await register(data.email, data.password, data.username);
      
      if (config.debug) {
      }
      
      if (result.success) {
        if (config.debug) {
        }
        navigate('/category', { replace: true });
      } else {
        if (config.debug) {
          console.error('Registration error:', result.error);
        }
        setError(result.error || t('authPage.register.error'));
      }
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    originalHandleChange(e);
    
    // Validate on change
    if (name === 'username') {
      const result = validateUsername(value);
      setValidationErrors(prev => ({ ...prev, username: result.errors }));
    } else if (name === 'email') {
      const emailResult = validateEmail(value);
      const domainResult = value.includes('@') ? validateEmailDomain(value) : { isValid: true, errors: [] };
      setValidationErrors(prev => ({ 
        ...prev, 
        email: [...emailResult.errors, ...domainResult.errors] 
      }));
    } else if (name === 'password') {
      const result = validatePasswordStrength(value);
      setValidationErrors(prev => ({ ...prev, password: result.errors }));
    }
  };

  const handleBlur = (fieldName: 'username' | 'email' | 'password') => {
    setTouched(prev => ({ ...prev, [fieldName]: true }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Mark all fields as touched
    setTouched({ username: true, email: true, password: true });
    
    // Validate all fields
    const usernameResult = validateUsername(formData.username);
    const emailResult = validateEmail(formData.email);
    const emailDomainResult = formData.email.includes('@') ? validateEmailDomain(formData.email) : { isValid: true, errors: [] };
    const passwordResult = validatePasswordStrength(formData.password);
    
    setValidationErrors({
      username: usernameResult.errors,
      email: [...emailResult.errors, ...emailDomainResult.errors],
      password: passwordResult.errors
    });
    
    // If any validation fails, don't submit
    if (!usernameResult.isValid || !emailResult.isValid || !emailDomainResult.isValid || !passwordResult.isValid) {
      return;
    }
    
    // Call original submit handler
    originalHandleSubmit(e);
  };

  return (
    <div className="flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="theme-surface theme-border border rounded-lg theme-shadow p-6 md:p-8 theme-transition">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold theme-text-primary mb-2">
              {t('authPage.register.title')}
            </h2>
            <p className="theme-text-secondary">
              {t('authPage.register.subtitle')}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium theme-text-primary">
                {t('authPage.register.usernameRequired')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MdOutlineDriveFileRenameOutline className="w-4 h-4 theme-text-tertiary" />
                </div>
                <input
                  type="text"
                  name="username"
                  placeholder={t('authPage.register.usernamePlaceholder')}
                  value={formData.username}
                  onChange={handleChange}
                  onBlur={() => handleBlur('username')}
                  className={`w-full pl-10 pr-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 ${
                    touched.username && validationErrors.username.length > 0
                      ? 'border-red-500 focus:ring-red-500'
                      : 'focus:ring-blue-500'
                  } focus:border-transparent theme-transition theme-bg theme-text-primary`}
                  required
                />
              </div>
              {touched.username && validationErrors.username.length > 0 && (
                <div className="mt-1 space-y-1">
                  {validationErrors.username.map((err, idx) => (
                    <p key={idx} className="text-red-500 text-xs">{err}</p>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <EmailInput 
                value={formData.email} 
                onChange={handleChange}
                onBlur={() => handleBlur('email')}
                error={touched.email && validationErrors.email.length > 0 ? validationErrors.email[0] : ""} 
              />
              {touched.email && validationErrors.email.length > 1 && (
                <div className="mt-1 space-y-1">
                  {validationErrors.email.slice(1).map((err, idx) => (
                    <p key={idx} className="text-red-500 text-xs">{err}</p>
                  ))}
                </div>
              )}
            </div>
            
            <div className="space-y-2">
              <PasswordInput 
                value={formData.password} 
                onChange={handleChange}
                onBlur={() => handleBlur('password')}
              />
              {touched.password && validationErrors.password.length > 0 && (
                <div className="mt-1 space-y-1">
                  {validationErrors.password.map((err, idx) => (
                    <p key={idx} className="text-red-500 text-xs">{err}</p>
                  ))}
                </div>
              )}
            </div>
            
            {error && (
              <div className="theme-error-light theme-border border rounded-lg p-4">
                <p className="theme-error text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full theme-accent-bg hover:theme-accent-hover theme-text-inverse font-semibold py-3 px-4 rounded-lg theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('authPage.register.loading') : t('authPage.register.submit')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="theme-text-secondary">
              {t('authPage.register.hasAccount')}{' '}
              <Link 
                to="/login" 
                className="theme-accent hover:theme-accent-hover font-medium theme-transition"
              >
                {t('authPage.register.loginLink')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}