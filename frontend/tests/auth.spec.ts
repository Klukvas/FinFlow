import { test, expect } from '@playwright/test';
import { AuthActions } from './interface/AuthActions';
import { NavigationActions } from './interface/NavigationActions';
import { SidebarInterface } from './interface/SidebarInterface';

// Define UserCredentials interface locally to avoid import issues
interface UserCredentials {
  email: string;
  password: string;
}

// Test data
const validUser: UserCredentials = {
  email: 'root@root.root',
  password: 'Sololane56457!'
};

const invalidUser: UserCredentials = {
  email: 'invalid@example.com',
  password: 'wrongpassword'
};

const newUser = {
  username: 'newuser123',
  email: 'newuser@example.com',
  password: 'SupaPupaStrongBibasPassword83218034!'
};

test.describe('Authentication', () => {
  let auth: AuthActions;
  let navigation: NavigationActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    await page.goto('')
    auth = new AuthActions(page)
    navigation = new NavigationActions(page);
    sidebar = new SidebarInterface(page);
  });

  test('should login with valid credentials', async ({ page }) => {
    await auth.login(validUser.email, validUser.password);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await auth.loginAndExpectFailure(invalidUser.email, invalidUser.password)
  });

  test('should close login modal', async ({ page }) => {
    await auth.openLoginModal()
    await auth.closeLoginModal()
  });

  test('should switch between login and register modals', async ({ page }) => {
    await auth.openLoginModal()
    await auth.swithFromLoginToRegisterModal()
  });

  test('should register new user', async ({ page }) => {
    await auth.register(newUser.username, newUser.email, newUser.password);
    await page.waitForURL('**/category**');
  });

  // test('should validate registration form', async ({ page }) => {
  //   await navigation.goto('category');

  //   // Open register modal
  //   await auth.openRegisterModal(); await auth.expectRegisterModalVisible(); await auth.expectRegisterFormElementsVisible();

  //   // Try to submit empty form
  //   await auth.submitRegister();

  //   // Verify validation errors
  //   await auth.expectUsernameInputError();
  //   await auth.expectEmailInputError();
  //   await auth.expectPasswordInputError();

  //   // Verify register button is disabled
  //   await auth.expectRegisterButtonDisabled();
  // });

  // test('should validate password strength', async ({ page }) => {
  //   await navigation.goto('category');

  //   // Open register modal
  //   await auth.openRegisterModal(); await auth.expectRegisterModalVisible(); await auth.expectRegisterFormElementsVisible();

  //   // Try weak passwords
  //   const weakPasswords = ['123', 'password', '12345678'];

  //   for (const password of weakPasswords) {
  //     await auth.clearPasswordInput();
  //     await auth.fillRegisterForm('username', 'email@test.com', password);
      
  //     // Trigger validation
  //     await auth.submitRegister();
      
  //     // Verify error message
  //     await auth.expectPasswordInputError();
  //   }
  // });

  // test('should logout user', async ({ page }) => {
  //   // Login first
  //   await auth.login(validUser);
  //   expect(page.url()).toContain('/category');

  //   // Verify user is logged in
  //   await sidebar.expectUserLoggedIn();

  //   // Logout using sidebar
  //   await sidebar.performLogout();

  //   // Should be redirected to homepage
  //   expect(page.url()).toContain('/');
    
  //   // Verify user is logged out
  //   await sidebar.expectUserLoggedOut();
  // });

  // test('should handle session expiration', async ({ page }) => {
  //   // Login first
  //   await auth.login(validUser);
  //   expect(page.url()).toContain('/category');

  //   // Clear localStorage to simulate session expiration
  //   await page.evaluate(() => { localStorage.clear(); });

  //   // Try to navigate to protected page
  //   await navigation.goto('category');

  //   // Should be redirected to homepage
  //   expect(page.url()).toContain('/');
    
  //   // Verify login modal can be opened
  //   await auth.openLoginModal(); await auth.expectLoginModalVisible(); await auth.expectLoginFormElementsVisible();
  // });

  // test('should remember user login state on page refresh', async ({ page }) => {
  //   // Login first
  //   await auth.login(validUser);
  //   expect(page.url()).toContain('/category');

  //   // Refresh page
  //   await page.reload();

  //   // Should still be logged in
  //   expect(page.url()).toContain('/category');
  //   await sidebar.expectUserLoggedIn();
  //   await auth.expectLoginModalTriggerHidden();
  // });

  // test('should redirect to intended page after login', async ({ page }) => {
  //   // Try to access protected page without login
  //   await sidebar.navigateToExpense();

  //   // Should be redirected to homepage
  //   expect(page.url()).toContain('/');

  //   // Login
  //   await auth.performLogin(validUser.email, validUser.password);

  //   // Should be redirected to the originally requested page
  //   await page.waitForURL('**/expense**');
  //   expect(page.url()).toContain('/expense');
  // });

  // test('should show loading state during authentication', async ({ page }) => {
  //   await navigation.goto('category');

  //   // Open login modal
  //   await auth.openLoginModal(); await auth.expectLoginModalVisible(); await auth.expectLoginFormElementsVisible();

  //   // Fill form
  //   await auth.fillLoginForm(validUser.email, validUser.password);

  //   // Click login and check for loading state
  //   await auth.submitLogin();
    
  //   // Verify loading spinner appears
  //   await auth.expectLoginButtonLoading();
  // });
});

