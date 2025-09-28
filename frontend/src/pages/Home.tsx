import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartBar, FaShieldAlt, FaMobile, FaClock, FaUsers, FaCog } from 'react-icons/fa';
import { Button } from '@/components/ui/Button';
import { useModal } from '@/contexts/ModalContext';

export const Home: React.FC = () => {
  const { openLoginModal, openRegisterModal } = useModal();
  
  const features = [
    {
      icon: FaChartBar,
      title: 'Аналитика и отчеты',
      description: 'Детальная аналитика ваших финансов с красивыми графиками и диаграммами'
    },
    {
      icon: FaShieldAlt,
      title: 'Безопасность',
      description: 'Ваши данные защищены современными методами шифрования'
    },
    {
      icon: FaMobile,
      title: 'Мобильная версия',
      description: 'Управляйте финансами с любого устройства, где бы вы ни находились'
    },
    {
      icon: FaClock,
      title: 'Автоматизация',
      description: 'Настройте повторяющиеся платежи и получайте уведомления'
    },
    {
      icon: FaUsers,
      title: 'Семейный учет',
      description: 'Ведите совместный учет с членами семьи'
    },
    {
      icon: FaCog,
      title: 'Настройки',
      description: 'Персонализируйте приложение под свои потребности'
    }
  ];

  const stats = [
    { number: '10,000+', label: 'Активных пользователей' },
    { number: '50М$+', label: 'Управляемых средств' },
  ];

  return (
    <div className="theme-bg theme-transition">
      {/* Hero Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-4xl lg:text-6xl font-bold theme-text-primary mb-6">
              Управляйте финансами
              <span className="block theme-accent">просто и эффективно</span>
            </h1>
            <p className="text-xl theme-text-secondary mb-8 max-w-3xl mx-auto">
              Современное приложение для учета доходов и расходов. 
              Отслеживайте бюджет, планируйте покупки и достигайте финансовых целей.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                className="w-full sm:w-auto"
                onClick={openRegisterModal}
              >
                Начать бесплатно
              </Button>
              <Button 
                variant="outline" 
                size="lg" 
                className="w-full sm:w-auto"
                onClick={openLoginModal}
              >
                Войти в систему
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 theme-bg-secondary">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl lg:text-4xl font-bold theme-accent mb-2">
                  {stat.number}
                </div>
                <div className="theme-text-secondary">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold theme-text-primary mb-4">
              Почему выбирают нас
            </h2>
            <p className="text-xl theme-text-secondary max-w-2xl mx-auto">
              Все необходимые инструменты для управления личными финансами в одном месте
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className="theme-surface theme-border border rounded-lg p-6 theme-shadow hover:theme-shadow-hover theme-transition"
                >
                  <div className="theme-accent-bg w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 theme-text-inverse" />
                  </div>
                  <h3 className="text-xl font-semibold theme-text-primary mb-3">
                    {feature.title}
                  </h3>
                  <p className="theme-text-secondary">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 theme-accent-bg">
        <div className="max-w-4xl mx-auto text-center px-6">
          <h2 className="text-3xl lg:text-4xl font-bold theme-text-inverse mb-6">
            Готовы начать управлять финансами?
          </h2>
          <p className="text-xl theme-text-inverse opacity-90 mb-8">
            Присоединяйтесь к тысячам пользователей, которые уже контролируют свои деньги
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              variant="secondary" 
              className="w-full sm:w-auto"
              onClick={openRegisterModal}
            >
              Создать аккаунт
            </Button>
            <Link to="/features">
              <Button variant="outline" size="lg" className="w-full sm:w-auto theme-text-inverse border-white hover:bg-white hover:theme-text-primary">
                Узнать больше
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
