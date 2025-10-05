import { expect, Locator, Page } from "@playwright/test";
import { BasePage } from "../BasePage";

export class HeaderComponent extends BasePage {
  header: Locator
  loginButton: Locator
  registerButton: Locator
  constructor(page: Page) {
    super(page);
    this.header = this.getByTestId('desktop-header')
    this.loginButton = this.header.getByTestId('login-modal-trigger')
    this.registerButton = this.header.getByTestId('register-modal-trigger')
  }

  async expectUserAuthorized(): Promise<void> {
    await expect(this.loginButton).toBeHidden()
    await expect(this.registerButton).toBeHidden()
  }

  async expectUserUnauthorized(): Promise<void> {
    await expect(this.loginButton).toBeVisible()
    await expect(this.registerButton).toBeVisible()
  }

}