import React from "react";
import { useTranslation } from "react-i18next";
import { ContactResponse } from "@/types/contact";
import { ContactCard } from "../contact/ContactCard";
import { Button } from "@/components/ui/shared/Button";
import { Card, CardContent } from "@/components/ui";
import { UserPlus, Users } from "lucide-react";

interface ContactsListProps {
 contacts: ContactResponse[];
 onEdit: (contact: ContactResponse) => void;
 onCreateClick: () => void;
}

export const ContactsList: React.FC<ContactsListProps> = ({
 contacts,
 onEdit,
 onCreateClick,
}) => {
 const { t } = useTranslation();

 if (contacts.length === 0) {
 return (
 <Card className="bg-elevated border-[var(--color-border)]">
 <CardContent className="p-12 text-center">
 <Users className="w-12 h-12 mx-auto mb-4 text-content-tertiary" />
 <h3 className="text-lg font-medium mb-2 text-content">
 {t("debtPage.emptyStates.noContactsTitle")}
 </h3>
 <p className="mb-6 text-content-secondary">
 {t("debtPage.emptyStates.noContactsDescription")}
 </p>
 <Button onClick={onCreateClick}>
 <UserPlus className="w-4 h-4 mr-2" />
 {t("debtPage.emptyStates.addFirstContact")}
 </Button>
 </CardContent>
 </Card>
 );
 }

 return (
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
 {contacts.map((contact) => (
 <ContactCard key={contact.id} contact={contact} onEdit={onEdit} />
 ))}
 </div>
 );
};
