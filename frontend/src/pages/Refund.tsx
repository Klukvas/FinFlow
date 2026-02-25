import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";

export const Refund: React.FC = () => {
  const { t } = useTranslation();

  const sections = [
    {
      title: t("refundPage.sections.moneyBack.title"),
      content: [
        t("refundPage.sections.moneyBack.item1"),
        t("refundPage.sections.moneyBack.item2"),
        t("refundPage.sections.moneyBack.item3"),
      ],
    },
    {
      title: t("refundPage.sections.cancellation.title"),
      content: [
        t("refundPage.sections.cancellation.item1"),
        t("refundPage.sections.cancellation.item2"),
        t("refundPage.sections.cancellation.item3"),
      ],
    },
    {
      title: t("refundPage.sections.howToRequest.title"),
      content: [
        t("refundPage.sections.howToRequest.item1"),
        t("refundPage.sections.howToRequest.item2"),
      ],
    },
    {
      title: t("refundPage.sections.contact.title"),
      content: [t("refundPage.sections.contact.item1")],
    },
  ];

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Back link */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 theme-text-secondary hover:theme-text-primary theme-transition mb-8"
        >
          <FaArrowLeft className="w-4 h-4" />
          {t("refundPage.backToHome")}
        </Link>

        {/* Header */}
        <div className="mb-12">
          <h1 className="text-3xl md:text-4xl font-bold theme-text-primary mb-4">
            {t("refundPage.title")}
          </h1>
          <p className="theme-text-secondary">
            {t("refundPage.lastUpdated")}: {t("refundPage.updateDate")}
          </p>
        </div>

        {/* Introduction */}
        <div className="theme-surface theme-border border rounded-xl p-6 mb-8">
          <p className="theme-text-secondary leading-relaxed">
            {t("refundPage.intro")}
          </p>
        </div>

        {/* Sections */}
        <div className="space-y-8">
          {sections.map((section, index) => (
            <div
              key={index}
              className="theme-surface theme-border border rounded-xl p-6"
            >
              <h2 className="text-xl font-semibold theme-text-primary mb-4 flex items-center gap-3">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm font-bold">
                  {index + 1}
                </span>
                {section.title}
              </h2>
              <div className="space-y-3 ml-11">
                {section.content.map((item, itemIndex) => (
                  <p
                    key={itemIndex}
                    className="theme-text-secondary leading-relaxed"
                  >
                    {index === 3 ? (
                      // Contact section - no bullet points
                      item
                    ) : (
                      // Other sections - with bullet points
                      <span className="flex gap-2">
                        <span className="text-blue-500">•</span>
                        {item}
                      </span>
                    )}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 theme-border border-t text-center">
          <p className="theme-text-tertiary text-sm">
            {t("refundPage.footer")}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Refund;
