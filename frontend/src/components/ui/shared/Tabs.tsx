import React from "react";
import { cn } from "@/utils/cn";

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
  children?: React.ReactNode;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onTabChange,
  className = "",
  children,
}) => (
  <div className={className}>
    <div
      className="flex gap-1 p-1 bg-[var(--bg-raised)] rounded-[var(--radius-md)] border border-[var(--border)]"
      role="tablist"
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 text-[13px] font-medium rounded-[var(--radius-sm)] transition-all duration-150 cursor-pointer border-0 whitespace-nowrap touch-manipulation",
            activeTab === tab.id
              ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-[var(--shadow-sm)]"
              : "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
          )}
        >
          {tab.icon && <span className="flex-shrink-0">{tab.icon}</span>}
          {tab.label}
        </button>
      ))}
    </div>
    {children}
  </div>
);

/* Tab content wrapper */
interface TabsContentProps {
  value: string;
  activeTab: string;
  children: React.ReactNode;
  className?: string;
}

export const TabsContent: React.FC<TabsContentProps> = ({
  value,
  activeTab,
  children,
  className = "",
}) => {
  if (value !== activeTab) return null;
  return (
    <div role="tabpanel" className={cn("mt-4", className)}>
      {children}
    </div>
  );
};
