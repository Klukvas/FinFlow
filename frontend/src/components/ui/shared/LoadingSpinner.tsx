import React from "react";
import { useTranslation } from "react-i18next";

interface LoadingSpinnerProps {
 size?: "sm" | "md" | "lg" | "xl";
 className?: string;
 "data-testid"?: string;
}

const sizeClasses = {
 sm: "h-4 w-4",
 md: "h-6 w-6",
 lg: "h-8 w-8",
 xl: "h-12 w-12",
};

export const LoadingSpinner = React.memo<LoadingSpinnerProps>(
 ({ size = "md", className = "", "data-testid": testId }) => {
 const { t } = useTranslation();

 return (
 <div
 className={`animate-spin rounded-full border-2 border-current border-t-transparent ${sizeClasses[size]} ${className}`}
 data-testid={testId || "loading-spinner"}
 role="status"
 aria-label={t("common.loading")}
 >
 <span className="sr-only">{t("common.loading")}</span>
 </div>
 );
 },
);

LoadingSpinner.displayName = "LoadingSpinner";
