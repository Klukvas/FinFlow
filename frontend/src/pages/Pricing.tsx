import React from 'react';
import { FaCheck, FaCrown, FaRocket } from 'react-icons/fa';
import { Button } from '@/components/ui/Button';

export const Pricing: React.FC = () => {
  const plans = [
    {
      name: 'Базовый',
      price: '0',
      period: 'навсегда',
      description: 'Идеально для начала управления личными финансами',
      icon: null,
      features: [
        'До 5 категорий расходов',
        'Базовые отчеты',
        'Мобильная версия',
        'Поддержка по email',
        'Синхронизация данных'
      ],
      limitations: [
        'Ограниченная аналитика',
        'Нет экспорта данных'
      ],
      popular: false
    },
    {
      name: 'Профессиональный',
      price: '299',
      period: 'в месяц',
      description: 'Для тех, кто серьезно относится к управлению финансами',
      icon: FaRocket,
      features: [
        'Неограниченные категории',
        'Расширенная аналитика',
        'Экспорт в Excel/PDF',
        'Повторяющиеся платежи',
        'Приоритетная поддержка',
        'Семейный доступ (до 4 человек)',
        'Автоматическая категоризация',
        'Напоминания о платежах'
      ],
      limitations: [],
      popular: true
    },
    {
      name: 'Корпоративный',
      price: '999',
      period: 'в месяц',
      description: 'Для команд и малого бизнеса',
      icon: FaCrown,
      features: [
        'Все возможности Профессионального',
        'Неограниченные пользователи',
        'API доступ',
        'Интеграции с банками',
        'Персональный менеджер',
        'Кастомные отчеты',
        'Белый лейбл',
        'SLA 99.9%'
      ],
      limitations: [],
      popular: false
    }
  ];

  return (
    <div className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold theme-text-primary mb-6">
            Выберите подходящий план
          </h1>
          <p className="text-xl theme-text-secondary max-w-3xl mx-auto">
            Начните бесплатно и переходите на платные планы по мере роста ваших потребностей
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative theme-surface theme-border border rounded-lg p-8 theme-shadow hover:theme-shadow-hover theme-transition ${
                plan.popular ? 'ring-2 ring-blue-500 scale-105' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="theme-accent-bg theme-text-inverse px-4 py-1 rounded-full text-sm font-medium">
                    Популярный
                  </span>
                </div>
              )}
              
              <div className="text-center mb-8">
                {plan.icon && (
                  <div className="theme-accent-bg w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <plan.icon className="w-6 h-6 theme-text-inverse" />
                  </div>
                )}
                <h3 className="text-2xl font-bold theme-text-primary mb-2">
                  {plan.name}
                </h3>
                <p className="theme-text-secondary mb-4">
                  {plan.description}
                </p>
                <div className="mb-6">
                  <span className="text-4xl font-bold theme-text-primary">
                    ₽{plan.price}
                  </span>
                  <span className="theme-text-secondary ml-2">
                    {plan.period}
                  </span>
                </div>
              </div>

              <div className="space-y-4 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-start">
                    <FaCheck className="w-5 h-5 theme-success mr-3 mt-0.5 flex-shrink-0" />
                    <span className="theme-text-primary text-sm">
                      {feature}
                    </span>
                  </div>
                ))}
                {plan.limitations.map((limitation, limitationIndex) => (
                  <div key={limitationIndex} className="flex items-start">
                    <span className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0 text-gray-400">✕</span>
                    <span className="theme-text-tertiary text-sm line-through">
                      {limitation}
                    </span>
                  </div>
                ))}
              </div>

              <Button
                variant={plan.popular ? 'primary' : 'outline'}
                fullWidth
                size="lg"
              >
                {plan.price === '0' ? 'Начать бесплатно' : 'Выбрать план'}
              </Button>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold theme-text-primary mb-4">
            Есть вопросы о тарифах?
          </h2>
          <p className="theme-text-secondary mb-6">
            Свяжитесь с нами, и мы поможем выбрать подходящий план
          </p>
          <Button variant="outline" size="lg">
            Связаться с нами
          </Button>
        </div>
      </div>
    </div>
  );
};
