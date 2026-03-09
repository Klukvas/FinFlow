import React from "react";
import {
 FaEnvelope,
 FaGlobe,
 FaMapMarkerAlt,
 FaBuilding,
} from "react-icons/fa";
import { Button } from "@/components/ui/shared/Button";
import { useTranslation } from "react-i18next";
import { SEOHead, SEOConfigs } from "@/components/seo/SEOHead";

export const Contact: React.FC = () => {
 const { t } = useTranslation();

 const faqQuestions = t("contactPage.faq.questions", {
 returnObjects: true,
 }) as Array<{ question: string; answer: string }>;

 const faqStructuredData = {
 "@context": "https://schema.org",
 "@type": "FAQPage",
 mainEntity: Array.isArray(faqQuestions)
 ? faqQuestions.map((faq) => ({
 "@type": "Question",
 name: faq.question,
 acceptedAnswer: {
 "@type": "Answer",
 text: faq.answer,
 },
 }))
 : [],
 };

 const contactInfo = [
 {
 icon: FaBuilding,
 title: t("contactPage.contactInfo.company.title"),
 value: t("contactPage.contactInfo.company.value"),
 description: t("contactPage.contactInfo.company.description"),
 },
 {
 icon: FaEnvelope,
 title: t("contactPage.contactInfo.email.title"),
 value: "finflow@flux-lab.dev",
 description: t("contactPage.contactInfo.email.description"),
 isLink: true,
 href: "mailto:finflow@flux-lab.dev",
 },
 {
 icon: FaGlobe,
 title: t("contactPage.contactInfo.website.title"),
 value: "https://finflow.ltd",
 description: t("contactPage.contactInfo.website.description"),
 isLink: true,
 href: "https://finflow.ltd",
 },
 {
 icon: FaMapMarkerAlt,
 title: t("contactPage.contactInfo.address.title"),
 value: t("contactPage.contactInfo.address.value"),
 description: t("contactPage.contactInfo.address.description"),
 },
 ];

 return (
 <>
 <SEOHead
 {...SEOConfigs.contact}
 url="https://finflow.ltd/contact"
 structuredData={faqStructuredData}
 />
 <div className="py-20 px-6">
 <div className="max-w-7xl mx-auto">
 <div className="text-center mb-16">
 <h1 className="text-4xl font-bold text-content mb-6">
 {t("contactPage.title")}
 </h1>
 <p className="text-xl text-content-secondary max-w-3xl mx-auto">
 {t("contactPage.subtitle")}
 </p>
 </div>

 <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
 {/* Contact Information */}
 <div>
 <h2 className="text-2xl font-bold text-content mb-8">
 {t("contactPage.contactInfo.title")}
 </h2>

 <div className="space-y-6">
 {contactInfo.map((info, index) => {
 const Icon = info.icon;
 return (
 <div key={index} className="flex items-start">
 <div className="bg-accent-base w-12 h-12 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
 <Icon className="w-6 h-6 text-content-inverse" />
 </div>
 <div>
 <h3 className="text-lg font-semibold text-content mb-1">
 {info.title}
 </h3>
 {info.isLink && info.href ? (
 <a
 href={info.href}
 target={
 info.href.startsWith("http")
 ? "_blank"
 : undefined
 }
 rel={
 info.href.startsWith("http")
 ? "noopener noreferrer"
 : undefined
 }
 className="text-accent-base hover:underline font-medium mb-1 block"
 >
 {info.value}
 </a>
 ) : (
 <p className="text-content font-medium mb-1">
 {info.value}
 </p>
 )}
 <p className="text-content-secondary text-sm">
 {info.description}
 </p>
 </div>
 </div>
 );
 })}
 </div>

 <div className="mt-8 bg-elevated border-[var(--color-border)] border rounded-lg p-6">
 <h3 className="text-lg font-semibold text-content mb-4">
 {t("contactPage.faq.title")}
 </h3>
 <div className="space-y-3">
 {faqQuestions.map((faq, index: number) => (
 <div key={index}>
 <p className="text-content font-medium mb-1">
 {faq.question}
 </p>
 <p className="text-content-secondary text-sm">
 {faq.answer}
 </p>
 </div>
 ))}
 </div>
 </div>
 </div>

 {/* Contact Form */}
 <div>
 <h2 className="text-2xl font-bold text-content mb-8">
 {t("contactPage.form.title")}
 </h2>

 <form className="space-y-6">
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
 <div>
 <label className="block text-sm font-medium text-content mb-2">
 {t("contactPage.form.name")}
 </label>
 <input
 type="text"
 className="w-full px-3 py-2 border-[var(--color-border)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)] bg-surface text-content"
 placeholder={t("contactPage.form.namePlaceholder")}
 />
 </div>
 <div>
 <label className="block text-sm font-medium text-content mb-2">
 {t("contactPage.form.email")}
 </label>
 <input
 type="email"
 className="w-full px-3 py-2 border-[var(--color-border)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)] bg-surface text-content"
 placeholder={t("contactPage.form.emailPlaceholder")}
 />
 </div>
 </div>

 <div>
 <label className="block text-sm font-medium text-content mb-2">
 {t("contactPage.form.subject")}
 </label>
 <input
 type="text"
 className="w-full px-3 py-2 border-[var(--color-border)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)] bg-surface text-content"
 placeholder={t("contactPage.form.subjectPlaceholder")}
 />
 </div>

 <div>
 <label className="block text-sm font-medium text-content mb-2">
 {t("contactPage.form.message")}
 </label>
 <textarea
 rows={6}
 className="w-full px-3 py-2 border-[var(--color-border)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)] bg-surface text-content resize-none"
 placeholder={t("contactPage.form.messagePlaceholder")}
 ></textarea>
 </div>

 <Button type="submit" size="lg" fullWidth>
 {t("contactPage.form.submit")}
 </Button>
 </form>
 </div>
 </div>
 </div>
 </div>
 </>
 );
};
