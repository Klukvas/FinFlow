import React from "react";
import {
  Tabs as BaseTabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@klukvas/flux-b2c-ui";

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
  <BaseTabs value={activeTab} onValueChange={onTabChange} className={className}>
    <TabsList>
      {tabs.map((tab) => (
        <TabsTrigger key={tab.id} value={tab.id}>
          {tab.icon && <span className="mr-2">{tab.icon}</span>}
          {tab.label}
        </TabsTrigger>
      ))}
    </TabsList>
    {children}
  </BaseTabs>
);
