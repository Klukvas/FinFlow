import React from "react";
import { DebtPaymentResponse, PaymentMethod } from "@/types/debt";
import { Card, CardContent } from "@/components/ui/shared/Card";
import { Badge } from "@/components/ui/shared/Badge";
import {
  DollarSign,
  Calendar,
  CreditCard,
  Banknote,
  Wallet,
  CheckCircle,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface PaymentListProps {
  payments: DebtPaymentResponse[];
  currency: string;
  isLoading?: boolean;
}

const getPaymentMethodIcon = (method: PaymentMethod) => {
  switch (method) {
    case "CASH":
      return <Banknote className="w-4 h-4" />;
    case "CARD":
      return <CreditCard className="w-4 h-4" />;
    case "TRANSFER":
      return <Wallet className="w-4 h-4" />;
    case "CHECK":
      return <DollarSign className="w-4 h-4" />;
    case "AUTOMATIC":
      return <CheckCircle className="w-4 h-4" />;
    default:
      return <DollarSign className="w-4 h-4" />;
  }
};

const getPaymentMethodLabel = (method: PaymentMethod) => {
  switch (method) {
    case "CASH":
      return "Cash";
    case "CARD":
      return "Card";
    case "TRANSFER":
      return "Transfer";
    case "CHECK":
      return "Check";
    case "AUTOMATIC":
      return "Automatic";
    default:
      return "Other";
  }
};

export const PaymentList: React.FC<PaymentListProps> = ({
  payments,
  currency,
  isLoading = false,
}) => {
  const { formatCurrency } = useCurrencyConversion();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTotalPayments = () => {
    return payments.reduce((total, payment) => total + payment.amount, 0);
  };

  const getTotalPrincipal = () => {
    return payments.reduce(
      (total, payment) => total + (payment.principal_amount || 0),
      0,
    );
  };

  const getTotalInterest = () => {
    return payments.reduce(
      (total, payment) => total + (payment.interest_amount || 0),
      0,
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, index) => (
          <Card
            key={index}
            className="animate-pulse theme-surface theme-border border"
          >
            <CardContent className="p-6">
              <div className="space-y-3">
                <div className="h-4 theme-bg-tertiary rounded w-1/4" />
                <div className="h-3 theme-bg-tertiary rounded w-1/2" />
                <div className="h-3 theme-bg-tertiary rounded w-1/3" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <Card className="theme-surface theme-border border">
        <CardContent className="p-8 text-center">
          <DollarSign className="w-12 h-12 mx-auto mb-4 theme-text-tertiary" />
          <h3 className="text-lg font-medium mb-2 theme-text-secondary">
            No Payments Yet
          </h3>
          <p className="theme-text-tertiary">
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
        <Card className="theme-surface theme-border border">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingDown className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium theme-text-secondary">
                Total Payments
              </span>
            </div>
            <p className="text-2xl font-bold theme-text-primary">
              {formatCurrency(getTotalPayments(), currency)}
            </p>
            <p className="text-xs mt-1 theme-text-tertiary">
              {payments.length} payment{payments.length !== 1 ? "s" : ""}
            </p>
          </CardContent>
        </Card>

        <Card className="theme-surface theme-border border">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium theme-text-secondary">
                Principal Paid
              </span>
            </div>
            <p className="text-2xl font-bold theme-text-primary">
              {formatCurrency(getTotalPrincipal(), currency)}
            </p>
            <p className="text-xs mt-1 theme-text-tertiary">
              {((getTotalPrincipal() / getTotalPayments()) * 100).toFixed(1)}%
              of total
            </p>
          </CardContent>
        </Card>

        <Card className="theme-surface theme-border border">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingUp className="w-5 h-5 text-red-500" />
              <span className="text-sm font-medium theme-text-secondary">
                Interest Paid
              </span>
            </div>
            <p className="text-2xl font-bold theme-text-primary">
              {formatCurrency(getTotalInterest(), currency)}
            </p>
            <p className="text-xs mt-1 theme-text-tertiary">
              {((getTotalInterest() / getTotalPayments()) * 100).toFixed(1)}% of
              total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Payment List */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold theme-text-primary">
          Payment History
        </h3>

        {payments.map((payment) => (
          <Card
            key={payment.id}
            className="transition-all duration-200 hover:shadow-md theme-surface theme-border border hover:theme-border"
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="p-2 rounded-lg theme-success-light">
                      <DollarSign className="w-4 h-4 text-green-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold theme-text-primary">
                        {formatCurrency(payment.amount, currency)}
                      </h4>
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-3 h-3 theme-text-tertiary" />
                        <span className="text-sm theme-text-tertiary">
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
                          <div className="w-2 h-2 rounded-full bg-blue-500" />
                          <span className="text-xs theme-text-tertiary">
                            Principal:{" "}
                            {formatCurrency(payment.principal_amount, currency)}
                          </span>
                        </div>
                      )}
                      {payment.interest_amount && (
                        <div className="flex items-center space-x-1">
                          <div className="w-2 h-2 rounded-full bg-red-500" />
                          <span className="text-xs theme-text-tertiary">
                            Interest:{" "}
                            {formatCurrency(payment.interest_amount, currency)}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Description */}
                  {payment.description && (
                    <p className="text-sm theme-text-secondary">
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
                        <span>
                          {getPaymentMethodLabel(payment.payment_method)}
                        </span>
                      </span>
                    </Badge>
                  )}

                  {/* Created Date */}
                  <span className="text-xs theme-text-tertiary">
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
