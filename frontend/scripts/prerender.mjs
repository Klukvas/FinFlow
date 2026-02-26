#!/usr/bin/env node

/**
 * Prerender public pages to static HTML for SEO.
 * Run after `vite build`: node scripts/prerender.mjs
 *
 * This script:
 * 1. Starts a local server serving the built dist/ folder
 * 2. Uses Puppeteer to navigate to each public route
 * 3. Waits for the 'prerender-ready' event (dispatched by App.tsx)
 * 4. Saves the fully rendered HTML back to dist/
 */

import { createServer } from 'http';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import puppeteer from 'puppeteer';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST_DIR = join(__dirname, '..', 'dist');
const PORT = 4173;

const PUBLIC_ROUTES = [
  '/',
  '/about',
  '/features',
  '/pricing',
  '/contact',
  '/terms',
  '/privacy',
  '/refund',
];

// Simple static file server for the dist folder
function startServer() {
  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.txt': 'text/plain',
    '.xml': 'application/xml',
  };

  const server = createServer((req, res) => {
    let filePath = join(DIST_DIR, req.url === '/' ? 'index.html' : req.url);

    // SPA fallback: serve index.html for non-file routes
    if (!existsSync(filePath) || !filePath.includes('.')) {
      filePath = join(DIST_DIR, 'index.html');
    }

    try {
      const content = readFileSync(filePath);
      const ext = '.' + filePath.split('.').pop();
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
      res.end(content);
    } catch {
      res.writeHead(404);
      res.end('Not Found');
    }
  });

  return new Promise((resolve) => {
    server.listen(PORT, () => {
      console.log(`  Server running on http://localhost:${PORT}`);
      resolve(server);
    });
  });
}

async function prerenderRoute(browser, route) {
  const page = await browser.newPage();
  const url = `http://localhost:${PORT}${route}`;

  try {
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

    // Wait for the prerender-ready event or timeout after 5s
    await page.evaluate(() => {
      return new Promise((resolve) => {
        if (document.__PRERENDER_READY) {
          resolve();
          return;
        }
        document.addEventListener('prerender-ready', resolve, { once: true });
        setTimeout(resolve, 5000);
      });
    });

    // Small delay for any final renders
    await new Promise((r) => setTimeout(r, 500));

    const html = await page.content();

    // Determine output path
    const outputDir = route === '/'
      ? DIST_DIR
      : join(DIST_DIR, route);

    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true });
    }

    const outputPath = join(outputDir, 'index.html');
    writeFileSync(outputPath, html, 'utf-8');
    console.log(`  Prerendered: ${route} -> ${outputPath.replace(DIST_DIR, 'dist')}`);
  } catch (error) {
    console.error(`  Failed to prerender ${route}:`, error.message);
  } finally {
    await page.close();
  }
}

async function main() {
  console.log('\nPrerendering public pages...\n');

  // Verify dist exists
  if (!existsSync(join(DIST_DIR, 'index.html'))) {
    console.error('Error: dist/index.html not found. Run "vite build" first.');
    process.exit(1);
  }

  const server = await startServer();

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    for (const route of PUBLIC_ROUTES) {
      await prerenderRoute(browser, route);
    }
    console.log(`\nPrerendered ${PUBLIC_ROUTES.length} pages successfully.\n`);
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((error) => {
  console.error('Prerender failed:', error);
  process.exit(1);
});
