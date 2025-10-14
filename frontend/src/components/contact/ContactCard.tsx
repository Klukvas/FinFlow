import React from 'react';
import { ContactResponse } from '@/types/contact';
import { useTheme } from '@/contexts/ThemeContext';
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

  return (
    <Card className={`transition-all duration-200 hover:shadow-lg ${
      actualTheme === 'dark' 
        ? 'bg-gray-800 border-gray-700 hover:border-gray-600' 
        : 'bg-white border-gray-200 hover:border-gray-300'
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-full ${
              actualTheme === 'dark' ? 'bg-blue-900/50' : 'bg-blue-100'
            }`}>
              <User className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <CardTitle className={`text-lg ${
                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {contact.name}
              </CardTitle>
              {contact.company && (
                <div className="flex items-center space-x-1 mt-1">
                  <Building2 className="w-3 h-3 text-gray-500" />
                  <span className={`text-sm ${
                    actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    {contact.company}
                  </span>
                </div>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className={`${actualTheme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700'}`}
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
              <Mail className={`w-4 h-4 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <a 
                href={`mailto:${contact.email}`}
                className={`text-sm hover:underline ${
                  actualTheme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'
                }`}
              >
                {contact.email}
              </a>
            </div>
          )}

          {contact.phone && (
            <div className="flex items-center space-x-3">
              <Phone className={`w-4 h-4 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <a 
                href={`tel:${contact.phone}`}
                className={`text-sm hover:underline ${
                  actualTheme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'
                }`}
              >
                {contact.phone}
              </a>
            </div>
          )}

          {contact.address && (
            <div className="flex items-start space-x-3">
              <MapPin className={`w-4 h-4 mt-0.5 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <span className={`text-sm ${
                actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {contact.address}
              </span>
            </div>
          )}
        </div>

        {/* Notes */}
        {contact.notes && (
          <div className={`p-3 rounded-lg ${
            actualTheme === 'dark' ? 'bg-gray-700/50' : 'bg-gray-50'
          }`}>
            <div className="flex items-start space-x-2">
              <FileText className={`w-4 h-4 mt-0.5 ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <div>
                <span className={`text-xs font-medium ${
                  actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Notes
                </span>
                <p className={`text-sm mt-1 ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  {contact.notes}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Debt Information */}
        {debtsCount > 0 && (
          <div className={`p-3 rounded-lg border ${
            actualTheme === 'dark' ? 'bg-gray-700/30 border-gray-600' : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-blue-500" />
                <span className={`text-sm font-medium ${
                  actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Associated Debts
                </span>
              </div>
              <Badge variant="secondary" className="text-xs">
                {debtsCount} debt{debtsCount !== 1 ? 's' : ''}
              </Badge>
            </div>
            <p className={`text-lg font-semibold ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {formatCurrency(totalDebtAmount)}
            </p>
            <p className={`text-xs mt-1 ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Total debt amount
            </p>
          </div>
        )}

        {/* Created Date */}
        <div className="flex items-center space-x-2 pt-2 border-t border-gray-200 dark:border-gray-600">
          <Calendar className={`w-3 h-3 ${
            actualTheme === 'dark' ? 'text-gray-500' : 'text-gray-400'
          }`} />
          <span className={`text-xs ${
            actualTheme === 'dark' ? 'text-gray-500' : 'text-gray-400'
          }`}>
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
