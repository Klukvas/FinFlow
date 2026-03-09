import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";
import { SEOHead, SEOConfigs } from "@/components/seo/SEOHead";

export const PrivacyPolicy: React.FC = () => {
 const { t } = useTranslation();

 const sections = [
 {
 title: t("privacyPage.sections.dataCollection.title"),
 content: [
 t("privacyPage.sections.dataCollection.item1"),
 t("privacyPage.sections.dataCollection.item2"),
 t("privacyPage.sections.dataCollection.item3"),
 t("privacyPage.sections.dataCollection.item4"),
 t("privacyPage.sections.dataCollection.item5"),
 ],
 },
 {
 title: t("privacyPage.sections.dataUsage.title"),
 content: [
 t("privacyPage.sections.dataUsage.item1"),
 t("privacyPage.sections.dataUsage.item2"),
 t("privacyPage.sections.dataUsage.item3"),
 t("privacyPage.sections.dataUsage.item4"),
 t("privacyPage.sections.dataUsage.item5"),
 t("privacyPage.sections.dataUsage.item6"),
 ],
 },
 {
 title: t("privacyPage.sections.thirdParty.title"),
 content: [
 t("privacyPage.sections.thirdParty.item1"),
 t("privacyPage.sections.thirdParty.item2"),
 t("privacyPage.sections.thirdParty.item3"),
 t("privacyPage.sections.thirdParty.item4"),
 ],
 },
 {
 title: t("privacyPage.sections.dataSecurity.title"),
 content: [
 t("privacyPage.sections.dataSecurity.item1"),
 t("privacyPage.sections.dataSecurity.item2"),
 t("privacyPage.sections.dataSecurity.item3"),
 t("privacyPage.sections.dataSecurity.item4"),
 t("privacyPage.sections.dataSecurity.item5"),
 ],
 },
 {
 title: t("privacyPage.sections.cookies.title"),
 content: [
 t("privacyPage.sections.cookies.item1"),
 t("privacyPage.sections.cookies.item2"),
 t("privacyPage.sections.cookies.item3"),
 ],
 },
 {
 title: t("privacyPage.sections.userRights.title"),
 content: [
 t("privacyPage.sections.userRights.item1"),
 t("privacyPage.sections.userRights.item2"),
 t("privacyPage.sections.userRights.item3"),
 t("privacyPage.sections.userRights.item4"),
 ],
 },
 {
 title: t("privacyPage.sections.dataRetention.title"),
 content: [
 t("privacyPage.sections.dataRetention.item1"),
 t("privacyPage.sections.dataRetention.item2"),
 ],
 },
 {
 title: t("privacyPage.sections.changes.title"),
 content: [
 t("privacyPage.sections.changes.item1"),
 t("privacyPage.sections.changes.item2"),
 ],
 },
 {
 title: t("privacyPage.sections.contact.title"),
 content: [t("privacyPage.sections.contact.item1")],
 },
 ];

 return (
 <>
 <SEOHead {...SEOConfigs.privacyPolicy} />
 <div className="min-h-screen bg-surface">
 <div className="max-w-4xl mx-auto px-6 py-12">
 {/* Back link */}
 <Link
 to="/"
 className="inline-flex items-center gap-2 text-content-secondary hover:text-content transition-colors mb-8"
 >
 <FaArrowLeft className="w-4 h-4" />
 {t("privacyPage.backToHome")}
 </Link>

 {/* Header */}
 <div className="mb-12">
 <h1 className="text-3xl md:text-4xl font-bold text-content mb-4">
 {t("privacyPage.title")}
 </h1>
 <p className="text-content-secondary">
 {t("privacyPage.lastUpdated")}: {t("privacyPage.updateDate")}
 </p>
 </div>

 {/* Introduction */}
 <div className="bg-elevated border-[var(--color-border)] border rounded-xl p-6 mb-8">
 <p className="text-content-secondary leading-relaxed">
 {t("privacyPage.intro")}
 </p>
 <p className="text-content-secondary leading-relaxed mt-4">
 {t("privacyPage.acceptance")}
 </p>
 </div>

 {/* Sections */}
 <div className="space-y-8">
 {sections.map((section, index) => (
 <div
 key={index}
 className="bg-elevated border-[var(--color-border)] border rounded-xl p-6"
 >
 <h2 className="text-xl font-semibold text-content mb-4 flex items-center gap-3">
 <span className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-accent-light)] text-accent-base text-sm font-bold">
 {index + 1}
 </span>
 {section.title}
 </h2>
 <div className="space-y-3 ml-11">
 {section.content.map((item, itemIndex) => (
 <p
 key={itemIndex}
 className="text-content-secondary leading-relaxed"
 >
 {index === 8 ? (
 item
 ) : (
 <span className="flex gap-2">
 <span className="text-accent-base">&bull;</span>
 {item}
 </span>
 )}
 </p>
 ))}
 </div>
 </div>
 ))}
 </div>

 {/* Footer */}
 <div className="mt-12 pt-8 border-[var(--color-border)] border-t text-center">
 <p className="text-content-tertiary text-sm">
 {t("privacyPage.footer")}
 </p>
 </div>
 </div>
 </div>
 </>
 );
};

export default PrivacyPolicy;
