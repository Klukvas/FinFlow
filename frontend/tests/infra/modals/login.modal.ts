import { Locator, Page, expect } from '@playwright/test';
import { BasePage } from '../BasePage';

export class LoginModal extends BasePage {
  
  modal: Locator
  emailInput: Locator
  passwordInput: Locator
  loginButton: Locator
  closeButton: Locator
  loginError: Locator
  switchToRegister: Locator

  constructor(page: Page) {
    super(page);
    this.modal = this.page.getByTestId('login-modal')
    this.emailInput = this.modal.getByTestId('email-input')
    this.passwordInput = this.modal.getByTestId('password-input')
    this.loginButton = this.modal.getByTestId('submit-login-button')
    this.closeButton = this.modal.getByTestId('modal-close-button')
    this.loginError = this.modal.getByTestId('login-error')
    this.switchToRegister = this.modal.getByTestId('switch-to-register')
  }

  // Element expectations using expect
  async expectModal(): Promise<void> {
    await expect(this.modal).toBeVisible();
    await expect(this.emailInput).toBeVisible()
    await expect(this.passwordInput).toBeVisible()
    await expect(this.loginButton).toBeVisible()
    await expect(this.closeButton).toBeVisible()
    await expect(this.switchToRegister).toBeVisible()

  }

  async fillForm(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
  }

}