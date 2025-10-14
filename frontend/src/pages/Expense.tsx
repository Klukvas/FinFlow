import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CreateExpense } from '../components/ui/expense/createExpense';
import { ExpenseList } from '../components/ui/expense/expenseList';
import { ExpenseDashboard } from '../components/ui/expense/ExpenseDashboard';
import { Modal } from '../components/ui/shared/Modal';
import { Button } from '../components/ui/shared/Button';
import { Tabs } from '../components/ui/shared/Tabs';
import { FaPlus, FaTable, FaChartBar } from 'react-icons/fa';

export const Expense = () => {
  const { t } = useTranslation();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('table');

  const tabs = [
    {
      id: 'table',
      label: t('expensePage.tabs.table'),
      icon: <FaTable className="w-4 h-4" />
    },
    {
      id: 'dashboard',
      label: t('expensePage.tabs.dashboard'),
      icon: <FaChartBar className="w-4 h-4" />
    }
  ];

  const handleExpenseCreated = () => {
    setRefreshTrigger(prev => prev + 1);
    setIsCreateModalOpen(false);
  };

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Page Header */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-red-600/10 to-orange-600/10 rounded-xl sm:rounded-2xl blur-3xl"></div>
          <div className="relative theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border p-4 sm:p-6 lg:p-8 theme-shadow">
            <div className="flex flex-col gap-4 sm:gap-6">
              <div className="space-y-2 sm:space-y-3">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg sm:rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-4 h-4 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <h1 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold theme-text-primary leading-tight">
                    {t('expensePage.title')}
                  </h1>
                </div>
                <p className="theme-text-secondary text-xs sm:text-sm md:text-base max-w-2xl leading-relaxed">
                  {t('expensePage.subtitle')}
                </p>
              </div>
              
              <div className="flex-shrink-0">
                <Button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="group relative bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-semibold px-4 sm:px-6 py-3 sm:py-3 rounded-lg sm:rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 flex items-center gap-2 sm:gap-3 w-full sm:w-auto justify-center min-h-[44px] sm:min-h-[48px] text-sm sm:text-base"
                >
                  <div className="w-4 h-4 sm:w-5 sm:h-5 group-hover:rotate-90 transition-transform duration-200">
                    <FaPlus className="w-full h-full" />
                  </div>
                  <span>{t('expensePage.addButton')}</span>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border theme-shadow overflow-hidden">
          <Tabs 
            tabs={tabs} 
            activeTab={activeTab} 
            onTabChange={setActiveTab}
            className="px-4 sm:px-6"
          />
        </div>

        {/* Tab Content */}
        {activeTab === 'table' && (
          <div className="theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border theme-shadow overflow-hidden">
            <ExpenseList key={refreshTrigger} />
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="theme-surface backdrop-blur-sm rounded-xl sm:rounded-2xl border theme-border theme-shadow p-4 sm:p-6 lg:p-8">
            <ExpenseDashboard />
          </div>
        )}

        {/* Create Expense Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t('expensePage.createModalTitle')}
          size="lg"
        >
          <CreateExpense onExpenseCreated={handleExpenseCreated} />
        </Modal>
      </div>
    </div>
  );
};