import type { AuthResponse, User } from "@/lib/api";

const accessTokenKey = "avault_access_token";
const refreshTokenKey = "avault_refresh_token";
const userKey = "avault_user";

export function saveAuth(response: AuthResponse) {
  window.localStorage.setItem(accessTokenKey, response.access);
  window.localStorage.setItem(refreshTokenKey, response.refresh);
  window.localStorage.setItem(userKey, JSON.stringify(response.user));
}

export function getAccessToken() {
  return window.localStorage.getItem(accessTokenKey);
}

export function getRefreshToken() {
  return window.localStorage.getItem(refreshTokenKey);
}

export function getStoredUser(): User | null {
  const storedUser = window.localStorage.getItem(userKey);
  return storedUser ? (JSON.parse(storedUser) as User) : null;
}

export function clearAuth() {
  window.localStorage.removeItem(accessTokenKey);
  window.localStorage.removeItem(refreshTokenKey);
  window.localStorage.removeItem(userKey);
}
