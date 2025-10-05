import { useCallback } from 'react';

const TOKEN_KEY = 'access_token';

export const useAuthToken = () => {
  const getToken = useCallback(() => {
    return localStorage.getItem(TOKEN_KEY);
  }, []);

  const setToken = useCallback((token: string) => {
    localStorage.setItem(TOKEN_KEY, token);
  }, []);

  const removeToken = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
  }, []);

  return {
    getToken,
    setToken,
    removeToken,
  };
}; 