import { test, expect } from '@playwright/test';
import { AuthActions } from '../../interface/AuthActions';
import { NavigationActions } from '../../interface/NavigationActions';
import { SidebarInterface } from '../../interface/SidebarInterface';

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

test.describe('Sign Up Flow', () => {
  let auth: AuthActions;
  let navigation: NavigationActions;
  let sidebar: SidebarInterface;

  test.beforeEach(async ({ page }) => {
    await page.goto('')
    auth = new AuthActions(page)
    navigation = new NavigationActions(page);
    sidebar = new SidebarInterface(page);
  });


  test('should register new user', async ({ page }) => {
    await auth.register(newUser.username, newUser.email, newUser.password);
    await page.waitForURL('**/category**');
  });

  test.describe('Validation', () => {
    test('Email validation', async () => {
      await auth.registerAndExpectValidationFailure(
        newUser.username, 
        'invalid-email', 
        newUser.password, 
        'Please enter a valid email address'
      );
    });

    test.describe('Password validation', () => {
      test('Password validation (no uppercase letter)', async () => {
        await auth.openRegisterModal()
        await auth.registerModal.fillForm(
          newUser.username, 
          newUser.email, 
          'invalid-password'
        );
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          'Password must contain at least one uppercase letter'
        );
      });
      test('Password validation (less than 8 characters)', async () => {
        await auth.openRegisterModal()
        await auth.registerModal.fillForm(
          newUser.username, 
          newUser.email, 
          'invalid'
        );
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          'Password must be at least 8 characters long'
        );
      });
      test('Password validation (no number)', async () => {
        await auth.openRegisterModal()
        await auth.registerModal.fillForm(
          newUser.username, 
          newUser.email, 
          'passwordWithoutNumbers!'
        );
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          'Password must contain at least one number'
        );
      });
      test('Password validation (no special character)', async () => {
        await auth.openRegisterModal()
        await auth.registerModal.fillForm(
          newUser.username, 
          newUser.email, 
          'passwordWithoutNumbers123'
        );
        await auth.registerModal.emailInput.click();
        await auth.registerModal.expectPasswordInputError(
          'Password must contain at least one special character'
        );
      });
    })

    
  });

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

