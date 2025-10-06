import React from 'react';
import { FaDollarSign, FaChartPie, FaArrowUp } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/Button';
import { useModal } from '@/contexts/ModalContext';
import { BackgroundCanvas } from '@/components/ui/BackgroundCanvas';
import { AnimatedBackground } from '@/components/ui/AnimatedBackground';

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const { openLoginModal, openRegisterModal } = useModal();

  return (
    <div className="min-h-screen relative theme-bg">
      {/* Animated Background Layers */}
      <BackgroundCanvas />
      <AnimatedBackground />
      
      {/* Content Layer */}
      <div className="relative z-30">
      {/* Hero Section */}
      <section className="relative py-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl lg:text-7xl font-bold theme-text-primary mb-8 geometric-text">
            {t('homepage.hero.title')}
          </h1>
          <p className="text-xl lg:text-2xl theme-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed">
            {t('homepage.hero.subtitle')}
          </p>
          <Button 
            size="lg" 
            className="futuristic-button px-12 py-4 text-lg neon-glow-hover"
            onClick={openRegisterModal}
          >
            {t('homepage.hero.cta')}
          </Button>
        </div>
      </section>

      {/* Trust Bar */}
      <section className="px-6 pb-12">
        <div className="max-w-6xl mx-auto theme-bg-secondary rounded-xl py-6 px-4 theme-border border">
          <p className="text-center theme-text-secondary mb-6">
            {t('homepage.trustBar.text')} <span className="theme-gold font-semibold">{t('homepage.trustBar.users')}</span> {t('homepage.trustBar.and')}
          </p>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-6 items-center justify-items-center px-4">
            {['BankOne','SafePay','LedgerX','BlockMint','AuditPro','Vaultly'].map((name) => (
              <div key={name} className="w-28 h-10 flex items-center justify-center rounded theme-bg-tertiary">
                <span className="text-sm theme-text-primary opacity-80">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Metrics Cards */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Expenses Card */}
            <div className="futuristic-card p-8 text-center gold-glow-hover gold-border border theme-transition">
              <div className="flex items-center justify-center mb-4 icon-draw">
                <FaDollarSign className="text-3xl theme-gold" />
              </div>
              <div className="text-3xl font-bold theme-text-primary mb-2">{t('homepage.metrics.expenses.amount')}</div>
              <div className="text-sm theme-text-secondary">{t('homepage.metrics.expenses.period')}</div>
              <div className="text-xs theme-text-tertiary mt-2">{t('homepage.metrics.expenses.label')}</div>
            </div>

            {/* Budget Overview Card with Circular Progress */}
            <div className="futuristic-card p-8 text-center gold-glow-hover gold-border border theme-transition">
              <div className="flex items-center justify-center mb-4">
                <div className="circular-progress">
                  <div className="circular-progress-text">{t('homepage.metrics.budget.percentage')}</div>
                </div>
              </div>
              <div className="text-lg font-semibold theme-text-primary mb-1">{t('homepage.metrics.budget.amount')}</div>
              <div className="text-sm theme-text-secondary">{t('homepage.metrics.budget.label')}</div>
            </div>

            {/* Income Card */}
            <div className="futuristic-card p-8 text-center gold-glow-hover gold-border border theme-transition">
              <div className="flex items-center justify-center mb-4 icon-draw">
                <FaArrowUp className="text-3xl theme-gold" />
              </div>
              <div className="text-3xl font-bold theme-text-primary mb-2">{t('homepage.metrics.income.amount')}</div>
              <div className="text-sm theme-text-secondary">{t('homepage.metrics.income.period')}</div>
              <div className="text-xs theme-text-tertiary mt-2">{t('homepage.metrics.income.label')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Benefits */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="futuristic-card gold-border border p-8 text-center gold-glow-hover theme-transition">
            <div className="mb-4 icon-draw flex justify-center">
              <FaChartPie className="text-3xl theme-gold" />
            </div>
            <h3 className="text-xl font-semibold theme-text-primary mb-2 fade-up">{t('homepage.benefits.clarity.title')}</h3>
            <p className="theme-text-secondary fade-up delay-100">{t('homepage.benefits.clarity.subtitle')}</p>
            <p className="theme-text-tertiary fade-up delay-200">{t('homepage.benefits.clarity.description')}</p>
          </div>
          <div className="futuristic-card gold-border border p-8 text-center gold-glow-hover theme-transition">
            <div className="mb-4 icon-draw flex justify-center">
              <span className="text-3xl theme-gold">⫶≡</span>
            </div>
            <h3 className="text-xl font-semibold theme-text-primary mb-2 fade-up">{t('homepage.benefits.control.title')}</h3>
            <p className="theme-text-secondary fade-up delay-100">{t('homepage.benefits.control.subtitle')}</p>
            <p className="theme-text-tertiary fade-up delay-200">{t('homepage.benefits.control.description')}</p>
          </div>
          <div className="futuristic-card gold-border border p-8 text-center gold-glow-hover theme-transition">
            <div className="mb-4 icon-draw flex justify-center">
              <span className="text-3xl theme-gold">⚡</span>
            </div>
            <h3 className="text-xl font-semibold theme-text-primary mb-2 fade-up">{t('homepage.benefits.automation.title')}</h3>
            <p className="theme-text-secondary fade-up delay-100">{t('homepage.benefits.automation.subtitle')}</p>
            <p className="theme-text-tertiary fade-up delay-200">{t('homepage.benefits.automation.description')}</p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="testimonial-card p-8 theme-transition">
            <div className="text-4xl theme-gold mb-4">"</div>
            <p className="theme-text-primary text-lg mb-4">{t('homepage.testimonials.elena.quote')}</p>
            <div className="flex items-center gap-3 theme-text-secondary">
              <div className="w-8 h-8 rounded-full theme-bg-tertiary theme-border border" />
              <span>{t('homepage.testimonials.elena.author')}</span>
            </div>
          </div>
          <div className="testimonial-card p-8 theme-transition">
            <div className="text-4xl theme-gold mb-4">"</div>
            <p className="theme-text-primary text-lg mb-4">{t('homepage.testimonials.tomas.quote')}</p>
            <div className="flex items-center gap-3 theme-text-secondary">
              <div className="w-8 h-8 rounded-full theme-bg-tertiary theme-border border" />
              <span>{t('homepage.testimonials.tomas.author')}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Note */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-lg theme-text-tertiary leading-relaxed">
            {t('homepage.footer.text')}
          </p>
        </div>
      </section>
      </div>
    </div>
  );
};