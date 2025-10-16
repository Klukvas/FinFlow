import { chromium, FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Set base URL
    const baseURL = config.projects[0].use.baseURL || 'http://localhost:5173';

    // Navigate to the application
    await page.goto(baseURL);
    await page.waitForLoadState('networkidle');

    // You can add cleanup here:
    // - Delete test users
    // - Clear test data
    // - Reset test environment
    // - Clean up any created resources

    // Example: Clear test data
    // await clearTestData(page);


  } catch (error) {
    console.error('Global teardown failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  } finally {
    await browser.close();
  }
}

export default globalTeardown;

