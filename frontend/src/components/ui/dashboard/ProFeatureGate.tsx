import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Lock, type LucideIcon } from "lucide-react";

interface ProFeatureGateProps {
 planCode: string;
 featureTitle: string;
 featureIcon?: LucideIcon;
 children: React.ReactNode;
}

export const ProFeatureGate: React.FC<ProFeatureGateProps> = ({
 planCode,
 featureTitle,
 featureIcon: Icon,
 children,
}) => {
 const { t } = useTranslation();
 const isBasic = planCode === "basic";

 if (!isBasic) {
 return <>{children}</>;
 }

 return (
 <div className="bg-elevated rounded-lg theme-shadow border-[var(--color-border)] border p-6 flex flex-col items-center justify-center min-h-[200px]">
 <div className="relative mb-3">
 {Icon ? (
 <Icon className="w-10 h-10 text-content-tertiary" />
 ) : (
 <Lock className="w-10 h-10 text-content-tertiary" />
 )}
 <Lock className="w-4 h-4 text-content-secondary absolute -bottom-1 -right-1 bg-elevated rounded-full p-0.5" />
 </div>
 <p className="text-base font-semibold text-content mb-1">
 {featureTitle}
 </p>
 <p className="text-sm text-content-secondary mb-4 text-center">
 {t("dashboard.proGate.description")}
 </p>
 <Link
 to="/pricing"
 className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
 >
 {t("dashboard.proGate.upgrade")}
 </Link>
 </div>
 );
};
