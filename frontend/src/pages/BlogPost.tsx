import React from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SEOHead } from "@/components/seo/SEOHead";
import { getPostBySlug } from "@/utils/blog";
import { config } from "@/config/env";
import { NotFound } from "./NotFound";

export const BlogPost: React.FC = () => {
 const { slug } = useParams<{ slug: string }>();
 const { t, i18n } = useTranslation();
 const post = slug ? getPostBySlug(slug) : undefined;

 if (!post) {
 return <NotFound />;
 }

 const structuredData = {
 "@context": "https://schema.org",
 "@type": "Article",
 headline: post.title,
 description: post.description,
 datePublished: post.date,
 author: {
 "@type": "Organization",
 name: post.author,
 },
 publisher: {
 "@type": "Organization",
 name: "FinFlow",
 url: config.app.url,
 },
 mainEntityOfPage: {
 "@type": "WebPage",
 "@id": `${config.app.url}/blog/${post.slug}`,
 },
 };

 return (
 <>
 <SEOHead
 title={post.title}
 description={post.description}
 keywords={post.tags.join(", ")}
 url={`${config.app.url}/blog/${post.slug}`}
 type="article"
 structuredData={structuredData}
 />

 <article className="py-20 px-6">
 <div className="max-w-3xl mx-auto">
 {/* Back link */}
 <Link
 to="/blog"
 className="inline-flex items-center text-sm text-accent-base hover:underline mb-8"
 >
 &larr; {t("blogPage.backToBlog")}
 </Link>

 {/* Article header */}
 <header className="mb-10">
 <div className="flex flex-wrap gap-2 mb-4">
 {post.tags.map((tag) => (
 <span
 key={tag}
 className="text-xs px-2 py-1 rounded-full bg-[var(--accent-dim)] text-accent-base font-medium"
 >
 {tag}
 </span>
 ))}
 </div>

 <h1 className="text-3xl md:text-4xl font-bold text-content mb-4 geometric-text leading-tight">
 {post.title}
 </h1>

 <div className="flex items-center gap-4 text-content-tertiary text-sm">
 <span>{post.author}</span>
 <span>&middot;</span>
 <time dateTime={post.date}>
 {t("blogPage.publishedOn")}{" "}
 {new Date(post.date).toLocaleDateString(i18n.language, {
 year: "numeric",
 month: "long",
 day: "numeric",
 })}
 </time>
 </div>
 </header>

 {/* Article body */}
 <div className="blog-prose">
 <Markdown remarkPlugins={[remarkGfm]}>{post.content}</Markdown>
 </div>

 {/* CTA Section */}
 <div className="mt-16 p-8 rounded-xl bg-[var(--accent-dim)] text-center">
 <h3 className="text-xl font-bold text-content mb-3">
 {t("blogPage.cta.title")}
 </h3>
 <p className="text-content-secondary mb-6 max-w-md mx-auto">
 {t("blogPage.cta.description")}
 </p>
 <Link
 to="/"
 className="inline-block px-6 py-3 rounded-lg bg-accent-base text-content-inverse hover:bg-accent-base-hover transition-colors font-medium"
 >
 {t("blogPage.cta.button")}
 </Link>
 </div>
 </div>
 </article>
 </>
 );
};
