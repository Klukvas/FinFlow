import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Goal, Milestone } from "../../../types/goal";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import {
 getStatusBadgeVariant,
 getPriorityBadgeVariant,
 getTrackStatus,
 getTrackStatusColor,
 getTrackDotColor,
 getProgressBarColor,
 getDaysRemaining,
 getRequiredMonthlySaving,
 formatAmount,
 formatDate,
 STATUS_I18N_MAP,
 PRIORITY_I18N_MAP,
 GOAL_TYPE_I18N_MAP,
 TRACK_STATUS_I18N_MAP,
} from "./goalsHelpers";

interface GoalSidePanelProps {
 goal: Goal | null;
 milestones: Milestone[];
 milestonesLoading: boolean;
 isOpen: boolean;
 onClose: () => void;
 onUpdateProgress: () => void;
 onEdit: () => void;
 onDelete: () => void;
 onPauseResume: () => void;
}

export const GoalSidePanel: React.FC<GoalSidePanelProps> = ({
 goal,
 milestones,
 milestonesLoading,
 isOpen,
 onClose,
 onUpdateProgress,
 onEdit,
 onDelete,
 onPauseResume,
}) => {
 const { t } = useTranslation();

 // Close on ESC
 useEffect(() => {
 const handler = (e: KeyboardEvent) => {
 if (e.key === "Escape" && isOpen) onClose();
 };
 window.addEventListener("keydown", handler);
 return () => window.removeEventListener("keydown", handler);
 }, [isOpen, onClose]);

 // Prevent body scroll when panel is open
 useEffect(() => {
 if (isOpen) {
 document.body.style.overflow = "hidden";
 } else {
 document.body.style.overflow = "";
 }
 return () => {
 document.body.style.overflow = "";
 };
 }, [isOpen]);

 if (!goal) return null;

 const trackStatus = getTrackStatus(goal);
 const daysRemaining = getDaysRemaining(goal.target_date);
 const requiredMonthly = getRequiredMonthlySaving(goal);
 const isOverdue = daysRemaining !== null && daysRemaining < 0;
 const isPaused = goal.status === "PAUSED";
 const canToggle = goal.status === "ACTIVE" || goal.status === "PAUSED";

 // Projected completion: if current saving rate > 0, extrapolate
 const getProjectedCompletion = (): string | null => {
 if (
 !goal.target_date ||
 goal.current_amount <= 0 ||
 goal.progress_percentage >= 100
 )
 return null;
 const start = new Date(goal.start_date).getTime();
 const now = Date.now();
 const elapsed = now - start;
 if (elapsed <= 0) return null;

 const remaining = goal.target_amount - goal.current_amount;
 const rate = goal.current_amount / elapsed; // amount per ms
 if (rate <= 0) return null;

 const msToComplete = remaining / rate;
 const projected = new Date(now + msToComplete);
 return projected.toLocaleDateString("uk-UA");
 };

 const projectedCompletion = getProjectedCompletion();

 const overviewRows = [
 {
 label: t("goalsPage.sidePanel.currentAmount"),
 value: formatAmount(goal.current_amount, goal.currency),
 valueClass: "text-success-base/80 font-semibold",
 },
 {
 label: t("goalsPage.sidePanel.targetAmount"),
 value: formatAmount(goal.target_amount, goal.currency),
 valueClass: "text-content font-semibold",
 },
 {
 label: t("goalsPage.table.progress"),
 value: `${goal.progress_percentage.toFixed(1)}%`,
 valueClass: `font-semibold ${getProgressBarColor(goal.progress_percentage).replace("bg-", "text-").replace("/70", "/80")}`,
 },
 {
 label: t("goalsPage.sidePanel.requiredMonthly"),
 value:
 requiredMonthly !== null
 ? formatAmount(requiredMonthly, goal.currency)
 : "\u2014",
 valueClass: "text-content",
 },
 {
 label: t("goalsPage.sidePanel.startDate"),
 value: formatDate(goal.start_date),
 valueClass: "text-content",
 },
 {
 label: t("goalsPage.sidePanel.targetDate"),
 value: formatDate(goal.target_date),
 valueClass: "text-content",
 },
 {
 label: t("goalsPage.table.info.daysRemaining"),
 value:
 daysRemaining !== null
 ? isOverdue
 ? t("goalsPage.table.overdueDays", {
 days: Math.abs(daysRemaining),
 })
 : t("goalsPage.table.remainingDays", { days: daysRemaining })
 : "\u2014",
 valueClass: isOverdue
 ? "text-danger-base/80 font-medium"
 : "text-content",
 },
 {
 label: t("goalsPage.table.info.onTrack"),
 value: t(TRACK_STATUS_I18N_MAP[trackStatus]),
 valueClass: getTrackStatusColor(trackStatus),
 dot: getTrackDotColor(trackStatus),
 },
 ];

 const getMilestoneBadgeVariant = (milestone: Milestone) => {
 return milestone.is_completed ? "success" : "secondary";
 };

 return (
 <>
 {/* Backdrop */}
 <div
 className={`fixed inset-0 bg-black/30 z-30 transition-opacity duration-300 ${
 isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
 }`}
 onClick={onClose}
 />

 {/* Panel */}
 <div
 className={`fixed inset-y-0 right-0 z-40 w-full sm:w-[480px] lg:w-[40%] max-w-[560px] bg-elevated border-l border-[var(--color-border)] shadow-2xl transform transition-transform duration-300 flex flex-col ${
 isOpen ? "translate-x-0" : "translate-x-full"
 }`}
 >
 {/* Header - sticky */}
 <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[var(--color-border)] flex-shrink-0">
 <div className="flex items-center gap-3 min-w-0">
 <div className="min-w-0">
 <h2 className="text-lg font-semibold text-content truncate">
 {goal.title}
 </h2>
 <div className="flex items-center gap-2 mt-1 flex-wrap">
 <span className="text-xs text-content-tertiary">
 {t(GOAL_TYPE_I18N_MAP[goal.goal_type])}
 </span>
 <Badge
 variant={getPriorityBadgeVariant(goal.priority) as any}
 size="sm"
 >
 {t(PRIORITY_I18N_MAP[goal.priority])}
 </Badge>
 <Badge
 variant={getStatusBadgeVariant(goal.status) as any}
 size="sm"
 >
 {t(STATUS_I18N_MAP[goal.status])}
 </Badge>
 <span
 className={`w-2 h-2 rounded-full ${getTrackDotColor(trackStatus)}`}
 />
 </div>
 </div>
 </div>
 <button
 onClick={onClose}
 className="p-2 rounded-lg hover:bg-surface-alt transition-colors text-content-secondary flex-shrink-0"
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

 {/* Scrollable content */}
 <div className="flex-1 overflow-y-auto">
 {/* Progress bar */}
 <div className="px-4 sm:px-6 pt-4">
 <div className="w-full h-2 rounded-full bg-surface-alt overflow-hidden">
 <div
 className={`h-full rounded-full transition-all duration-500 ${getProgressBarColor(goal.progress_percentage)}`}
 style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
 />
 </div>
 </div>

 {/* Overview */}
 <div className="p-4 sm:p-6 space-y-4">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("goalsPage.sidePanel.overview")}
 </h3>
 <div className="space-y-3">
 {overviewRows.map((row) => (
 <div
 key={row.label}
 className="flex items-center justify-between"
 >
 <span className="text-sm text-content-secondary">
 {row.label}
 </span>
 <span
 className={`text-sm tabular-nums flex items-center gap-1.5 ${row.valueClass}`}
 >
 {"dot" in row && row.dot && (
 <span className={`w-2 h-2 rounded-full ${row.dot}`} />
 )}
 {row.value}
 </span>
 </div>
 ))}
 </div>
 </div>

 {/* Divider */}
 <div className="border-t border-[var(--color-border)]" />

 {/* Milestones */}
 {goal.is_milestone_based && (
 <>
 <div className="p-4 sm:p-6 space-y-3">
 <div className="flex items-center justify-between">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("goalsPage.sidePanel.milestones")}
 </h3>
 {milestones.length > 0 && (
 <span className="text-xs text-content-tertiary">
 {t("goalsPage.sidePanel.milestonesCount", {
 count: milestones.length,
 })}
 </span>
 )}
 </div>

 {milestonesLoading ? (
 <div className="flex justify-center py-4">
 <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
 </div>
 ) : milestones.length === 0 ? (
 <p className="text-sm text-content-tertiary italic py-2">
 {t("goalsPage.sidePanel.noMilestones")}
 </p>
 ) : (
 <div className="rounded-lg border border-[var(--color-border)] overflow-x-auto">
 <table className="w-full">
 <thead className="bg-surface-alt">
 <tr>
 <th className="px-3 py-2 text-left text-xs font-medium text-content-secondary">
 {t("goalsPage.sidePanel.milestoneTitle")}
 </th>
 <th className="px-3 py-2 text-right text-xs font-medium text-content-secondary">
 {t("goalsPage.sidePanel.milestoneTarget")}
 </th>
 <th className="px-3 py-2 text-right text-xs font-medium text-content-secondary">
 {t("goalsPage.sidePanel.milestoneCurrent")}
 </th>
 <th className="px-3 py-2 text-left text-xs font-medium text-content-secondary">
 {t("goalsPage.sidePanel.milestoneStatus")}
 </th>
 </tr>
 </thead>
 <tbody className="divide-y border-[var(--color-border)]">
 {milestones.map((milestone) => (
 <tr key={milestone.id}>
 <td className="px-3 py-2 text-sm text-content">
 {milestone.title}
 </td>
 <td className="px-3 py-2 text-sm text-content-secondary tabular-nums text-right">
 {formatAmount(
 milestone.target_amount,
 goal.currency,
 )}
 </td>
 <td className="px-3 py-2 text-sm tabular-nums text-right text-success-base/80">
 {formatAmount(
 milestone.current_amount,
 goal.currency,
 )}
 </td>
 <td className="px-3 py-2">
 <Badge
 variant={
 getMilestoneBadgeVariant(milestone) as any
 }
 size="sm"
 >
 {milestone.is_completed
 ? t("goalsPage.sidePanel.milestoneCompleted")
 : t("goalsPage.sidePanel.milestonePending")}
 </Badge>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 )}
 </div>

 <div className="border-t border-[var(--color-border)]" />
 </>
 )}

 {/* Projection */}
 <div className="p-4 sm:p-6 space-y-3">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("goalsPage.sidePanel.projection")}
 </h3>
 <div className="space-y-3">
 <div className="flex items-center justify-between">
 <span className="text-sm text-content-secondary">
 {t("goalsPage.sidePanel.requiredMonthly")}
 </span>
 <span className="text-sm font-medium text-content tabular-nums">
 {requiredMonthly !== null
 ? formatAmount(requiredMonthly, goal.currency)
 : "\u2014"}
 </span>
 </div>
 <div className="flex items-center justify-between">
 <span className="text-sm text-content-secondary">
 {t("goalsPage.sidePanel.projectedCompletion")}
 </span>
 <span className="text-sm font-medium text-content">
 {goal.progress_percentage >= 100
 ? t("goalsPage.filters.completed")
 : projectedCompletion
 ? projectedCompletion
 : goal.target_date
 ? "\u2014"
 : t("goalsPage.sidePanel.noTargetDate")}
 </span>
 </div>
 </div>
 </div>

 {/* Divider */}
 <div className="border-t border-[var(--color-border)]" />

 {/* Notes */}
 <div className="p-4 sm:p-6 space-y-2">
 <h3 className="text-sm font-semibold text-content uppercase tracking-wide">
 {t("goalsPage.sidePanel.notes")}
 </h3>
 <p
 className={`text-sm ${goal.description ? "text-content-secondary" : "text-content-tertiary italic"}`}
 >
 {goal.description || t("goalsPage.sidePanel.noNotes")}
 </p>
 </div>
 </div>

 {/* Action Footer - sticky */}
 <div className="border-t border-[var(--color-border)] p-4 sm:p-6 flex-shrink-0">
 <div className="flex flex-wrap gap-2">
 <Button
 variant="primary"
 size="sm"
 onClick={onUpdateProgress}
 className="flex-1 sm:flex-none"
 >
 {t("goalsPage.sidePanel.updateProgress")}
 </Button>
 {canToggle && (
 <Button
 variant={isPaused ? "outline" : "outline"}
 size="sm"
 onClick={onPauseResume}
 >
 {isPaused
 ? t("goalsPage.sidePanel.resume")
 : t("goalsPage.sidePanel.pause")}
 </Button>
 )}
 <Button variant="ghost" size="sm" onClick={onEdit}>
 {t("goalsPage.sidePanel.edit")}
 </Button>
 <Button
 variant="ghost"
 size="sm"
 onClick={onDelete}
 className="text-danger-base hover:text-danger-base-hover"
 >
 {t("goalsPage.sidePanel.delete")}
 </Button>
 </div>
 </div>
 </div>
 </>
 );
};
