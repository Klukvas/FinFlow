import React from 'react';
import { ContactResponse } from '@/types/contact';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/shared/Card';
import { Badge } from '@/components/ui/shared/Badge';
import { Button } from '@/components/ui/shared/Button';
import {
 User,
 Mail,
 Phone,
 Building2,
 MapPin,
 FileText,
 MoreVertical,
 DollarSign,
 Calendar
} from 'lucide-react';

interface ContactCardProps {
 contact: ContactResponse;
 debtsCount?: number;
 totalDebtAmount?: number;
 onEdit?: (contact: ContactResponse) => void;
 onDelete?: (contactId: number) => void;
 onViewDebts?: (contactId: number) => void;
}

export const ContactCard: React.FC<ContactCardProps> = ({
 contact,
 debtsCount = 0,
 totalDebtAmount = 0,
 onEdit,
 onViewDebts
}) => {
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

 return (
 <Card className="bg-elevated border-[var(--border)] border transition-all duration-200 hover:shadow-lg hover:border-[var(--border)]">
 <CardHeader className="pb-3">
 <div className="flex items-start justify-between">
 <div className="flex items-center space-x-3">
 <div className="p-3 rounded-full bg-[var(--accent-dim)]">
 <User className="w-6 h-6 text-accent-base" />
 </div>
 <div>
 <CardTitle className="text-lg text-content">
 {contact.name}
 </CardTitle>
 {contact.company && (
 <div className="flex items-center space-x-1 mt-1">
 <Building2 className="w-3 h-3 text-content-secondary" />
 <span className="text-sm text-content-secondary">
 {contact.company}
 </span>
 </div>
 )}
 </div>
 </div>
 <Button
 variant="ghost"
 size="sm"
 className="text-content-secondary hover:text-content"
 >
 <MoreVertical className="w-4 h-4" />
 </Button>
 </div>
 </CardHeader>

 <CardContent className="space-y-4">
 {/* Contact Information */}
 <div className="space-y-3">
 {contact.email && (
 <div className="flex items-center space-x-3">
 <Mail className="w-4 h-4 text-content-secondary" />
 <a
 href={`mailto:${contact.email}`}
 className="text-sm text-accent-base hover:underline"
 >
 {contact.email}
 </a>
 </div>
 )}

 {contact.phone && (
 <div className="flex items-center space-x-3">
 <Phone className="w-4 h-4 text-content-secondary" />
 <a
 href={`tel:${contact.phone}`}
 className="text-sm text-accent-base hover:underline"
 >
 {contact.phone}
 </a>
 </div>
 )}

 {contact.address && (
 <div className="flex items-start space-x-3">
 <MapPin className="w-4 h-4 mt-0.5 text-content-secondary" />
 <span className="text-sm text-content-tertiary">
 {contact.address}
 </span>
 </div>
 )}
 </div>

 {/* Notes */}
 {contact.notes && (
 <div className="p-3 rounded-lg bg-[var(--accent-dim)]">
 <div className="flex items-start space-x-2">
 <FileText className="w-4 h-4 mt-0.5 text-content-secondary" />
 <div>
 <span className="text-xs font-medium text-content-secondary">
 Notes
 </span>
 <p className="text-sm mt-1 text-content-tertiary">
 {contact.notes}
 </p>
 </div>
 </div>
 </div>
 )}

 {/* Debt Information */}
 {debtsCount > 0 && (
 <div className="p-3 rounded-lg bg-[var(--accent-dim)] border-[var(--border)] border">
 <div className="flex items-center justify-between mb-2">
 <div className="flex items-center space-x-2">
 <DollarSign className="w-4 h-4 text-accent-base" />
 <span className="text-sm font-medium text-content-tertiary">
 Associated Debts
 </span>
 </div>
 <Badge variant="secondary" className="text-xs">
 {debtsCount} debt{debtsCount !== 1 ? 's' : ''}
 </Badge>
 </div>
 <p className="text-lg font-semibold text-content">
 {formatCurrency(totalDebtAmount)}
 </p>
 <p className="text-xs mt-1 text-content-secondary">
 Total debt amount
 </p>
 </div>
 )}

 {/* Created Date */}
 <div className="flex items-center space-x-2 pt-2 border-t border-[var(--border)]">
 <Calendar className="w-3 h-3 text-content-secondary" />
 <span className="text-xs text-content-secondary">
 Created {formatDate(contact.created_at)}
 </span>
 </div>

 {/* Action Buttons */}
 <div className="flex flex-wrap gap-2 pt-2">
 {debtsCount > 0 && (
 <Button
 size="sm"
 variant="secondary"
 onClick={() => onViewDebts?.(contact.id)}
 className="flex-1 min-w-[120px]"
 >
 <DollarSign className="w-4 h-4 mr-2" />
 View Debts
 </Button>
 )}
 <Button
 size="sm"
 variant="outline"
 onClick={() => onEdit?.(contact)}
 className="flex-1 min-w-[100px]"
 >
 Edit
 </Button>
 </div>
 </CardContent>
 </Card>
 );
};
