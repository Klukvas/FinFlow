import React from "react";
import { Helmet } from "react-helmet-async";
import { config } from "@/config/env";

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
 title = "FinFlow - Умный учет финансов и бюджетирование",
 description = "Автоматизируйте учет финансов с помощью ИИ. Парсинг банковских выписок, категоризация трат, планирование бюджета и аналитика расходов.",
 keywords = "учет финансов, бюджетирование, парсинг банковских выписок, финансовая аналитика, управление деньгами, личные финансы",
 image = `${config.app.url}/og-image.png`,
 url = config.app.url,
 type = "website",
 structuredData,
}) => {
 const fullTitle = title.includes("FinFlow") ? title : `${title} | FinFlow`;

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
 title: "FinFlow - Умный учет финансов и бюджетирование",
 description:
 "Автоматизируйте учет финансов с помощью ИИ. Парсинг банковских выписок, категоризация трат, планирование бюджета и аналитика расходов в одном приложении.",
 keywords:
 "учет финансов, бюджетирование, парсинг банковских выписок, финансовая аналитика, управление деньгами, личные финансы",
 structuredData: {
 "@context": "https://schema.org",
 "@type": "WebApplication",
 name: "FinFlow",
 description:
 "Умное приложение для учета финансов с автоматической категоризацией трат",
 url: config.app.url,
 applicationCategory: "FinanceApplication",
 operatingSystem: "Web",
 offers: {
 "@type": "Offer",
 price: "0",
 priceCurrency: "USD",
 },
 },
 },

 dashboard: {
 title: "Панель управления финансами",
 description:
 "Управляйте своими финансами с помощью интуитивной панели управления. Отслеживайте доходы, расходы и анализируйте финансовые тренды.",
 keywords:
 "панель управления финансами, финансовый дашборд, анализ расходов, управление бюджетом",
 },

 pdfParser: {
 title: "Парсинг банковских выписок",
 description:
 "Автоматически извлекайте данные из банковских PDF выписок. Поддержка Monobank, ПриватБанк и других банков Украины.",
 keywords:
 "парсинг банковских выписок, Monobank, ПриватБанк, автоматический учет транзакций, MCC коды",
 },

 categories: {
 title: "Управление категориями расходов",
 description:
 "Создавайте и управляйте категориями для автоматической классификации ваших трат. Умная категоризация с помощью MCC кодов.",
 keywords:
 "категории расходов, классификация трат, MCC коды, автоматическая категоризация",
 },

 analytics: {
 title: "Финансовая аналитика и отчеты",
 description:
 "Получайте детальную аналитику ваших финансов. Графики расходов, тренды, прогнозы и рекомендации по оптимизации бюджета.",
 keywords:
 "финансовая аналитика, отчеты по расходам, графики трат, финансовые тренды, оптимизация бюджета",
 },

 about: {
 title: "О нас - FinFlow",
 description:
 "Узнайте о FinFlow - умном приложении для учета финансов с автоматической категоризацией трат и парсингом банковских выписок.",
 keywords: "о нас, команда FinFlow, финансовая аналитика, учет финансов",
 },

 features: {
 title: "Возможности - FinFlow",
 description:
 "Откройте для себя все возможности FinFlow: парсинг банковских выписок, автоматическая категоризация, аналитика и многое другое.",
 keywords:
 "возможности, функции, парсинг банковских выписок, автоматическая категоризация трат, финансовая аналитика",
 },

 pricing: {
 title: "Тарифы и цены - FinFlow",
 description:
 "Выберите подходящий тарифный план для управления вашими финансами. Бесплатный план и премиум возможности.",
 keywords:
 "тарифы, цены, премиум план, бесплатный план, финансовая аналитика",
 },

 contact: {
 title: "Связаться с нами - FinFlow",
 description:
 "Свяжитесь с командой FinFlow. Мы всегда готовы помочь вам с вопросами о нашем приложении для учета финансов.",
 keywords:
 "контакты, поддержка, свяжитесь с нами, помощь, обслуживание клиентов",
 },

 terms: {
 title: "Условия использования - FinFlow",
 description:
 "Условия использования сервиса FinFlow. Информация о поставщике услуг, правила использования, подписки и оплата.",
 keywords:
 "условия использования, пользовательское соглашение, правила, подписка, оплата",
 url: `${config.app.url}/terms`,
 },

 privacyPolicy: {
 title: "Политика конфиденциальности - FinFlow",
 description:
 "Политика конфиденциальности FinFlow. Как мы собираем, используем и защищаем ваши персональные данные.",
 keywords:
 "политика конфиденциальности, защита данных, персональные данные, GDPR, приватность",
 url: `${config.app.url}/privacy`,
 },

 refund: {
 title: "Политика возврата - FinFlow",
 description:
 "Политика возврата средств FinFlow. Информация о гарантии возврата денег, отмене подписки и процедуре возврата.",
 keywords:
 "возврат средств, отмена подписки, гарантия возврата, политика возврата",
 url: `${config.app.url}/refund`,
 },

 blog: {
 title: "Блог - FinFlow",
 description:
 "Статьи о финансовом учёте, автоматизации расходов, парсинге банковских выписок и управлении бюджетом.",
 keywords:
 "финансовый блог, учёт расходов, парсинг выписок, бюджетирование, автоматизация финансов",
 url: `${config.app.url}/blog`,
 },
};
