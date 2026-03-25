import React from "react";
import { useTranslation } from "react-i18next";
import DOMPurify from "dompurify";
import { AnalysisSection as AnalysisSectionType } from "@/types";

const PRIORITY_STYLES: Record<string, string> = {
 high: "bg-[var(--danger-dim)] text-danger-base",
 medium: "bg-[var(--warning-dim)] text-warning-base",
 low: "bg-[var(--success-dim)] text-success-base",
};

interface AnalysisSectionProps {
 section: AnalysisSectionType;
}

export const AnalysisSectionCard: React.FC<AnalysisSectionProps> = ({
 section,
}) => {
 const { t } = useTranslation();
 const priorityStyle =
 PRIORITY_STYLES[section.priority] || PRIORITY_STYLES.medium;

 const sanitizedHtml = DOMPurify.sanitize(formatMarkdown(section.content), {
 ALLOWED_TAGS: ["p", "strong", "em", "ul", "ol", "li", "br"],
 ALLOWED_ATTR: [],
 });

 return (
 <div className="p-4 rounded-lg border-[var(--border)] border">
 <div className="flex items-center gap-2 mb-3">
 <h3 className="text-sm font-semibold text-content">
 {section.title}
 </h3>
 <span
 className={`text-xs px-2 py-0.5 rounded-full font-medium ${priorityStyle}`}
 >
 {t(`aiAssistant.priority.${section.priority}`)}
 </span>
 </div>
 <div
 className="text-sm text-content-secondary prose prose-sm max-w-none
 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5
 [&_li]:mb-1 [&_p]:mb-2 [&_strong]:text-content"
 dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
 />
 </div>
 );
};

function formatMarkdown(text: string): string {
 return text
 .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
 .replace(/\*(.*?)\*/g, "<em>$1</em>")
 .replace(/^- (.+)$/gm, "<li>$1</li>")
 .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
 .replace(/<\/ul>\s*<ul>/g, "")
 .replace(/\n\n/g, "</p><p>")
 .replace(/\n/g, "<br>")
 .replace(/^(?!<[uol]|<li|<p|<br)(.+)$/gm, "<p>$1</p>");
}
