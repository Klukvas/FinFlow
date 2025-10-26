import React from 'react';
import { Helmet } from 'react-helmet-async';

interface SEOHeadProps {
  title?: string;
  description?: string;
  keywords?: string;
  image?: string;
  url?: string;
  type?: string;
  structuredData?: object;
}

export const SEOHead: React.FC<SEOHeadProps> = ({
  title = 'FinFlow - Умный учет финансов и бюджетирование',
  description = 'Автоматизируйте учет финансов с помощью ИИ. Парсинг банковских выписок, категоризация трат, планирование бюджета и аналитика расходов.',
  keywords = 'учет финансов, бюджетирование, парсинг банковских выписок, финансовая аналитика, управление деньгами, личные финансы',
  image = 'https://finflow.ltd/og-image.jpg',
  url = 'https://finflow.ltd',
  type = 'website',
  structuredData
}) => {
  const fullTitle = title.includes('FinFlow') ? title : `${title} | FinFlow`;
  
  return (
    <Helmet>
      {/* Primary Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="title" content={fullTitle} />
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      
      {/* Twitter */}
      <meta property="twitter:card" content="summary_large_image" />
      <meta property="twitter:url" content={url} />
      <meta property="twitter:title" content={fullTitle} />
      <meta property="twitter:description" content={description} />
      <meta property="twitter:image" content={image} />
      
      {/* Canonical URL */}
      <link rel="canonical" href={url} />
      
      {/* Structured Data */}
      {structuredData && (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      )}
    </Helmet>
  );
};

// Предустановленные SEO конфигурации для разных страниц
export const SEOConfigs = {
  home: {
    title: 'FinFlow - Умный учет финансов и бюджетирование',
    description: 'Автоматизируйте учет финансов с помощью ИИ. Парсинг банковских выписок, категоризация трат, планирование бюджета и аналитика расходов в одном приложении.',
    keywords: 'учет финансов, бюджетирование, парсинг банковских выписок, финансовая аналитика, управление деньгами, личные финансы',
    structuredData: {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      "name": "FinFlow",
      "description": "Умное приложение для учета финансов с автоматической категоризацией трат",
      "url": "https://finflow.ltd",
      "applicationCategory": "FinanceApplication",
      "operatingSystem": "Web",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      }
    }
  },
  
  dashboard: {
    title: 'Панель управления финансами',
    description: 'Управляйте своими финансами с помощью интуитивной панели управления. Отслеживайте доходы, расходы и анализируйте финансовые тренды.',
    keywords: 'панель управления финансами, финансовый дашборд, анализ расходов, управление бюджетом'
  },
  
  pdfParser: {
    title: 'Парсинг банковских выписок',
    description: 'Автоматически извлекайте данные из банковских PDF выписок. Поддержка Monobank, ПриватБанк и других банков Украины.',
    keywords: 'парсинг банковских выписок, Monobank, ПриватБанк, автоматический учет транзакций, MCC коды'
  },
  
  categories: {
    title: 'Управление категориями расходов',
    description: 'Создавайте и управляйте категориями для автоматической классификации ваших трат. Умная категоризация с помощью MCC кодов.',
    keywords: 'категории расходов, классификация трат, MCC коды, автоматическая категоризация'
  },
  
  analytics: {
    title: 'Финансовая аналитика и отчеты',
    description: 'Получайте детальную аналитику ваших финансов. Графики расходов, тренды, прогнозы и рекомендации по оптимизации бюджета.',
    keywords: 'финансовая аналитика, отчеты по расходам, графики трат, финансовые тренды, оптимизация бюджета'
  }
};
