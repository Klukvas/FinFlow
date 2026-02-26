import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";
import { SEOHead, SEOConfigs } from "@/components/seo/SEOHead";

export const Terms: React.FC = () => {
  const { t } = useTranslation();

  const sections = [
    {
      title: t("termsPage.sections.provider.title"),
      content: [
        t("termsPage.sections.provider.fop"),
        t("termsPage.sections.provider.tax"),
        t("termsPage.sections.provider.country"),
      ],
    },
    {
      title: t("termsPage.sections.services.title"),
      content: [
        t("termsPage.sections.services.item1"),
        t("termsPage.sections.services.item2"),
        t("termsPage.sections.services.item3"),
      ],
    },
    {
      title: t("termsPage.sections.trial.title"),
      content: [
        t("termsPage.sections.trial.item1"),
        t("termsPage.sections.trial.item2"),
        t("termsPage.sections.trial.item3"),
      ],
    },
    {
      title: t("termsPage.sections.subscription.title"),
      content: [
        t("termsPage.sections.subscription.item1"),
        t("termsPage.sections.subscription.item2"),
        t("termsPage.sections.subscription.item3"),
        t("termsPage.sections.subscription.item4"),
        t("termsPage.sections.subscription.item5"),
      ],
    },
    {
      title: t("termsPage.sections.refund.title"),
      content: [
        t("termsPage.sections.refund.item1"),
        t("termsPage.sections.refund.item2"),
        t("termsPage.sections.refund.item3"),
      ],
    },
    {
      title: t("termsPage.sections.liability.title"),
      content: [
        t("termsPage.sections.liability.item1"),
        t("termsPage.sections.liability.item2"),
        t("termsPage.sections.liability.item3"),
      ],
    },
    {
      title: t("termsPage.sections.law.title"),
      content: [t("termsPage.sections.law.item1")],
    },
    {
      title: t("termsPage.sections.contact.title"),
      content: [t("termsPage.sections.contact.item1")],
    },
  ];

  return (
    <>
      <SEOHead {...SEOConfigs.terms} />
      <div className="min-h-screen theme-bg">
        <div className="max-w-4xl mx-auto px-6 py-12">
          {/* Back link */}
          <Link
            to="/"
            className="inline-flex items-center gap-2 theme-text-secondary hover:theme-text-primary theme-transition mb-8"
          >
            <FaArrowLeft className="w-4 h-4" />
            {t("termsPage.backToHome")}
          </Link>

          {/* Header */}
          <div className="mb-12">
            <h1 className="text-3xl md:text-4xl font-bold theme-text-primary mb-4">
              {t("termsPage.title")}
            </h1>
            <p className="theme-text-secondary">
              {t("termsPage.lastUpdated")}: {t("termsPage.updateDate")}
            </p>
          </div>

          {/* Introduction */}
          <div className="theme-surface theme-border border rounded-xl p-6 mb-8">
            <p className="theme-text-secondary leading-relaxed">
              {t("termsPage.intro")}
            </p>
            <p className="theme-text-secondary leading-relaxed mt-4">
              {t("termsPage.acceptance")}
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
                      {index === 0 || index === 7 ? (
                        // Provider and Contact sections - no bullet points
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
              {t("termsPage.footer")}
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Terms;
