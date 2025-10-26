import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useApiClients } from '@/hooks/useApiClients';
import { useTheme } from '@/contexts/ThemeContext';
import { DebtResponse, DebtCreate, DebtUpdate, DebtSummary } from '@/types/debt';
import { ContactResponse, ContactCreate, ContactUpdate } from '@/types/contact';
import { Category } from '@/types/category';
import { DebtForm } from '@/components/debt/DebtForm';
import { PaymentForm } from '@/components/debt/PaymentForm';
import { PaymentList } from '@/components/debt/PaymentList';
import { DebtStats } from '@/components/debt/DebtStats';
import { DebtTabs } from '@/components/debt/DebtTabs';
import { DebtsList } from '@/components/debt/DebtsList';
import { ContactsList } from '@/components/debt/ContactsList';
import { ContactForm } from '@/components/contact/ContactForm';
import { Button } from '@/components/ui/shared/Button';
import { Modal } from '@/components/ui/shared/Modal';
import { toast } from 'sonner';
import { Plus } from 'lucide-react';

type ViewMode = 'list' | 'create' | 'edit' | 'payments' | 'payment-form' | 'contacts' | 'create-contact' | 'edit-contact';
type TabType = 'debts' | 'contacts';

export const Debts: React.FC = () => {
  const { debt, contact, category } = useApiClients();
  const { actualTheme } = useTheme();
  const { t } = useTranslation();
  
  const [debts, setDebts] = useState<DebtResponse[]>([]);
  const [contacts, setContacts] = useState<ContactResponse[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [summary, setSummary] = useState<DebtSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [activeTab, setActiveTab] = useState<TabType>('debts');
  const [selectedDebt, setSelectedDebt] = useState<DebtResponse | null>(null);
  const [selectedContact, setSelectedContact] = useState<ContactResponse | null>(null);
  const [showDebtModal, setShowDebtModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [debtsResult, contactsResult, categoriesResult, summaryResult] = await Promise.all([
        debt.getDebts(),
        contact.getContacts(),
        category.getCategories(),
        debt.getDebtSummary()
      ]);

      if (!('error' in debtsResult)) {
        setDebts(debtsResult);
      }
      if (!('error' in contactsResult)) {
        setContacts(contactsResult);
      } else {
        console.error('Error loading contacts:', contactsResult);
      }
      if (!('error' in categoriesResult)) {
        setCategories(categoriesResult);
      }
      if (!('error' in summaryResult)) {
        setSummary(summaryResult);
      }
    } catch (error) {
      console.error('Error loading debts data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDebt = (debtData: DebtCreate | DebtUpdate) => {
    (async () => {
      try {
        const result = await debt.createDebt(debtData as DebtCreate);
        if (!('error' in result)) {
          setDebts(prev => [...prev, result]);
          setShowDebtModal(false);
          loadData(); // Refresh summary
          toast.success(t('debtPage.messages.debtCreated'));
        } else {
          console.error('Error creating debt:', result.error);
          toast.error('Failed to create debt. Please try again.');
        }
      } catch (error) {
        console.error('Error creating debt:', error);
        toast.error('Failed to create debt. Please try again.');
      }
    })();
  };

  const handleUpdateDebt = (debtData: DebtCreate | DebtUpdate) => {
    if (!selectedDebt) return;
    
    (async () => {
      try {
        const result = await debt.updateDebt(selectedDebt.id, debtData as DebtUpdate);
        if (!('error' in result)) {
          setDebts(prev => prev.map(d => d.id === selectedDebt.id ? result : d));
          setViewMode('list');
          setSelectedDebt(null);
          loadData(); // Refresh summary
          toast.success(t('debtPage.messages.debtUpdated'));
        } else {
          console.error('Error updating debt:', result.error);
          toast.error('Failed to update debt. Please try again.');
        }
      } catch (error) {
        console.error('Error updating debt:', error);
        toast.error('Failed to update debt. Please try again.');
      }
    })();
  };

  const handleMakePayment = async (paymentData: any) => {
    if (!selectedDebt) return;
    
    try {
      const result = await debt.createPayment(selectedDebt.id, paymentData);
      if (!('error' in result)) {
        // Refresh the debt to get updated balance
        const updatedDebtResult = await debt.getDebt(selectedDebt.id);
        if (!('error' in updatedDebtResult)) {
          setDebts(prev => prev.map(d => d.id === selectedDebt.id ? updatedDebtResult : d));
          setSelectedDebt(updatedDebtResult);
        }
        loadData(); // Refresh summary
                  toast.success(t('debtPage.messages.paymentMade'));
        } else {
          console.error('Error making payment:', result.error);
          toast.error('Failed to make payment. Please try again.');
        }
      } catch (error) {
        console.error('Error making payment:', error);
        toast.error('Failed to make payment. Please try again.');
    }
  };

  const handleDeleteDebt = async (debtId: number) => {
    if (!window.confirm(t('debtPage.deleteConfirm'))) {
      return;
    }
    
    try {
      const result = await debt.deleteDebt(debtId);
      if (typeof result === 'boolean' && result === true) {
        // Remove the debt from the list
        setDebts(prev => prev.filter(d => d.id !== debtId));
        // If we're viewing this debt, clear the selection
        if (selectedDebt && selectedDebt.id === debtId) {
          setSelectedDebt(null);
          setViewMode('list');
        }
        // Refresh the debt summary
        loadData();
        // Show success toast
                  toast.success(t('debtPage.messages.debtDeleted'));
        } else {
          const errorMsg = typeof result === 'object' && 'error' in result ? result.error : 'Unknown error';
          console.error('Error deleting debt:', errorMsg);
          toast.error('Failed to delete debt. Please try again.');
        }
      } catch (error) {
        console.error('Error deleting debt:', error);
        toast.error('Failed to delete debt. Please try again.');
    }
  };

  const handleCreateContact = (contactData: ContactCreate | ContactUpdate) => {
    (async () => {
      try {
        const result = await contact.createContact(contactData as ContactCreate);
        if (!('error' in result)) {
          setContacts(prev => [...prev, result]);
          setShowContactModal(false);
          toast.success(t('debtPage.messages.contactCreated'));
        } else {
          console.error('Error creating contact:', result.error);
          toast.error('Failed to create contact. Please try again.');
        }
      } catch (error) {
        console.error('Error creating contact:', error);
        toast.error('Failed to create contact. Please try again.');
      }
    })();
  };

  const handleUpdateContact = (contactData: ContactCreate | ContactUpdate) => {
    if (!selectedContact) return;
    
    (async () => {
      try {
        const result = await contact.updateContact(selectedContact.id, contactData as ContactUpdate);
        if (!('error' in result)) {
          setContacts(prev => prev.map(c => c.id === selectedContact.id ? result : c));
          setViewMode('contacts');
          setSelectedContact(null);
          toast.success(t('debtPage.messages.contactUpdated'));
        } else {
          console.error('Error updating contact:', result.error);
          toast.error('Failed to update contact. Please try again.');
        }
      } catch (error) {
        console.error('Error updating contact:', error);
        toast.error('Failed to update contact. Please try again.');
      }
    })();
  };

  const filteredDebts = debts;
  const filteredContacts = contacts;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className={`h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/4`} />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className={`h-32 bg-gray-300 dark:bg-gray-600 rounded`} />
              ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className={`h-64 bg-gray-300 dark:bg-gray-600 rounded`} />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }


  if (viewMode === 'edit' && selectedDebt) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Button
              variant="secondary"
              onClick={() => setViewMode(activeTab === 'debts' ? 'list' : 'contacts')}
              className="mb-4"
            >
              {t('debtPage.backTo')} {activeTab === 'debts' ? t('debtPage.tabs.debts') : t('debtPage.tabs.contacts')}
            </Button>
            <DebtForm
              initialData={selectedDebt}
              contacts={contacts}
              categories={categories}
              onSubmit={handleUpdateDebt}
              onCancel={() => setViewMode(activeTab === 'debts' ? 'list' : 'contacts')}
              mode="edit"
            />
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'edit-contact' && selectedContact) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Button
              variant="secondary"
              onClick={() => setViewMode('contacts')}
              className="mb-4"
            >
              {t('debtPage.backTo')} {t('debtPage.tabs.contacts')}
            </Button>
            <ContactForm
              initialData={selectedContact}
              onSubmit={handleUpdateContact}
              onCancel={() => setViewMode('contacts')}
              mode="edit"
            />
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'payment-form' && selectedDebt) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Button
              variant="secondary"
              onClick={() => setViewMode('list')}
              className="mb-4"
            >
              {t('debtPage.backTo')} {t('debtPage.tabs.debts')}
            </Button>
            <PaymentForm
              debtId={selectedDebt.id}
              currentBalance={selectedDebt.current_balance}
              onSubmit={handleMakePayment}
              onCancel={() => setViewMode('list')}
            />
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'payments' && selectedDebt) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <Button
              variant="secondary"
              onClick={() => setViewMode('list')}
              className="mb-4"
            >
              {t('debtPage.backTo')} {t('debtPage.tabs.debts')}
            </Button>
            <h1 className={`text-3xl font-bold mb-6 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {t('debtPage.paymentHistory')} - {selectedDebt.name}
            </h1>
            <PaymentList
              payments={[]} // TODO: Load payments for this debt
              isLoading={false}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
          <div>
            <h1 className={`text-3xl font-bold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {t('debtPage.title')}
            </h1>
            <p className={`mt-2 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
            }`}>
              {t('debtPage.subtitle')}
            </p>
          </div>
          <Button
            onClick={() => activeTab === 'debts' ? setShowDebtModal(true) : setShowContactModal(true)}
            className="mt-4 sm:mt-0"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('debtPage.addButton')} {activeTab === 'debts' ? t('debtPage.tabs.debts') : t('debtPage.tabs.contacts')}
          </Button>
        </div>

        {/* Tabs */}
        <DebtTabs
          activeTab={activeTab}
          onTabChange={(tab) => {
            setActiveTab(tab);
            setViewMode(tab === 'debts' ? 'list' : 'contacts');
          }}
          actualTheme={actualTheme}
        />

        {/* Summary Cards */}
        {activeTab === 'debts' && summary && (
          <DebtStats summary={summary} actualTheme={actualTheme} />
        )}

        {/* Content based on active tab */}
        {activeTab === 'debts' ? (
          <DebtsList
            debts={filteredDebts}
            onEdit={(debt) => {
              setSelectedDebt(debt);
              setViewMode('edit');
            }}
            onViewPayments={(debtId) => {
              const debt = debts.find(d => d.id === debtId);
              if (debt) {
                setSelectedDebt(debt);
                setViewMode('payments');
              }
            }}
            onMakePayment={(debtId) => {
              const debt = debts.find(d => d.id === debtId);
              if (debt) {
                setSelectedDebt(debt);
                setViewMode('payment-form');
              }
            }}
            onDelete={handleDeleteDebt}
            onCreateClick={() => setShowDebtModal(true)}
            actualTheme={actualTheme}
          />
        ) : (
          <ContactsList
            contacts={filteredContacts}
            onEdit={(contact) => {
              setSelectedContact(contact);
              setViewMode('edit-contact');
            }}
            onCreateClick={() => setShowContactModal(true)}
            actualTheme={actualTheme}
          />
        )}

        {/* Debt Create Modal */}
        <Modal
          isOpen={showDebtModal}
          onClose={() => setShowDebtModal(false)}
          title={t('debtPage.form.title')}
          size="xl"
        >
          <DebtForm
            contacts={contacts}
            categories={categories}
            onSubmit={handleCreateDebt}
            onCancel={() => setShowDebtModal(false)}
            mode="create"
            showCard={false}
          />
        </Modal>

        {/* Contact Create Modal */}
        <Modal
          isOpen={showContactModal}
          onClose={() => setShowContactModal(false)}
          title={t('debtPage.contacts.form.createTitle')}
          size="xl"
        >
          <ContactForm
            onSubmit={handleCreateContact}
            onCancel={() => setShowContactModal(false)}
            mode="create"
            showCard={false}
          />
        </Modal>
      </div>
    </div>
  );
};
