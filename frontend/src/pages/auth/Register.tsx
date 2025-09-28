import { EmailInput, PasswordInput } from '../../components';
import { Link, useNavigate } from 'react-router-dom';
import React from 'react';
import { RegisterRequest } from '../../services/api/userApiClient';
import { useAuth } from '../../contexts/AuthContext';
import { useAuthForm } from '../../hooks';
import { MdOutlineDriveFileRenameOutline } from "react-icons/md";
import { config } from '@/config/env';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  
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
    onSubmit: async (data: RegisterRequest) => {
      if (config.debug) {
        console.log('Attempting registration with:', data);
      }
      
      const result = await register(data.email, data.password, data.username);
      
      if (config.debug) {
        console.log('Registration result:', result);
      }
      
      if (result.success) {
        if (config.debug) {
          console.log('Registration successful, navigating to category page');
        }
        navigate('/category', { replace: true });
      } else {
        if (config.debug) {
          console.error('Registration error:', result.error);
        }
        setError(result.error || 'Ошибка при регистрации');
      }
    },
  });

  return (
    <div className="flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="theme-surface theme-border border rounded-lg theme-shadow p-6 md:p-8 theme-transition">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold theme-text-primary mb-2">
              Регистрация
            </h2>
            <p className="theme-text-secondary">
              Создайте новый аккаунт для начала работы
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium theme-text-primary">
                Имя пользователя <span className="theme-error">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MdOutlineDriveFileRenameOutline className="w-4 h-4 theme-text-tertiary" />
                </div>
                <input
                  type="text"
                  name="username"
                  placeholder="Введите имя пользователя"
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full pl-10 pr-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary"
                  required
                />
              </div>
            </div>

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
              {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="theme-text-secondary">
              Уже есть аккаунт?{' '}
              <Link 
                to="/login" 
                className="theme-accent hover:theme-accent-hover font-medium theme-transition"
              >
                Войти
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}