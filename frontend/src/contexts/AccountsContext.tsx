import React, {
 createContext,
 useContext,
 useEffect,
 useState,
 useCallback,
 ReactNode,
} from "react";
import { useApiClients } from "@/hooks/useApiClients";
import { useAuth } from "@/contexts/AuthContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { AccountResponse } from "@/types";
import { logger } from "@/utils/logger";

interface AccountsContextType {
 accounts: AccountResponse[];
 activeAccounts: AccountResponse[];
 archivedAccounts: AccountResponse[];
 isLoading: boolean;
 error: string | null;
 refreshAccounts: () => Promise<void>;
 getAccountById: (id: number) => AccountResponse | undefined;
 getAccountsByCurrency: (currency: string) => AccountResponse[];
}

const AccountsContext = createContext<AccountsContextType | undefined>(
 undefined,
);

interface AccountsProviderProps {
 children: ReactNode;
}

export const AccountsProvider: React.FC<AccountsProviderProps> = ({
 children,
}) => {
 const { account } = useApiClients();
 const { isAuthenticated, isLoading: authLoading } = useAuth();
 const { currentWorkspaceId, isLoading: workspaceLoading } = useWorkspace();
 const [accounts, setAccounts] = useState<AccountResponse[]>([]);
 const [isLoading, setIsLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 const fetchAccounts = useCallback(async () => {
 // Don't fetch if not authenticated, auth is still loading, or workspace is not selected
 if (
 !isAuthenticated ||
 authLoading ||
 workspaceLoading ||
 !currentWorkspaceId
 ) {
 return;
 }

 try {
 setIsLoading(true);
 setError(null);

 const response = await account.getAccounts();

 if ("error" in response) {
 logger.error(
 "AccountsContext: Failed to fetch accounts:",
 response.error,
 );
 setError(response.error);
 setAccounts([]);
 } else {
 setAccounts(response);
 }
 } catch (err) {
 const errorMessage =
 err instanceof Error ? err.message : "Failed to fetch accounts";
 logger.error("AccountsContext: Error fetching accounts:", err);
 setError(errorMessage);
 setAccounts([]);
 } finally {
 setIsLoading(false);
 }
 }, [
 account,
 isAuthenticated,
 authLoading,
 workspaceLoading,
 currentWorkspaceId,
 ]);

 const refreshAccounts = useCallback(async () => {
 await fetchAccounts();
 }, [fetchAccounts]);

 // Computed values
 const activeAccounts = accounts.filter((acc) => !acc.is_archived);
 const archivedAccounts = accounts.filter((acc) => acc.is_archived);

 // Helper methods
 const getAccountById = useCallback(
 (id: number): AccountResponse | undefined => {
 return accounts.find((acc) => acc.id === id);
 },
 [accounts],
 );

 const getAccountsByCurrency = useCallback(
 (currency: string): AccountResponse[] => {
 return accounts.filter(
 (acc) => acc.currency === currency && !acc.is_archived,
 );
 },
 [accounts],
 );

 // Fetch accounts on mount and when user changes
 useEffect(() => {
 fetchAccounts();
 }, [fetchAccounts]);

 const value: AccountsContextType = {
 accounts,
 activeAccounts,
 archivedAccounts,
 isLoading,
 error,
 refreshAccounts,
 getAccountById,
 getAccountsByCurrency,
 };

 return (
 <AccountsContext.Provider value={value}>
 {children}
 </AccountsContext.Provider>
 );
};

export const useAccounts = (): AccountsContextType => {
 const context = useContext(AccountsContext);
 if (context === undefined) {
 throw new Error("useAccounts must be used within an AccountsProvider");
 }
 return context;
};
