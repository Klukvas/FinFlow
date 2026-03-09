import React from "react";
import { Link } from "react-router-dom";
import { FaEnvelope } from "react-icons/fa";
import { useTranslation } from "react-i18next";

export const PublicFooter: React.FC = () => {
 const { t } = useTranslation();
 const currentYear = new Date().getFullYear();

 const footerLinks = {
 product: [
 { label: t("footer.links.product.features"), href: "/features" },
 { label: t("footer.links.product.pricing"), href: "/pricing" },
 { label: t("footer.links.product.blog"), href: "/blog" },
 ],
 platform: [
 { label: t("footer.links.platform.architecture"), href: "/about" },
 { label: t("footer.links.platform.security"), href: "/about" },
 ],
 company: [
 { label: t("footer.links.company.about"), href: "/about" },
 { label: t("footer.links.company.contact"), href: "/contact" },
 ],
 legal: [
 { label: t("footer.links.legal.privacy"), href: "/privacy" },
 { label: t("footer.links.legal.terms"), href: "/terms" },
 { label: t("footer.links.legal.refund"), href: "/refund" },
 ],
 };

 const socialLinks = [
 { icon: FaEnvelope, href: "mailto:finflow@flux-lab.dev", label: "Email" },
 ];

 return (
 <footer className="bg-elevated border-[var(--color-border)] border-t transition-colors">
 <div className="max-w-6xl mx-auto px-6 py-12">
 <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-8">
 {/* Brand Section */}
 <div className="col-span-2 sm:col-span-3 lg:col-span-1">
 <h3 className="text-base font-bold text-content mb-3">
 {t("footer.brand.title")}
 </h3>
 <p className="text-content-secondary text-sm mb-4 leading-relaxed">
 {t("footer.brand.description")}
 </p>
 <div className="flex space-x-3 mb-4">
 {socialLinks.map((social) => {
 const Icon = social.icon;
 return (
 <a
 key={social.label}
 href={social.href}
 target="_blank"
 rel="noopener noreferrer"
 className="text-content-tertiary hover:text-content transition-colors"
 title={social.label}
 >
 <Icon className="w-4 h-4" />
 </a>
 );
 })}
 </div>
 <a
 href="mailto:finflow@flux-lab.dev"
 className="text-sm text-content-tertiary hover:text-content transition-colors"
 >
 finflow@flux-lab.dev
 </a>
 </div>

 {/* Product Links */}
 <div>
 <h4 className="text-sm font-semibold text-content mb-3">
 {t("footer.sections.product")}
 </h4>
 <ul className="space-y-2">
 {footerLinks.product.map((link) => (
 <li key={link.label}>
 <Link
 to={link.href}
 className="text-content-secondary hover:text-content text-sm transition-colors"
 >
 {link.label}
 </Link>
 </li>
 ))}
 </ul>
 </div>

 {/* Platform Links */}
 <div>
 <h4 className="text-sm font-semibold text-content mb-3">
 {t("footer.sections.platform")}
 </h4>
 <ul className="space-y-2">
 {footerLinks.platform.map((link) => (
 <li key={link.label}>
 <Link
 to={link.href}
 className="text-content-secondary hover:text-content text-sm transition-colors"
 >
 {link.label}
 </Link>
 </li>
 ))}
 </ul>
 </div>

 {/* Company Links */}
 <div>
 <h4 className="text-sm font-semibold text-content mb-3">
 {t("footer.sections.company")}
 </h4>
 <ul className="space-y-2">
 {footerLinks.company.map((link) => (
 <li key={link.label}>
 <Link
 to={link.href}
 className="text-content-secondary hover:text-content text-sm transition-colors"
 >
 {link.label}
 </Link>
 </li>
 ))}
 </ul>
 </div>

 {/* Legal Links */}
 <div>
 <h4 className="text-sm font-semibold text-content mb-3">
 {t("footer.sections.legal")}
 </h4>
 <ul className="space-y-2">
 {footerLinks.legal.map((link) => (
 <li key={link.label}>
 <Link
 to={link.href}
 className="text-content-secondary hover:text-content text-sm transition-colors"
 >
 {link.label}
 </Link>
 </li>
 ))}
 </ul>
 </div>
 </div>

 {/* Bottom Section */}
 <div className="mt-10 pt-6 border-[var(--color-border)] border-t">
 <div className="flex flex-col sm:flex-row justify-between items-center gap-2">
 <p className="text-content-tertiary text-xs">
 {t("footer.bottom.copyright", { year: currentYear })}
 </p>
 <p className="text-content-tertiary text-xs">
 {t("footer.bottom.madeWith")}
 </p>
 </div>
 </div>
 </div>
 </footer>
 );
};
