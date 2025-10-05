import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaGlobe, FaChevronDown } from 'react-icons/fa';

export const LanguageSelector: React.FC = () => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: 'en', name: t('language.english'), flag: '🇺🇸' },
    { code: 'ru', name: t('language.russian'), flag: '🇷🇺' },
  ];

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0] || { code: 'en', name: 'English', flag: '🇺🇸' };

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
    setIsOpen(false);
  };

  return (
    <div className="relative" data-testid="language-selector">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 text-sm font-medium theme-text-secondary hover:theme-text-primary hover:theme-surface-hover rounded-lg theme-transition"
        title={t('language.select')}
        data-testid="language-selector-button"
      >
        <FaGlobe className="w-4 h-4" />
        <span>{currentLanguage.flag}</span>
        <span className="hidden sm:inline">{currentLanguage.name}</span>
        <FaChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
            data-testid="language-selector-backdrop"
          />
          
          {/* Dropdown */}
          <div
            className="absolute right-0 mt-2 w-48 theme-surface theme-border border theme-shadow rounded-lg py-1 z-20"
            data-testid="language-selector-dropdown"
          >
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageChange(language.code)}
                className={`w-full flex items-center space-x-3 px-4 py-2 text-sm theme-transition ${
                  i18n.language === language.code
                    ? 'theme-accent-light theme-accent'
                    : 'theme-text-secondary hover:theme-surface-hover hover:theme-text-primary'
                }`}
                data-testid={`language-option-${language.code}`}
              >
                <span className="text-lg">{language.flag}</span>
                <span>{language.name}</span>
                {i18n.language === language.code && (
                  <span className="ml-auto text-xs">✓</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
