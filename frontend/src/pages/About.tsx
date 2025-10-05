import React from 'react';
import { useTranslation } from 'react-i18next';

export const About: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold theme-text-primary mb-8 text-center">
          {t('aboutPage.title')}
        </h1>
        
        <div className="prose prose-lg max-w-none theme-text-primary">
          <p className="text-xl theme-text-secondary mb-6">
            {t('aboutPage.intro')}
          </p>
          
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            {t('aboutPage.mission.title')}
          </h2>
          <p className="theme-text-secondary mb-6">
            {t('aboutPage.mission.description')}
          </p>
          
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            {t('aboutPage.offerings.title')}
          </h2>
          <ul className="theme-text-secondary mb-6 space-y-2">
            {t('aboutPage.offerings.items', { returnObjects: true }).map((item: string, index: number) => (
              <li key={index}>• {item}</li>
            ))}
          </ul>
          
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            {t('aboutPage.team.title')}
          </h2>
          <p className="theme-text-secondary">
            {t('aboutPage.team.description')}
          </p>
        </div>
      </div>
    </div>
  );
};
