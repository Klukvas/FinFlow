import React from 'react';
import { useTranslation } from 'react-i18next';
import { ContactResponse } from '@/types/contact';
import { ContactCard } from '../contact/ContactCard';
import { Button } from '@/components/ui/shared/Button';
import { Card, CardContent } from '@/components/ui';
import { UserPlus, Users } from 'lucide-react';

interface ContactsListProps {
  contacts: ContactResponse[];
  onEdit: (contact: ContactResponse) => void;
  onCreateClick: () => void;
  actualTheme: 'light' | 'dark';
}

export const ContactsList: React.FC<ContactsListProps> = ({
  contacts,
  onEdit,
  onCreateClick,
  actualTheme
}) => {
  const { t } = useTranslation();

  if (contacts.length === 0) {
    return (
      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-12 text-center">
          <Users className={`w-12 h-12 mx-auto mb-4 ${
            actualTheme === 'dark' ? 'text-gray-600' : 'text-gray-400'
          }`} />
          <h3 className={`text-lg font-medium mb-2 ${
            actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            {t('debtPage.emptyStates.noContactsTitle')}
          </h3>
          <p className={`mb-6 ${
            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            {t('debtPage.emptyStates.noContactsDescription')}
          </p>
          <Button onClick={onCreateClick}>
            <UserPlus className="w-4 h-4 mr-2" />
            {t('debtPage.emptyStates.addFirstContact')}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {contacts.map((contact) => (
        <ContactCard
          key={contact.id}
          contact={contact}
          onEdit={onEdit}
        />
      ))}
    </div>
  );
};

