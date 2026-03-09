import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { SEOHead, SEOConfigs } from "@/components/seo/SEOHead";
import { getAllPosts } from "@/utils/blog";
import { config } from "@/config/env";

const ANIMATION_DELAYS = ["", "delay-100", "delay-200", "delay-300"];

export const Blog: React.FC = () => {
 const { t, i18n } = useTranslation();
 const posts = useMemo(() => getAllPosts(), []);

 return (
 <>
 <SEOHead {...SEOConfigs.blog} url={`${config.app.url}/blog`} />

 <section className="py-20 px-6">
 <div className="max-w-5xl mx-auto">
 {/* Header */}
 <div className="text-center mb-16 fade-up">
 <h1 className="text-4xl md:text-5xl font-bold text-content mb-4 geometric-text">
 {t("blogPage.title")}
 </h1>
 <p className="text-lg text-content-secondary max-w-2xl mx-auto">
 {t("blogPage.subtitle")}
 </p>
 </div>

 {/* Articles Grid */}
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
 {posts.map((post, index) => (
 <Link
 key={post.slug}
 to={`/blog/${post.slug}`}
 className={`group bg-elevated border-[var(--color-border)] border rounded-xl p-6 theme-shadow hover:theme-shadow-hover transition-colors fade-up ${
 ANIMATION_DELAYS[Math.min(index, ANIMATION_DELAYS.length - 1)]
 }`}
 >
 {/* Tags */}
 <div className="flex flex-wrap gap-2 mb-4">
 {post.tags.slice(0, 3).map((tag) => (
 <span
 key={tag}
 className="text-xs px-2 py-1 rounded-full bg-[var(--color-accent-light)] text-accent-base font-medium"
 >
 {tag}
 </span>
 ))}
 </div>

 {/* Title */}
 <h2 className="text-lg font-semibold text-content mb-2 group-hover:text-accent-base transition-colors line-clamp-2">
 {post.title}
 </h2>

 {/* Description */}
 <p className="text-sm text-content-secondary mb-4 line-clamp-3">
 {post.description}
 </p>

 {/* Meta */}
 <div className="flex items-center justify-between mt-auto">
 <time
 dateTime={post.date}
 className="text-xs text-content-tertiary"
 >
 {new Date(post.date).toLocaleDateString(i18n.language, {
 year: "numeric",
 month: "long",
 day: "numeric",
 })}
 </time>
 <span className="text-sm font-medium text-accent-base group-hover:underline">
 {t("blogPage.readMore")} &rarr;
 </span>
 </div>
 </Link>
 ))}
 </div>

 {/* Empty state */}
 {posts.length === 0 && (
 <div className="text-center py-16">
 <p className="text-content-secondary text-lg">
 {t("blogPage.noPosts")}
 </p>
 </div>
 )}
 </div>
 </section>
 </>
 );
};
