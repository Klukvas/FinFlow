import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster, toast } from "sonner";
import { registerSW } from "virtual:pwa-register";
import "./index.css";
import App from "./App";
// import './utils/initLogging'; // Initialize frontend logging - disabled

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
    <Toaster richColors position="top-right" />
  </StrictMode>,
);

const updateSW = registerSW({
  onNeedRefresh() {
    toast("Update available", {
      description: "A new version of FinFlow is available.",
      action: {
        label: "Update",
        onClick: () => {
          updateSW(true).catch(() => {
            toast.error("Update failed. Please refresh manually.");
          });
        },
      },
      duration: Infinity,
    });
  },
  onOfflineReady() {
    toast.success("App ready for offline use", { duration: 8000 });
  },
});
