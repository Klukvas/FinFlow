import React from 'react';
import { Link } from 'react-router-dom';
import { FaGithub, FaLinkedin, FaTwitter, FaEnvelope } from 'react-icons/fa';
import { useTranslation } from 'react-i18next';

export const PublicFooter: React.FC = () => {
  const { t } = useTranslation();
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { label: t('footer.links.product.features'), href: '/features' },
      { label: t('footer.links.product.pricing'), href: '/pricing' },
      { label: t('footer.links.product.api'), href: '/api' },
      { label: t('footer.links.product.integrations'), href: '/integrations' },
    ],
    company: [
      { label: t('footer.links.company.about'), href: '/about' },
      { label: t('footer.links.company.blog'), href: '/blog' },
      { label: t('footer.links.company.careers'), href: '/careers' },
      { label: t('footer.links.company.contact'), href: '/contact' },
    ],
    support: [
      { label: t('footer.links.support.help'), href: '/help' },
      { label: t('footer.links.support.docs'), href: '/docs' },
      { label: t('footer.links.support.status'), href: '/status' },
      { label: t('footer.links.support.community'), href: '/community' },
    ],
    legal: [
      { label: t('footer.links.legal.privacy'), href: '/privacy' },
      { label: t('footer.links.legal.terms'), href: '/terms' },
      { label: t('footer.links.legal.cookies'), href: '/cookies' },
      { label: t('footer.links.legal.gdpr'), href: '/gdpr' },
    ],
  };

  const socialLinks = [
    { icon: FaGithub, href: 'https://github.com', label: 'GitHub' },
    { icon: FaLinkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
    { icon: FaTwitter, href: 'https://twitter.com', label: 'Twitter' },
    { icon: FaEnvelope, href: 'mailto:support@example.com', label: 'Email' },
  ];

  return (
    <footer className="theme-surface theme-border border-t theme-transition">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-1">
            <h3 className="text-lg font-bold theme-text-primary mb-4">
              {t('footer.brand.title')}
            </h3>
            <p className="theme-text-secondary text-sm mb-4">
              {t('footer.brand.description')}
            </p>
            <div className="flex space-x-4">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.label}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="theme-text-tertiary hover:theme-text-primary theme-transition"
                    title={social.label}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-semibold theme-text-primary mb-4">{t('footer.sections.product')}</h4>
            <ul className="space-y-2">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="theme-text-secondary hover:theme-text-primary text-sm theme-transition"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-semibold theme-text-primary mb-4">{t('footer.sections.company')}</h4>
            <ul className="space-y-2">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="theme-text-secondary hover:theme-text-primary text-sm theme-transition"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support Links */}
          <div>
            <h4 className="font-semibold theme-text-primary mb-4">{t('footer.sections.support')}</h4>
            <ul className="space-y-2">
              {footerLinks.support.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="theme-text-secondary hover:theme-text-primary text-sm theme-transition"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-semibold theme-text-primary mb-4">{t('footer.sections.legal')}</h4>
            <ul className="space-y-2">
              {footerLinks.legal.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="theme-text-secondary hover:theme-text-primary text-sm theme-transition"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="mt-8 pt-8 theme-border border-t">
          <div className="flex flex-col lg:flex-row justify-between items-center">
            <p className="theme-text-tertiary text-sm">
              {t('footer.bottom.copyright', { year: currentYear })}
            </p>
            <div className="mt-4 lg:mt-0">
              <p className="theme-text-tertiary text-sm">
                {t('footer.bottom.madeWith')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
