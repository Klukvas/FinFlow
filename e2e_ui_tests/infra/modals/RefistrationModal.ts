import { expect, Locator, Page } from "@playwright/test";
import { BasePage } from "../BasePage";

export class RegistrationModal extends BasePage {
    modal: Locator
    emailInput: Locator
    passwordInput: Locator
    submitButton: Locator
    formFieldError: Locator
    switchToLogin: Locator
    constructor(page: Page) {
        super(page);
        this.modal = this.getByTestId('register-modal')
        this.emailInput = this.modal.getByTestId('email-input')
        this.passwordInput = this.modal.getByTestId('password-input')
        this.submitButton = this.modal.getByTestId('submit-register-button')
        this.formFieldError = this.modal.getByTestId('form-field-error')
        this.switchToLogin = this.modal.locator('button', { hasText: /login|sign in/i })
    }

    async expectModal(){
        await expect(this.modal).toBeVisible()
        await expect(this.emailInput).toBeVisible()
        await expect(this.passwordInput).toBeVisible()
        await expect(this.submitButton).toBeVisible()
    }

    async fillForm(email: string, password: string): Promise<void> {
        await this.emailInput.fill(email)
        await this.passwordInput.fill(password)
    }

    async expectEmailInputError(error?: string): Promise<void> {
        await expect(this.formFieldError.first()).toBeVisible()
        if (error) {
            await expect(this.formFieldError.first()).toHaveText(error)
        }
    }
    async expectPasswordInputError(error?: string): Promise<void> {
        await expect(this.formFieldError.first()).toBeVisible()
        if (error) {
            await expect(this.formFieldError.first()).toHaveText(error)
        }
    }

}
