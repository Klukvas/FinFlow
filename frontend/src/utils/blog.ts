import yaml from "js-yaml";
import { logger } from "@/utils/logger";

/**
 * Browser-compatible frontmatter parser.
 * Replaces gray-matter which depends on Node.js Buffer.
 */
function parseFrontmatter(raw: string): {
  data: Record<string, unknown>;
  content: string;
} {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return { data: {}, content: raw };
  const data = (yaml.load(match[1]) ?? {}) as Record<string, unknown>;
  const content = raw.slice(match[0].length).trim();
  return { data, content };
}

export interface BlogPostMeta {
  slug: string;
  title: string;
  description: string;
  date: string;
  tags: string[];
  author: string;
}

export interface BlogPost extends BlogPostMeta {
  content: string;
}

const modules = import.meta.glob("/content/blog/*.md", {
  eager: true,
  query: "?raw",
  import: "default",
}) as Record<string, string>;

function toSafeSlug(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/[^a-z0-9\u0400-\u04FF-]/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-|-$/g, "");
}

function parsePost(filePath: string, raw: string): BlogPost | null {
  const { data, content } = parseFrontmatter(raw);
  const fileName = filePath.split("/").pop()?.replace(".md", "") ?? "";

  const title = typeof data.title === "string" ? data.title : null;
  const description =
    typeof data.description === "string" ? data.description : "";

  // js-yaml may parse "2026-02-25" as a Date object, so handle both
  const rawDate = data.date;
  const date =
    rawDate instanceof Date
      ? rawDate.toISOString().slice(0, 10)
      : typeof rawDate === "string" && !isNaN(Date.parse(rawDate))
        ? rawDate
        : null;
  const tags = Array.isArray(data.tags) ? (data.tags as string[]) : [];
  const author = typeof data.author === "string" ? data.author : "FinFlow";
  const rawSlug = typeof data.slug === "string" ? data.slug : fileName;
  const slug = toSafeSlug(rawSlug) || toSafeSlug(fileName);

  if (!title || !date || !slug) {
    logger.error(
      `[blog] Skipping "${filePath}": missing required frontmatter (title, date, slug)`,
    );
    return null;
  }

  return { slug, title, description, date, tags, author, content };
}

function parsePosts(): BlogPost[] {
  return Object.entries(modules).flatMap(([filePath, raw]) => {
    try {
      const result = parsePost(filePath, raw);
      return result ? [result] : [];
    } catch (err) {
      logger.error(`[blog] Failed to parse "${filePath}":`, err);
      return [];
    }
  });
}

let posts: BlogPost[] = [];
try {
  posts = parsePosts();
} catch (err) {
  logger.error("[blog] Failed to parse blog posts:", err);
}

export function getAllPosts(): BlogPostMeta[] {
  return [...posts]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .map(({ content: _, ...meta }) => meta);
}

export function getPostBySlug(slug: string): BlogPost | undefined {
  return posts.find((p) => p.slug === slug);
}
