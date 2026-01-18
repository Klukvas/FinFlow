import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheck, FaTimes } from 'react-icons/fa';
import { Modal } from '@/components/ui/shared/Modal';
import { Button } from '@/components/ui/shared/Button';
import { PaymentButton } from '@/components/payment/PaymentButton';

interface UpgradePlanModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UpgradePlanModal: React.FC<UpgradePlanModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();

  const plans = t('pricingPage.plans', { returnObjects: true }) as Array<{
    name: string;
    price: string;
    period: string;
    description: string;
    features: string[];
    limitations: string[];
    popular?: boolean;
    available?: boolean;
    code?: string;
  }>;

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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative theme-surface theme-border border rounded-xl p-6 transition-all ${
                plan.popular ? 'ring-2 ring-blue-500 scale-[1.02]' : ''
              } ${
                !plan.available ? 'opacity-50' : 'hover:theme-shadow hover:scale-[1.01]'
              }`}
            >
              {plan.popular && plan.available && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1 rounded-full text-xs font-medium shadow-lg">
                    {t('pricingPage.popular')}
                  </span>
                </div>
              )}
              
              <div className="text-center mb-6 pt-2">
                <h3 className="text-xl font-bold theme-text-primary mb-2">
                  {plan.name}
                </h3>
                <p className="theme-text-secondary text-sm mb-4">
                  {plan.description}
                </p>
                <div>
                  <span className="text-4xl font-bold theme-text-primary">
                    ${plan.price}
                  </span>
                  <span className="theme-text-secondary text-sm ml-1">
                    {plan.period}
                  </span>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                {plan.features.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-start text-sm">
                    <FaCheck className="w-4 h-4 theme-success mr-3 mt-0.5 flex-shrink-0" />
                    <span className="theme-text-primary">{feature}</span>
                  </div>
                ))}
              </div>

              {plan.price === '0' ? (
                <Button
                  variant="outline"
                  fullWidth
                  size="md"
                  onClick={onClose}
                >
                  {t('subscription.currentPlan')}
                </Button>
              ) : plan.available ? (
                <PaymentButton
                  planCode={plan.code || plan.name.toLowerCase().replace(/\s+/g, '-')}
                  planName={plan.name}
                  amount={parseFloat(plan.price)}
                  currency="UAH"
                  variant={plan.popular ? 'primary' : 'outline'}
                  size="md"
                  fullWidth
                />
              ) : (
                <Button
                  variant="outline"
                  fullWidth
                  size="md"
                  disabled
                >
                  {t('pricingPage.inDevelopment')}
                </Button>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-center pt-2">
          <Button variant="outline" onClick={onClose}>
            <FaTimes className="mr-2" />
            {t('common.close')}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
