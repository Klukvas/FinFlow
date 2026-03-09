import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { SEOHead } from "@/components/seo/SEOHead";

export const NotFound: React.FC = () => {
 const { t } = useTranslation();

 return (
 <>
 <SEOHead
 title={t("notFoundPage.title", "Page Not Found")}
 description={t(
 "notFoundPage.message",
 "The page you are looking for does not exist or has been moved.",
 )}
 />
 <div className="min-h-screen bg-surface flex items-center justify-center px-6">
 <div className="text-center max-w-md">
 <h1 className="text-8xl font-bold text-accent-base mb-4">404</h1>
 <h2 className="text-2xl font-semibold text-content mb-4">
 {t("notFoundPage.title", "Page Not Found")}
 </h2>
 <p className="text-content-secondary mb-8">
 {t(
 "notFoundPage.message",
 "The page you are looking for does not exist or has been moved.",
 )}
 </p>
 <Link
 to="/"
 className="inline-flex items-center px-6 py-3 rounded-lg font-medium text-content-inverse bg-accent-base hover:bg-accent-base-hover transition-colors"
 >
 {t("notFoundPage.backHome", "Back to Home")}
 </Link>
 </div>
 </div>
 </>
 );
};

export default NotFound;
