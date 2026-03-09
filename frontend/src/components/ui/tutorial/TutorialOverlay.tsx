import React, { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useTutorial } from "@/contexts/TutorialContext";
import { FaArrowRight, FaArrowLeft, FaTimes, FaCheck } from "react-icons/fa";

interface TargetRect {
 top: number;
 left: number;
 width: number;
 height: number;
}

export const TutorialOverlay: React.FC = () => {
 const { t } = useTranslation();
 const {
 isActive,
 currentStep,
 totalSteps,
 currentStepData,
 nextStep,
 prevStep,
 skipTutorial,
 completeTutorial,
 } = useTutorial();

 const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
 const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

 const updateTargetPosition = useCallback(() => {
 if (!currentStepData) return;

 const element = document.querySelector(currentStepData.targetSelector);
 if (element) {
 const rect = element.getBoundingClientRect();
 setTargetRect({
 top: rect.top,
 left: rect.left,
 width: rect.width,
 height: rect.height,
 });

 // Calculate tooltip position based on step position preference
 const padding = 16;
 const tooltipWidth = 320;
 const tooltipHeight = 200;

 let top = rect.top;
 let left = rect.left + rect.width + padding;

 // Position based on preference
 switch (currentStepData.position) {
 case "top":
 top = rect.top - tooltipHeight - padding;
 left = rect.left + rect.width / 2 - tooltipWidth / 2;
 break;
 case "bottom":
 top = rect.bottom + padding;
 left = rect.left + rect.width / 2 - tooltipWidth / 2;
 break;
 case "left":
 top = rect.top + rect.height / 2 - tooltipHeight / 2;
 left = rect.left - tooltipWidth - padding;
 break;
 case "right":
 default:
 top = rect.top + rect.height / 2 - tooltipHeight / 2;
 left = rect.right + padding;
 break;
 }

 // Ensure tooltip stays within viewport
 const viewportWidth = window.innerWidth;
 const viewportHeight = window.innerHeight;

 if (left + tooltipWidth > viewportWidth - padding) {
 left = viewportWidth - tooltipWidth - padding;
 }
 if (left < padding) {
 left = padding;
 }
 if (top + tooltipHeight > viewportHeight - padding) {
 top = viewportHeight - tooltipHeight - padding;
 }
 if (top < padding) {
 top = padding;
 }

 setTooltipPosition({ top, left });
 }
 }, [currentStepData]);

 useEffect(() => {
 if (isActive) {
 updateTargetPosition();

 // Update position on resize/scroll
 window.addEventListener("resize", updateTargetPosition);
 window.addEventListener("scroll", updateTargetPosition);

 return () => {
 window.removeEventListener("resize", updateTargetPosition);
 window.removeEventListener("scroll", updateTargetPosition);
 };
 }
 return undefined;
 }, [isActive, currentStep, updateTargetPosition]);

 // Handle keyboard navigation
 useEffect(() => {
 if (!isActive) return;

 const handleKeyDown = (e: KeyboardEvent) => {
 switch (e.key) {
 case "ArrowRight":
 case "Enter":
 if (currentStep === totalSteps - 1) {
 completeTutorial();
 } else {
 nextStep();
 }
 break;
 case "ArrowLeft":
 prevStep();
 break;
 case "Escape":
 skipTutorial();
 break;
 default:
 break;
 }
 };

 window.addEventListener("keydown", handleKeyDown);
 return () => window.removeEventListener("keydown", handleKeyDown);
 }, [
 isActive,
 currentStep,
 totalSteps,
 nextStep,
 prevStep,
 skipTutorial,
 completeTutorial,
 ]);

 if (!isActive || !currentStepData) return null;

 const isLastStep = currentStep === totalSteps - 1;
 const isFirstStep = currentStep === 0;

 return (
 <div className="fixed inset-0 z-[9999]" role="dialog" aria-modal="true">
 {/* Dark overlay with spotlight effect */}
 <div className="absolute inset-0 bg-black/60 transition-opacity duration-300" />

 {/* Spotlight cutout */}
 {targetRect && (
 <div
 className="absolute transition-all duration-300 ease-out"
 style={{
 top: targetRect.top - 8,
 left: targetRect.left - 8,
 width: targetRect.width + 16,
 height: targetRect.height + 16,
 boxShadow: "0 0 0 9999px rgba(0, 0, 0, 0.6)",
 borderRadius: "12px",
 pointerEvents: "none",
 }}
 />
 )}

 {/* Highlight ring around target */}
 {targetRect && (
 <div
 className="absolute border-2 border-accent-base rounded-xl transition-all duration-300 ease-out animate-pulse"
 style={{
 top: targetRect.top - 8,
 left: targetRect.left - 8,
 width: targetRect.width + 16,
 height: targetRect.height + 16,
 pointerEvents: "none",
 }}
 />
 )}

 {/* Tooltip */}
 <div
 className="absolute w-80 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden transition-all duration-300 ease-out"
 style={{
 top: tooltipPosition.top,
 left: tooltipPosition.left,
 }}
 >
 {/* Header with progress */}
 <div className="px-5 py-3 bg-gradient-to-r from-accent-base/20 to-purple-600/20 border-b border-slate-700/50">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <span className="text-xs font-medium text-accent-base">
 {t("tutorial.step")} {currentStep + 1} / {totalSteps}
 </span>
 </div>
 <button
 onClick={skipTutorial}
 className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-700/50"
 aria-label={t("tutorial.skip")}
 >
 <FaTimes className="w-4 h-4" />
 </button>
 </div>
 {/* Progress bar */}
 <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
 <div
 className="h-full bg-gradient-to-r from-accent-base to-purple-500 transition-all duration-300"
 style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
 />
 </div>
 </div>

 {/* Content */}
 <div className="px-5 py-4">
 <h3 className="text-lg font-semibold text-white mb-2">
 {t(currentStepData.titleKey)}
 </h3>
 <p className="text-sm text-slate-300 leading-relaxed">
 {t(currentStepData.descriptionKey)}
 </p>
 </div>

 {/* Actions */}
 <div className="px-5 py-3 bg-slate-800/50 border-t border-slate-700/50 flex items-center justify-between">
 <button
 onClick={prevStep}
 disabled={isFirstStep}
 className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
 isFirstStep
 ? "text-slate-500 cursor-not-allowed"
 : "text-slate-300 hover:text-white hover:bg-slate-700/50"
 }`}
 >
 <FaArrowLeft className="w-3 h-3" />
 {t("tutorial.back")}
 </button>

 {isLastStep ? (
 <button
 onClick={completeTutorial}
 className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-success-base to-success-base hover:from-success-base hover:to-success-base-hover text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-green-500/25"
 >
 <FaCheck className="w-3 h-3" />
 {t("tutorial.complete")}
 </button>
 ) : (
 <button
 onClick={nextStep}
 className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accent-base to-purple-600 hover:from-accent-base hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-500/25"
 >
 {t("tutorial.next")}
 <FaArrowRight className="w-3 h-3" />
 </button>
 )}
 </div>
 </div>

 {/* Skip hint */}
 <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-slate-400 text-xs">
 {t("tutorial.pressEscToSkip")}
 </div>
 </div>
 );
};
