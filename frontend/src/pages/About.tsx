import React from 'react';

export const About: React.FC = () => {
  return (
    <div className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold theme-text-primary mb-8 text-center">
          О нас
        </h1>
        
        <div className="prose prose-lg max-w-none theme-text-primary">
          <p className="text-xl theme-text-secondary mb-6">
            Мы создали Финансовый учет, чтобы помочь людям лучше управлять своими деньгами 
            и достигать финансовых целей.
          </p>
          
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            Наша миссия
          </h2>
          <p className="theme-text-secondary mb-6">
            Сделать управление личными финансами простым, понятным и доступным для каждого. 
            Мы верим, что каждый человек заслуживает иметь полный контроль над своими деньгами 
            и возможность планировать свое финансовое будущее.
          </p>
          
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            Что мы предлагаем
          </h2>
          <ul className="theme-text-secondary mb-6 space-y-2">
            <li>• Простой и интуитивный интерфейс</li>
            <li>• Полный контроль над доходами и расходами</li>
            <li>• Детальная аналитика и отчеты</li>
            <li>• Безопасное хранение данных</li>
            <li>• Поддержка на всех устройствах</li>
          </ul>
          
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            Наша команда
          </h2>
          <p className="theme-text-secondary">
            Мы — команда разработчиков и финансовых экспертов, которые понимают важность 
            правильного управления деньгами. Наш опыт и знания помогают создавать продукты, 
            которые действительно решают проблемы пользователей.
          </p>
        </div>
      </div>
    </div>
  );
};
