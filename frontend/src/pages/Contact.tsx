import React from 'react';
import { FaEnvelope, FaPhone, FaMapMarkerAlt, FaClock } from 'react-icons/fa';
import { Button } from '@/components/ui/Button';
import { useTranslation } from 'react-i18next';

export const Contact: React.FC = () => {
  const { t } = useTranslation();

  const contactInfo = [
    {
      icon: FaEnvelope,
      title: t('contactPage.contactInfo.email.title'),
      value: 'support@financial-app.com',
      description: t('contactPage.contactInfo.email.description')
    },
    {
      icon: FaPhone,
      title: t('contactPage.contactInfo.phone.title'),
      value: '+7 (800) 123-45-67',
      description: t('contactPage.contactInfo.phone.description')
    },
    {
      icon: FaMapMarkerAlt,
      title: t('contactPage.contactInfo.address.title'),
      value: 'Москва, ул. Примерная, 123',
      description: t('contactPage.contactInfo.address.description')
    },
    {
      icon: FaClock,
      title: t('contactPage.contactInfo.hours.title'),
      value: '24/7',
      description: t('contactPage.contactInfo.hours.description')
    }
  ];

  return (
    <div className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold theme-text-primary mb-6">
            {t('contactPage.title')}
          </h1>
          <p className="text-xl theme-text-secondary max-w-3xl mx-auto">
            {t('contactPage.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Information */}
          <div>
            <h2 className="text-2xl font-bold theme-text-primary mb-8">
              {t('contactPage.contactInfo.title')}
            </h2>
            
            <div className="space-y-6">
              {contactInfo.map((info, index) => {
                const Icon = info.icon;
                return (
                  <div key={index} className="flex items-start">
                    <div className="theme-accent-bg w-12 h-12 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
                      <Icon className="w-6 h-6 theme-text-inverse" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold theme-text-primary mb-1">
                        {info.title}
                      </h3>
                      <p className="theme-text-primary font-medium mb-1">
                        {info.value}
                      </p>
                      <p className="theme-text-secondary text-sm">
                        {info.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 theme-surface theme-border border rounded-lg p-6">
              <h3 className="text-lg font-semibold theme-text-primary mb-4">
                {t('contactPage.faq.title')}
              </h3>
              <div className="space-y-3">
                {t('contactPage.faq.questions', { returnObjects: true }).map((faq: any, index: number) => (
                  <div key={index}>
                    <p className="theme-text-primary font-medium mb-1">
                      {faq.question}
                    </p>
                    <p className="theme-text-secondary text-sm">
                      {faq.answer}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div>
            <h2 className="text-2xl font-bold theme-text-primary mb-8">
              {t('contactPage.form.title')}
            </h2>
            
            <form className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium theme-text-primary mb-2">
                    {t('contactPage.form.name')}
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
                    placeholder={t('contactPage.form.namePlaceholder')}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium theme-text-primary mb-2">
                    {t('contactPage.form.email')}
                  </label>
                  <input
                    type="email"
                    className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
                    placeholder={t('contactPage.form.emailPlaceholder')}
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text-primary mb-2">
                  {t('contactPage.form.subject')}
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
                  placeholder={t('contactPage.form.subjectPlaceholder')}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text-primary mb-2">
                  {t('contactPage.form.message')}
                </label>
                <textarea
                  rows={6}
                  className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary resize-none"
                  placeholder={t('contactPage.form.messagePlaceholder')}
                ></textarea>
              </div>
              
              <Button type="submit" size="lg" fullWidth>
                {t('contactPage.form.submit')}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
