import React from 'react';
import { useTranslation } from 'react-i18next';
import { PaymentHistoryList } from '@/components/payment/PaymentHistoryList';
import { FaReceipt } from 'react-icons/fa';
import { SEOHead } from '@/components/seo/SEOHead';

export const PaymentHistory: React.FC = () => {
  const { t } = useTranslation();

  return (
    <>
      <SEOHead
        title={t('payment.historyTitle')}
        description={t('payment.historyDescription')}
      />
      <div className="py-8 px-4 max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
            <FaReceipt className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold theme-text-primary">
              {t('payment.historyTitle')}
            </h1>
            <p className="theme-text-secondary">{t('payment.historyDescription')}</p>
          </div>
        </div>

        <PaymentHistoryList limit={50} />
      </div>
    </>
  );
};

export default PaymentHistory;
