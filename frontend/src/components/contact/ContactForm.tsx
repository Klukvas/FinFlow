import React, { useState } from 'react';
import { ContactCreate, ContactUpdate } from '@/types/contact';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/forms/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { User, Mail, Phone, Building2, MapPin, FileText } from 'lucide-react';

interface ContactFormProps {
  initialData?: Partial<ContactCreate>;
  onSubmit: (data: ContactCreate | ContactUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
}

export const ContactForm: React.FC<ContactFormProps> = ({
  initialData = {},
  onSubmit,
  onCancel,
  isLoading = false,
  mode
}) => {
  const { actualTheme } = useTheme();
  
  const [formData, setFormData] = useState<ContactCreate>({
    name: initialData.name || '',
    email: initialData.email || null,
    phone: initialData.phone || null,
    company: initialData.company || null,
    address: initialData.address || null,
    notes: initialData.notes || null
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Contact name is required';
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      // Convert empty strings to null for optional fields
      const submitData = {
        ...formData,
        email: formData.email?.trim() || null,
        phone: formData.phone?.trim() || null,
        company: formData.company?.trim() || null,
        address: formData.address?.trim() || null,
        notes: formData.notes?.trim() || null
      };
      onSubmit(submitData);
    }
  };

  const handleInputChange = (field: keyof ContactCreate, value: string | null) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Card className={`max-w-2xl mx-auto ${
      actualTheme === 'dark' 
        ? 'bg-gray-800 border-gray-700' 
        : 'bg-white border-gray-200'
    }`}>
      <CardHeader>
        <CardTitle className={`flex items-center space-x-2 ${
          actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          <User className="w-5 h-5" />
          <span>{mode === 'create' ? 'Create New Contact' : 'Edit Contact'}</span>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              <User className="w-4 h-4 inline mr-2" />
              Contact Name *
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., John Smith, Bank of America"
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } ${errors.name ? 'border-red-500' : ''}`}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          {/* Email and Phone */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="email" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                <Mail className="w-4 h-4 inline mr-2" />
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                value={formData.email || ''}
                onChange={(e) => handleInputChange('email', e.target.value || null)}
                placeholder="john@example.com"
                className={`${
                  actualTheme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                } ${errors.email ? 'border-red-500' : ''}`}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                <Phone className="w-4 h-4 inline mr-2" />
                Phone Number
              </Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone || ''}
                onChange={(e) => handleInputChange('phone', e.target.value || null)}
                placeholder="+1 (555) 123-4567"
                className={`${
                  actualTheme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
          </div>

          {/* Company */}
          <div className="space-y-2">
            <Label htmlFor="company" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              <Building2 className="w-4 h-4 inline mr-2" />
              Company/Organization
            </Label>
            <Input
              id="company"
              value={formData.company || ''}
              onChange={(e) => handleInputChange('company', e.target.value || null)}
              placeholder="e.g., Bank of America, Credit Union"
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
          </div>

          {/* Address */}
          <div className="space-y-2">
            <Label htmlFor="address" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              <MapPin className="w-4 h-4 inline mr-2" />
              Address
            </Label>
            <Textarea
              id="address"
              value={formData.address || ''}
              onChange={(e) => handleInputChange('address', e.target.value || null)}
              placeholder="123 Main St, City, State 12345"
              rows={3}
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              <FileText className="w-4 h-4 inline mr-2" />
              Notes
            </Label>
            <Textarea
              id="notes"
              value={formData.notes || ''}
              onChange={(e) => handleInputChange('notes', e.target.value || null)}
              placeholder="Additional information about this contact..."
              rows={4}
              className={`${
                actualTheme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-6">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Saving...' : mode === 'create' ? 'Create Contact' : 'Update Contact'}
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
    </Card>
  );
};
