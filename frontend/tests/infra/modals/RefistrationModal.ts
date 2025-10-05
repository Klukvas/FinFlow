import { expect, Locator, Page } from "@playwright/test";
import { BasePage } from "../BasePage";

export class RegistrationModal extends BasePage {
    modal: Locator
    usernameInput: Locator
    emailInput: Locator
    passwordInput: Locator
    closeButton: Locator
    switchToLogin: Locator
    submitButton: Locator
    constructor(page: Page) {
        super(page);
        this.modal = this.getByTestId('register-modal')
        this.usernameInput = this.page.getByTestId('username-input')
        this.emailInput = this.page.getByTestId('email-input')
        this.passwordInput = this.page.getByTestId('password-input')
        this.submitButton = this.page.getByTestId('submit-register-button')
    }

    async expectModal(){
        await expect(this.modal).toBeVisible()
        await expect(this.usernameInput).toBeVisible()
        await expect(this.emailInput).toBeVisible()
        await expect(this.passwordInput).toBeVisible()
        await expect(this.submitButton).toBeVisible()
    }

    async fillForm(username: string, email: string, password: string): Promise<void> {
        await this.usernameInput.fill(username)
        await this.emailInput.fill(email)
        await this.passwordInput.fill(password)
    }

}