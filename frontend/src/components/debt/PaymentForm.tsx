import React, { useState } from 'react';
import { DebtPaymentCreate, PaymentMethod } from '@/types/debt';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/forms/Input';
import { Label } from '@/components/ui/Label';
import { MoneyInput } from '@/components/ui/MoneyInput';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Calendar, DollarSign, CreditCard, Wallet, Banknote } from 'lucide-react';

interface PaymentFormProps {
  debtId: number;
  currentBalance: number;
  onSubmit: (payment: DebtPaymentCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const paymentMethods: { value: PaymentMethod; label: string; icon: React.ReactNode }[] = [
  { value: 'CASH', label: 'Cash', icon: <Banknote className="w-4 h-4" /> },
  { value: 'CARD', label: 'Credit/Debit Card', icon: <CreditCard className="w-4 h-4" /> },
  { value: 'TRANSFER', label: 'Bank Transfer', icon: <Wallet className="w-4 h-4" /> },
  { value: 'CHECK', label: 'Check', icon: <DollarSign className="w-4 h-4" /> },
  { value: 'AUTOMATIC', label: 'Automatic Payment', icon: <CreditCard className="w-4 h-4" /> },
  { value: 'OTHER', label: 'Other', icon: <DollarSign className="w-4 h-4" /> }
];

export const PaymentForm: React.FC<PaymentFormProps> = ({
  debtId,
  currentBalance,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const { actualTheme } = useTheme();
  
  const [formData, setFormData] = useState<DebtPaymentCreate>({
    amount: 0,
    principal_amount: null,
    interest_amount: null,
    payment_date: new Date().toISOString().split('T')[0],
    description: '',
    payment_method: null
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.amount || formData.amount <= 0) {
      newErrors.amount = 'Payment amount must be greater than 0';
    }

    if (formData.amount > currentBalance) {
      newErrors.amount = 'Payment amount cannot exceed current balance';
    }

    if (formData.principal_amount !== null && formData.principal_amount < 0) {
      newErrors.principal_amount = 'Principal amount cannot be negative';
    }

    if (formData.interest_amount !== null && formData.interest_amount < 0) {
      newErrors.interest_amount = 'Interest amount cannot be negative';
    }

    if (formData.principal_amount !== null && formData.interest_amount !== null) {
      const total = formData.principal_amount + formData.interest_amount;
      if (Math.abs(total - formData.amount) > 0.01) {
        newErrors.interest_amount = 'Principal + Interest must equal total payment amount';
      }
    }

    if (!formData.payment_date) {
      newErrors.payment_date = 'Payment date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field: keyof DebtPaymentCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const calculateRemainingBalance = () => {
    return currentBalance - formData.amount;
  };

  return (
    <Card className={`max-w-lg mx-auto ${
      actualTheme === 'dark' 
        ? 'bg-gray-800 border-gray-700' 
        : 'bg-white border-gray-200'
    }`}>
      <CardHeader>
        <CardTitle className={`flex items-center space-x-2 ${
          actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          <DollarSign className="w-5 h-5" />
          <span>Make Payment</span>
        </CardTitle>
      </CardHeader>

      <CardContent>
        {/* Current Balance Info */}
        <div className={`p-4 rounded-lg mb-6 ${
          actualTheme === 'dark' ? 'bg-gray-700/50' : 'bg-blue-50'
        }`}>
          <div className="flex justify-between items-center">
            <span className={`text-sm font-medium ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              Current Balance
            </span>
            <span className={`text-lg font-bold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {formatCurrency(currentBalance)}
            </span>
          </div>
          {formData.amount > 0 && (
            <div className="flex justify-between items-center mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                After Payment
              </span>
              <span className={`text-lg font-bold ${
                actualTheme === 'dark' ? 'text-green-400' : 'text-green-600'
              }`}>
                {formatCurrency(calculateRemainingBalance())}
              </span>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Payment Amount */}
          <MoneyInput
            label="Payment Amount"
            value={formData.amount}
            onChange={(value) => handleInputChange('amount', parseFloat(value) || 0)}
            placeholder="0.00"
            required
            error={errors.amount}
            className="w-full"
          />

          {/* Payment Date */}
          <div className="space-y-2">
            <Label htmlFor="payment_date" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              Payment Date *
            </Label>
            <div className="relative">
              <Calendar className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <Input
                id="payment_date"
                type="date"
                value={formData.payment_date}
                onChange={(e) => handleInputChange('payment_date', e.target.value)}
                className={`pl-10 ${
                  actualTheme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                } ${errors.payment_date ? 'border-red-500' : ''}`}
              />
            </div>
            {errors.payment_date && (
              <p className="text-sm text-red-500">{errors.payment_date}</p>
            )}
          </div>

          {/* Payment Method */}
          <div className="space-y-2">
            <Label className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              Payment Method
            </Label>
            <Select
              value={formData.payment_method || ''}
              onValueChange={(value) => handleInputChange('payment_method', value || null)}
            >
              <SelectTrigger className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-900'
              }`}>
                <SelectValue placeholder="Select payment method (optional)" />
              </SelectTrigger>
              <SelectContent className={actualTheme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}>
                <SelectItem 
                  value=""
                  className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                >
                  No method specified
                </SelectItem>
                {paymentMethods.map((method) => (
                  <SelectItem 
                    key={method.value} 
                    value={method.value}
                    className={actualTheme === 'dark' ? 'text-white hover:bg-gray-600' : 'text-gray-900 hover:bg-gray-100'}
                  >
                    <span className="flex items-center space-x-2">
                      {method.icon}
                      <span>{method.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Breakdown (Optional) */}
          <div className="space-y-4">
            <div className={`p-3 rounded-lg ${
              actualTheme === 'dark' ? 'bg-gray-700/30' : 'bg-gray-50'
            }`}>
              <Label className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Payment Breakdown (Optional)
              </Label>
              <p className={`text-xs mt-1 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`}>
                Specify how much goes to principal vs interest
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <MoneyInput
                label="Principal Amount"
                value={formData.principal_amount || ''}
                onChange={(value) => handleInputChange('principal_amount', value ? parseFloat(value) : null)}
                placeholder="0.00"
                error={errors.principal_amount}
                className="w-full"
              />

              <MoneyInput
                label="Interest Amount"
                value={formData.interest_amount || ''}
                onChange={(value) => handleInputChange('interest_amount', value ? parseFloat(value) : null)}
                placeholder="0.00"
                error={errors.interest_amount}
                className="w-full"
              />
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              Description
            </Label>
            <Textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Payment notes or reference..."
              rows={3}
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-6">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Processing...' : 'Record Payment'}
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
