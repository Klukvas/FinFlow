import React from 'react';
import { DebtPaymentResponse, PaymentMethod } from '@/types/debt';
import { useTheme } from '@/contexts/ThemeContext';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { 
  DollarSign, 
  Calendar, 
  CreditCard, 
  Banknote, 
  Wallet, 
  CheckCircle,
  TrendingDown,
  TrendingUp
} from 'lucide-react';

interface PaymentListProps {
  payments: DebtPaymentResponse[];
  isLoading?: boolean;
}

const getPaymentMethodIcon = (method: PaymentMethod) => {
  switch (method) {
    case 'CASH':
      return <Banknote className="w-4 h-4" />;
    case 'CARD':
      return <CreditCard className="w-4 h-4" />;
    case 'TRANSFER':
      return <Wallet className="w-4 h-4" />;
    case 'CHECK':
      return <DollarSign className="w-4 h-4" />;
    case 'AUTOMATIC':
      return <CheckCircle className="w-4 h-4" />;
    default:
      return <DollarSign className="w-4 h-4" />;
  }
};

const getPaymentMethodLabel = (method: PaymentMethod) => {
  switch (method) {
    case 'CASH':
      return 'Cash';
    case 'CARD':
      return 'Card';
    case 'TRANSFER':
      return 'Transfer';
    case 'CHECK':
      return 'Check';
    case 'AUTOMATIC':
      return 'Automatic';
    default:
      return 'Other';
  }
};

export const PaymentList: React.FC<PaymentListProps> = ({
  payments,
  isLoading = false
}) => {
  const { actualTheme } = useTheme();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTotalPayments = () => {
    return payments.reduce((total, payment) => total + payment.amount, 0);
  };

  const getTotalPrincipal = () => {
    return payments.reduce((total, payment) => total + (payment.principal_amount || 0), 0);
  };

  const getTotalInterest = () => {
    return payments.reduce((total, payment) => total + (payment.interest_amount || 0), 0);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, index) => (
          <Card key={index} className={`animate-pulse ${
            actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
          }`}>
            <CardContent className="p-6">
              <div className="space-y-3">
                <div className={`h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/4`} />
                <div className={`h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2`} />
                <div className={`h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/3`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-8 text-center">
          <DollarSign className={`w-12 h-12 mx-auto mb-4 ${
            actualTheme === 'dark' ? 'text-gray-600' : 'text-gray-400'
          }`} />
          <h3 className={`text-lg font-medium mb-2 ${
            actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            No Payments Yet
          </h3>
          <p className={`${
            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Payments made towards this debt will appear here.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className={`${
          actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingDown className="w-5 h-5 text-green-500" />
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Total Payments
              </span>
            </div>
            <p className={`text-2xl font-bold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {formatCurrency(getTotalPayments())}
            </p>
            <p className={`text-xs mt-1 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {payments.length} payment{payments.length !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>

        <Card className={`${
          actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="w-5 h-5 text-blue-500" />
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Principal Paid
              </span>
            </div>
            <p className={`text-2xl font-bold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {formatCurrency(getTotalPrincipal())}
            </p>
            <p className={`text-xs mt-1 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {((getTotalPrincipal() / getTotalPayments()) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>

        <Card className={`${
          actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingUp className="w-5 h-5 text-red-500" />
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Interest Paid
              </span>
            </div>
            <p className={`text-2xl font-bold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {formatCurrency(getTotalInterest())}
            </p>
            <p className={`text-xs mt-1 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {((getTotalInterest() / getTotalPayments()) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Payment List */}
      <div className="space-y-3">
        <h3 className={`text-lg font-semibold ${
          actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          Payment History
        </h3>
        
        {payments.map((payment) => (
          <Card key={payment.id} className={`transition-all duration-200 hover:shadow-md ${
            actualTheme === 'dark' 
              ? 'bg-gray-800 border-gray-700 hover:border-gray-600' 
              : 'bg-white border-gray-200 hover:border-gray-300'
          }`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`p-2 rounded-lg ${
                      actualTheme === 'dark' ? 'bg-green-900/50' : 'bg-green-100'
                    }`}>
                      <DollarSign className="w-4 h-4 text-green-600" />
                    </div>
                    <div>
                      <h4 className={`font-semibold ${
                        actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>
                        {formatCurrency(payment.amount)}
                      </h4>
                      <div className="flex items-center space-x-2">
                        <Calendar className={`w-3 h-3 ${
                          actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                        }`} />
                        <span className={`text-sm ${
                          actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          {formatDate(payment.payment_date)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Payment Breakdown */}
                  {(payment.principal_amount || payment.interest_amount) && (
                    <div className="flex space-x-4 mb-2">
                      {payment.principal_amount && (
                        <div className="flex items-center space-x-1">
                          <div className={`w-2 h-2 rounded-full bg-blue-500`} />
                          <span className={`text-xs ${
                            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            Principal: {formatCurrency(payment.principal_amount)}
                          </span>
                        </div>
                      )}
                      {payment.interest_amount && (
                        <div className="flex items-center space-x-1">
                          <div className={`w-2 h-2 rounded-full bg-red-500`} />
                          <span className={`text-xs ${
                            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            Interest: {formatCurrency(payment.interest_amount)}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Description */}
                  {payment.description && (
                    <p className={`text-sm ${
                      actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                    }`}>
                      {payment.description}
                    </p>
                  )}
                </div>

                <div className="flex flex-col items-end space-y-2">
                  {/* Payment Method */}
                  {payment.payment_method && (
                    <Badge variant="secondary" className="text-xs">
                      <span className="flex items-center space-x-1">
                        {getPaymentMethodIcon(payment.payment_method)}
                        <span>{getPaymentMethodLabel(payment.payment_method)}</span>
                      </span>
                    </Badge>
                  )}

                  {/* Created Date */}
                  <span className={`text-xs ${
                    actualTheme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                  }`}>
                    {formatDateTime(payment.created_at)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
