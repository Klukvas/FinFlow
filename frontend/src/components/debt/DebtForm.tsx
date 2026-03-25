import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { DebtCreate, DebtUpdate, DebtType } from "@/types/debt";
import { ContactResponse } from "@/types/contact";
import {
 Button,
 Input,
 Label,
 FormattedNumberInput,
 Select,
 SelectContent,
 SelectItem,
 SelectTrigger,
 SelectValue,
 Textarea,
 Card,
 CardContent,
 CardHeader,
 CardTitle,
} from "@/components/ui";
import { CurrencySelect } from "@/components/ui/forms/CurrencySelect";
import {
 removeSpacesFromNumber,
 formatNumberWithSpaces,
} from "@/utils/numberFormat";
import { Calendar, DollarSign, User, Building2 } from "lucide-react";

interface DebtFormProps {
 initialData?: Partial<DebtCreate>;
 contacts: ContactResponse[];
 categories: Array<{ id: number; name: string }>;
 onSubmit: (data: DebtCreate | DebtUpdate) => void;
 onCancel: () => void;
 isLoading?: boolean;
 mode: "create" | "edit";
 showCard?: boolean;
 paymentCount?: number; // Number of payments for validation
}

const debtTypeConfigs: { value: DebtType; labelKey: string; icon: string }[] = [
 { value: "CREDIT_CARD", labelKey: "debtPage.types.creditCard", icon: "💳" },
 {
 value: "PERSONAL_LOAN",
 labelKey: "debtPage.types.personalLoan",
 icon: "🏦",
 },
 { value: "AUTO_LOAN", labelKey: "debtPage.types.autoLoan", icon: "🚗" },
 { value: "STUDENT_LOAN", labelKey: "debtPage.types.studentLoan", icon: "🎓" },
 { value: "MORTGAGE", labelKey: "debtPage.types.mortgage", icon: "🏠" },
 { value: "LOAN", labelKey: "debtPage.types.generalLoan", icon: "💰" },
 { value: "OTHER", labelKey: "debtPage.types.other", icon: "📋" },
];

export const DebtForm: React.FC<DebtFormProps> = ({
 initialData = {},
 contacts,
 categories,
 onSubmit,
 onCancel,
 isLoading = false,
 mode,
 showCard = true,
 paymentCount = 0,
}) => {
 const { t } = useTranslation();

 const [formData, setFormData] = useState<DebtCreate>({
 name: initialData.name || "",
 description: initialData.description || "",
 debt_type: initialData.debt_type || "CREDIT_CARD",
 contact_id: initialData.contact_id || null,
 category_id: initialData.category_id || null,
 currency: initialData.currency || "USD",
 initial_amount: initialData.initial_amount || 0,
 interest_rate: initialData.interest_rate || null,
 minimum_payment: initialData.minimum_payment || null,
 start_date:
 initialData.start_date || new Date().toISOString().split("T")[0] || "",
 due_date: initialData.due_date || null,
 });
 const [initialAmountDisplay, setInitialAmountDisplay] = useState(
 initialData.initial_amount
 ? formatNumberWithSpaces(initialData.initial_amount.toString())
 : "",
 );
 const [minimumPaymentDisplay, setMinimumPaymentDisplay] = useState(
 initialData.minimum_payment
 ? formatNumberWithSpaces(initialData.minimum_payment.toString())
 : "",
 );

 // Debug: log formData after initialization

 const [errors, setErrors] = useState<Record<string, string>>({});

 const validateForm = (): boolean => {
 const newErrors: Record<string, string> = {};

 if (!formData.name.trim()) {
 newErrors.name = t("debtPage.form.errors.nameRequired");
 }

 // Category is optional for debts

 if (!formData.initial_amount || formData.initial_amount === 0) {
 newErrors.initial_amount = t(
 "debtPage.form.errors.initialAmountCannotBeZero",
 );
 }

 if (
 formData.interest_rate !== null &&
 formData.interest_rate !== undefined &&
 (formData.interest_rate < 0 || formData.interest_rate > 100)
 ) {
 newErrors.interest_rate = t("debtPage.form.errors.interestRateRange");
 }

 if (
 formData.minimum_payment !== null &&
 formData.minimum_payment !== undefined &&
 formData.minimum_payment <= 0
 ) {
 newErrors.minimum_payment = t(
 "debtPage.form.errors.minimumPaymentMustBeGreater",
 );
 }

 if (!formData.start_date) {
 newErrors.start_date = t("debtPage.form.errors.startDateRequired");
 }

 setErrors(newErrors);
 return Object.keys(newErrors).length === 0;
 };

 const handleSubmit = (e: React.FormEvent) => {
 e.preventDefault();

 // Prevent currency changes if debt has payments
 if (mode === "edit" && paymentCount > 0 && initialData?.currency) {
 if (formData.currency !== initialData.currency) {
 setErrors((prev) => ({
 ...prev,
 currency: t("debtPage.form.currencyLocked"),
 }));
 return;
 }
 }

 if (validateForm()) {
 // Clean the form data - ensure empty strings become null
 const cleanedFormData = {
 ...formData,
 description: formData.description?.trim() || null,
 interest_rate: formData.interest_rate || null,
 minimum_payment: formData.minimum_payment || null,
 due_date: formData.due_date || null,
 };
 onSubmit(cleanedFormData);
 }
 };

 const handleInputChange = (field: keyof DebtCreate, value: any) => {
 setFormData((prev) => ({ ...prev, [field]: value }));
 // Clear error when user starts typing
 if (errors[field]) {
 setErrors((prev) => ({ ...prev, [field]: "" }));
 }
 };

 const getDebtTypes = () => {
 return debtTypeConfigs.map((config) => ({
 value: config.value,
 label: t(config.labelKey),
 icon: config.icon,
 }));
 };

 const debtTypes = getDebtTypes();
 const selectedDebtType = debtTypes.find(
 (type) => type.value === formData.debt_type,
 );

 const formContent = (
 <>
 {showCard && (
 <div className="mb-4">
 <h2 className="text-lg font-semibold text-content">
 {mode === "create"
 ? t("debtPage.form.title")
 : t("debtPage.form.editTitle")}
 </h2>
 </div>
 )}
 <form onSubmit={handleSubmit} className="space-y-6">
 {/* Debt Name */}
 <div className="space-y-2">
 <Label htmlFor="name" className="text-content-secondary">
 {t("debtPage.form.name")} *
 </Label>
 <Input
 id="name"
 value={formData.name}
 onChange={(e) => handleInputChange("name", e.target.value)}
 placeholder={t("debtPage.form.namePlaceholder")}
 className={`bg-elevated border-[var(--border)] border text-content placeholder:text-content-tertiary ${errors.name ? "border-danger-base" : ""}`}
 />
 {errors.name && <p className="text-sm text-danger-base">{errors.name}</p>}
 </div>

 {/* Debt Type */}
 <div className="space-y-2">
 <Label className="text-content-secondary">
 {t("debtPage.form.debtType")} *
 </Label>
 <Select
 value={formData.debt_type}
 onValueChange={(value: string) =>
 handleInputChange("debt_type", value as DebtType)
 }
 >
 <SelectTrigger className="bg-elevated border-[var(--border)] border text-content">
 <SelectValue>
 {selectedDebtType && (
 <span className="flex items-center space-x-2">
 <span>{selectedDebtType.icon}</span>
 <span>{selectedDebtType.label}</span>
 </span>
 )}
 </SelectValue>
 </SelectTrigger>
 <SelectContent className="bg-elevated border-[var(--border)] border">
 {debtTypes.map((type) => (
 <SelectItem
 key={type.value}
 value={type.value}
 className="text-content hover:bg-surface-alt"
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
 <Label htmlFor="description" className="text-content-secondary">
 {t("debtPage.form.description")}
 </Label>
 <Textarea
 id="description"
 value={formData.description || ""}
 onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
 handleInputChange("description", e.target.value)
 }
 placeholder={t("debtPage.form.descriptionPlaceholder")}
 rows={3}
 className="bg-elevated border-[var(--border)] border text-content placeholder:text-content-tertiary"
 />
 </div>

 {/* Currency */}
 <div className="space-y-2">
 <Label htmlFor="currency" className="text-content-secondary">
 {t("debtPage.form.currency")}
 </Label>
 <CurrencySelect
 value={formData.currency}
 onChange={(value) => {
 // Prevent changes if debt has payments
 if (mode === "edit" && paymentCount > 0) {
 return;
 }
 handleInputChange("currency", value);
 }}
 disabled={mode === "edit" && paymentCount > 0}
 className={`bg-elevated border-[var(--border)] border text-content ${mode === "edit" && paymentCount > 0 ? "opacity-50 cursor-not-allowed" : ""}`}
 placeholder={t("debtPage.form.selectCurrency")}
 showFlags={true}
 />
 {errors.currency && (
 <p className="text-sm text-danger-base">{errors.currency}</p>
 )}
 {mode === "edit" && paymentCount > 0 && !errors.currency && (
 <p className="text-xs mt-1 text-warning-base">
 ⚠️ {t("debtPage.form.currencyLocked")}
 </p>
 )}
 </div>

 {/* Amount and Financial Details */}
 <div className="space-y-4">
 <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
 <div>
 <FormattedNumberInput
 label={t("debtPage.form.initialAmount")}
 value={initialAmountDisplay}
 onChange={(value) => {
 setInitialAmountDisplay(value);
 const cleanedValue = removeSpacesFromNumber(value);
 const numValue = cleanedValue
 ? Math.round(parseFloat(cleanedValue) * 100) / 100
 : 0;
 handleInputChange("initial_amount", numValue);
 }}
 placeholder="0.00"
 required
 error={errors.initial_amount || ""}
 className="w-full"
 />
 <div className="mt-2 text-xs text-content-tertiary">
 💡 <strong>{t("debtPage.form.tip")}</strong>{" "}
 {t("debtPage.form.amountTip")}
 </div>
 </div>

 <div className="space-y-2">
 <Label htmlFor="interest_rate" className="text-content-secondary">
 {t("debtPage.form.interestRate")}
 </Label>
 <Input
 id="interest_rate"
 type="number"
 step="0.01"
 min="0"
 max="100"
 value={formData.interest_rate || ""}
 onChange={(e) => {
 const value = e.target.value;
 // Use parseFloat but round to 2 decimal places to avoid precision errors
 const numValue = value
 ? Math.round(parseFloat(value) * 100) / 100
 : null;
 handleInputChange("interest_rate", numValue);
 }}
 placeholder="0.00"
 className={`bg-elevated border-[var(--border)] border text-content placeholder:text-content-tertiary ${errors.interest_rate ? "border-danger-base" : ""}`}
 />
 {errors.interest_rate && (
 <p className="text-sm text-danger-base">{errors.interest_rate}</p>
 )}
 </div>
 </div>

 <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
 <div>
 <FormattedNumberInput
 label={t("debtPage.form.minimumPayment")}
 value={minimumPaymentDisplay}
 onChange={(value) => {
 setMinimumPaymentDisplay(value);
 const cleanedValue = removeSpacesFromNumber(value);
 const numValue = cleanedValue
 ? Math.round(parseFloat(cleanedValue) * 100) / 100
 : null;
 handleInputChange("minimum_payment", numValue);
 }}
 placeholder="0"
 error={errors.minimum_payment || ""}
 className="w-full"
 />
 </div>

 <div className="space-y-2">
 <Label htmlFor="category_id" className="text-content-secondary">
 {t("debtPage.form.category")}
 </Label>
 <Select
 value={formData.category_id?.toString() || "none"}
 onValueChange={(value: string) =>
 handleInputChange(
 "category_id",
 value && value !== "none" ? parseInt(value) : null,
 )
 }
 >
 <SelectTrigger className="bg-elevated border-[var(--border)] border text-content">
 <SelectValue>
 {formData.category_id
 ? categories.find((c) => c.id === formData.category_id)
 ?.name
 : t("debtPage.form.noCategory")}
 </SelectValue>
 </SelectTrigger>
 <SelectContent className="bg-elevated border-[var(--border)] border">
 <SelectItem
 value="none"
 className="text-content hover:bg-surface-alt"
 >
 {t("debtPage.form.noCategory")}
 </SelectItem>
 {categories.map((category) => (
 <SelectItem
 key={category.id}
 value={category.id.toString()}
 className="text-content hover:bg-surface-alt"
 >
 {category.name}
 </SelectItem>
 ))}
 </SelectContent>
 </Select>
 </div>
 </div>
 </div>

 {/* Dates */}
 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
 <div className="space-y-2">
 <Label htmlFor="start_date" className="text-content-secondary">
 {t("debtPage.form.startDate")} *
 </Label>
 <div className="relative">
 <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-content-tertiary" />
 <Input
 id="start_date"
 type="date"
 value={formData.start_date}
 onChange={(e) =>
 handleInputChange("start_date", e.target.value)
 }
 className={`pl-10 bg-elevated border-[var(--border)] border text-content ${errors.start_date ? "border-danger-base" : ""}`}
 />
 </div>
 {errors.start_date && (
 <p className="text-sm text-danger-base">{errors.start_date}</p>
 )}
 </div>

 <div className="space-y-2">
 <Label htmlFor="due_date" className="text-content-secondary">
 {t("debtPage.form.dueDate")}
 </Label>
 <div className="relative">
 <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-content-tertiary" />
 <Input
 id="due_date"
 type="date"
 value={formData.due_date || ""}
 onChange={(e) =>
 handleInputChange("due_date", e.target.value || null)
 }
 className="pl-10 bg-elevated border-[var(--border)] border text-content"
 />
 </div>
 </div>
 </div>

 {/* Contact Selection */}
 <div className="space-y-2">
 <Label className="text-content-secondary">
 <User className="w-4 h-4 inline mr-2" />
 {t("debtPage.form.contactInformation")}
 </Label>
 <div className="p-4 rounded-lg bg-elevated border-[var(--border)] border">
 <p className="text-sm mb-3 text-content-secondary">
 {t("debtPage.form.selectContact")}
 </p>
 {contacts.length === 0 ? (
 <div className="p-3 rounded-lg border bg-[var(--warning-dim)] border-[var(--border)]">
 <p className="text-sm text-warning-base">
 ⚠️ {t("debtPage.form.noContactsAvailable")}
 </p>
 </div>
 ) : (
 <div className="relative">
 <Select
 value={formData.contact_id?.toString() || ""}
 onValueChange={(value: string) => {
 handleInputChange(
 "contact_id",
 value ? parseInt(value) : null,
 );
 }}
 >
 <SelectTrigger className="bg-elevated border-[var(--border)] border text-content">
 <SelectValue placeholder={t("debtPage.form.chooseContact")}>
 {formData.contact_id
 ? (() => {
 const selectedContact = contacts.find(
 (c) => c.id === formData.contact_id,
 );
 return selectedContact ? (
 <span className="flex items-center space-x-2">
 <User className="w-4 h-4" />
 <span>{selectedContact.name}</span>
 {selectedContact.company && (
 <>
 <Building2 className="w-4 h-4" />
 <span className="text-sm opacity-75">
 ({selectedContact.company})
 </span>
 </>
 )}
 </span>
 ) : null;
 })()
 : null}
 </SelectValue>
 </SelectTrigger>
 <SelectContent className="bg-elevated border-[var(--border)] border">
 <SelectItem
 value=""
 className="text-content hover:bg-surface-alt"
 >
 <span className="flex items-center space-x-2">
 <span>👤</span>
 <span>{t("debtPage.form.noSpecificContact")}</span>
 </span>
 </SelectItem>
 {contacts.map((contact) => (
 <SelectItem
 key={contact.id}
 value={contact.id.toString()}
 className="text-content hover:bg-surface-alt"
 >
 <span className="flex items-center space-x-2">
 <User className="w-4 h-4" />
 <span>{contact.name}</span>
 {contact.company && (
 <>
 <Building2 className="w-4 h-4" />
 <span className="text-sm opacity-75">
 ({contact.company})
 </span>
 </>
 )}
 </span>
 </SelectItem>
 ))}
 </SelectContent>
 </Select>
 </div>
 )}
 <div className="mt-3 text-xs text-content-tertiary">
 💡 <strong>{t("debtPage.form.tip")}</strong>
 <br />• <strong>{t("debtPage.form.positiveAmount")}</strong>{" "}
 {t("debtPage.form.theyOweYou")}
 <br />• <strong>{t("debtPage.form.negativeAmount")}</strong>{" "}
 {t("debtPage.form.youOweThem")}
 <br />• {t("debtPage.form.useContacts")}
 </div>
 </div>
 </div>

 {/* Action Buttons */}
 <div className="flex flex-col sm:flex-row gap-3 pt-6">
 <Button type="submit" disabled={isLoading} className="flex-1">
 {isLoading
 ? t("debtPage.form.saving")
 : mode === "create"
 ? t("debtPage.form.create")
 : t("debtPage.form.update")}
 </Button>
 <Button
 type="button"
 variant="outline"
 onClick={onCancel}
 disabled={isLoading}
 className="flex-1"
 >
 {t("common.cancel")}
 </Button>
 </div>
 </form>
 </>
 );

 if (!showCard) {
 return formContent;
 }

 return (
 <Card className="max-w-2xl mx-auto bg-elevated border-[var(--border)] border">
 <CardHeader>
 <CardTitle className="flex items-center space-x-2 text-content">
 <DollarSign className="w-5 h-5" />
 <span>
 {mode === "create"
 ? t("debtPage.form.title")
 : t("debtPage.form.editTitle")}
 </span>
 </CardTitle>
 </CardHeader>
 <CardContent>{formContent}</CardContent>
 </Card>
 );
};
