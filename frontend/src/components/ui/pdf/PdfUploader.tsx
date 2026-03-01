import React, { useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useApiClients } from "@/hooks/useApiClients";
import { ParsedTransaction } from "@/services/api/pdfParserApiClient";
import i18n from "@/i18n";
import { normalizeLanguageCode } from "@/utils";

interface PdfUploaderProps {
  onTransactionsParsed: (transactions: ParsedTransaction[]) => void;
  onClose: () => void;
}

export const PdfUploader: React.FC<PdfUploaderProps> = ({
  onTransactionsParsed,
  onClose,
}) => {
  const { t } = useTranslation();
  const { pdfParser } = useApiClients();
  const [file, setFile] = useState<File | null>(null);
  const [bankType, setBankType] = useState<string>("");
  const [supportedBanks, setSupportedBanks] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingBanks, setIsLoadingBanks] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    loadSupportedBanks();
  }, []);

  const loadSupportedBanks = async () => {
    try {
      setIsLoadingBanks(true);
      const response = await pdfParser.getSupportedBanks();
      if ("error" in response) {
        setError(response.error);
      } else {
        setSupportedBanks(response.supported_banks);
      }
    } catch (err) {
      setError(t("pdfParserPage.uploadModal.errors.loadBanksFailed"));
    } finally {
      setIsLoadingBanks(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      const allowedTypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
      ];
      if (!allowedTypes.includes(selectedFile.type)) {
        setError(t("pdfParserPage.uploadModal.errors.selectFile"));
        return;
      }
      if (selectedFile.size > 10 * 1024 * 1024) {
        // 10MB limit
        setError(t("pdfParserPage.uploadModal.errors.fileSizeLimit"));
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError(t("pdfParserPage.uploadModal.errors.selectFile"));
      return;
    }

    if (!bankType) {
      setError(t("pdfParserPage.uploadModal.errors.selectBankType"));
      return;
    }

    try {
      setIsUploading(true);
      setError(null);

      // Normalize language code for the API
      const language = normalizeLanguageCode(i18n.language);
      const response = await pdfParser.parsePDF(file, bankType, language);

      if ("error" in response) {
        logger.error("Upload error:", response.error);
        setError(response.error);
      } else {
        onTransactionsParsed(response.transactions);
        onClose();
      }
    } catch (err) {
      setError(t("pdfParserPage.uploadModal.errors.parseFailed"));
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    const allowedDropTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "text/csv",
    ];
    if (droppedFile && allowedDropTypes.includes(droppedFile.type)) {
      if (droppedFile.size > 10 * 1024 * 1024) {
        setError(t("pdfParserPage.uploadModal.errors.fileSizeLimit"));
        return;
      }
      setFile(droppedFile);
      setError(null);
    } else {
      setError(t("pdfParserPage.uploadModal.errors.dropFile"));
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="theme-surface rounded-lg p-6 w-full max-w-md mx-4 theme-shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold theme-text-primary">
            {t("pdfParserPage.uploadModal.title")}
          </h2>
          <button
            onClick={onClose}
            className="theme-text-tertiary hover:theme-text-primary theme-transition"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 theme-error-light theme-border border theme-error-bg rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-4 w-4 theme-error"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm theme-text-primary">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {/* Bank Type Selection */}
          <div>
            <label
              htmlFor="bank-type-select"
              className="block text-sm font-medium theme-text-primary mb-2"
            >
              {t("pdfParserPage.uploadModal.bankTypeLabel")} *
            </label>
            <select
              id="bank-type-select"
              value={bankType}
              onChange={(e) => setBankType(e.target.value)}
              className="w-full p-3 theme-border border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 theme-text-primary theme-surface"
              disabled={isLoadingBanks}
              required
            >
              <option value="">
                {t("pdfParserPage.uploadModal.bankTypePlaceholder")}
              </option>
              {supportedBanks.map((bank) => (
                <option key={bank} value={bank} className="theme-text-primary">
                  {bank.charAt(0).toUpperCase() + bank.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Bank Request Banner */}
          <div className="p-3 rounded-lg border theme-border theme-accent-light">
            <p className="text-sm theme-text-secondary">
              {t("pdfParserPage.uploadModal.bankRequestBanner")}{" "}
              <a
                href="mailto:finflow@flux-lab.dev"
                className="theme-accent underline font-medium"
              >
                finflow@flux-lab.dev
              </a>
            </p>
          </div>

          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              {t("pdfParserPage.uploadModal.pdfFileLabel")} *
            </label>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed theme-border rounded-lg p-6 text-center hover:theme-border-hover transition-colors"
            >
              <input
                ref={fileInputRef}
                id="pdf-file-input"
                name="pdf-file"
                type="file"
                accept=".pdf,.xlsx,.csv"
                onChange={handleFileSelect}
                className="hidden"
              />

              {file ? (
                <div>
                  <div className="flex items-center justify-center mb-2">
                    <svg
                      className="w-8 h-8 theme-success mr-2"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <p className="theme-success font-medium">{file.name}</p>
                  </div>
                  <p className="text-sm theme-text-tertiary">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <svg
                    className="mx-auto h-12 w-12 theme-text-tertiary mb-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3H4v7"
                    />
                  </svg>
                  <p className="theme-text-secondary mb-4">
                    {t("pdfParserPage.uploadModal.dropOrClick")}
                  </p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 rounded-lg font-medium transition-colors bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white theme-shadow hover:theme-shadow-hover"
                  >
                    {t("pdfParserPage.uploadModal.chooseFile")}
                  </button>
                  <p className="text-xs theme-text-tertiary mt-2">
                    {t("pdfParserPage.uploadModal.maxFileSize")}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 theme-border border theme-text-primary rounded-lg hover:theme-surface-hover theme-transition font-medium"
            >
              {t("pdfParserPage.uploadModal.cancel")}
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || !bankType || isUploading}
              className="flex-1 px-4 py-3 rounded-lg font-medium transition-colors bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 text-white disabled:cursor-not-allowed theme-shadow hover:theme-shadow-hover disabled:shadow-none"
            >
              {isUploading ? (
                <div className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {t("pdfParserPage.uploadModal.parsing")}
                </div>
              ) : (
                t("pdfParserPage.uploadModal.parseButton")
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
