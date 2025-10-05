import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClients } from '@/hooks/useApiClients';
import { UserUpdate } from '@/services/api/userApiClient';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { FormField } from '@/components/ui/forms/FormField';
import { Input } from '@/components/ui/forms/Input';
import { FaUser, FaEdit, FaSave, FaTimes, FaEnvelope, FaCalendarAlt } from 'react-icons/fa';
import { config } from '@/config/env';

export const Profile = () => {
  const { user, isLoading } = useAuth();
  const { user: userApi } = useApiClients();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || ''
      });
    }
  }, [user]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEditProfile = async () => {
    setIsEditing(true);
    setError('');
    setSuccess('');

    try {
      if (!user) {
        setError('Пользователь не найден');
        return;
      }

      // Подготавливаем данные для обновления
      const updateData: UserUpdate = {};
      
      if (formData.username !== user.username) {
        updateData.username = formData.username;
      }
      
      if (formData.email !== user.email) {
        updateData.email = formData.email;
      }

      // Если нет изменений, просто закрываем модал
      if (Object.keys(updateData).length === 0) {
        setIsEditModalOpen(false);
        return;
      }

      if (config.debug) {
      }

      const response = await userApi.updateProfile(updateData);
      
      if ('error' in response) {
        setError(response.error);
        if (config.debug) {
          console.error('Profile update error:', response.error);
        }
      } else {
        setSuccess('Профиль успешно обновлен!');
        setIsEditModalOpen(false);
        
        // Обновляем данные пользователя
        // TODO: Добавить обновление данных пользователя через AuthContext
      }
    } catch (err) {
      setError('Ошибка при обновлении профиля');
      console.error('Profile update error:', err);
    } finally {
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || ''
      });
    }
    setError('');
    setSuccess('');
    setIsEditModalOpen(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 theme-accent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">Профиль пользователя</h1>
          <p className="theme-text-secondary mt-1">
            Управление личными данными и настройками аккаунта
          </p>
        </div>
        
        <Button
          onClick={() => setIsEditModalOpen(true)}
          className="flex items-center gap-2"
        >
          <FaEdit className="w-4 h-4" />
          Редактировать профиль
        </Button>
      </div>

      {/* Profile Information */}
      <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
        <div className="flex items-start space-x-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            <div className="w-24 h-24 theme-accent-light rounded-full flex items-center justify-center">
              <FaUser className="w-12 h-12 theme-accent" />
            </div>
          </div>

          {/* User Info */}
          <div className="flex-1 space-y-4">
            <div>
              <h2 className="text-xl font-semibold theme-text-primary">
                {user?.username || 'Пользователь'}
              </h2>
              <p className="theme-text-secondary">{user?.email}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <FaUser className="w-5 h-5 theme-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium theme-text-tertiary">Имя пользователя</p>
                    <p className="theme-text-primary">{user?.username || 'Не указано'}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <FaEnvelope className="w-5 h-5 theme-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium theme-text-tertiary">Email</p>
                    <p className="theme-text-primary">{user?.email}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <FaCalendarAlt className="w-5 h-5 theme-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium theme-text-tertiary">ID пользователя</p>
                    <p className="theme-text-primary">#{user?.id}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Account Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 theme-success-light rounded-full flex items-center justify-center">
                <FaUser className="w-4 h-4 theme-success" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium theme-text-tertiary">Статус аккаунта</p>
              <p className="text-lg font-semibold theme-text-primary">Активен</p>
            </div>
          </div>
        </div>

        <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 theme-accent-light rounded-full flex items-center justify-center">
                <FaCalendarAlt className="w-4 h-4 theme-accent" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium theme-text-tertiary">Дата регистрации</p>
              <p className="text-lg font-semibold theme-text-primary">
                {user?.id ? 'Недавно' : 'Неизвестно'}
              </p>
            </div>
          </div>
        </div>

        <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 theme-accent-light rounded-full flex items-center justify-center">
                <FaEnvelope className="w-4 h-4 theme-accent" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium theme-text-tertiary">Email подтвержден</p>
              <p className="text-lg font-semibold theme-text-primary">Да</p>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={handleCancelEdit}
        title="Редактировать профиль"
        size="md"
      >
        <div className="space-y-4">
          {error && (
            <div className="theme-error-light theme-border border theme-error rounded-lg p-4">
              <p className="theme-error text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="theme-success-light theme-border border theme-success rounded-lg p-4">
              <p className="theme-success text-sm">{success}</p>
            </div>
          )}

          <FormField label="Имя пользователя" required>
            <Input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Введите имя пользователя"
            />
          </FormField>

          <FormField label="Email" required>
            <Input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Введите email"
              disabled
            />
            <p className="text-xs theme-text-tertiary mt-1">
              Email нельзя изменить
            </p>
          </FormField>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={handleCancelEdit}
              disabled={isEditing}
            >
              <FaTimes className="w-4 h-4 mr-2" />
              Отмена
            </Button>
            <Button
              onClick={handleEditProfile}
              disabled={isEditing}
              loading={isEditing}
            >
              <FaSave className="w-4 h-4 mr-2" />
              Сохранить
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
