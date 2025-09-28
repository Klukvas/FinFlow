export const tokenStorage = {
    set(token: string) {
      localStorage.setItem("access_token", token);
    },
    get() {
      return localStorage.getItem("access_token");
    },
    clear() {
      localStorage.removeItem("access_token");
    },
  };