import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Zap, Wifi, Smartphone, Share2, SquarePlus } from "lucide-react";
import { Modal } from "@/components/ui/shared/Modal";
import { Button } from "@/components/ui/shared/Button";
import { setPWADismissed, InstallOutcome } from "@/hooks/usePWAInstall";

interface InstallPWAModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly platform: "android" | "ios" | "desktop";
  readonly onInstall: () => Promise<InstallOutcome>;
}

export const InstallPWAModal: React.FC<InstallPWAModalProps> = ({
  isOpen,
  onClose,
  platform,
  onInstall,
}) => {
  const { t } = useTranslation();
  const [dontShowAgain, setDontShowAgain] = useState(false);

  const handleClose = () => {
    if (dontShowAgain) {
      setPWADismissed();
    }
    setDontShowAgain(false);
    onClose();
  };

  const handleInstall = async () => {
    const outcome = await onInstall();
    if (outcome === "accepted") {
      handleClose();
    }
  };

  const benefits = [
    { icon: Wifi, text: t("pwa.installBenefits.offline") },
    { icon: Zap, text: t("pwa.installBenefits.fast") },
    { icon: Smartphone, text: t("pwa.installBenefits.homescreen") },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t("pwa.installTitle")}
      size="sm"
      data-testid="pwa-install-modal"
    >
      <div className="space-y-4 pt-2">
        <p className="text-content-secondary text-sm">
          {t("pwa.installDescription")}
        </p>

        {/* Benefits list */}
        <ul className="space-y-3">
          {benefits.map(({ icon: Icon, text }) => (
            <li key={text} className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-dim)]">
                <Icon className="h-4 w-4 text-accent-base" />
              </div>
              <span className="text-sm text-content">{text}</span>
            </li>
          ))}
        </ul>

        {platform === "ios" ? (
          /* iOS manual instructions */
          <div className="space-y-3 rounded-xl bg-surface-alt p-4">
            <p className="text-sm font-medium text-content">
              {t("pwa.iosInstructions.title")}
            </p>
            <ol className="space-y-2 text-sm text-content-secondary">
              <li className="flex items-start gap-2">
                <span className="font-medium text-accent-base">1.</span>
                <span className="flex items-center gap-1.5">
                  {t("pwa.iosInstructions.step1")}
                  <Share2 className="inline h-3.5 w-3.5 text-accent-base" />
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium text-accent-base">2.</span>
                <span className="flex items-center gap-1.5">
                  {t("pwa.iosInstructions.step2")}
                  <SquarePlus className="inline h-3.5 w-3.5 text-accent-base" />
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-medium text-accent-base">3.</span>
                <span>{t("pwa.iosInstructions.step3")}</span>
              </li>
            </ol>
          </div>
        ) : (
          /* Android / Desktop install button */
          <Button
            onClick={handleInstall}
            fullWidth
            data-testid="pwa-install-confirm"
          >
            {t("pwa.installButton")}
          </Button>
        )}

        {/* Don't show again + dismiss */}
        <div className="flex items-center justify-between border-t border-[var(--border)] pt-3">
          <label className="flex cursor-pointer items-center gap-2 text-xs text-content-secondary">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              className="rounded"
              data-testid="pwa-dont-show-again"
            />
            {t("pwa.dontShowAgain")}
          </label>

          <button
            onClick={handleClose}
            className="text-xs text-content-secondary hover:text-content transition-colors"
            data-testid="pwa-dismiss"
          >
            {t("pwa.dismissButton")}
          </button>
        </div>
      </div>
    </Modal>
  );
};
