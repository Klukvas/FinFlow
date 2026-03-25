import React, { useState } from "react";
import { DebtPaymentCreate, PaymentMethod } from "@/types/debt";
import { Button } from "@/components/ui/shared/Button";
import { Input } from "@/components/ui/forms/Input";
import { Label } from "@/components/ui/forms/Label";
import { FormattedNumberInput } from "@/components/ui/forms/FormattedNumberInput";
import {
 Select,
 SelectContent,
 SelectItem,
 SelectTrigger,
 SelectValue,
} from "@/components/ui/forms/Select";
import { Textarea } from "@/components/ui/forms/Textarea";
import { removeSpacesFromNumber } from "@/utils/numberFormat";
import {
 Card,
 CardContent,
 CardHeader,
 CardTitle,
} from "@/components/ui/shared/Card";
import {
 Calendar,
 DollarSign,
 CreditCard,
 Wallet,
 Banknote,
} from "lucide-react";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface PaymentFormProps {
 debtId: number;
 currentBalance: number;
 currency: string;
 onSubmit: (payment: DebtPaymentCreate) => void;
 onCancel: () => void;
 isLoading?: boolean;
 showCard?: boolean;
}

const paymentMethods: {
 value: PaymentMethod;
 label: string;
 icon: React.ReactNode;
}[] = [
 { value: "CASH", label: "Cash", icon: <Banknote className="w-4 h-4" /> },
 {
 value: "CARD",
 label: "Credit/Debit Card",
 icon: <CreditCard className="w-4 h-4" />,
 },
 {
 value: "TRANSFER",
 label: "Bank Transfer",
 icon: <Wallet className="w-4 h-4" />,
 },
 { value: "CHECK", label: "Check", icon: <DollarSign className="w-4 h-4" /> },
 {
 value: "AUTOMATIC",
 label: "Automatic Payment",
 icon: <CreditCard className="w-4 h-4" />,
 },
 { value: "OTHER", label: "Other", icon: <DollarSign className="w-4 h-4" /> },
];

export const PaymentForm: React.FC<PaymentFormProps> = ({
 currentBalance,
 currency,
 onSubmit,
 onCancel,
 isLoading = false,
 showCard = true,
}) => {
 const { formatCurrency } = useCurrencyConversion();

 const [formData, setFormData] = useState<DebtPaymentCreate>({
 amount: 0,
 principal_amount: null,
 interest_amount: null,
 payment_date: (new Date().toISOString().split("T")[0] || "") as string,
 description: null,
 payment_method: "CASH",
 });

 const [errors, setErrors] = useState<Record<string, string>>({});
 const [amountDisplay, setAmountDisplay] = useState("");
 const [principalAmountDisplay, setPrincipalAmountDisplay] = useState("");
 const [interestAmountDisplay, setInterestAmountDisplay] = useState("");

 const validateForm = (): boolean => {
 const newErrors: Record<string, string> = {};

 if (!formData.amount || formData.amount <= 0) {
 newErrors.amount = "Payment amount must be greater than 0";
 }

 if (formData.amount > currentBalance) {
 newErrors.amount = "Payment amount cannot exceed current balance";
 }

 if (
 formData.principal_amount !== null &&
 formData.principal_amount !== undefined &&
 formData.principal_amount < 0
 ) {
 newErrors.principal_amount = "Principal amount cannot be negative";
 }

 if (
 formData.interest_amount !== null &&
 formData.interest_amount !== undefined &&
 formData.interest_amount < 0
 ) {
 newErrors.interest_amount = "Interest amount cannot be negative";
 }

 if (
 formData.principal_amount !== null &&
 formData.principal_amount !== undefined &&
 formData.interest_amount !== null &&
 formData.interest_amount !== undefined
 ) {
 const total =
 (formData.principal_amount || 0) + (formData.interest_amount || 0);
 if (Math.abs(total - formData.amount) > 0.01) {
 newErrors.interest_amount =
 "Principal + Interest must equal total payment amount";
 }
 }

 if (!formData.payment_date) {
 newErrors.payment_date = "Payment date is required";
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
 setFormData((prev) => ({ ...prev, [field]: value }));
 // Clear error when user starts typing
 if (errors[field]) {
 setErrors((prev) => ({ ...prev, [field]: "" }));
 }
 };

 const calculateRemainingBalance = () => {
 return currentBalance - formData.amount;
 };

 const content = (
 <>
 <CardContent>
 {/* Current Balance Info */}
 <div className="p-4 rounded-lg mb-6 bg-[var(--accent-dim)]">
 <div className="flex justify-between items-center">
 <span className="text-sm font-medium text-content-secondary">
 Current Balance
 </span>
 <span className="text-lg font-bold text-content">
 {formatCurrency(currentBalance, currency)}
 </span>
 </div>
 {formData.amount > 0 && (
 <div className="flex justify-between items-center mt-2 pt-2 border-[var(--border)] border-t">
 <span className="text-sm font-medium text-content-secondary">
 After Payment
 </span>
 <span className="text-lg font-bold text-success-base">
 {formatCurrency(calculateRemainingBalance(), currency)}
 </span>
 </div>
 )}
 </div>

 <form onSubmit={handleSubmit} className="space-y-6">
 {/* Payment Amount */}
 <FormattedNumberInput
 label="Payment Amount"
 value={amountDisplay}
 onChange={(value) => {
 setAmountDisplay(value);
 const cleanedValue = removeSpacesFromNumber(value);
 const numValue = cleanedValue
 ? Math.round(parseFloat(cleanedValue) * 100) / 100
 : 0;
 handleInputChange("amount", numValue);
 }}
 placeholder="0.00"
 required
 error={errors.amount || ""}
 className="w-full"
 />

 {/* Payment Date */}
 <div className="space-y-2">
 <Label htmlFor="payment_date" className="text-content-secondary">
 Payment Date *
 </Label>
 <div className="relative">
 <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-content-tertiary" />
 <Input
 id="payment_date"
 type="date"
 value={formData.payment_date}
 onChange={(e) =>
 handleInputChange("payment_date", e.target.value)
 }
 className={`pl-10 bg-elevated border-[var(--border)] border text-content ${errors.payment_date ? "border-danger-base" : ""}`}
 />
 </div>
 {errors.payment_date && (
 <p className="text-sm text-danger-base">{errors.payment_date}</p>
 )}
 </div>

 {/* Payment Method */}
 <div className="space-y-2">
 <Label className="text-content-secondary">Payment Method</Label>
 <Select
 value={formData.payment_method || ""}
 onValueChange={(value) =>
 handleInputChange("payment_method", value || null)
 }
 >
 <SelectTrigger className="bg-elevated border-[var(--border)] border text-content">
 <SelectValue placeholder="Select payment method (optional)" />
 </SelectTrigger>
 <SelectContent className="bg-elevated border-[var(--border)] border">
 <SelectItem
 value=""
 className="text-content hover:bg-surface-alt"
 >
 No method specified
 </SelectItem>
 {paymentMethods.map((method) => (
 <SelectItem
 key={method.value}
 value={method.value}
 className="text-content hover:bg-surface-alt"
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
 <div className="p-3 rounded-lg bg-[var(--accent-dim)]">
 <Label className="text-sm font-medium text-content-secondary">
 Payment Breakdown (Optional)
 </Label>
 <p className="text-xs mt-1 text-content-tertiary">
 Specify how much goes to principal vs interest
 </p>
 </div>

 <div className="grid grid-cols-2 gap-4">
 <FormattedNumberInput
 label="Principal Amount"
 value={principalAmountDisplay}
 onChange={(value) => {
 setPrincipalAmountDisplay(value);
 const cleanedValue = removeSpacesFromNumber(value);
 const numValue = cleanedValue
 ? Math.round(parseFloat(cleanedValue) * 100) / 100
 : null;
 handleInputChange("principal_amount", numValue);
 }}
 placeholder="0.00"
 error={errors.principal_amount || ""}
 className="w-full"
 />

 <FormattedNumberInput
 label="Interest Amount"
 value={interestAmountDisplay}
 onChange={(value) => {
 setInterestAmountDisplay(value);
 const cleanedValue = removeSpacesFromNumber(value);
 const numValue = cleanedValue
 ? Math.round(parseFloat(cleanedValue) * 100) / 100
 : null;
 handleInputChange("interest_amount", numValue);
 }}
 placeholder="0.00"
 error={errors.interest_amount || ""}
 className="w-full"
 />
 </div>
 </div>

 {/* Description */}
 <div className="space-y-2">
 <Label htmlFor="description" className="text-content-secondary">
 Description
 </Label>
 <Textarea
 id="description"
 value={formData.description || ""}
 onChange={(e) => handleInputChange("description", e.target.value)}
 placeholder="Payment notes or reference..."
 rows={3}
 className="bg-elevated border-[var(--border)] border text-content placeholder:text-content-tertiary"
 />
 </div>

 {/* Action Buttons */}
 <div className="flex flex-col sm:flex-row gap-3 pt-6">
 <Button type="submit" disabled={isLoading} className="flex-1">
 {isLoading ? "Processing..." : "Record Payment"}
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
 </>
 );

 if (!showCard) {
 return <div className="space-y-4">{content}</div>;
 }

 return (
 <Card className="max-w-lg mx-auto bg-elevated border-[var(--border)] border">
 <CardHeader>
 <CardTitle className="flex items-center space-x-2 text-content">
 <DollarSign className="w-5 h-5" />
 <span>Make Payment</span>
 </CardTitle>
 </CardHeader>
 {content}
 </Card>
 );
};
