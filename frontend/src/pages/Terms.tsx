import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
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
      <div className="min-h-screen bg-surface">
        <div className="max-w-4xl mx-auto px-6 py-12">
          {/* Back link */}
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-content-secondary hover:text-content transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            {t("termsPage.backToHome")}
          </Link>

          {/* Header */}
          <div className="mb-12">
            <h1 className="text-3xl md:text-4xl font-bold text-content mb-4">
              {t("termsPage.title")}
            </h1>
            <p className="text-content-secondary">
              {t("termsPage.lastUpdated")}: {t("termsPage.updateDate")}
            </p>
          </div>

          {/* Introduction */}
          <div className="bg-elevated border-[var(--border)] border rounded-xl p-6 mb-8">
            <p className="text-content-secondary leading-relaxed">
              {t("termsPage.intro")}
            </p>
            <p className="text-content-secondary leading-relaxed mt-4">
              {t("termsPage.acceptance")}
            </p>
          </div>

          {/* Sections */}
          <div className="space-y-8">
            {sections.map((section, index) => (
              <div
                key={index}
                className="bg-elevated border-[var(--border)] border rounded-xl p-6"
              >
                <h2 className="text-xl font-semibold text-content mb-4 flex items-center gap-3">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--accent-dim)] text-accent-base text-sm font-bold">
                    {index + 1}
                  </span>
                  {section.title}
                </h2>
                <div className="space-y-3 ml-11">
                  {section.content.map((item, itemIndex) => (
                    <p
                      key={itemIndex}
                      className="text-content-secondary leading-relaxed"
                    >
                      {index === 0 || index === 7 ? (
                        // Provider and Contact sections - no bullet points
                        item
                      ) : (
                        // Other sections - with bullet points
                        <span className="flex gap-2">
                          <span className="text-accent-base">•</span>
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
          <div className="mt-12 pt-8 border-[var(--border)] border-t text-center">
            <p className="text-content-tertiary text-sm">
              {t("termsPage.footer")}
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Terms;
