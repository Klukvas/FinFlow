import React, { useState } from 'react';
import { DebtCreate, DebtUpdate, DebtType } from '@/types/debt';
import { ContactResponse } from '@/types/contact';
import { useTheme } from '@/contexts/ThemeContext';
import { 
  Button, 
  Input, 
  Label, 
  MoneyInput,
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue, 
  Textarea, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '@/components/ui';
import { Calendar, DollarSign, User, Building2 } from 'lucide-react';

interface DebtFormProps {
  initialData?: Partial<DebtCreate>;
  contacts: ContactResponse[];
  categories: Array<{ id: number; name: string }>;
  onSubmit: (data: DebtCreate | DebtUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
}

const debtTypes: { value: DebtType; label: string; icon: string }[] = [
  { value: 'CREDIT_CARD', label: 'Credit Card', icon: '💳' },
  { value: 'PERSONAL_LOAN', label: 'Personal Loan', icon: '🏦' },
  { value: 'AUTO_LOAN', label: 'Auto Loan', icon: '🚗' },
  { value: 'STUDENT_LOAN', label: 'Student Loan', icon: '🎓' },
  { value: 'MORTGAGE', label: 'Mortgage', icon: '🏠' },
  { value: 'LOAN', label: 'General Loan', icon: '💰' },
  { value: 'OTHER', label: 'Other', icon: '📋' }
];

export const DebtForm: React.FC<DebtFormProps> = ({
  initialData = {},
  contacts,
  categories,
  onSubmit,
  onCancel,
  isLoading = false,
  mode
}) => {
  const { actualTheme } = useTheme();
  
  // Debug: log contacts data
  console.log('🔧 DebtForm - contacts:', contacts);
  
  const [formData, setFormData] = useState<DebtCreate>({
    name: initialData.name || '',
    description: initialData.description || '',
    debt_type: initialData.debt_type || 'CREDIT_CARD',
    contact_id: initialData.contact_id || null,
    category_id: initialData.category_id || null,
    initial_amount: initialData.initial_amount || 0,
    interest_rate: initialData.interest_rate || null,
    minimum_payment: initialData.minimum_payment || null,
    start_date: initialData.start_date || new Date().toISOString().split('T')[0] || '',
    due_date: initialData.due_date || null
  });

  // Debug: log formData after initialization
  console.log('🔧 DebtForm - formData.contact_id:', formData.contact_id);

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Debt name is required';
    }

    // Category is optional for debts

    if (!formData.initial_amount || formData.initial_amount === 0) {
      newErrors.initial_amount = 'Initial amount cannot be zero';
    }

    if (formData.interest_rate !== null && formData.interest_rate !== undefined && (formData.interest_rate < 0 || formData.interest_rate > 100)) {
      newErrors.interest_rate = 'Interest rate must be between 0 and 100';
    }

    if (formData.minimum_payment !== null && formData.minimum_payment !== undefined && formData.minimum_payment <= 0) {
      newErrors.minimum_payment = 'Minimum payment must be greater than 0';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      // Clean the form data - ensure empty strings become null
      const cleanedFormData = {
        ...formData,
        description: formData.description?.trim() || null,
        interest_rate: formData.interest_rate || null,
        minimum_payment: formData.minimum_payment || null,
        due_date: formData.due_date || null,
      };
      console.log('🔧 DebtForm - Submitting cleaned form data:', cleanedFormData);
      onSubmit(cleanedFormData);
    }
  };

  const handleInputChange = (field: keyof DebtCreate, value: any) => {
    console.log(`🔧 DebtForm - handleInputChange: ${field} = ${value}`);
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const selectedDebtType = debtTypes.find(type => type.value === formData.debt_type);

  return (
    <Card className={`max-w-2xl mx-auto ${
      actualTheme === 'dark' 
        ? 'bg-gray-800 border-gray-700' 
        : 'bg-white border-gray-200'
    }`}>
      <CardHeader>
        <CardTitle className={`flex items-center space-x-2 ${
          actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          <DollarSign className="w-5 h-5" />
          <span>{mode === 'create' ? 'Create New Debt' : 'Edit Debt'}</span>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Debt Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              Debt Name *
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Credit Card - Visa, Car Loan"
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } ${errors.name ? 'border-red-500' : ''}`}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          {/* Debt Type */}
          <div className="space-y-2">
            <Label className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              Debt Type *
            </Label>
            <Select
              value={formData.debt_type}
              onValueChange={(value: string) => handleInputChange('debt_type', value as DebtType)}
            >
              <SelectTrigger className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-900'
              }`}>
                <SelectValue>
                  {selectedDebtType && (
                    <span className="flex items-center space-x-2">
                      <span>{selectedDebtType.icon}</span>
                      <span>{selectedDebtType.label}</span>
                    </span>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className={actualTheme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}>
                {debtTypes.map((type) => (
                  <SelectItem 
                    key={type.value} 
                    value={type.value}
                    className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                  >
                    <span className="flex items-center space-x-2">
                      <span>{type.icon}</span>
                      <span>{type.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              Description
            </Label>
            <Textarea
              id="description"
              value={formData.description || ''}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleInputChange('description', e.target.value)}
              placeholder="Additional details about this debt..."
              rows={3}
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
          </div>

          {/* Amount and Financial Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <MoneyInput
                label="Initial Amount"
                value={formData.initial_amount}
                onChange={(value) => {
                  const numValue = value ? Math.round(parseFloat(value) * 100) / 100 : 0;
                  handleInputChange('initial_amount', numValue);
                }}
                placeholder="0.00 (positive = they owe me, negative = I owe them)"
                required
                error={errors.initial_amount}
                className="w-full"
              />
              <div className={`text-xs ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`}>
                💡 <strong>Tip:</strong> Positive amount = they owe you, Negative amount = you owe them
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="interest_rate" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                Interest Rate (%)
              </Label>
              <Input
                id="interest_rate"
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={formData.interest_rate || ''}
                onChange={(e) => {
                  const value = e.target.value;
                  // Use parseFloat but round to 2 decimal places to avoid precision errors
                  const numValue = value ? Math.round(parseFloat(value) * 100) / 100 : null;
                  handleInputChange('interest_rate', numValue);
                }}
                placeholder="0.00"
                className={`${
                  actualTheme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                } ${errors.interest_rate ? 'border-red-500' : ''}`}
              />
              {errors.interest_rate && (
                <p className="text-sm text-red-500">{errors.interest_rate}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="minimum_payment" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                Minimum Payment
              </Label>
              <div className="relative">
                <DollarSign className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`} />
                <Input
                  id="minimum_payment"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.minimum_payment || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Use parseFloat but round to 2 decimal places to avoid precision errors
                    const numValue = value ? Math.round(parseFloat(value) * 100) / 100 : null;
                    handleInputChange('minimum_payment', numValue);
                  }}
                  placeholder="0.00"
                  className={`pl-10 ${
                    actualTheme === 'dark' 
                      ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  } ${errors.minimum_payment ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.minimum_payment && (
                <p className="text-sm text-red-500">{errors.minimum_payment}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="category_id" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                Category (Optional)
              </Label>
              <Select
                value={formData.category_id?.toString() || ''}
                onValueChange={(value: string) => handleInputChange('category_id', value ? parseInt(value) : null)}
              >
                <SelectTrigger className={`${
                  actualTheme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                }`}>
                  <SelectValue placeholder="Select a category (optional)" />
                </SelectTrigger>
                <SelectContent className={actualTheme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}>
                  <SelectItem 
                    value=""
                    className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                  >
                    No category
                  </SelectItem>
                  {categories.map((category) => (
                    <SelectItem 
                      key={category.id} 
                      value={category.id.toString()}
                      className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                    >
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Dates */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start_date" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                Start Date *
              </Label>
              <div className="relative">
                <Calendar className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`} />
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => handleInputChange('start_date', e.target.value)}
                  className={`pl-10 ${
                    actualTheme === 'dark' 
                      ? 'bg-gray-700 border-gray-600 text-white' 
                      : 'bg-white border-gray-300 text-gray-900'
                  } ${errors.start_date ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.start_date && (
                <p className="text-sm text-red-500">{errors.start_date}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="due_date" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                Due Date
              </Label>
              <div className="relative">
                <Calendar className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`} />
                <Input
                  id="due_date"
                  type="date"
                  value={formData.due_date || ''}
                  onChange={(e) => handleInputChange('due_date', e.target.value || null)}
                  className={`pl-10 ${
                    actualTheme === 'dark' 
                      ? 'bg-gray-700 border-gray-600 text-white' 
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}
                />
              </div>
            </div>
          </div>

          {/* Contact Selection */}
          <div className="space-y-2">
            <Label className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              <User className="w-4 h-4 inline mr-2" />
              Contact Information
            </Label>
            <div className={`p-4 rounded-lg border ${
              actualTheme === 'dark' 
                ? 'bg-gray-700 border-gray-600' 
                : 'bg-gray-50 border-gray-300'
            }`}>
              <p className={`text-sm mb-3 ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Select who this debt involves (optional):
              </p>
              {contacts.length === 0 ? (
                <div className={`p-3 rounded-lg border ${
                  actualTheme === 'dark' 
                    ? 'bg-gray-600 border-gray-500' 
                    : 'bg-yellow-50 border-yellow-200'
                }`}>
                  <p className={`text-sm ${
                    actualTheme === 'dark' ? 'text-gray-300' : 'text-yellow-700'
                  }`}>
                    ⚠️ No contacts available. You can create contacts in the Contacts tab.
                  </p>
                </div>
              ) : (
                <div className="relative">
                  <Select
                    value={formData.contact_id?.toString() || ''}
                    onValueChange={(value: string) => {
                      console.log('🔧 DebtForm - Select onValueChange called with:', value);
                      handleInputChange('contact_id', value ? parseInt(value) : null);
                    }}
                  >
                    <SelectTrigger className={`${
                      actualTheme === 'dark' 
                        ? 'bg-gray-800 border-gray-600 text-white' 
                        : 'bg-white border-gray-300 text-gray-900'
                    }`}>
                      <SelectValue placeholder="Choose contact or leave blank">
                        {formData.contact_id ? (() => {
                          const selectedContact = contacts.find(c => c.id === formData.contact_id);
                          return selectedContact ? (
                            <span className="flex items-center space-x-2">
                              <User className="w-4 h-4" />
                              <span>{selectedContact.name}</span>
                              {selectedContact.company && (
                                <>
                                  <Building2 className="w-4 h-4" />
                                  <span className="text-sm opacity-75">({selectedContact.company})</span>
                                </>
                              )}
                            </span>
                          ) : null;
                        })() : null}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className={actualTheme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}>
                      <SelectItem 
                        value=""
                        className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                      >
                        <span className="flex items-center space-x-2">
                          <span>👤</span>
                          <span>No specific contact</span>
                        </span>
                      </SelectItem>
                      {contacts.map((contact) => (
                          <SelectItem 
                            key={contact.id} 
                            value={contact.id.toString()}
                            className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                          >
                          <span className="flex items-center space-x-2">
                            <User className="w-4 h-4" />
                            <span>{contact.name}</span>
                            {contact.company && (
                              <>
                                <Building2 className="w-4 h-4" />
                                <span className="text-sm opacity-75">({contact.company})</span>
                              </>
                            )}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className={`mt-3 text-xs ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`}>
                💡 <strong>Tip:</strong> 
                <br />• <strong>Positive amount</strong> = They owe you money (💰 incoming)
                <br />• <strong>Negative amount</strong> = You owe them money (💸 outgoing)
                <br />• Use contacts to track specific people or organizations
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-6">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Saving...' : mode === 'create' ? 'Create Debt' : 'Update Debt'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
