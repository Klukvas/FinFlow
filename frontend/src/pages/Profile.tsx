import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTutorial } from '@/contexts/TutorialContext';
import { useApiClients } from '@/hooks/useApiClients';
import { UserUpdate } from '@/services/api/userApiClient';
import { Modal } from '@/components/ui/shared/Modal';
import { Button } from '@/components/ui/shared/Button';
import { FormField } from '@/components/ui/forms/FormField';
import { Input } from '@/components/ui/forms/Input';
import { FaUser, FaEdit, FaSave, FaTimes, FaEnvelope, FaCalendarAlt, FaWallet, FaCrown, FaGraduationCap, FaReceipt, FaArrowRight } from 'react-icons/fa';
import { config } from '@/config/env';
import { CurrencySelect } from '@/components/ui/forms/CurrencySelect';
import { ProfileSkeleton } from '@/components/ui/profile/ProfileSkeleton';
import { SubscriptionLimits } from '@/components/ui/subscription/SubscriptionLimits';
import { SubscriptionResponse } from '@/types/subscription';

export const Profile = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isLoading, refreshUserProfile } = useAuth();
  const { startTutorial } = useTutorial();
  const { user: userApi, subscription: subscriptionApi } = useApiClients();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    currency: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [subscription, setSubscription] = useState<SubscriptionResponse | null>(null);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || '',
        currency: user.base_currency || ''
      });
    }
  }, [user]);

  useEffect(() => {
    const loadSubscription = async () => {
      if (!user?.id) return;

      try {
        setSubscriptionLoading(true);
        const response = await subscriptionApi.getUserSubscription(user.id);
        
        if (!('error' in response)) {
          setSubscription(response);
        }
      } catch (err) {
        console.error('Failed to load subscription:', err);
      } finally {
        setSubscriptionLoading(false);
      }
    };

    loadSubscription();
  }, [user?.id, subscriptionApi]);

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
        setError(t('user.errors.notFound'));
        return;
      }

      // Подготавливаем данные для обновления
      const updateData: UserUpdate = {};

      if (formData.email !== user.email) {
        updateData.email = formData.email;
      }

      if (formData.currency !== user.base_currency) {
        updateData.base_currency = formData.currency;
      }

      // Если нет изменений, просто закрываем модал
      if (Object.keys(updateData).length === 0) {
        setIsEditModalOpen(false);
        return;
      }

      const response = await userApi.updateProfile(updateData);
      
      if ('error' in response) {
        setError(response.error);
        if (config.debug) {
          console.error('Profile update error:', response.error);
        }
      } else {
        setSuccess(t('profile.profileUpdated'));
        
        // Refresh user profile data
        await refreshUserProfile();
        
        setIsEditModalOpen(false);
      }
    } catch (err) {
      setError(t('profile.profileUpdateError'));
      console.error('Profile update error:', err);
    } finally {
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    if (user) {
      setFormData({
        email: user.email || '',
        currency: user.base_currency || ''
      });
    }
    setError('');
    setSuccess('');
    setIsEditModalOpen(false);
  };

  if (isLoading) {
    return <ProfileSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">{t('profile.title')}</h1>
          <p className="theme-text-secondary mt-1">
            {t('profile.subtitle')}
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={startTutorial}
            className="flex items-center gap-2"
          >
            <FaGraduationCap className="w-4 h-4" />
            {t('profile.restartTutorial')}
          </Button>
          <Button
            onClick={() => setIsEditModalOpen(true)}
            className="flex items-center gap-2"
          >
            <FaEdit className="w-4 h-4" />
            {t('profile.editButton')}
          </Button>
        </div>
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
                {user?.email || t('profile.defaultUsername')}
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <FaWallet className="w-5 h-5 theme-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium theme-text-tertiary">{t('profile.baseCurrency')}</p>
                    <p className="theme-text-primary">{user?.base_currency || t('profile.notSpecified')}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <FaEnvelope className="w-5 h-5 theme-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium theme-text-tertiary">{t('common.email')}</p>
                    <p className="theme-text-primary">{user?.email}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <FaCalendarAlt className="w-5 h-5 theme-text-tertiary" />
                  <div>
                    <p className="text-sm font-medium theme-text-tertiary">{t('profile.userId')}</p>
                    <p className="theme-text-primary">#{user?.id}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FaCrown className="w-5 h-5 theme-text-tertiary" />
                    <div>
                      <p className="text-sm font-medium theme-text-tertiary">{t('profile.subscription')}</p>
                      {subscriptionLoading ? (
                        <p className="theme-text-secondary">{t('common.loading')}</p>
                      ) : subscription ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="theme-text-primary font-medium capitalize">{subscription.plan_code}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              subscription.status === 'active' 
                                ? 'theme-success-light theme-success' 
                                : 'theme-error-light theme-error'
                            }`}>
                              {subscription.status}
                            </span>
                          </div>
                          <div className="text-xs theme-text-secondary space-y-0.5">
                            <p>
                              {t('profile.subscriptionStarted')}: {new Date(subscription.started_at).toLocaleDateString()}
                            </p>
                            {subscription.expires_at && subscription.plan_code !== 'basic' && !subscription.plan_code.startsWith('basic-') && (
                              <p>
                                {t('profile.nextBilling')}: {new Date(subscription.expires_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </div>
                      ) : (
                        <p className="theme-text-secondary">{t('profile.noSubscription')}</p>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate('/payment/history')}
                    className="ml-2"
                  >
                    <FaReceipt className="mr-1" />
                    {t('payment.history')}
                  </Button>
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
              <p className="text-sm font-medium theme-text-tertiary">{t('profile.accountStatus')}</p>
              <p className="text-lg font-semibold theme-text-primary">{t('profile.active')}</p>
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
              <p className="text-sm font-medium theme-text-tertiary">{t('profile.registrationDate')}</p>
              <p className="text-lg font-semibold theme-text-primary">
                {user?.id ? t('profile.recently') : t('profile.notSpecified')}
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
              <p className="text-sm font-medium theme-text-tertiary">{t('profile.emailVerified')}</p>
              <p className="text-lg font-semibold theme-text-primary">{t('common.yes')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Subscription Limits */}
      <SubscriptionLimits />

      {/* Edit Profile Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={handleCancelEdit}
        title={t('profile.editModalTitle')}
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

          <FormField label={t('common.email')} required>
            <Input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder={t('auth.email')}
              disabled
            />
          </FormField>

          <FormField label={t('profile.baseCurrency')} required>
            <CurrencySelect
              showFlags={true}
              value={formData.currency}
              onChange={(value) => handleInputChange({ target: { name: 'currency', value } } as any)}
              placeholder={t('profile.baseCurrency')}
            />
          </FormField>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={handleCancelEdit}
              disabled={isEditing}
            >
              <FaTimes className="w-4 h-4 mr-2" />
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleEditProfile}
              disabled={isEditing}
              loading={isEditing}
            >
              <FaSave className="w-4 h-4 mr-2" />
              {t('common.save')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
