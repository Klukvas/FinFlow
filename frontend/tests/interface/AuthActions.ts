import { expect, Page } from "@playwright/test";
import { LoginModal } from "../infra/modals";
import { HeaderComponent } from "../infra/components/header.component";
import { SidebarComponent   } from "../infra/components/SidebarComponent";
import { RegistrationModal } from "../infra/modals/RefistrationModal";

export class AuthActions {
    
    loginModal: LoginModal
    header: HeaderComponent
    sideBar: SidebarComponent
    registerModal: RegistrationModal
    
    constructor(page: Page){
        this.loginModal = new LoginModal(page)
        this.header = new HeaderComponent(page);
        this.sideBar = new SidebarComponent(page);
        this.registerModal = new RegistrationModal(page)
    }



    async login(email: string, password: string): Promise<void> {
        await this.openLoginModal()
        await this.loginModal.fillForm(email, password);
        await this.loginModal.loginButton.click()
        await this.header.expectUserAuthorized();
        await this.sideBar.expectComponent()
    }

    async register(username: string, email: string, password: string): Promise<void> {
        await this.openRegisterModal()
        await this.registerModal.fillForm(username, email, password);
        await this.registerModal.submitButton.click()
        await this.header.expectUserAuthorized();
        await this.sideBar.expectComponent()
    }

    async registerAndExpectValidationFailure(username: string, email: string, password: string, errorMessage?: string): Promise<void> {
        await this.openRegisterModal()
        await this.registerModal.fillForm(username, email, password);
        await this.registerModal.expectEmailInputError(errorMessage)
    }

    async loginAndExpectFailure(email: string, password: string, errorMessage?: string): Promise<void> {
        await this.openLoginModal()
        await this.loginModal.fillForm(email, password);
        await this.loginModal.loginButton.click()
        await expect(this.loginModal.loginError).toBeVisible()
        if (errorMessage) {
            await expect(this.loginModal.loginError).toHaveText(errorMessage)
        }
    }

    async openLoginModal(){
        await this.header.expectUserUnauthorized()
        await this.header.loginButton.click()
        await this.loginModal.expectModal()
    }

    async closeLoginModal(){
        await this.loginModal.closeButton.click()
    }

    async swithFromLoginToRegisterModal(){
        await this.loginModal.switchToRegister.click()
        await this.registerModal.expectModal()
    }

    async swithFromRegisterToLoginModal(){
        await this.registerModal.switchToLogin.click()
        await this.loginModal.expectModal()
    }

    async openRegisterModal(){
        await this.header.registerButton.click()
        await this.registerModal.expectModal()
    }

}