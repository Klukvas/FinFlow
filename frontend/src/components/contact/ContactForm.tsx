import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ContactCreate, ContactUpdate } from '@/types/contact';
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
 <h2 className="text-lg font-semibold text-content">
 {mode === 'create' ? t('debtPage.contacts.form.createTitle') : t('debtPage.contacts.form.editTitle')}
 </h2>
 </div>
 )}
 <form onSubmit={handleSubmit} className="space-y-6">
 {/* Contact Name */}
 <div className="space-y-2">
 <Label htmlFor="name" className="text-content-secondary">
 <User className="w-4 h-4 inline mr-2" />
 {t('debtPage.contacts.form.name')} *
 </Label>
 <Input
 id="name"
 value={formData.name}
 onChange={(e) => handleInputChange('name', e.target.value)}
 placeholder={t('debtPage.contacts.form.namePlaceholder')}
 className={`bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary ${errors.name ? 'border-danger-base' : ''}`}
 />
 {errors.name && (
 <p className="text-sm text-danger-base">{errors.name}</p>
 )}
 </div>

 {/* Email and Phone */}
 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
 <div className="space-y-2">
 <Label htmlFor="email" className="text-content-secondary">
 <Mail className="w-4 h-4 inline mr-2" />
 {t('debtPage.contacts.form.email')}
 </Label>
 <Input
 id="email"
 type="email"
 value={formData.email || ''}
 onChange={(e) => handleInputChange('email', e.target.value || null)}
 placeholder={t('debtPage.contacts.form.emailPlaceholder')}
 className={`bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary ${errors.email ? 'border-danger-base' : ''}`}
 />
 {errors.email && (
 <p className="text-sm text-danger-base">{errors.email}</p>
 )}
 </div>

 <div className="space-y-2">
 <Label htmlFor="phone" className="text-content-secondary">
 <Phone className="w-4 h-4 inline mr-2" />
 {t('debtPage.contacts.form.phone')}
 </Label>
 <Input
 id="phone"
 type="tel"
 value={formData.phone || ''}
 onChange={(e) => handleInputChange('phone', e.target.value || null)}
 placeholder={t('debtPage.contacts.form.phonePlaceholder')}
 className="bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary"
 />
 </div>
 </div>

 {/* Company */}
 <div className="space-y-2">
 <Label htmlFor="company" className="text-content-secondary">
 <Building2 className="w-4 h-4 inline mr-2" />
 {t('debtPage.contacts.form.company')}
 </Label>
 <Input
 id="company"
 value={formData.company || ''}
 onChange={(e) => handleInputChange('company', e.target.value || null)}
 placeholder={t('debtPage.contacts.form.companyPlaceholder')}
 className="bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary"
 />
 </div>

 {/* Address */}
 <div className="space-y-2">
 <Label htmlFor="address" className="text-content-secondary">
 <MapPin className="w-4 h-4 inline mr-2" />
 {t('debtPage.contacts.form.address')}
 </Label>
 <Textarea
 id="address"
 value={formData.address || ''}
 onChange={(e) => handleInputChange('address', e.target.value || null)}
 placeholder={t('debtPage.contacts.form.addressPlaceholder')}
 rows={3}
 className="bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary"
 />
 </div>

 {/* Notes */}
 <div className="space-y-2">
 <Label htmlFor="notes" className="text-content-secondary">
 <FileText className="w-4 h-4 inline mr-2" />
 {t('debtPage.contacts.form.notes')}
 </Label>
 <Textarea
 id="notes"
 value={formData.notes || ''}
 onChange={(e) => handleInputChange('notes', e.target.value || null)}
 placeholder={t('debtPage.contacts.form.notesPlaceholder')}
 rows={4}
 className="bg-elevated border-[var(--color-border)] border text-content placeholder:text-content-tertiary"
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
 <Card className="max-w-2xl mx-auto bg-elevated border-[var(--color-border)] border">
 <CardHeader>
 <CardTitle className="flex items-center space-x-2 text-content">
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
