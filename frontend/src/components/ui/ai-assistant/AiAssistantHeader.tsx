import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaRobot } from 'react-icons/fa';

export const AiAssistantHeader: React.FC = () => {
 const { t } = useTranslation();

 return (
 <div className="mb-8">
 <div className="flex items-center gap-3 mb-2">
 <div className="w-10 h-10 rounded-lg bg-[var(--color-accent-light)] flex items-center justify-center">
 <FaRobot className="w-5 h-5 text-accent-base" />
 </div>
 <div>
 <h1 className="text-2xl font-bold text-content">
 {t('aiAssistant.title')}
 </h1>
 <p className="text-sm text-content-secondary">
 {t('aiAssistant.subtitle')}
 </p>
 </div>
 </div>
 </div>
 );
};
