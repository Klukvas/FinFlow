import React from 'react';
import { useTranslation } from 'react-i18next';

interface ConsentCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  planName: string;
  amount: number;
  currency: string;
  nextBillingDate: string;
}

export const ConsentCheckbox: React.FC<ConsentCheckboxProps> = ({
  checked,
  onChange,
  planName,
  amount,
  currency,
  nextBillingDate,
}) => {
  const { t, i18n } = useTranslation();
  
  // Calculate day of month for billing
  const billingDay = new Date(nextBillingDate).getDate();
  const today = new Date().toISOString().split('T')[0];
  
  return (
    <div className="space-y-3 p-4 rounded-lg border theme-border theme-bg-secondary">
      <label className="flex items-start gap-3 cursor-pointer group">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="mt-1 w-5 h-5 rounded border-gray-300 theme-accent-border text-blue-600 focus:ring-blue-500 focus:ring-2 cursor-pointer"
          aria-label={t('subscription.consent.ariaLabel', 'Agree to subscription terms')}
        />
        <div className="flex-1 text-sm">
          <p className="font-semibold mb-3 theme-text-primary">
            {t('subscription.consent.title', {
              planName,
              defaultValue: `I agree to subscribe to ${planName} plan`,
            })}
          </p>
          
          <p className="mb-2 theme-text-secondary text-xs">
            {t('subscription.consent.intro', 'By subscribing, I confirm that:')}
          </p>
          
          <ul className="space-y-2 theme-text-secondary text-xs">
            <li className="flex items-start gap-2">
              <span className="theme-text-primary mt-0.5">•</span>
              <span>
                {t(
                  'subscription.consent.tokenization',
                  'My payment card details will be securely tokenized and stored by WayForPay payment processor'
                )}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-text-primary mt-0.5">•</span>
              <span>
                {t('subscription.consent.recurring', {
                  amount,
                  currency,
                  defaultValue: `I authorize automatic monthly charges of ${amount} ${currency} to my payment card`,
                })}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-text-primary mt-0.5">•</span>
              <span>
                {t('subscription.consent.billingDate', {
                  day: billingDay,
                  startDate: today,
                  defaultValue: `Charges will occur on the ${billingDay}${getOrdinalSuffix(billingDay)} of each month starting from ${today}`,
                })}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-text-primary mt-0.5">•</span>
              <span>
                {t(
                  'subscription.consent.cancellation',
                  'I can cancel my subscription at any time from my account settings'
                )}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-text-primary mt-0.5">•</span>
              <span>
                {t(
                  'subscription.consent.noFutureCharges',
                  'Upon cancellation, no future charges will be made'
                )}
              </span>
            </li>
          </ul>
        </div>
      </label>
      
      {!checked && (
        <div className="pl-8 text-xs theme-warning flex items-start gap-2">
          <span className="mt-0.5">⚠️</span>
          <span>
            {t(
              'subscription.consent.required',
              'You must accept the terms to proceed with subscription'
            )}
          </span>
        </div>
      )}
    </div>
  );
};

function getOrdinalSuffix(day: number): string {
  if (day > 3 && day < 21) return 'th';
  switch (day % 10) {
    case 1: return 'st';
    case 2: return 'nd';
    case 3: return 'rd';
    default: return 'th';
  }
}
