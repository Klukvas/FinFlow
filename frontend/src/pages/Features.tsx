import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { SEOHead, SEOConfigs } from "@/components/seo/SEOHead";
import { FeatureGroup } from "@/components/ui/shared/FeatureGroup";

import {
  FaWallet,
  FaExchangeAlt,
  FaGlobe,
  FaSitemap,
  FaRedo,
  FaClock,
  FaCreditCard,
  FaSyncAlt,
  FaUsers,
  FaUserShield,
  FaEnvelopeOpenText,
  FaLock,
  FaBullseye,
  FaBalanceScale,
  FaChartLine,
  FaFileInvoice,
  FaRocket,
  FaKey,
  FaShieldAlt,
  FaServer,
  FaChevronDown,
} from "react-icons/fa";

export const Features: React.FC = () => {
  const { t } = useTranslation();
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (id: string) => {
    setExpandedSection((prev) => (prev === id ? null : id));
  };

  const financialCoreItems = [
    {
      icon: FaWallet,
      title: t("featuresPage.sections.core.accounts.title"),
      description: t("featuresPage.sections.core.accounts.desc"),
    },
    {
      icon: FaExchangeAlt,
      title: t("featuresPage.sections.core.transactions.title"),
      description: t("featuresPage.sections.core.transactions.desc"),
    },
    {
      icon: FaGlobe,
      title: t("featuresPage.sections.core.currency.title"),
      description: t("featuresPage.sections.core.currency.desc"),
    },
    {
      icon: FaSitemap,
      title: t("featuresPage.sections.core.categories.title"),
      description: t("featuresPage.sections.core.categories.desc"),
    },
  ];

  const automationItems = [
    {
      icon: FaRedo,
      title: t("featuresPage.sections.automation.recurring.title"),
      description: t("featuresPage.sections.automation.recurring.desc"),
    },
    {
      icon: FaClock,
      title: t("featuresPage.sections.automation.scheduler.title"),
      description: t("featuresPage.sections.automation.scheduler.desc"),
    },
    {
      icon: FaCreditCard,
      title: t("featuresPage.sections.automation.subscriptions.title"),
      description: t("featuresPage.sections.automation.subscriptions.desc"),
    },
    {
      icon: FaSyncAlt,
      title: t("featuresPage.sections.automation.balance.title"),
      description: t("featuresPage.sections.automation.balance.desc"),
    },
  ];

  const workspaceItems = [
    {
      icon: FaUserShield,
      title: t("featuresPage.sections.workspace.personal.title"),
      description: t("featuresPage.sections.workspace.personal.desc"),
    },
    {
      icon: FaUsers,
      title: t("featuresPage.sections.workspace.shared.title"),
      description: t("featuresPage.sections.workspace.shared.desc"),
    },
    {
      icon: FaKey,
      title: t("featuresPage.sections.workspace.roles.title"),
      description: t("featuresPage.sections.workspace.roles.desc"),
    },
    {
      icon: FaEnvelopeOpenText,
      title: t("featuresPage.sections.workspace.invites.title"),
      description: t("featuresPage.sections.workspace.invites.desc"),
    },
    {
      icon: FaLock,
      title: t("featuresPage.sections.workspace.isolation.title"),
      description: t("featuresPage.sections.workspace.isolation.desc"),
    },
  ];

  const intelligenceItems = [
    {
      icon: FaBullseye,
      title: t("featuresPage.sections.intelligence.goals.title"),
      description: t("featuresPage.sections.intelligence.goals.desc"),
    },
    {
      icon: FaBalanceScale,
      title: t("featuresPage.sections.intelligence.debts.title"),
      description: t("featuresPage.sections.intelligence.debts.desc"),
    },
    {
      icon: FaChartLine,
      title: t("featuresPage.sections.intelligence.progress.title"),
      description: t("featuresPage.sections.intelligence.progress.desc"),
    },
    {
      icon: FaFileInvoice,
      title: t("featuresPage.sections.intelligence.pdf.title"),
      description: t("featuresPage.sections.intelligence.pdf.desc"),
    },
  ];

  const platformItems = [
    {
      icon: FaRocket,
      title: t("featuresPage.sections.platform.plans.title"),
      description: t("featuresPage.sections.platform.plans.desc"),
    },
    {
      icon: FaShieldAlt,
      title: t("featuresPage.sections.platform.entitlements.title"),
      description: t("featuresPage.sections.platform.entitlements.desc"),
    },
    {
      icon: FaCreditCard,
      title: t("featuresPage.sections.platform.payments.title"),
      description: t("featuresPage.sections.platform.payments.desc"),
    },
    {
      icon: FaServer,
      title: t("featuresPage.sections.platform.renewal.title"),
      description: t("featuresPage.sections.platform.renewal.desc"),
    },
  ];

  const technicalDetails: Record<string, string[]> = {
    core: [
      t("featuresPage.technical.core.0"),
      t("featuresPage.technical.core.1"),
      t("featuresPage.technical.core.2"),
    ],
    automation: [
      t("featuresPage.technical.automation.0"),
      t("featuresPage.technical.automation.1"),
      t("featuresPage.technical.automation.2"),
    ],
    workspace: [
      t("featuresPage.technical.workspace.0"),
      t("featuresPage.technical.workspace.1"),
      t("featuresPage.technical.workspace.2"),
    ],
    intelligence: [
      t("featuresPage.technical.intelligence.0"),
      t("featuresPage.technical.intelligence.1"),
      t("featuresPage.technical.intelligence.2"),
    ],
    platform: [
      t("featuresPage.technical.platform.0"),
      t("featuresPage.technical.platform.1"),
      t("featuresPage.technical.platform.2"),
    ],
  };

  const sections = [
    {
      id: "core",
      label: t("featuresPage.sections.core.label"),
      title: t("featuresPage.sections.core.title"),
      description: t("featuresPage.sections.core.description"),
      items: financialCoreItems,
      columns: 2 as const,
    },
    {
      id: "automation",
      label: t("featuresPage.sections.automation.label"),
      title: t("featuresPage.sections.automation.title"),
      description: t("featuresPage.sections.automation.description"),
      items: automationItems,
      columns: 2 as const,
    },
    {
      id: "workspace",
      label: t("featuresPage.sections.workspace.label"),
      title: t("featuresPage.sections.workspace.title"),
      description: t("featuresPage.sections.workspace.description"),
      items: workspaceItems,
      columns: 3 as const,
    },
    {
      id: "intelligence",
      label: t("featuresPage.sections.intelligence.label"),
      title: t("featuresPage.sections.intelligence.title"),
      description: t("featuresPage.sections.intelligence.description"),
      items: intelligenceItems,
      columns: 2 as const,
    },
    {
      id: "platform",
      label: t("featuresPage.sections.platform.label"),
      title: t("featuresPage.sections.platform.title"),
      description: t("featuresPage.sections.platform.description"),
      items: platformItems,
      columns: 2 as const,
    },
  ];

  return (
    <>
      <SEOHead {...SEOConfigs.features} url="https://finflow.ltd/features" />
      <div className="py-20 lg:py-28 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Hero */}
          <div className="mb-20 lg:mb-28">
            <span className="inline-block text-xs font-semibold uppercase tracking-widest theme-accent mb-4">
              {t("featuresPage.hero.label")}
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold theme-text-primary mb-5 leading-tight">
              {t("featuresPage.hero.title")}
            </h1>
            <p className="text-lg theme-text-secondary max-w-2xl leading-relaxed">
              {t("featuresPage.hero.subtitle")}
            </p>
          </div>

          {/* Feature Sections */}
          <div className="space-y-20 lg:space-y-28">
            {sections.map((section) => (
              <div key={section.id}>
                {/* Workspace section gets a highlighted wrapper */}
                {section.id === "workspace" ? (
                  <div className="rounded-2xl border theme-border p-6 sm:p-10 theme-bg-secondary">
                    <FeatureGroup
                      label={section.label}
                      title={section.title}
                      description={section.description}
                      items={section.items}
                      columns={section.columns}
                    />

                    {/* Technical details toggle */}
                    <TechnicalDetails
                      id={section.id}
                      details={technicalDetails[section.id] ?? []}
                      expanded={expandedSection === section.id}
                      onToggle={() => toggleSection(section.id)}
                      label={t("featuresPage.technicalToggle")}
                    />
                  </div>
                ) : (
                  <>
                    <FeatureGroup
                      label={section.label}
                      title={section.title}
                      description={section.description}
                      items={section.items}
                      columns={section.columns}
                    />

                    {/* Technical details toggle */}
                    <TechnicalDetails
                      id={section.id}
                      details={technicalDetails[section.id] ?? []}
                      expanded={expandedSection === section.id}
                      onToggle={() => toggleSection(section.id)}
                      label={t("featuresPage.technicalToggle")}
                    />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};

/* ── Technical Details Collapsible ── */

interface TechnicalDetailsProps {
  id: string;
  details: string[];
  expanded: boolean;
  onToggle: () => void;
  label: string;
}

const TechnicalDetails: React.FC<TechnicalDetailsProps> = ({
  id,
  details,
  expanded,
  onToggle,
  label,
}) => {
  return (
    <div className="mt-6">
      <button
        onClick={onToggle}
        className="flex items-center gap-2 text-xs font-medium theme-text-tertiary hover:theme-text-secondary theme-transition"
        data-testid={`technical-toggle-${id}`}
      >
        <FaChevronDown
          className={`w-3 h-3 theme-transition ${expanded ? "rotate-180" : ""}`}
        />
        {label}
      </button>

      {expanded && (
        <ul className="mt-3 space-y-2 pl-5">
          {details.map((detail, i) => (
            <li
              key={i}
              className="text-xs theme-text-tertiary flex items-start gap-2"
            >
              <span className="w-1 h-1 rounded-full bg-[var(--color-accent)] mt-1.5 flex-shrink-0" />
              {detail}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
