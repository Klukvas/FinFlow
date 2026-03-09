import { useState, useEffect, useCallback, useRef } from "react";

export type Platform = "android" | "ios" | "desktop";

export type InstallOutcome = "accepted" | "dismissed" | "unavailable";

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
  prompt(): Promise<void>;
}

export interface PWAInstallState {
  readonly isInstallable: boolean;
  readonly isInstalled: boolean;
  readonly platform: Platform;
  install(): Promise<InstallOutcome>;
}

export const PWA_DISMISS_KEY = "finflow_pwa_dismissed";
const PWA_SESSION_KEY = "finflow_pwa_prompt_shown";

export const getPWADismissed = (): boolean => {
  try {
    return localStorage.getItem(PWA_DISMISS_KEY) === "true";
  } catch {
    return false;
  }
};

export const setPWADismissed = (): void => {
  try {
    localStorage.setItem(PWA_DISMISS_KEY, "true");
  } catch {
    // Private browsing or storage full — ignore
  }
};

export const getPWAPromptShown = (): boolean => {
  try {
    return sessionStorage.getItem(PWA_SESSION_KEY) === "true";
  } catch {
    return false;
  }
};

export const setPWAPromptShown = (): void => {
  try {
    sessionStorage.setItem(PWA_SESSION_KEY, "true");
  } catch {
    // ignore
  }
};

const detectPlatform = (): Platform => {
  if (typeof navigator === "undefined") return "desktop";
  const ua = navigator.userAgent;
  if (/iPad|iPhone|iPod/.test(ua)) return "ios";
  if (/Android/.test(ua)) return "android";
  return "desktop";
};

const checkIsInstalled = (): boolean => {
  if (typeof window === "undefined") return false;
  if (
    "standalone" in navigator &&
    (navigator as { standalone?: boolean }).standalone
  ) {
    return true;
  }
  return window.matchMedia("(display-mode: standalone)").matches;
};

export const usePWAInstall = (): PWAInstallState => {
  const deferredPromptRef = useRef<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(() => checkIsInstalled());
  const platform = useRef(detectPlatform()).current;

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      deferredPromptRef.current = e as BeforeInstallPromptEvent;
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      deferredPromptRef.current = null;
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt,
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const install = useCallback(async (): Promise<InstallOutcome> => {
    const prompt = deferredPromptRef.current;
    if (!prompt) return "unavailable";

    try {
      await prompt.prompt();
      const { outcome } = await prompt.userChoice;

      if (outcome === "accepted") {
        setIsInstalled(true);
        setIsInstallable(false);
      }
      return outcome;
    } catch {
      return "unavailable";
    } finally {
      deferredPromptRef.current = null;
    }
  }, []);

  return { isInstallable, isInstalled, platform, install };
};
