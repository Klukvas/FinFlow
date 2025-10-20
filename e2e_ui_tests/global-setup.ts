import { chromium, FullConfig } from '@playwright/test';
import { UserApiActions } from './interface/api/UserApiActions';
import { UserApiClient } from './infra/api/UserApiClient';
import { users } from './users';

async function createTestUsers(){
  const userApi = new UserApiActions(new UserApiClient('http://localhost:8001'));
  await userApi.registerMultipleUsers(users);
}


async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  // Set base URL
  const baseURL = config.projects[0].use.baseURL || 'http://localhost:3000';

  // Wait for the application to be ready
  await page.goto(baseURL);
  await page.waitForLoadState('networkidle');

  // Check if the application is running
  const isAppReady = await page.locator('body').isVisible();
  if (!isAppReady) {
    throw new Error('Application is not ready');
  }


  await createTestUsers();


  // You can add additional setup here:
  // - Create test users
  // - Set up test data
  // - Configure test environment
  // - Clear any existing test data

  // Example: Create a test user if needed
  // await createTestUser(page);


  await browser.close();
}

export default globalSetup;

