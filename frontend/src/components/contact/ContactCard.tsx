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
    <Card className="theme-surface theme-border border transition-all duration-200 hover:shadow-lg hover:theme-border">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-full theme-accent-light">
              <User className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-lg theme-text-primary">
                {contact.name}
              </CardTitle>
              {contact.company && (
                <div className="flex items-center space-x-1 mt-1">
                  <Building2 className="w-3 h-3 theme-text-secondary" />
                  <span className="text-sm theme-text-secondary">
                    {contact.company}
                  </span>
                </div>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="theme-text-secondary hover:theme-text-primary"
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
              <Mail className="w-4 h-4 theme-text-secondary" />
              <a
                href={`mailto:${contact.email}`}
                className="text-sm theme-accent hover:underline"
              >
                {contact.email}
              </a>
            </div>
          )}

          {contact.phone && (
            <div className="flex items-center space-x-3">
              <Phone className="w-4 h-4 theme-text-secondary" />
              <a
                href={`tel:${contact.phone}`}
                className="text-sm theme-accent hover:underline"
              >
                {contact.phone}
              </a>
            </div>
          )}

          {contact.address && (
            <div className="flex items-start space-x-3">
              <MapPin className="w-4 h-4 mt-0.5 theme-text-secondary" />
              <span className="text-sm theme-text-tertiary">
                {contact.address}
              </span>
            </div>
          )}
        </div>

        {/* Notes */}
        {contact.notes && (
          <div className="p-3 rounded-lg theme-accent-light">
            <div className="flex items-start space-x-2">
              <FileText className="w-4 h-4 mt-0.5 theme-text-secondary" />
              <div>
                <span className="text-xs font-medium theme-text-secondary">
                  Notes
                </span>
                <p className="text-sm mt-1 theme-text-tertiary">
                  {contact.notes}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Debt Information */}
        {debtsCount > 0 && (
          <div className="p-3 rounded-lg theme-accent-light theme-border border">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-medium theme-text-tertiary">
                  Associated Debts
                </span>
              </div>
              <Badge variant="secondary" className="text-xs">
                {debtsCount} debt{debtsCount !== 1 ? 's' : ''}
              </Badge>
            </div>
            <p className="text-lg font-semibold theme-text-primary">
              {formatCurrency(totalDebtAmount)}
            </p>
            <p className="text-xs mt-1 theme-text-secondary">
              Total debt amount
            </p>
          </div>
        )}

        {/* Created Date */}
        <div className="flex items-center space-x-2 pt-2 border-t theme-border">
          <Calendar className="w-3 h-3 theme-text-secondary" />
          <span className="text-xs theme-text-secondary">
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
