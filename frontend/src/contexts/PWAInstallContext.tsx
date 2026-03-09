import React, { createContext, useContext } from "react";
import { usePWAInstall, PWAInstallState } from "@/hooks/usePWAInstall";

const PWAInstallContext = createContext<PWAInstallState | null>(null);

export const PWAInstallProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const pwaInstall = usePWAInstall();

  return (
    <PWAInstallContext.Provider value={pwaInstall}>
      {children}
    </PWAInstallContext.Provider>
  );
};

export const usePWAInstallContext = (): PWAInstallState => {
  const context = useContext(PWAInstallContext);
  if (!context) {
    throw new Error(
      "usePWAInstallContext must be used within a PWAInstallProvider",
    );
  }
  return context;
};
