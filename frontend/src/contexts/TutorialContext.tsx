import React, {
 createContext,
 useContext,
 useState,
 useCallback,
 useEffect,
 ReactNode,
} from "react";
import { useAuth } from "./AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import { logger } from "@/utils/logger";

// Current tutorial version - increment when tutorial content changes significantly
export const CURRENT_TUTORIAL_VERSION = 1;

export interface TutorialStep {
 id: string;
 targetSelector: string;
 titleKey: string;
 descriptionKey: string;
 position?: "top" | "bottom" | "left" | "right";
}

// Tutorial steps for sidebar walkthrough
export const TUTORIAL_STEPS: TutorialStep[] = [
 {
 id: "welcome",
 targetSelector: '[data-testid="sidebar"]',
 titleKey: "tutorial.steps.welcome.title",
 descriptionKey: "tutorial.steps.welcome.description",
 position: "right",
 },
 {
 id: "categories",
 targetSelector: '[data-testid="sidebar-category-link"]',
 titleKey: "tutorial.steps.categories.title",
 descriptionKey: "tutorial.steps.categories.description",
 position: "right",
 },
 {
 id: "accounts",
 targetSelector: '[data-testid="sidebar-account-link"]',
 titleKey: "tutorial.steps.accounts.title",
 descriptionKey: "tutorial.steps.accounts.description",
 position: "right",
 },
 {
 id: "expenses",
 targetSelector: '[data-testid="sidebar-expense-link"]',
 titleKey: "tutorial.steps.expenses.title",
 descriptionKey: "tutorial.steps.expenses.description",
 position: "right",
 },
 {
 id: "income",
 targetSelector: '[data-testid="sidebar-income-link"]',
 titleKey: "tutorial.steps.income.title",
 descriptionKey: "tutorial.steps.income.description",
 position: "right",
 },
 {
 id: "debts",
 targetSelector: '[data-testid="sidebar-debts-link"]',
 titleKey: "tutorial.steps.debts.title",
 descriptionKey: "tutorial.steps.debts.description",
 position: "right",
 },
 {
 id: "recurring",
 targetSelector: '[data-testid="sidebar-recurring-link"]',
 titleKey: "tutorial.steps.recurring.title",
 descriptionKey: "tutorial.steps.recurring.description",
 position: "right",
 },
 {
 id: "goals",
 targetSelector: '[data-testid="sidebar-goals-link"]',
 titleKey: "tutorial.steps.goals.title",
 descriptionKey: "tutorial.steps.goals.description",
 position: "right",
 },
 {
 id: "pdf-parser",
 targetSelector: '[data-testid="sidebar-pdf-parser-link"]',
 titleKey: "tutorial.steps.pdfParser.title",
 descriptionKey: "tutorial.steps.pdfParser.description",
 position: "right",
 },
 {
 id: "workspaces",
 targetSelector: '[data-testid="sidebar-workspaces-link"]',
 titleKey: "tutorial.steps.workspaces.title",
 descriptionKey: "tutorial.steps.workspaces.description",
 position: "right",
 },
 {
 id: "complete",
 targetSelector: '[data-testid="sidebar"]',
 titleKey: "tutorial.steps.complete.title",
 descriptionKey: "tutorial.steps.complete.description",
 position: "right",
 },
];

interface TutorialContextType {
 isActive: boolean;
 currentStep: number;
 totalSteps: number;
 currentStepData: TutorialStep | null;
 startTutorial: () => void;
 nextStep: () => void;
 prevStep: () => void;
 skipTutorial: () => void;
 completeTutorial: () => Promise<void>;
 shouldShowTutorial: boolean;
}

const TutorialContext = createContext<TutorialContextType | undefined>(
 undefined,
);

interface TutorialProviderProps {
 children: ReactNode;
}

export const TutorialProvider: React.FC<TutorialProviderProps> = ({
 children,
}) => {
 const { user, refreshUserProfile } = useAuth();
 const { user: userApi } = useApiClients();
 const [isActive, setIsActive] = useState(false);
 const [currentStep, setCurrentStep] = useState(0);

 // Check if user should see the tutorial (new user or tutorial updated)
 const shouldShowTutorial =
 user !== null && user.tutorial_version < CURRENT_TUTORIAL_VERSION;

 // Auto-start tutorial for new users
 useEffect(() => {
 if (shouldShowTutorial && !isActive) {
 // Small delay to ensure UI is ready
 const timer = setTimeout(() => {
 setIsActive(true);
 setCurrentStep(0);
 }, 1000);
 return () => clearTimeout(timer);
 }
 return undefined;
 }, [shouldShowTutorial, isActive]);

 const startTutorial = useCallback(() => {
 setIsActive(true);
 setCurrentStep(0);
 }, []);

 const nextStep = useCallback(() => {
 if (currentStep < TUTORIAL_STEPS.length - 1) {
 setCurrentStep((prev) => prev + 1);
 }
 }, [currentStep]);

 const prevStep = useCallback(() => {
 if (currentStep > 0) {
 setCurrentStep((prev) => prev - 1);
 }
 }, [currentStep]);

 const completeTutorial = useCallback(async () => {
 setIsActive(false);
 setCurrentStep(0);

 try {
 const result = await userApi.updateTutorial({
 tutorial_version: CURRENT_TUTORIAL_VERSION,
 });
 if (!("error" in result)) {
 await refreshUserProfile();
 }
 } catch (error) {
 logger.error("Failed to save tutorial completion:", error);
 }
 }, [userApi, refreshUserProfile]);

 const skipTutorial = useCallback(() => {
 completeTutorial();
 }, [completeTutorial]);

 const currentStepData = isActive
 ? (TUTORIAL_STEPS[currentStep] ?? null)
 : null;

 const value: TutorialContextType = {
 isActive,
 currentStep,
 totalSteps: TUTORIAL_STEPS.length,
 currentStepData,
 startTutorial,
 nextStep,
 prevStep,
 skipTutorial,
 completeTutorial,
 shouldShowTutorial,
 };

 return (
 <TutorialContext.Provider value={value}>
 {children}
 </TutorialContext.Provider>
 );
};

export const useTutorial = (): TutorialContextType => {
 const context = useContext(TutorialContext);
 if (context === undefined) {
 throw new Error("useTutorial must be used within a TutorialProvider");
 }
 return context;
};
