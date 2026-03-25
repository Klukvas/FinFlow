import React from "react";
import {
  Banknote,
  ArrowLeftRight,
  DollarSign,
  Clock,
  CalendarDays,
  CreditCard,
  Flag,
  FileDown,
  BarChart3,
  ShieldCheck,
  Server,
  Users,
  Lock,
  Building2,
  ArrowRight,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/shared/Button";
import { useModal } from "@/contexts/ModalContext";
import { SEOHead, SEOConfigs } from "@/components/seo/SEOHead";

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const { openRegisterModal } = useModal();

  const featureGroups = [
    {
      titleKey: "homepage.features.groups.core.title",
      items: [
        {
          icon: Banknote,
          titleKey: "homepage.features.groups.core.accounts.title",
          descKey: "homepage.features.groups.core.accounts.desc",
        },
        {
          icon: ArrowLeftRight,
          titleKey: "homepage.features.groups.core.transactions.title",
          descKey: "homepage.features.groups.core.transactions.desc",
        },
        {
          icon: DollarSign,
          titleKey: "homepage.features.groups.core.currency.title",
          descKey: "homepage.features.groups.core.currency.desc",
        },
      ],
    },
    {
      titleKey: "homepage.features.groups.automation.title",
      items: [
        {
          icon: Clock,
          titleKey: "homepage.features.groups.automation.recurring.title",
          descKey: "homepage.features.groups.automation.recurring.desc",
        },
        {
          icon: CalendarDays,
          titleKey: "homepage.features.groups.automation.scheduler.title",
          descKey: "homepage.features.groups.automation.scheduler.desc",
        },
        {
          icon: CreditCard,
          titleKey: "homepage.features.groups.automation.subscriptions.title",
          descKey: "homepage.features.groups.automation.subscriptions.desc",
        },
      ],
    },
    {
      titleKey: "homepage.features.groups.intelligence.title",
      items: [
        {
          icon: Flag,
          titleKey: "homepage.features.groups.intelligence.goals.title",
          descKey: "homepage.features.groups.intelligence.goals.desc",
        },
        {
          icon: BarChart3,
          titleKey: "homepage.features.groups.intelligence.debts.title",
          descKey: "homepage.features.groups.intelligence.debts.desc",
        },
        {
          icon: FileDown,
          titleKey: "homepage.features.groups.intelligence.pdf.title",
          descKey: "homepage.features.groups.intelligence.pdf.desc",
        },
      ],
    },
  ];

  const trustBadges = [
    { icon: ShieldCheck, labelKey: "homepage.trust.badges.secure" },
    {
      icon: Server,
      labelKey: "homepage.trust.badges.architecture",
    },
    { icon: CreditCard, labelKey: "homepage.trust.badges.saas" },
    { icon: Lock, labelKey: "homepage.trust.badges.jwt" },
    { icon: FileDown, labelKey: "homepage.trust.badges.pdf" },
  ];

  const plans = [
    {
      nameKey: "homepage.plans.basic.name",
      priceKey: "homepage.plans.basic.price",
      highlightKey: "homepage.plans.basic.highlight",
    },
    {
      nameKey: "homepage.plans.professional.name",
      priceKey: "homepage.plans.professional.price",
      highlightKey: "homepage.plans.professional.highlight",
      featured: true,
    },
    {
      nameKey: "homepage.plans.enterprise.name",
      priceKey: "homepage.plans.enterprise.price",
      highlightKey: "homepage.plans.enterprise.highlight",
    },
  ];

  return (
    <>
      <SEOHead {...SEOConfigs.home} url="https://finflow.ltd/" />
      <div className="min-h-screen relative bg-surface">
        <div className="relative">
          {/* ====== HERO SECTION ====== */}
          <section className="relative pt-24 pb-20 lg:pt-32 lg:pb-28 px-6">
            <div className="max-w-4xl mx-auto text-center">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-content mb-6 geometric-text leading-tight">
                {t("homepage.hero.title")}
              </h1>
              <p className="text-lg lg:text-xl text-content-secondary mb-10 max-w-2xl mx-auto leading-relaxed">
                {t("homepage.hero.subtitle")}
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button
                  size="lg"
                  className="futuristic-button px-10 py-3.5 text-base"
                  onClick={openRegisterModal}
                >
                  {t("homepage.hero.cta")}
                </Button>
                <a
                  href="/features"
                  className="inline-flex items-center gap-2 px-8 py-3.5 text-base font-medium text-content-secondary hover:text-content transition-colors rounded-xl border border-[var(--border)] hover:border-[var(--border-hover)]"
                >
                  {t("homepage.hero.ctaSecondary")}
                  <ArrowRight className="w-4 h-4" />
                </a>
              </div>
            </div>

            {/* Product Preview */}
            <div className="max-w-5xl mx-auto mt-16">
              <div className="rounded-2xl border border-[var(--border)] bg-elevated p-6 lg:p-8">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                  {/* Workspace Switcher */}
                  <div className="col-span-2 sm:col-span-3 lg:col-span-5 flex items-center gap-3 pb-4 border-b border-[var(--border)] mb-2">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-alt">
                      <Users className="w-4 h-4 text-content-secondary" />
                      <span className="text-sm font-medium text-content">
                        {t("homepage.hero.preview.workspace")}
                      </span>
                    </div>
                    <span className="text-xs text-content-tertiary">/</span>
                    <span className="text-sm text-content-secondary">
                      {t("homepage.hero.preview.personal")}
                    </span>
                  </div>

                  {/* Account Card */}
                  <div className="rounded-xl bg-surface-alt p-4">
                    <div className="text-xs text-content-tertiary mb-1">
                      {t("homepage.hero.preview.accounts")}
                    </div>
                    <div className="text-lg font-semibold text-content">
                      $12,450
                    </div>
                    <div className="text-xs text-content-secondary mt-1">
                      3 {t("homepage.hero.preview.active")}
                    </div>
                  </div>

                  {/* Expenses Card */}
                  <div className="rounded-xl bg-surface-alt p-4">
                    <div className="text-xs text-content-tertiary mb-1">
                      {t("homepage.hero.preview.expenses")}
                    </div>
                    <div className="text-lg font-semibold text-content">
                      $2,180
                    </div>
                    <div className="text-xs text-danger-base mt-1">-12%</div>
                  </div>

                  {/* Income Card */}
                  <div className="rounded-xl bg-surface-alt p-4">
                    <div className="text-xs text-content-tertiary mb-1">
                      {t("homepage.hero.preview.income")}
                    </div>
                    <div className="text-lg font-semibold text-content">
                      $5,400
                    </div>
                    <div className="text-xs text-success-base mt-1">+8%</div>
                  </div>

                  {/* Recurring Badge */}
                  <div className="rounded-xl bg-surface-alt p-4">
                    <div className="text-xs text-content-tertiary mb-1">
                      {t("homepage.hero.preview.recurring")}
                    </div>
                    <div className="text-lg font-semibold text-content">7</div>
                    <div className="flex items-center gap-1 mt-1">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-success-base"></span>
                      <span className="text-xs text-content-secondary">
                        {t("homepage.hero.preview.automated")}
                      </span>
                    </div>
                  </div>

                  {/* Goal Progress */}
                  <div className="rounded-xl bg-surface-alt p-4">
                    <div className="text-xs text-content-tertiary mb-1">
                      {t("homepage.hero.preview.goal")}
                    </div>
                    <div className="text-lg font-semibold text-content">
                      68%
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-surface-alt mt-2">
                      <div
                        className="h-full rounded-full bg-[var(--accent)]"
                        style={{ width: "68%" }}
                      ></div>
                    </div>
                  </div>

                  {/* Currency Indicator */}
                  <div className="col-span-2 sm:col-span-3 lg:col-span-5 flex items-center gap-4 pt-3 border-t border-[var(--border)] mt-2">
                    <div className="flex items-center gap-2 text-xs text-content-tertiary">
                      <DollarSign className="w-4 h-4" />
                      <span>USD</span>
                      <span className="text-content-secondary">1.00</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-content-tertiary">
                      <span>EUR</span>
                      <span className="text-content-secondary">0.92</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-content-tertiary">
                      <span>UAH</span>
                      <span className="text-content-secondary">41.25</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-content-tertiary">
                      <span>GBP</span>
                      <span className="text-content-secondary">0.79</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ====== TRUST SECTION ====== */}
          <section className="px-6 py-16">
            <div className="max-w-5xl mx-auto">
              <div className="flex flex-wrap items-center justify-center gap-4 lg:gap-6">
                {trustBadges.map((badge) => {
                  const Icon = badge.icon;
                  return (
                    <div
                      key={badge.labelKey}
                      className="flex items-center gap-2.5 px-5 py-3 rounded-xl border border-[var(--border)] bg-elevated transition-colors"
                    >
                      <Icon className="w-5 h-5 text-content-secondary flex-shrink-0" />
                      <span className="text-sm font-medium text-content whitespace-nowrap">
                        {t(badge.labelKey)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* ====== FEATURES SECTION ====== */}
          <section className="py-20 px-6">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-16">
                <h2 className="text-3xl lg:text-4xl font-bold text-content mb-4 geometric-text">
                  {t("homepage.features.title")}
                </h2>
                <p className="text-lg text-content-secondary max-w-2xl mx-auto">
                  {t("homepage.features.subtitle")}
                </p>
              </div>

              <div className="space-y-16">
                {featureGroups.map((group) => (
                  <div key={group.titleKey}>
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-content-tertiary mb-6 pl-1">
                      {t(group.titleKey)}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                      {group.items.map((item) => {
                        const Icon = item.icon;
                        return (
                          <div
                            key={item.titleKey}
                            className="group rounded-xl border border-[var(--border)] bg-elevated p-6 hover:border-[var(--border-hover)] transition-colors"
                          >
                            <div className="flex items-start gap-4">
                              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-surface-alt flex items-center justify-center">
                                <Icon className="w-5 h-5 text-content-secondary group-hover:text-accent-base transition-colors" />
                              </div>
                              <div>
                                <h4 className="text-base font-semibold text-content mb-1">
                                  {t(item.titleKey)}
                                </h4>
                                <p className="text-sm text-content-secondary leading-relaxed">
                                  {t(item.descKey)}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ====== WORKSPACES SECTION ====== */}
          <section className="py-20 px-6">
            <div className="max-w-5xl mx-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                <div>
                  <h2 className="text-3xl lg:text-4xl font-bold text-content mb-6 geometric-text">
                    {t("homepage.workspaces.title")}
                  </h2>
                  <p className="text-lg text-content-secondary mb-8 leading-relaxed">
                    {t("homepage.workspaces.description")}
                  </p>
                  <ul className="space-y-4">
                    {(["personal", "invite", "roles", "useCases"] as const).map(
                      (key) => (
                        <li key={key} className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-surface-alt flex items-center justify-center mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]"></span>
                          </span>
                          <span className="text-sm text-content-secondary leading-relaxed">
                            {t(`homepage.workspaces.items.${key}`)}
                          </span>
                        </li>
                      ),
                    )}
                  </ul>
                </div>

                {/* Workspace Visual */}
                <div className="rounded-2xl border border-[var(--border)] bg-elevated p-6">
                  <div className="space-y-3">
                    {/* Personal Workspace */}
                    <div className="flex items-center justify-between rounded-xl bg-surface-alt p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-surface-alt flex items-center justify-center">
                          <Lock className="w-4 h-4 text-content-secondary" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-content">
                            {t("homepage.workspaces.visual.personal")}
                          </div>
                          <div className="text-xs text-content-tertiary">
                            {t("homepage.workspaces.visual.personalRole")}
                          </div>
                        </div>
                      </div>
                      <span className="text-xs px-2 py-1 rounded-md bg-[var(--accent-dim)] text-accent-base font-medium">
                        {t("homepage.workspaces.visual.active")}
                      </span>
                    </div>

                    {/* Shared Workspace */}
                    <div className="flex items-center justify-between rounded-xl bg-surface-alt p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-surface-alt flex items-center justify-center">
                          <Users className="w-4 h-4 text-content-secondary" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-content">
                            {t("homepage.workspaces.visual.shared")}
                          </div>
                          <div className="text-xs text-content-tertiary">
                            {t("homepage.workspaces.visual.sharedMembers")}
                          </div>
                        </div>
                      </div>
                      <div className="flex -space-x-2">
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)]"></div>
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)]"></div>
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)] flex items-center justify-center">
                          <span className="text-[10px] text-content-tertiary">
                            +2
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Business Workspace */}
                    <div className="flex items-center justify-between rounded-xl bg-surface-alt p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-surface-alt flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-content-secondary" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-content">
                            {t("homepage.workspaces.visual.business")}
                          </div>
                          <div className="text-xs text-content-tertiary">
                            {t("homepage.workspaces.visual.businessMembers")}
                          </div>
                        </div>
                      </div>
                      <div className="flex -space-x-2">
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)]"></div>
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)]"></div>
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)]"></div>
                        <div className="w-6 h-6 rounded-full bg-surface-alt border-2 border-[var(--bg-surface)] flex items-center justify-center">
                          <span className="text-[10px] text-content-tertiary">
                            +5
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ====== PLANS SECTION ====== */}
          <section className="py-20 px-6">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl lg:text-4xl font-bold text-content mb-4 geometric-text">
                {t("homepage.plans.title")}
              </h2>
              <p className="text-lg text-content-secondary mb-12 max-w-xl mx-auto">
                {t("homepage.plans.subtitle")}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {plans.map((plan) => (
                  <div
                    key={plan.nameKey}
                    className={`rounded-xl border p-6 text-center transition-colors ${
                      plan.featured
                        ? "border-[var(--accent)] bg-elevated shadow-sm"
                        : "border-[var(--border)] bg-elevated"
                    }`}
                  >
                    <div className="text-base font-semibold text-content mb-1">
                      {t(plan.nameKey)}
                    </div>
                    <div className="text-2xl font-bold text-content mb-2">
                      {t(plan.priceKey)}
                    </div>
                    <div className="text-sm text-content-secondary">
                      {t(plan.highlightKey)}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-8">
                <a
                  href="/pricing"
                  className="inline-flex items-center gap-2 text-sm font-medium text-accent-base hover:underline"
                >
                  {t("homepage.plans.viewAll")}
                  <ArrowRight className="w-4 h-4" />
                </a>
              </div>
            </div>
          </section>

          {/* ====== FINAL CTA ====== */}
          <section className="py-20 px-6">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-2xl lg:text-3xl font-bold text-content mb-4 geometric-text">
                {t("homepage.cta.title")}
              </h2>
              <p className="text-base text-content-secondary mb-8 max-w-xl mx-auto leading-relaxed">
                {t("homepage.cta.description")}
              </p>
              <Button
                size="lg"
                className="futuristic-button px-10 py-3.5 text-base"
                onClick={openRegisterModal}
              >
                {t("homepage.hero.cta")}
              </Button>
            </div>
          </section>
        </div>
      </div>
    </>
  );
};
