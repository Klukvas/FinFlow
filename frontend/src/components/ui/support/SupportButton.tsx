import React, { useState, useCallback, useMemo } from "react";
import { MessageCircleQuestion } from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/shared/Modal";
import { AuthHttpClient, ApiError } from "@/services/api/AuthHttpClient";
import { useAuth } from "@/contexts/AuthContext";
import { config } from "@/config/env";

const MESSAGE_MAX_LENGTH = 1000;

export const SupportButton: React.FC = () => {
  const { t } = useTranslation();
  const { token, refreshAccessToken } = useAuth();

  const client = useMemo(
    () =>
      new AuthHttpClient(
        config.api.baseUrl,
        () => token,
        refreshAccessToken,
        true,
      ),
    [token, refreshAccessToken],
  );

  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleOpen = useCallback(() => setIsOpen(true), []);

  const handleClose = useCallback(() => {
    if (!isSending) {
      setIsOpen(false);
      setMessage("");
    }
  }, [isSending]);

  const handleMessageChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setMessage(e.target.value);
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      const trimmed = message.trim();
      if (!trimmed || isSending) return;

      setIsSending(true);

      try {
        const result = await client.post("/v1/support/message", {
          message: trimmed,
          page_url: window.location.pathname,
        });

        if ("error" in (result as ApiError)) {
          toast.error(t("support.errorSending"));
        } else {
          toast.success(t("support.messageSent"));
          setIsOpen(false);
          setMessage("");
        }
      } catch {
        toast.error(t("support.errorSending"));
      } finally {
        setIsSending(false);
      }
    },
    [message, isSending, client, t],
  );

  const charsRemaining = MESSAGE_MAX_LENGTH - message.length;
  const isOverLimit = charsRemaining < 0;
  const canSubmit = message.trim().length > 0 && !isOverLimit && !isSending;

  return (
    <>
      {/* Floating button */}
      <button
        type="button"
        onClick={handleOpen}
        className="fixed bottom-6 right-6 z-40 w-12 h-12 md:w-14 md:h-14 rounded-full bg-[var(--accent)] text-white border-0 cursor-pointer flex items-center justify-center shadow-lg transition-transform duration-200 hover:scale-110 active:scale-95 animate-[supportPulse_3s_ease-in-out_infinite] max-[768px]:bottom-4 max-[768px]:right-4"
        aria-label={t("support.buttonLabel")}
        data-testid="support-button"
      >
        <MessageCircleQuestion className="w-6 h-6 max-[768px]:w-5 max-[768px]:h-5" />
      </button>

      {/* Support form modal */}
      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title={t("support.title")}
        subtitle={t("support.subtitle")}
        size="sm"
        data-testid="support-modal"
      >
        <form onSubmit={handleSubmit}>
          <ModalBody>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="support-message"
                className="text-sm font-medium text-[var(--text-secondary)]"
              >
                {t("support.messageLabel")}
              </label>
              <textarea
                id="support-message"
                value={message}
                onChange={handleMessageChange}
                maxLength={MESSAGE_MAX_LENGTH}
                rows={5}
                required
                disabled={isSending}
                placeholder={t("support.messagePlaceholder")}
                className="w-full resize-y rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--bg-input,var(--bg-base))] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-h-[120px]"
                data-testid="support-message-input"
              />
              <span
                className={`text-xs text-right ${
                  isOverLimit
                    ? "text-[var(--error,#ef4444)]"
                    : "text-[var(--text-tertiary)]"
                }`}
              >
                {charsRemaining}/{MESSAGE_MAX_LENGTH}
              </span>
            </div>
          </ModalBody>

          <ModalFooter>
            <button
              type="button"
              onClick={handleClose}
              disabled={isSending}
              className="px-4 py-2 text-sm font-medium rounded-[var(--radius-md)] border border-[var(--border)] bg-transparent text-[var(--text-secondary)] cursor-pointer transition-colors hover:bg-[var(--bg-raised)] disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] touch-manipulation"
              data-testid="support-cancel-button"
            >
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="px-4 py-2 text-sm font-medium rounded-[var(--radius-md)] border-0 bg-[var(--accent)] text-white cursor-pointer transition-colors hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] touch-manipulation"
              data-testid="support-submit-button"
            >
              {isSending ? t("common.processing") : t("support.send")}
            </button>
          </ModalFooter>
        </form>
      </Modal>
    </>
  );
};

SupportButton.displayName = "SupportButton";
