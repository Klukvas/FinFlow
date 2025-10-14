import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { UserApiClient } from '@/services/api/userApiClient';
import { config } from '@/config/env';

interface User {
  id: number;
  email: string;
  username: string;
  base_currency: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, username: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshAccessToken: () => Promise<boolean>;
  refreshUserProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${config.api.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        const newToken = data.access_token;
        const newRefreshToken = data.refresh_token || refreshToken; // Keep old refresh token if not provided
        
        setToken(newToken);
        setRefreshToken(newRefreshToken);
        
        localStorage.setItem('access_token', newToken);
        if (newRefreshToken !== refreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }
        
        if (config.debug) {
          // Token refreshed successfully
        }
        
        return true;
      } else {
        console.error('Token refresh failed:', response.status);
        return false;
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      return false;
    }
  }, [refreshToken]);

  // Create API client with current token
  const userApi = React.useMemo(() => {
    const getToken = () => token;
    const refreshTokenFn = () => refreshAccessToken();
    return new UserApiClient(getToken, refreshTokenFn);
  }, [token, refreshAccessToken]);


  // Load tokens from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedRefreshToken = localStorage.getItem('refresh_token');
    
    if (storedToken) {
      setToken(storedToken);
    }
    if (storedRefreshToken) {
      setRefreshToken(storedRefreshToken);
    }
    
    setIsLoading(false);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setRefreshToken(null);
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    if (config.debug) {
      // Logged out successfully
    }
  }, []);

  const fetchUserProfile = useCallback(async () => {
    if (!token) return;

    try {
      const response = await userApi.getProfile();
      if ('error' in response) {
        console.error('Failed to fetch user profile:', response.error);
        // If profile fetch fails, try to refresh token
        if (refreshToken) {
          const refreshed = await refreshAccessToken();
          if (!refreshed) {
            logout();
          }
        } else {
          logout();
        }
      } else {
        setUser(response);
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
      logout();
    }
  }, [token, refreshToken, userApi, refreshAccessToken, logout]);

  // Fetch user profile when token changes
  useEffect(() => {
    if (token) {
      fetchUserProfile();
    } else {
      setUser(null);
    }
  }, [token, fetchUserProfile]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await userApi.login({ email, password });
      
      if ('error' in response) {
        return { success: false, error: response.error };
      }

      const { access_token, refresh_token } = response;
      
      setToken(access_token);
      setRefreshToken(refresh_token);
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      if (config.debug) {
        // Login successful
      }
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Ошибка при входе в систему' };
    }
  }, [userApi]);

  const register = useCallback(async (email: string, password: string, username: string) => {
    try {
      const response = await userApi.register({ email, password, username });
      
      if ('error' in response) {
        return { success: false, error: response.error };
      }

      const { access_token, refresh_token } = response;
      
      setToken(access_token);
      setRefreshToken(refresh_token);
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      if (config.debug) {
        // Registration successful
      }
      
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: 'Ошибка при регистрации' };
    }
  }, [userApi]);

  // Set up automatic token refresh
  useEffect(() => {
    if (!token || !refreshToken) return;

    const refreshInterval = setInterval(async () => {
      const refreshed = await refreshAccessToken();
      if (!refreshed) {
        logout();
      }
    }, 15 * 60 * 1000); // Refresh every 15 minutes

    return () => clearInterval(refreshInterval);
  }, [token, refreshToken, refreshAccessToken, logout]);

  const value: AuthContextType = {
    user,
    token,
    refreshToken,
    isAuthenticated: !!token,
    isLoading,
    login,
    register,
    logout,
    refreshAccessToken,
    refreshUserProfile: fetchUserProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
