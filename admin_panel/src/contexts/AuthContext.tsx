import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  ReactNode,
} from "react";
import { User } from "@/types";
import { UserService } from "@/services/userService";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (
    email: string,
    password: string,
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "admin_access_token";
const REFRESH_TOKEN_KEY = "admin_refresh_token";

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY),
  );
  const [isLoading, setIsLoading] = useState(true);

  const tokenRef = useRef(token);
  tokenRef.current = token;

  const getToken = useCallback(() => tokenRef.current, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }, []);

  const handleRefreshToken = useCallback(async (): Promise<string | null> => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) return null;

    const tempService = new UserService(
      () => null,
      () => {},
    );
    const result = await tempService.refreshToken(refreshToken);

    if ("error" in result) {
      return null;
    }

    const newAccessToken = result.access_token;
    localStorage.setItem(TOKEN_KEY, newAccessToken);
    setToken(newAccessToken);
    return newAccessToken;
  }, []);

  const userService = React.useMemo(
    () => new UserService(getToken, logout, handleRefreshToken),
    [getToken, logout, handleRefreshToken],
  );

  // Fetch user profile on mount or token change
  useEffect(() => {
    const fetchProfile = async () => {
      if (!token) {
        setIsLoading(false);
        return;
      }

      const result = await userService.getMe();

      if ("error" in result) {
        console.error("Failed to fetch profile:", result.error);
        logout();
      } else {
        if (result.role !== "admin") {
          console.error("User is not an admin");
          logout();
        } else {
          setUser(result);
        }
      }
      setIsLoading(false);
    };

    fetchProfile();
  }, [token, userService, logout]);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await userService.login(email, password);

      if ("error" in result) {
        return { success: false, error: result.error };
      }

      // Store both tokens
      const accessToken = result.access_token;
      localStorage.setItem(TOKEN_KEY, accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token);
      setToken(accessToken);

      // Fetch user profile to verify admin role
      const tempService = new UserService(
        () => accessToken,
        () => {},
      );
      const profileResult = await tempService.getMe();

      if ("error" in profileResult) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        setToken(null);
        return { success: false, error: "Failed to fetch user profile" };
      }

      if (profileResult.role !== "admin") {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        setToken(null);
        return {
          success: false,
          error: "Access denied. Admin privileges required.",
        };
      }

      setUser(profileResult);
      return { success: true };
    },
    [userService],
  );

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === "admin",
    isLoading,
    login,
    logout,
    refreshToken: handleRefreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
