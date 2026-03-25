import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Lock, type LucideIcon } from "lucide-react";
import { Badge } from "../shared/Badge";

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
    <div className="relative overflow-hidden rounded-[var(--radius-lg)]">
      {/* Blurred content behind */}
      <div className="blur-[4px] pointer-events-none select-none opacity-40">
        {children}
      </div>

      {/* Gate overlay */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 rounded-[var(--radius-lg)] border border-[var(--accent-border)]"
        style={{
          background: "var(--bg-overlay)",
          backdropFilter: "blur(2px)",
          WebkitBackdropFilter: "blur(2px)",
        }}
      >
        <div className="relative mb-1">
          {Icon ? (
            <Icon className="w-7 h-7 text-[var(--text-tertiary)]" strokeWidth={1.5} />
          ) : (
            <Lock className="w-7 h-7 text-[var(--text-tertiary)]" strokeWidth={1.5} />
          )}
        </div>
        <p className="text-[15px] font-semibold text-[var(--text-primary)]">
          {featureTitle}
        </p>
        <p className="text-[13px] text-[var(--text-secondary)] text-center max-w-[240px]">
          {t("dashboard.proGate.description")}
        </p>
        <Link
          to="/pricing"
          className="mt-1 inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-[var(--radius-md)] bg-[var(--accent)] text-[var(--accent-text)] hover:bg-[var(--accent-hover)] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(34,217,160,0.25)] transition-all duration-150"
        >
          <Badge variant="pro">PRO</Badge>
          {t("dashboard.proGate.upgrade")}
        </Link>
      </div>
    </div>
  );
};
