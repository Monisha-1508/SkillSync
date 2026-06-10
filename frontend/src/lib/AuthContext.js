"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ApiError, loadStoredToken, setAuthToken } from "@/lib/api";

/**
 * One account, read everywhere. The provider's job is small on purpose: load
 * whatever token is already in storage, ask the backend who it belongs to,
 * and expose four verbs - `login`, `register`, `logout`, and the `user`
 * itself - so a page never has to know *how* a session is carried, only
 * whether one exists.
 *
 * `status` starts at "checking" rather than assuming "signed out", because
 * a returning learner with a valid token sitting in storage should never
 * see a flash of "log in" before the real answer arrives.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("checking"); // checking | signed-in | signed-out

  useEffect(() => {
    const stored = loadStoredToken();
    if (!stored) {
      setStatus("signed-out");
      return;
    }
    api
      .get("/auth/me")
      .then((profile) => {
        setUser(profile);
        setStatus("signed-in");
      })
      .catch(() => {
        setAuthToken(null);
        setStatus("signed-out");
      });
  }, []);

  const _settle = useCallback((auth) => {
    setAuthToken(auth.token);
    setUser(auth.user);
    setStatus("signed-in");
    return auth.user;
  }, []);

  const login = useCallback(
    async (email, password) => _settle(await api.post("/auth/login", { email, password })),
    [_settle],
  );

  const register = useCallback(
    async (name, email, password) => _settle(await api.post("/auth/register", { name, email, password })),
    [_settle],
  );

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
    setStatus("signed-out");
  }, []);

  const value = useMemo(
    () => ({ user, status, isSignedIn: status === "signed-in", login, register, logout }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export { ApiError };
