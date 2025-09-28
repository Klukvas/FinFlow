import React from 'react';
import { FaChartBar, FaShieldAlt, FaMobile, FaClock, FaUsers, FaCog, FaBell, FaFileExport, FaSync, FaLock } from 'react-icons/fa';

export const Features: React.FC = () => {
  const features = [
    {
      icon: FaChartBar,
      title: 'Аналитика и отчеты',
      description: 'Получайте детальную аналитику ваших финансов с красивыми графиками и диаграммами. Отслеживайте тренды и выявляйте закономерности в ваших тратах.',
      details: ['Графики доходов и расходов', 'Категоризация трат', 'Сравнение периодов', 'Экспорт отчетов']
    },
    {
      icon: FaShieldAlt,
      title: 'Безопасность данных',
      description: 'Ваши финансовые данные защищены современными методами шифрования. Мы используем банковские стандарты безопасности.',
      details: ['256-bit SSL шифрование', 'Двухфакторная аутентификация', 'Регулярные резервные копии', 'Соответствие GDPR']
    },
    {
      icon: FaMobile,
      title: 'Мобильная версия',
      description: 'Управляйте финансами с любого устройства. Синхронизация данных происходит в реальном времени.',
      details: ['Адаптивный дизайн', 'Офлайн режим', 'Push-уведомления', 'Быстрый доступ']
    },
    {
      icon: FaClock,
      title: 'Автоматизация',
      description: 'Настройте повторяющиеся платежи, получайте напоминания и автоматически категоризируйте транзакции.',
      details: ['Повторяющиеся платежи', 'Умные напоминания', 'Автокатегоризация', 'Шаблоны операций']
    },
    {
      icon: FaUsers,
      title: 'Семейный учет',
      description: 'Ведите совместный учет с членами семьи. Устанавливайте лимиты и контролируйте общий бюджет.',
      details: ['Общие счета', 'Семейные категории', 'Лимиты трат', 'Роли пользователей']
    },
    {
      icon: FaCog,
      title: 'Настройки',
      description: 'Персонализируйте приложение под свои потребности. Создавайте собственные категории и настраивайте интерфейс.',
      details: ['Пользовательские категории', 'Настройка интерфейса', 'Импорт данных', 'API интеграции']
    }
  ];

  return (
    <div className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold theme-text-primary mb-6">
            Возможности приложения
          </h1>
          <p className="text-xl theme-text-secondary max-w-3xl mx-auto">
            Все необходимые инструменты для эффективного управления личными финансами
          </p>
        </div>

        <div className="space-y-16">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            const isEven = index % 2 === 0;
            
            return (
              <div
                key={index}
                className={`flex flex-col ${isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'} items-center gap-12`}
              >
                <div className="flex-1">
                  <div className="theme-accent-bg w-16 h-16 rounded-lg flex items-center justify-center mb-6">
                    <Icon className="w-8 h-8 theme-text-inverse" />
                  </div>
                  <h2 className="text-3xl font-bold theme-text-primary mb-4">
                    {feature.title}
                  </h2>
                  <p className="text-lg theme-text-secondary mb-6">
                    {feature.description}
                  </p>
                  <ul className="space-y-2">
                    {feature.details.map((detail, detailIndex) => (
                      <li key={detailIndex} className="flex items-center theme-text-secondary">
                        <span className="theme-accent w-2 h-2 rounded-full mr-3"></span>
                        {detail}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex-1">
                  <div className="theme-surface theme-border border rounded-lg p-8 theme-shadow">
                    <div className="aspect-video theme-bg-secondary rounded-lg flex items-center justify-center">
                      <Icon className="w-24 h-24 theme-text-tertiary" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
