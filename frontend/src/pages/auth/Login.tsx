import { EmailInput, PasswordInput } from '../../components';
import { Link, useNavigate } from 'react-router-dom';
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { useAuthForm } from '../../hooks';
import { LoginRequest } from '../../services/api/userApiClient';
import { config } from '@/config/env';

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
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
        navigate('/category', { replace: true });
      } else {
        if (config.debug) {
          console.error('Login error:', result.error);
        }
        setError(result.error || t('authPage.login.error'));
      }
    },
  });

  return (
    <div className="flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="theme-surface theme-border border rounded-lg theme-shadow p-6 md:p-8 theme-transition">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold theme-text-primary mb-2">
              {t('authPage.login.title')}
            </h2>
            <p className="theme-text-secondary">
              {t('authPage.login.subtitle')}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <EmailInput 
              value={formData.email} 
              onChange={handleChange} 
              error={error === "Введите корректный email." ? error : ""} 
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
              {isLoading ? t('authPage.login.loading') : t('authPage.login.submit')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="theme-text-secondary">
              {t('authPage.login.noAccount')}{' '}
              <Link 
                to="/register" 
                className="theme-accent hover:theme-accent-hover font-medium theme-transition"
              >
                {t('authPage.login.registerLink')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
