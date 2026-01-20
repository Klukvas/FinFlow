import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheck, FaTimes, FaSpinner } from 'react-icons/fa';
import { Modal } from '@/components/ui/shared/Modal';
import { Button } from '@/components/ui/shared/Button';
import { PaymentButton } from '@/components/payment/PaymentButton';
import { useApiClients } from '@/hooks/useApiClients';
import { PlanWithFeatures } from '@/types/subscription';

interface UpgradePlanModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Plan pricing configuration
const PLAN_PRICING: Record<string, { price: number; popular?: boolean }> = {
  basic: { price: 0 },
  professional: { price: 9.99, popular: true },
  enterprise: { price: 29.99 },
};

export const UpgradePlanModal: React.FC<UpgradePlanModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const { subscription } = useApiClients();
  const [plans, setPlans] = useState<PlanWithFeatures[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchPlans();
    }
  }, [isOpen]);

  const fetchPlans = async () => {
    setLoading(true);
    setError(null);
    
    const result = await subscription.getPlansWithFeatures();
    
    if ('error' in result) {
      setError(result.error);
    } else {
      // Sort plans: basic, professional, enterprise
      const sortedPlans = result.sort((a, b) => {
        const order = ['basic', 'professional', 'enterprise'];
        return order.indexOf(a.code) - order.indexOf(b.code);
      });
      setPlans(sortedPlans);
    }
    
    setLoading(false);
  };

  const formatFeatureLimit = (feature: { name: string; limit_value: number | null }): string => {
    if (feature.limit_value === null) {
      return `Unlimited ${feature.name}`;
    }
    return `${feature.limit_value} ${feature.name}`;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('subscription.upgradePlan')}
      size="4xl"
    >
      <div className="space-y-6">
        <p className="theme-text-secondary text-center">
          {t('subscription.upgradeDescription')}
        </p>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <FaSpinner className="animate-spin text-4xl theme-text-secondary" />
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchPlans} variant="outline">
              {t('common.retry', 'Retry')}
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const pricing = PLAN_PRICING[plan.code] || { price: 0 };
              const features = Object.values(plan.features);
              
              return (
                <div
                  key={plan.code}
                  className={`relative theme-surface theme-border border rounded-xl p-6 transition-all ${
                    pricing.popular ? 'ring-2 ring-blue-500 scale-[1.02]' : ''
                  } hover:theme-shadow hover:scale-[1.01]`}
                >
                  {pricing.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1 rounded-full text-xs font-medium shadow-lg">
                        {t('pricingPage.popular', 'Most Popular')}
                      </span>
                    </div>
                  )}
                  
                  <div className="text-center mb-6 pt-2">
                    <h3 className="text-xl font-bold theme-text-primary mb-2">
                      {plan.name}
                    </h3>
                    <div className="mb-4">
                      <span className="text-4xl font-bold theme-text-primary">
                        {pricing.price === 0 ? t('pricingPage.free', 'Free') : `$${pricing.price}`}
                      </span>
                      <span className="theme-text-secondary text-sm ml-1">
                        {pricing.price === 0 ? '' : t('pricingPage.perMonth', '/month')}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-3 mb-6 min-h-[280px]">
                    {features.map((feature) => (
                      <div key={feature.code} className="flex items-start text-sm">
                        <FaCheck className="w-4 h-4 theme-success mr-3 mt-0.5 flex-shrink-0" />
                        <span className="theme-text-primary">
                          {formatFeatureLimit(feature)}
                        </span>
                      </div>
                    ))}
                  </div>

                  {pricing.price === 0 ? (
                    <Button
                      variant="outline"
                      fullWidth
                      size="md"
                      onClick={onClose}
                    >
                      {t('subscription.currentPlan', 'Current Plan')}
                    </Button>
                  ) : (
                    <PaymentButton
                      planCode={plan.code}
                      planName={plan.name}
                      amount={pricing.price}
                      currency="UAH"
                      variant={pricing.popular ? 'primary' : 'outline'}
                      size="md"
                      fullWidth
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

      </div>
    </Modal>
  );
};
