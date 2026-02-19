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
    ],
    platform: [
      { label: t('footer.links.platform.architecture'), href: '/about' },
      { label: t('footer.links.platform.security'), href: '/about' },
      { label: t('footer.links.platform.status'), href: '/status' },
      { label: t('footer.links.platform.docs'), href: '/docs' },
    ],
    company: [
      { label: t('footer.links.company.about'), href: '/about' },
      { label: t('footer.links.company.contact'), href: '/contact' },
    ],
    legal: [
      { label: t('footer.links.legal.privacy'), href: '/privacy' },
      { label: t('footer.links.legal.terms'), href: '/terms' },
      { label: t('footer.links.legal.refund'), href: '/refund' },
    ],
  };

  const socialLinks = [
    { icon: FaGithub, href: 'https://github.com', label: 'GitHub' },
    { icon: FaLinkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
    { icon: FaTwitter, href: 'https://twitter.com', label: 'Twitter' },
    { icon: FaEnvelope, href: 'mailto:finflow@flux-lab.dev', label: 'Email' },
  ];

  return (
    <footer className="theme-surface theme-border border-t theme-transition">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-8">
          {/* Brand Section */}
          <div className="col-span-2 sm:col-span-3 lg:col-span-1">
            <h3 className="text-base font-bold theme-text-primary mb-3">
              {t('footer.brand.title')}
            </h3>
            <p className="theme-text-secondary text-sm mb-4 leading-relaxed">
              {t('footer.brand.description')}
            </p>
            <div className="flex space-x-3 mb-4">
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
                    <Icon className="w-4 h-4" />
                  </a>
                );
              })}
            </div>
            <a
              href="mailto:finflow@flux-lab.dev"
              className="text-sm theme-text-tertiary hover:theme-text-primary theme-transition"
            >
              finflow@flux-lab.dev
            </a>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="text-sm font-semibold theme-text-primary mb-3">{t('footer.sections.product')}</h4>
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

          {/* Platform Links */}
          <div>
            <h4 className="text-sm font-semibold theme-text-primary mb-3">{t('footer.sections.platform')}</h4>
            <ul className="space-y-2">
              {footerLinks.platform.map((link) => (
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
            <h4 className="text-sm font-semibold theme-text-primary mb-3">{t('footer.sections.company')}</h4>
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

          {/* Legal Links */}
          <div>
            <h4 className="text-sm font-semibold theme-text-primary mb-3">{t('footer.sections.legal')}</h4>
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
        <div className="mt-10 pt-6 theme-border border-t">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-2">
            <p className="theme-text-tertiary text-xs">
              {t('footer.bottom.copyright', { year: currentYear })}
            </p>
            <p className="theme-text-tertiary text-xs">
              {t('footer.bottom.madeWith')}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};
