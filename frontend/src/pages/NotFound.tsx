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
      <div className="min-h-screen theme-bg flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <h1 className="text-8xl font-bold theme-accent mb-4">404</h1>
          <h2 className="text-2xl font-semibold theme-text-primary mb-4">
            {t("notFoundPage.title", "Page Not Found")}
          </h2>
          <p className="theme-text-secondary mb-8">
            {t(
              "notFoundPage.message",
              "The page you are looking for does not exist or has been moved.",
            )}
          </p>
          <Link
            to="/"
            className="inline-flex items-center px-6 py-3 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            {t("notFoundPage.backHome", "Back to Home")}
          </Link>
        </div>
      </div>
    </>
  );
};

export default NotFound;
