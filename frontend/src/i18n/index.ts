import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uk from "./locales/uk.json";

const resources = {
  en: {
    translation: en,
  },
  ru: {
    translation: ru,
  },
  uk: {
    translation: uk,
  },
};

// Sync <html lang> attribute with current language
const updateHtmlLang = (lng: string) => {
  document.documentElement.lang = lng;
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    debug: false,

    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
    },

    interpolation: {
      escapeValue: false,
    },
  })
  .then(() => {
    if (i18n.language) {
      updateHtmlLang(i18n.language);
    }
  });

i18n.on("languageChanged", updateHtmlLang);

export default i18n;
