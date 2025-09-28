import { EmailInput, PasswordInput } from '../../components';
import { Link, useNavigate } from 'react-router-dom';
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useAuthForm } from '../../hooks';
import { LoginRequest } from '../../services/api/userApiClient';
import { config } from '@/config/env';

export default function Login() {
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
        console.log('Attempting login with:', data);
      }
      
      const result = await login(data.email, data.password);
      
      if (config.debug) {
        console.log('Login result:', result);
      }
      
      if (result.success) {
        if (config.debug) {
          console.log('Login successful, navigating to category page');
        }
        navigate('/category', { replace: true });
      } else {
        if (config.debug) {
          console.error('Login error:', result.error);
        }
        setError(result.error || 'Ошибка при входе в систему');
      }
    },
  });

  return (
    <div className="flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="theme-surface theme-border border rounded-lg theme-shadow p-6 md:p-8 theme-transition">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold theme-text-primary mb-2">
              Вход в систему
            </h2>
            <p className="theme-text-secondary">
              Войдите в свой аккаунт для продолжения
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
              <div className="theme-error-light theme-border border rounded-lg p-4">
                <p className="theme-error text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full theme-accent-bg hover:theme-accent-hover theme-text-inverse font-semibold py-3 px-4 rounded-lg theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Вход...' : 'Войти'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="theme-text-secondary">
              Нет аккаунта?{' '}
              <Link 
                to="/register" 
                className="theme-accent hover:theme-accent-hover font-medium theme-transition"
              >
                Зарегистрироваться
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
