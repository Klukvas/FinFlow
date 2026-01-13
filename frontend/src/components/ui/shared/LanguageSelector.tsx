import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaGlobe, FaChevronDown } from 'react-icons/fa';

interface LanguageSelectorProps {
  compact?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ compact = false }) => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: 'en', name: t('language.english'), flag: '🇺🇸' },
    { code: 'ru', name: t('language.russian'), flag: '🇷🇺' },
    { code: 'uk', name: t('language.ukrainian'), flag: '🇺🇦' },
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
        className={`flex items-center ${compact ? 'space-x-1 px-2 py-2' : 'space-x-2 px-3 py-2'} text-sm font-medium bg-gray-800 hover:bg-gray-700 text-white rounded-lg theme-transition border border-gray-700 hover:border-gray-600 hover:shadow-lg`}
        title={t('language.select')}
        data-testid="language-selector-button"
      >
        <FaGlobe className="w-4 h-4 text-white" />
        <span className={compact ? 'text-base' : 'text-lg'}>{currentLanguage.flag}</span>
        {!compact && (
          <>
            <span className="hidden sm:inline text-white">{currentLanguage.name}</span>
            <FaChevronDown className={`w-3 h-3 transition-transform text-white ${isOpen ? 'rotate-180' : ''}`} />
          </>
        )}
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
            className="absolute right-0 mt-2 w-48 bg-gray-800 border-2 border-gray-700 shadow-xl rounded-lg py-1 z-20 backdrop-blur-sm"
            data-testid="language-selector-dropdown"
          >
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageChange(language.code)}
                className={`w-full flex items-center space-x-3 px-4 py-3 text-sm theme-transition rounded-md mx-1 ${
                  i18n.language === language.code
                    ? 'bg-gray-700 text-white border-l-4 border-l-blue-500'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                data-testid={`language-option-${language.code}`}
              >
                <span className="text-xl">{language.flag}</span>
                <span className="font-medium">{language.name}</span>
                {i18n.language === language.code && (
                  <span className="ml-auto text-green-400 font-bold">✓</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
