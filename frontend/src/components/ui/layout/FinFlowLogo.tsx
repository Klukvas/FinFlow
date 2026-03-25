import React from "react";

interface FinFlowLogoProps {
  size?: number;
  className?: string;
}

/** FinFlow brand symbol — two stylised "F" letters + accent dot on dark rounded-rect bg */
export const FinFlowLogo: React.FC<FinFlowLogoProps> = ({
  size = 28,
  className,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 96 96"
    fill="none"
    className={className}
    role="img"
    aria-label="FinFlow"
  >
    <rect width="96" height="96" rx="24" fill="#111A27" />
    <rect
      x="0.5"
      y="0.5"
      width="95"
      height="95"
      rx="23.5"
      stroke="#22D9A0"
      strokeOpacity="0.2"
    />
    <rect width="96" height="48" rx="24" fill="#22D9A0" fillOpacity="0.03" />
    {/* F left — white */}
    <path d="M16 22H36V30H24V38H34V46H24V74H16V22Z" fill="#EFF4FB" />
    {/* F right — accent */}
    <path d="M38 22H58V30H46V38H56V46H46V74H38V22Z" fill="#22D9A0" />
    {/* cap bar */}
    <rect
      x="16"
      y="17"
      width="42"
      height="4"
      rx="2"
      fill="#22D9A0"
      fillOpacity="0.35"
    />
    {/* dot */}
    <circle cx="72" cy="44" r="8" fill="#22D9A0" />
    <circle cx="72" cy="44" r="13" fill="#22D9A0" fillOpacity="0.12" />
  </svg>
);

interface FinFlowWordmarkProps {
  className?: string;
}

/** "FinFlow" wordmark with split colouring: "Fin" in primary text, "Flow" in accent */
export const FinFlowWordmark: React.FC<FinFlowWordmarkProps> = ({
  className,
}) => (
  <span
    className={`text-lg font-extrabold tracking-[-0.04em] ${className ?? ""}`}
  >
    <span className="text-[var(--text-primary)]">Fin</span>
    <span className="text-[var(--accent)]">Flow</span>
  </span>
);
