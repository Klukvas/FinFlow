import React from "react";
import { AccountResponse, AccountSummary } from "@/types";
import { Card } from "../shared/Card";
import { EditButton } from "../shared/EditButton";
import { DeleteButton } from "../shared/DeleteButton";
import { FaWallet, FaDollarSign, FaChartLine } from "react-icons/fa";

interface AccountCardProps {
 account: AccountResponse;
 summary?: AccountSummary | undefined;
 onEdit: (account: AccountResponse) => void;
 onArchive: (id: number) => void;
}

export const AccountCard: React.FC<AccountCardProps> = ({
 account,
 summary,
 onEdit,
 onArchive,
}) => {
 const getAccountTypeIcon = (type: string) => {
 switch (type.toLowerCase()) {
 case "bank":
 return <FaWallet className="w-5 h-5" />;
 case "cash":
 return <FaDollarSign className="w-5 h-5" />;
 case "crypto":
 return <FaChartLine className="w-5 h-5" />;
 default:
 return <FaWallet className="w-5 h-5" />;
 }
 };

 const getAccountTypeColor = (type: string) => {
 switch (type.toLowerCase()) {
 case "bank":
 return "text-accent-base bg-[var(--color-accent-light)]";
 case "cash":
 return "text-success-base bg-[var(--color-success-light)]";
 case "crypto":
 return "text-purple-600 bg-purple-100";
 default:
 return "text-content-secondary bg-surface-alt";
 }
 };

 const formatBalance = (balance: number, currency: string) => {
 return new Intl.NumberFormat("ru-RU", {
 style: "currency",
 currency: currency || "RUB",
 }).format(balance);
 };

 return (
 <Card className="p-6 hover:bg-surface-alt transition-colors">
 <div className="flex items-start justify-between mb-4">
 <div className="flex items-center">
 <div
 className={`p-2 rounded-lg ${getAccountTypeColor(account.type)}`}
 >
 {getAccountTypeIcon(account.type)}
 </div>
 <div className="ml-3">
 <h3 className="font-semibold text-content">{account.name}</h3>
 <p className="text-sm text-content-secondary capitalize">
 {account.type}
 </p>
 </div>
 </div>

 <div className="flex items-center gap-2">
 <EditButton
 onEdit={() => {
 onEdit(account);
 }}
 />
 <DeleteButton onDelete={() => onArchive(account.id)} />
 </div>
 </div>

 <div className="space-y-3">
 <div className="flex justify-between items-center">
 <span className="text-sm text-content-secondary">Баланс:</span>
 <span className="font-semibold text-content">
 {formatBalance(account.balance, account.currency)}
 </span>
 </div>

 {summary && (
 <>
 <div className="flex justify-between items-center">
 <span className="text-sm text-content-secondary">Транзакций:</span>
 <span className="text-sm text-content">
 {summary.transaction_count}
 </span>
 </div>

 {summary.last_transaction_date && (
 <div className="flex justify-between items-center">
 <span className="text-sm text-content-secondary">
 Последняя операция:
 </span>
 <span className="text-sm text-content">
 {new Date(summary.last_transaction_date).toLocaleDateString(
 "ru-RU",
 )}
 </span>
 </div>
 )}
 </>
 )}

 <div className="pt-3 border-t border-[var(--color-border)]">
 <div className="flex justify-between items-center">
 <span className="text-xs text-content-tertiary">Создан:</span>
 <span className="text-xs text-content-tertiary">
 {new Date(account.created_at).toLocaleDateString("ru-RU")}
 </span>
 </div>
 </div>
 </div>
 </Card>
 );
};
