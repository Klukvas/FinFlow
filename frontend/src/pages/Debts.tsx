import React, { useState, useEffect } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { useTheme } from '@/contexts/ThemeContext';
import { DebtResponse, DebtCreate, DebtUpdate, DebtSummary } from '@/types/debt';
import { ContactResponse, ContactCreate, ContactUpdate } from '@/types/contact';
import { Category } from '@/types/category';
import { DebtCard } from '@/components/debt/DebtCard';
import { DebtForm } from '@/components/debt/DebtForm';
import { PaymentForm } from '@/components/debt/PaymentForm';
import { PaymentList } from '@/components/debt/PaymentList';
import { ContactCard } from '@/components/contact/ContactCard';
import { ContactForm } from '@/components/contact/ContactForm';
import { Button } from '@/components/ui/shared/Button';
import { Input } from '@/components/ui/forms/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui';
import { Card, CardContent } from '@/components/ui';
import { toast } from 'sonner';
import { 
  Plus, 
  Search, 
  DollarSign, 
  TrendingDown, 
  CreditCard,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
  Users,
  UserPlus
} from 'lucide-react';

type ViewMode = 'list' | 'create' | 'edit' | 'payments' | 'payment-form' | 'contacts' | 'create-contact' | 'edit-contact';
type TabType = 'debts' | 'contacts';

export const Debts: React.FC = () => {
  const { debt, contact, category } = useApiClients();
  const { actualTheme } = useTheme();
  
  const [debts, setDebts] = useState<DebtResponse[]>([]);
  const [contacts, setContacts] = useState<ContactResponse[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [summary, setSummary] = useState<DebtSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [activeTab, setActiveTab] = useState<TabType>('debts');
  const [selectedDebt, setSelectedDebt] = useState<DebtResponse | null>(null);
  const [selectedContact, setSelectedContact] = useState<ContactResponse | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [showSummary, setShowSummary] = useState(true);

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
          setViewMode('list');
          loadData(); // Refresh summary
          toast.success('Debt created successfully');
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
          toast.success('Debt updated successfully');
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
        toast.success('Payment made successfully');
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
    if (!window.confirm('Are you sure you want to delete this debt? This action cannot be undone.')) {
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
        toast.success('Debt deleted successfully');
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
          setViewMode('contacts');
          toast.success('Contact created successfully');
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
          toast.success('Contact updated successfully');
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

  const filteredDebts = debts.filter(debt => {
    const matchesSearch = debt.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         debt.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || debt.debt_type === filterType;
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'active' && debt.is_active) ||
                         (filterStatus === 'paid-off' && debt.is_paid_off) ||
                         (filterStatus === 'inactive' && !debt.is_active);
    
    return matchesSearch && matchesType && matchesStatus;
  });

  const filteredContacts = contacts.filter(contact => {
    const matchesSearch = contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         contact.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         contact.email?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch;
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

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

  if (viewMode === 'create') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Button
              variant="secondary"
              onClick={() => setViewMode(activeTab === 'debts' ? 'list' : 'contacts')}
              className="mb-4"
            >
              ← Back to {activeTab === 'debts' ? 'Debts' : 'Contacts'}
            </Button>
            <DebtForm
              contacts={contacts}
              categories={categories}
              onSubmit={handleCreateDebt}
              onCancel={() => setViewMode(activeTab === 'debts' ? 'list' : 'contacts')}
              mode="create"
            />
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'create-contact') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Button
              variant="secondary"
              onClick={() => setViewMode('contacts')}
              className="mb-4"
            >
              ← Back to Contacts
            </Button>
            <ContactForm
              onSubmit={handleCreateContact}
              onCancel={() => setViewMode('contacts')}
              mode="create"
            />
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
              ← Back to {activeTab === 'debts' ? 'Debts' : 'Contacts'}
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
              ← Back to Contacts
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
              ← Back to Debts
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
              ← Back to Debts
            </Button>
            <h1 className={`text-3xl font-bold mb-6 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Payment History - {selectedDebt.name}
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
              Debt Management
            </h1>
            <p className={`mt-2 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Track and manage your debts and payments
            </p>
          </div>
          <Button
            onClick={() => setViewMode(activeTab === 'debts' ? 'create' : 'create-contact')}
            className="mt-4 sm:mt-0"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add {activeTab === 'debts' ? 'Debt' : 'Contact'}
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8">
          <button
            onClick={() => {
              setActiveTab('debts');
              setViewMode('list');
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'debts'
                ? actualTheme === 'dark'
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-500 text-white'
                : actualTheme === 'dark'
                ? 'text-gray-400 hover:text-white hover:bg-gray-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <CreditCard className="w-4 h-4 inline mr-2" />
            Debts
          </button>
          <button
            onClick={() => {
              setActiveTab('contacts');
              setViewMode('contacts');
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'contacts'
                ? actualTheme === 'dark'
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-500 text-white'
                : actualTheme === 'dark'
                ? 'text-gray-400 hover:text-white hover:bg-gray-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Users className="w-4 h-4 inline mr-2" />
            Contacts
          </button>
        </div>

        {/* Summary Cards */}
        {activeTab === 'debts' && summary && showSummary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className={`${
              actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${
                      actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      Total Debt
                    </p>
                    <p className={`text-2xl font-bold ${
                      actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      {formatCurrency(summary.total_debt)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${
                    actualTheme === 'dark' ? 'bg-red-900/50' : 'bg-red-100'
                  }`}>
                    <TrendingDown className="w-6 h-6 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className={`${
              actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${
                      actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      Total Paid
                    </p>
                    <p className={`text-2xl font-bold ${
                      actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      {formatCurrency(summary.total_payments)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${
                    actualTheme === 'dark' ? 'bg-green-900/50' : 'bg-green-100'
                  }`}>
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className={`${
              actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${
                      actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      Active Debts
                    </p>
                    <p className={`text-2xl font-bold ${
                      actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      {summary.active_debts}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${
                    actualTheme === 'dark' ? 'bg-blue-900/50' : 'bg-blue-100'
                  }`}>
                    <CreditCard className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className={`${
              actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${
                      actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      Paid Off
                    </p>
                    <p className={`text-2xl font-bold ${
                      actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      {summary.paid_off_debts}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${
                    actualTheme === 'dark' ? 'bg-green-900/50' : 'bg-green-100'
                  }`}>
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          <div className="flex-1">
            <div className="relative">
              <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <Input
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`pl-10 ${
                  actualTheme === 'dark' 
                    ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
          </div>
          
          {activeTab === 'debts' && (
            <div className="flex gap-2">
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className={`w-32 ${
                  actualTheme === 'dark' 
                    ? 'bg-gray-800 border-gray-700 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                }`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className={actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-300'}>
                  <SelectItem value="all" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>All Types</SelectItem>
                  <SelectItem value="CREDIT_CARD" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Credit Card</SelectItem>
                  <SelectItem value="LOAN" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Loan</SelectItem>
                  <SelectItem value="MORTGAGE" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Mortgage</SelectItem>
                  <SelectItem value="OTHER" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Other</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className={`w-32 ${
                  actualTheme === 'dark' 
                    ? 'bg-gray-800 border-gray-700 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                }`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className={actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-300'}>
                  <SelectItem value="all" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>All Status</SelectItem>
                  <SelectItem value="active" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Active</SelectItem>
                  <SelectItem value="paid-off" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Paid Off</SelectItem>
                  <SelectItem value="inactive" className={actualTheme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-gray-900 hover:bg-gray-100'}>Inactive</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSummary(!showSummary)}
                className="px-3"
              >
                {showSummary ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
          )}
        </div>

        {/* Content based on active tab */}
        {activeTab === 'debts' ? (
          /* Debt Cards */
          filteredDebts.length === 0 ? (
            <Card className={`${
              actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <CardContent className="p-12 text-center">
                <AlertCircle className={`w-12 h-12 mx-auto mb-4 ${
                  actualTheme === 'dark' ? 'text-gray-600' : 'text-gray-400'
                }`} />
                <h3 className={`text-lg font-medium mb-2 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  No Debts Found
                </h3>
                <p className={`mb-6 ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {searchTerm || filterType !== 'all' || filterStatus !== 'all'
                    ? 'Try adjusting your search or filters.'
                    : 'Get started by adding your first debt.'}
                </p>
                <Button onClick={() => setViewMode('create')}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Your First Debt
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredDebts.map((debt) => (
                <DebtCard
                  key={debt.id}
                  debt={debt}
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
                />
              ))}
            </div>
          )
        ) : (
          /* Contact Cards */
          filteredContacts.length === 0 ? (
            <Card className={`${
              actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <CardContent className="p-12 text-center">
                <Users className={`w-12 h-12 mx-auto mb-4 ${
                  actualTheme === 'dark' ? 'text-gray-600' : 'text-gray-400'
                }`} />
                <h3 className={`text-lg font-medium mb-2 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  No Contacts Found
                </h3>
                <p className={`mb-6 ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {searchTerm
                    ? 'Try adjusting your search.'
                    : 'Get started by adding your first contact.'}
                </p>
                <Button onClick={() => setViewMode('create-contact')}>
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add Your First Contact
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredContacts.map((contact) => (
                <ContactCard
                  key={contact.id}
                  contact={contact}
                  onEdit={(contact) => {
                    setSelectedContact(contact);
                    setViewMode('edit-contact');
                  }}
                />
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
};
