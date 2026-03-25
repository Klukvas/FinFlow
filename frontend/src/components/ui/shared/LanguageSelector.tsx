import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Globe, ChevronDown, Check } from "lucide-react";

interface LanguageSelectorProps {
  compact?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  compact = false,
}) => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: "en", name: t("language.english"), flag: "🇺🇸" },
    { code: "ru", name: t("language.russian"), flag: "🇷🇺" },
    { code: "uk", name: t("language.ukrainian"), flag: "🇺🇦" },
  ];

  const currentLanguage = languages.find(
    (lang) => lang.code === i18n.language,
  ) ||
    languages[0] || { code: "en", name: "English", flag: "🇺🇸" };

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
    setIsOpen(false);
  };

  return (
    <div className="relative" data-testid="language-selector">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1.5 text-sm font-medium rounded-[var(--radius-md)] bg-transparent border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)] transition-all duration-150 ${
          compact ? "p-2" : "px-3 py-2"
        }`}
        title={t("language.select")}
        data-testid="language-selector-button"
      >
        <Globe className="w-4 h-4" strokeWidth={1.5} />
        <span className={compact ? "text-base" : "text-base"}>
          {currentLanguage.flag}
        </span>
        {!compact && (
          <>
            <span className="hidden sm:inline text-[13px]">
              {currentLanguage.name}
            </span>
            <ChevronDown
              className={`w-3 h-3 transition-transform ${isOpen ? "rotate-180" : ""}`}
              strokeWidth={1.5}
            />
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
            className="absolute right-0 mt-2 w-48 bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-lg)] py-1 z-20"
            style={{ boxShadow: "var(--shadow-md)" }}
            data-testid="language-selector-dropdown"
          >
            {languages.map((language) => {
              const isActive = i18n.language === language.code;
              return (
                <button
                  key={language.code}
                  onClick={() => handleLanguageChange(language.code)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-[13px] transition-colors ${
                    isActive
                      ? "bg-[var(--accent-dim)] text-[var(--accent)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-raised)] hover:text-[var(--text-primary)]"
                  }`}
                  data-testid={`language-option-${language.code}`}
                >
                  <span className="text-lg">{language.flag}</span>
                  <span className="font-medium flex-1 text-left">{language.name}</span>
                  {isActive && (
                    <Check className="w-4 h-4 text-[var(--accent)]" strokeWidth={1.5} />
                  )}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
