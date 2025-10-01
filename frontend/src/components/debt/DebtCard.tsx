import React from 'react';
import { DebtResponse, DebtType } from '@/types/debt';
import { useTheme } from '@/contexts/ThemeContext';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, DropdownMenu, DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui';
import { 
  CreditCard, 
  Home, 
  Car, 
  GraduationCap, 
  DollarSign, 
  Calendar,
  User,
  MoreVertical,
  TrendingDown,
  Trash2,
  Edit
} from 'lucide-react';

interface DebtCardProps {
  debt: DebtResponse;
  onEdit?: (debt: DebtResponse) => void;
  onDelete?: (debtId: number) => void;
  onViewPayments?: (debtId: number) => void;
  onMakePayment?: (debtId: number) => void;
}

const getDebtTypeIcon = (type: DebtType) => {
  switch (type) {
    case 'CREDIT_CARD':
      return <CreditCard className="w-4 h-4" />;
    case 'MORTGAGE':
      return <Home className="w-4 h-4" />;
    case 'AUTO_LOAN':
      return <Car className="w-4 h-4" />;
    case 'STUDENT_LOAN':
      return <GraduationCap className="w-4 h-4" />;
    default:
      return <DollarSign className="w-4 h-4" />;
  }
};

const getDebtTypeLabel = (type: DebtType) => {
  switch (type) {
    case 'CREDIT_CARD':
      return 'Credit Card';
    case 'PERSONAL_LOAN':
      return 'Personal Loan';
    case 'AUTO_LOAN':
      return 'Auto Loan';
    case 'STUDENT_LOAN':
      return 'Student Loan';
    case 'MORTGAGE':
      return 'Mortgage';
    case 'LOAN':
      return 'Loan';
    default:
      return 'Other';
  }
};

export const DebtCard: React.FC<DebtCardProps> = ({
  debt,
  onEdit,
  onDelete,
  onViewPayments,
  onMakePayment
}) => {
  const { actualTheme } = useTheme();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getProgressPercentage = () => {
    // For positive amounts (they owe us): progress = amount paid / initial amount
    // For negative amounts (we owe them): progress = amount paid / initial amount (both negative)
    const initialAbs = Math.abs(debt.initial_amount);
    const currentAbs = Math.abs(debt.current_balance);
    
    if (initialAbs === 0) return 0;
    
    // Calculate how much has been paid off
    const paidOff = initialAbs - currentAbs;
    const progress = (paidOff / initialAbs) * 100;
    
    return Math.max(0, Math.min(100, progress));
  };

  const progressPercentage = getProgressPercentage();

  return (
    <Card className={`transition-all duration-200 hover:shadow-lg ${
      actualTheme === 'dark' 
        ? 'bg-gray-800 border-gray-700 hover:border-gray-600' 
        : 'bg-white border-gray-200 hover:border-gray-300'
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${
              actualTheme === 'dark' ? 'bg-blue-900/50' : 'bg-blue-100'
            }`}>
              {getDebtTypeIcon(debt.debt_type)}
            </div>
            <div>
              <CardTitle className={`text-lg ${
                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {debt.name}
              </CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant="secondary" className="text-xs">
                  {getDebtTypeLabel(debt.debt_type)}
                </Badge>
                {debt.is_active ? (
                  <Badge variant="default" className="text-xs bg-green-500">
                    Active
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-xs">
                    Inactive
                  </Badge>
                )}
                {debt.is_paid_off && (
                  <Badge variant="default" className="text-xs bg-blue-500">
                    Paid Off
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <DropdownMenu
            trigger={
              <Button
                variant="secondary"
                size="sm"
                className={`${actualTheme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700'}`}
              >
                <MoreVertical className="w-4 h-4" />
              </Button>
            }
          >
            <DropdownMenuItem
              onClick={() => onEdit?.(debt)}
              className="flex items-center space-x-2"
            >
              <Edit className="w-4 h-4" />
              <span>Edit Debt</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => onDelete?.(debt.id)}
              className={`flex items-center space-x-2 ${
                actualTheme === 'dark' 
                  ? 'text-red-400 hover:text-red-300 hover:bg-red-900/20' 
                  : 'text-red-600 hover:text-red-700 hover:bg-red-50'
              }`}
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete Debt</span>
            </DropdownMenuItem>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Debt Amounts */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-3 rounded-lg ${
            actualTheme === 'dark' ? 'bg-gray-700/50' : 'bg-gray-50'
          }`}>
            <div className="flex items-center space-x-2 mb-1">
              {debt.current_balance >= 0 ? (
                <TrendingDown className="w-4 h-4 text-green-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
              )}
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Current Balance
              </span>
            </div>
            <p className={`text-xl font-bold ${
              debt.current_balance >= 0 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
            }`}>
              {formatCurrency(Math.abs(debt.current_balance))}
            </p>
            <p className={`text-xs mt-1 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {debt.current_balance >= 0 ? '💰 They owe me' : '💸 I owe them'}
            </p>
          </div>
          <div className={`p-3 rounded-lg ${
            actualTheme === 'dark' ? 'bg-gray-700/50' : 'bg-gray-50'
          }`}>
            <div className="flex items-center space-x-2 mb-1">
              <DollarSign className="w-4 h-4 text-blue-500" />
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Initial Amount
              </span>
            </div>
            <p className={`text-lg font-semibold ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
            }`}>
              {formatCurrency(Math.abs(debt.initial_amount))}
            </p>
            <p className={`text-xs mt-1 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {debt.initial_amount >= 0 ? '💰 They owe me' : '💸 I owe them'}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className={`${actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Progress
            </span>
            <span className={`font-medium ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
            }`}>
              {progressPercentage.toFixed(1)}%
            </span>
          </div>
          <div className={`w-full rounded-full h-2 ${
            actualTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'
          }`}>
            <div 
              className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Debt Details */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          {debt.interest_rate && (
            <div className="flex justify-between">
              <span className={`${actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Interest Rate
              </span>
              <span className={`font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {debt.interest_rate}%
              </span>
            </div>
          )}
          {debt.minimum_payment && (
            <div className="flex justify-between">
              <span className={`${actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Min Payment
              </span>
              <span className={`font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {formatCurrency(debt.minimum_payment)}
              </span>
            </div>
          )}
          {debt.due_date && (
            <div className="flex justify-between">
              <span className={`${actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Due Date
              </span>
              <span className={`font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {formatDate(debt.due_date)}
              </span>
            </div>
          )}
          {debt.last_payment_date && (
            <div className="flex justify-between">
              <span className={`${actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Last Payment
              </span>
              <span className={`font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {formatDate(debt.last_payment_date)}
              </span>
            </div>
          )}
        </div>

        {/* Contact Information */}
        {debt.contact && (
          <div className={`p-3 rounded-lg border ${
            debt.current_balance >= 0
              ? actualTheme === 'dark' 
                ? 'bg-green-900/20 border-green-700' 
                : 'bg-green-50 border-green-200'
              : actualTheme === 'dark' 
                ? 'bg-red-900/20 border-red-700' 
                : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center space-x-2 mb-2">
              <User className={`w-4 h-4 ${
                debt.current_balance >= 0 ? 'text-green-500' : 'text-red-500'
              }`} />
              <span className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {debt.current_balance >= 0 ? '💰 They owe me' : '💸 I owe them'}
              </span>
            </div>
            <p className={`text-sm font-medium ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
            }`}>
              {debt.contact.name}
              {debt.contact.company && (
                <span className={`ml-2 text-xs ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  • {debt.contact.company}
                </span>
              )}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 pt-2">
          <Button
            size="sm"
            variant="primary"
            onClick={() => onMakePayment?.(debt.id)}
            className="flex-1 min-w-[120px]"
          >
            <DollarSign className="w-4 h-4 mr-2" />
            Make Payment
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewPayments?.(debt.id)}
            className="flex-1 min-w-[120px]"
          >
            <Calendar className="w-4 h-4 mr-2" />
            View Payments
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
