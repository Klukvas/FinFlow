import React from 'react';
import { Modal } from './Modal';
import { EmailInput, PasswordInput } from '../';
import { useAuth } from '@/contexts/AuthContext';
import { useAuthForm } from '@/hooks';
import { RegisterRequest } from '@/services/api/userApiClient';
import { config } from '@/config/env';
import { MdOutlineDriveFileRenameOutline } from "react-icons/md";

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

export const RegisterModal: React.FC<RegisterModalProps> = ({ 
  isOpen, 
  onClose, 
  onSwitchToLogin 
}) => {
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
          console.log('Registration successful, closing modal');
        }
        onClose();
      } else {
        if (config.debug) {
          console.error('Registration error:', result.error);
        }
        setError(result.error || 'Ошибка при регистрации');
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
      title="Регистрация"
      size="md"
    >
      <div className="space-y-6">
        <p className="theme-text-secondary">
          Создайте новый аккаунт для начала работы
        </p>

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
            error={error === "Введите корректный email." ? error : undefined} 
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

        <div className="text-center">
          <p className="theme-text-secondary">
            Уже есть аккаунт?{' '}
            <button
              onClick={onSwitchToLogin}
              className="theme-accent hover:theme-accent-hover font-medium theme-transition"
            >
              Войти
            </button>
          </p>
        </div>
      </div>
    </Modal>
  );
};
