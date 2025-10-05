import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CreateIncome } from '../components/ui/income/CreateIncome';
import { Modal } from '../components/ui/Modal';
import { Button } from '../components/ui/Button';
import { FaPlus } from 'react-icons/fa';
import { IncomeList } from '@/components';

export const Income = () => {
  const { t } = useTranslation();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const handleIncomeCreated = () => {
    setRefreshTrigger(prev => prev + 1);
    setIsCreateModalOpen(false);
  };

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Page Header */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-green-600/10 to-emerald-600/10 rounded-xl sm:rounded-2xl blur-3xl"></div>
          <div className="relative theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border p-4 sm:p-6 lg:p-8 theme-shadow">
            <div className="flex flex-col gap-4 sm:gap-6">
              <div className="space-y-2 sm:space-y-3">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg sm:rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-4 h-4 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <h1 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold theme-text-primary leading-tight">
                    {t('incomePage.title')}
                  </h1>
                </div>
                <p className="theme-text-secondary text-xs sm:text-sm md:text-base max-w-2xl leading-relaxed">
                  {t('incomePage.subtitle')}
                </p>
              </div>
              
              <div className="flex-shrink-0">
                <Button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="group relative bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold px-4 sm:px-6 py-3 sm:py-3 rounded-lg sm:rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 flex items-center gap-2 sm:gap-3 w-full sm:w-auto justify-center min-h-[44px] sm:min-h-[48px] text-sm sm:text-base"
                >
                  <div className="w-4 h-4 sm:w-5 sm:h-5 group-hover:rotate-90 transition-transform duration-200">
                    <FaPlus className="w-full h-full" />
                  </div>
                  <span>{t('incomePage.addButton')}</span>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Incomes List */}
        <div className="theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border theme-shadow overflow-hidden">
          <IncomeList key={refreshTrigger} />
        </div>

        {/* Create Income Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t('incomePage.createModalTitle')}
          size="lg"
        >
          <CreateIncome onIncomeCreated={handleIncomeCreated} />
        </Modal>
      </div>
    </div>
  );
};
