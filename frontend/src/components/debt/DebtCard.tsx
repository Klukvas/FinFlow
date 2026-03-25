import React from "react";
import { DebtResponse, DebtType } from "@/types/debt";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";
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
  Edit,
  Lock,
} from "lucide-react";

interface DebtCardProps {
  debt: DebtResponse;
  onEdit?: (debt: DebtResponse) => void;
  onDelete?: (debtId: number) => void;
  onViewPayments?: (debtId: number) => void;
  onMakePayment?: (debtId: number) => void;
}

const getDebtTypeIcon = (type: DebtType) => {
  switch (type) {
    case "CREDIT_CARD":
      return <CreditCard className="w-4 h-4" />;
    case "MORTGAGE":
      return <Home className="w-4 h-4" />;
    case "AUTO_LOAN":
      return <Car className="w-4 h-4" />;
    case "STUDENT_LOAN":
      return <GraduationCap className="w-4 h-4" />;
    default:
      return <DollarSign className="w-4 h-4" />;
  }
};

const getDebtTypeLabel = (type: DebtType) => {
  switch (type) {
    case "CREDIT_CARD":
      return "Credit Card";
    case "PERSONAL_LOAN":
      return "Personal Loan";
    case "AUTO_LOAN":
      return "Auto Loan";
    case "STUDENT_LOAN":
      return "Student Loan";
    case "MORTGAGE":
      return "Mortgage";
    case "LOAN":
      return "Loan";
    default:
      return "Other";
  }
};

export const DebtCard: React.FC<DebtCardProps> = ({
  debt,
  onEdit,
  onDelete,
  onViewPayments,
  onMakePayment,
}) => {
  const { formatCurrency } = useCurrencyConversion();

  const formatAmount = (amount: number, currency?: string) => {
    return formatCurrency(amount, currency || debt.currency);
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
    <Card className="transition-all duration-200 hover:shadow-lg bg-elevated border-[var(--border)] border hover:border-[var(--border)]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-[var(--accent-dim)]">
              {getDebtTypeIcon(debt.debt_type)}
            </div>
            <div>
              <CardTitle className="text-lg flex items-center gap-1.5 text-content">
                {debt.name}
                {debt.is_read_only && (
                  <Lock className="w-4 h-4 text-warning-base flex-shrink-0" />
                )}
              </CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant="secondary" className="text-xs">
                  {getDebtTypeLabel(debt.debt_type)}
                </Badge>
                {debt.is_active ? (
                  <Badge variant="default" className="text-xs bg-success-base">
                    Active
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-xs">
                    Inactive
                  </Badge>
                )}
                {debt.is_paid_off && (
                  <Badge variant="default" className="text-xs bg-accent-base">
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
                className="text-content-tertiary hover:text-content"
              >
                <MoreVertical className="w-4 h-4" />
              </Button>
            }
          >
            <DropdownMenuItem
              onClick={() => onEdit?.(debt)}
              disabled={debt.is_read_only === true}
              className="flex items-center space-x-2"
              {...(debt.is_read_only
                ? { title: "Read-only: upgrade or delete excess records" }
                : {})}
            >
              <Edit className="w-4 h-4" />
              <span>Edit Debt</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => onDelete?.(debt.id)}
              className="flex items-center space-x-2 text-danger-base hover:bg-surface-alt"
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
          <div className="p-3 rounded-lg bg-[var(--accent-dim)]">
            <div className="flex items-center space-x-2 mb-1">
              {debt.current_balance >= 0 ? (
                <TrendingDown className="w-4 h-4 text-success-base" />
              ) : (
                <TrendingDown className="w-4 h-4 text-danger-base" />
              )}
              <span className="text-sm font-medium text-content-secondary">
                Current Balance
              </span>
            </div>
            <p
              className={`text-xl font-mono font-bold ${
                debt.current_balance >= 0
                  ? "text-success-base"
                  : "text-danger-base"
              }`}
            >
              {formatAmount(Math.abs(debt.current_balance), debt.currency)}
            </p>
            <p className="text-xs mt-1 text-content-tertiary">
              {debt.current_balance >= 0 ? "💰 They owe me" : "💸 I owe them"}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[var(--accent-dim)]">
            <div className="flex items-center space-x-2 mb-1">
              <DollarSign className="w-4 h-4 text-accent-base" />
              <span className="text-sm font-medium text-content-secondary">
                Initial Amount
              </span>
            </div>
            <p className="text-lg font-mono font-semibold text-content-secondary">
              {formatAmount(Math.abs(debt.initial_amount), debt.currency)}
            </p>
            <p className="text-xs mt-1 text-content-tertiary">
              {debt.initial_amount >= 0 ? "💰 They owe me" : "💸 I owe them"}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-content-tertiary">Progress</span>
            <span className="font-medium text-content-secondary">
              {progressPercentage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full rounded-full h-2 border-[var(--border)] bg-surface-alt">
            <div
              className="bg-[var(--accent)] h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Debt Details */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          {debt.interest_rate && (
            <div className="flex justify-between">
              <span className="text-content-tertiary">Interest Rate</span>
              <span className="font-medium text-content-secondary">
                {debt.interest_rate}%
              </span>
            </div>
          )}
          {debt.minimum_payment && (
            <div className="flex justify-between">
              <span className="text-content-tertiary">Min Payment</span>
              <span className="font-mono font-medium text-content-secondary">
                {formatAmount(debt.minimum_payment, debt.currency)}
              </span>
            </div>
          )}
          {debt.due_date && (
            <div className="flex justify-between">
              <span className="text-content-tertiary">Due Date</span>
              <span className="font-medium text-content-secondary">
                {formatDate(debt.due_date)}
              </span>
            </div>
          )}
          {debt.last_payment_date && (
            <div className="flex justify-between">
              <span className="text-content-tertiary">Last Payment</span>
              <span className="font-medium text-content-secondary">
                {formatDate(debt.last_payment_date)}
              </span>
            </div>
          )}
        </div>

        {/* Contact Information */}
        {debt.contact && (
          <div
            className={`p-3 rounded-lg border ${
              debt.current_balance >= 0
                ? "bg-[var(--success-dim)] border-[var(--border)]"
                : "bg-[var(--danger-dim)] border-[var(--border)]"
            }`}
          >
            <div className="flex items-center space-x-2 mb-2">
              <User
                className={`w-4 h-4 ${
                  debt.current_balance >= 0
                    ? "text-success-base"
                    : "text-danger-base"
                }`}
              />
              <span className="text-sm font-medium text-content-secondary">
                {debt.current_balance >= 0 ? "💰 They owe me" : "💸 I owe them"}
              </span>
            </div>
            <p className="text-sm font-medium text-content-secondary">
              {debt.contact.name}
              {debt.contact.company && (
                <span className="ml-2 text-xs text-content-tertiary">
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
