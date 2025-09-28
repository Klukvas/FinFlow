import React from 'react';
import { Link } from 'react-router-dom';
import { FaGithub, FaLinkedin, FaTwitter, FaEnvelope } from 'react-icons/fa';

export const PublicFooter: React.FC = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { label: 'Возможности', href: '/features' },
      { label: 'Тарифы', href: '/pricing' },
      { label: 'API', href: '/api' },
      { label: 'Интеграции', href: '/integrations' },
    ],
    company: [
      { label: 'О нас', href: '/about' },
      { label: 'Блог', href: '/blog' },
      { label: 'Карьера', href: '/careers' },
      { label: 'Контакты', href: '/contact' },
    ],
    support: [
      { label: 'Помощь', href: '/help' },
      { label: 'Документация', href: '/docs' },
      { label: 'Статус', href: '/status' },
      { label: 'Сообщество', href: '/community' },
    ],
    legal: [
      { label: 'Политика конфиденциальности', href: '/privacy' },
      { label: 'Условия использования', href: '/terms' },
      { label: 'Cookie', href: '/cookies' },
      { label: 'GDPR', href: '/gdpr' },
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
              Финансовый учет
            </h3>
            <p className="theme-text-secondary text-sm mb-4">
              Простое и эффективное управление личными финансами. 
              Отслеживайте доходы, расходы и планируйте бюджет.
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
            <h4 className="font-semibold theme-text-primary mb-4">Продукт</h4>
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
            <h4 className="font-semibold theme-text-primary mb-4">Компания</h4>
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
            <h4 className="font-semibold theme-text-primary mb-4">Поддержка</h4>
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
            <h4 className="font-semibold theme-text-primary mb-4">Правовая информация</h4>
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
              &copy; {currentYear} Финансовый учет. Все права защищены.
            </p>
            <div className="mt-4 lg:mt-0">
              <p className="theme-text-tertiary text-sm">
                Сделано с ❤️ для управления финансами
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
