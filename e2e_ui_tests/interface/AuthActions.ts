import { expect, Page } from "@playwright/test";
import { LoginModal } from "../infra/modals";
import { HeaderComponent } from "../infra/components/header.component";
import { SidebarComponent } from "../infra/components/SidebarComponent";
import { RegistrationModal } from "../infra/modals/RefistrationModal";

export class AuthActions {
  page: Page;
  loginModal: LoginModal;
  header: HeaderComponent;
  sideBar: SidebarComponent;
  registerModal: RegistrationModal;

  constructor(page: Page) {
    this.page = page;
    this.loginModal = new LoginModal(page);
    this.header = new HeaderComponent(page);
    this.sideBar = new SidebarComponent(page);
    this.registerModal = new RegistrationModal(page);
  }

  async login(email: string, password: string): Promise<void> {
    await this.openLoginModal();
    await this.loginModal.fillForm(email, password);
    await this.loginModal.loginButton.click();
    // Wait for login to complete - modal closes and page navigates
    await expect(this.loginModal.modal).toBeHidden({ timeout: 15000 });
    await this.page.waitForLoadState("networkidle");
    await this.dismissTutorialIfPresent();
  }

  async expectUserAuthorized(): Promise<void> {
    await this.header.expectUserAuthorized();
    await this.sideBar.expectComponent();
  }

  async register(email: string, password: string): Promise<void> {
    await this.openRegisterModal();
    await this.registerModal.fillForm(email, password);
    await this.registerModal.submitButton.click();
    // Wait for registration to complete
    await expect(this.registerModal.modal).toBeHidden({ timeout: 15000 });
    await this.page.waitForLoadState("networkidle");
    await this.dismissTutorialIfPresent();
  }

  async registerAndExpectEmailValidationFailure(
    email: string,
    password: string,
    errorMessage?: string,
  ): Promise<void> {
    await this.openRegisterModal();
    await this.registerModal.emailInput.fill(email);
    // Trigger email validation by blurring (clicking password field)
    await this.registerModal.passwordInput.click();
    await this.registerModal.expectEmailInputError(errorMessage);
  }

  async loginAndExpectFailure(
    email: string,
    password: string,
    errorMessage?: string,
  ): Promise<void> {
    await this.openLoginModal();
    await this.loginModal.fillForm(email, password);
    await this.loginModal.loginButton.click();
    await expect(this.loginModal.loginError).toBeVisible();
    if (errorMessage) {
      await expect(this.loginModal.loginError).toHaveText(errorMessage);
    }
  }

  async openLoginModal() {
    await this.header.expectUserUnauthorized();
    await this.header.loginButton.click();
    await this.loginModal.expectModal();
  }

  async closeLoginModal() {
    await this.loginModal.closeButton.click();
  }

  async swithFromLoginToRegisterModal() {
    await this.loginModal.switchToRegister.click();
    await this.registerModal.expectModal();
  }

  async swithFromRegisterToLoginModal() {
    await this.registerModal.switchToLogin.click();
    await this.loginModal.expectModal();
  }

  async openRegisterModal() {
    await this.header.registerButton.click();
    await this.registerModal.expectModal();
  }

  /**
   * Dismiss the onboarding tutorial overlay if it appears after login/register.
   * The tutorial auto-starts after 1s for users with tutorial_version < 1.
   */
  async dismissTutorialIfPresent(): Promise<void> {
    const tutorialOverlay = this.page.locator(
      'div[role="dialog"][aria-modal="true"].fixed',
    );
    try {
      await tutorialOverlay.waitFor({ state: "visible", timeout: 3000 });
      await this.page.keyboard.press("Escape");
      await tutorialOverlay.waitFor({ state: "hidden", timeout: 5000 });
    } catch {
      // Tutorial not present, continue
    }
  }
}
