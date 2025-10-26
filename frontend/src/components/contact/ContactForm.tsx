import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ContactCreate, ContactUpdate } from '@/types/contact';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/shared/Button';
import { Input } from '@/components/ui/forms/Input';
import { Label } from '@/components/ui/forms/Label';
import { Textarea } from '@/components/ui/forms/Textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/shared/Card';
import { User, Mail, Phone, Building2, MapPin, FileText } from 'lucide-react';

interface ContactFormProps {
  initialData?: Partial<ContactCreate>;
  onSubmit: (data: ContactCreate | ContactUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
  showCard?: boolean;
}

export const ContactForm: React.FC<ContactFormProps> = ({
  initialData = {},
  onSubmit,
  onCancel,
  isLoading = false,
  mode,
  showCard = true
}) => {
  const { t } = useTranslation();
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
      newErrors.name = t('debtPage.form.errors.contactNameRequired');
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = t('debtPage.form.errors.validEmail');
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

  const formContent = (
    <>
      {showCard && (
        <div className="mb-4">
          <h2 className={`text-lg font-semibold ${
            actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            {mode === 'create' ? t('debtPage.contacts.form.createTitle') : t('debtPage.contacts.form.editTitle')}
          </h2>
        </div>
      )}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              <User className="w-4 h-4 inline mr-2" />
              {t('debtPage.contacts.form.name')} *
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder={t('debtPage.contacts.form.namePlaceholder')}
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
                {t('debtPage.contacts.form.email')}
              </Label>
              <Input
                id="email"
                type="email"
                value={formData.email || ''}
                onChange={(e) => handleInputChange('email', e.target.value || null)}
                placeholder={t('debtPage.contacts.form.emailPlaceholder')}
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
                {t('debtPage.contacts.form.phone')}
              </Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone || ''}
                onChange={(e) => handleInputChange('phone', e.target.value || null)}
                placeholder={t('debtPage.contacts.form.phonePlaceholder')}
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
              {t('debtPage.contacts.form.company')}
            </Label>
            <Input
              id="company"
              value={formData.company || ''}
              onChange={(e) => handleInputChange('company', e.target.value || null)}
              placeholder={t('debtPage.contacts.form.companyPlaceholder')}
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
              {t('debtPage.contacts.form.address')}
            </Label>
            <Textarea
              id="address"
              value={formData.address || ''}
              onChange={(e) => handleInputChange('address', e.target.value || null)}
              placeholder={t('debtPage.contacts.form.addressPlaceholder')}
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
              {t('debtPage.contacts.form.notes')}
            </Label>
            <Textarea
              id="notes"
              value={formData.notes || ''}
              onChange={(e) => handleInputChange('notes', e.target.value || null)}
              placeholder={t('debtPage.contacts.form.notesPlaceholder')}
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
              {isLoading ? t('debtPage.contacts.form.saving') : mode === 'create' ? t('debtPage.contacts.form.create') : t('debtPage.contacts.form.update')}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1"
            >
              {t('common.cancel')}
            </Button>
          </div>
        </form>
    </>
  );

  if (!showCard) {
    return formContent;
  }

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
          <span>{mode === 'create' ? t('debtPage.contacts.form.createTitle') : t('debtPage.contacts.form.editTitle')}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {formContent}
      </CardContent>
    </Card>
  );
};
