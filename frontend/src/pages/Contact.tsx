import React from 'react';
import { FaEnvelope, FaPhone, FaMapMarkerAlt, FaClock } from 'react-icons/fa';
import { Button } from '@/components/ui/Button';

export const Contact: React.FC = () => {
  const contactInfo = [
    {
      icon: FaEnvelope,
      title: 'Email',
      value: 'support@financial-app.com',
      description: 'Пишите нам в любое время'
    },
    {
      icon: FaPhone,
      title: 'Телефон',
      value: '+7 (800) 123-45-67',
      description: 'Пн-Пт с 9:00 до 18:00'
    },
    {
      icon: FaMapMarkerAlt,
      title: 'Адрес',
      value: 'Москва, ул. Примерная, 123',
      description: 'Офис в центре города'
    },
    {
      icon: FaClock,
      title: 'Время работы',
      value: '24/7',
      description: 'Поддержка круглосуточно'
    }
  ];

  return (
    <div className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold theme-text-primary mb-6">
            Свяжитесь с нами
          </h1>
          <p className="text-xl theme-text-secondary max-w-3xl mx-auto">
            У вас есть вопросы? Мы всегда готовы помочь и ответить на любые вопросы
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Information */}
          <div>
            <h2 className="text-2xl font-bold theme-text-primary mb-8">
              Контактная информация
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
                Часто задаваемые вопросы
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="theme-text-primary font-medium mb-1">
                    Как начать пользоваться приложением?
                  </p>
                  <p className="theme-text-secondary text-sm">
                    Просто зарегистрируйтесь и начните добавлять свои доходы и расходы
                  </p>
                </div>
                <div>
                  <p className="theme-text-primary font-medium mb-1">
                    Безопасны ли мои данные?
                  </p>
                  <p className="theme-text-secondary text-sm">
                    Да, мы используем банковские стандарты шифрования для защиты ваших данных
                  </p>
                </div>
                <div>
                  <p className="theme-text-primary font-medium mb-1">
                    Можно ли экспортировать данные?
                  </p>
                  <p className="theme-text-secondary text-sm">
                    Да, в платных планах доступен экспорт в Excel и PDF форматах
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div>
            <h2 className="text-2xl font-bold theme-text-primary mb-8">
              Напишите нам
            </h2>
            
            <form className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium theme-text-primary mb-2">
                    Имя
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
                    placeholder="Ваше имя"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium theme-text-primary mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
                    placeholder="your@email.com"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text-primary mb-2">
                  Тема
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
                  placeholder="Тема сообщения"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text-primary mb-2">
                  Сообщение
                </label>
                <textarea
                  rows={6}
                  className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary resize-none"
                  placeholder="Ваше сообщение..."
                ></textarea>
              </div>
              
              <Button type="submit" size="lg" fullWidth>
                Отправить сообщение
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
