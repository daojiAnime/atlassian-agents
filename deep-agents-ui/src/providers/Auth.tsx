"use client";

import {
  createContext,
  useContext,
  ReactNode,
  useState,
} from "react";

interface AuthSession {
  accessToken: string;
}

interface AuthContextType {
  session: AuthSession | null;
}

const AuthContext = createContext<AuthContextType>({ session: null });

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize state with a lazy initializer to ensure consistent value on server and client
  const [session] = useState<AuthSession | null>(() => ({
    accessToken: process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "demo-token",
  }));

  return (
    <AuthContext.Provider value={{ session }}>{children}</AuthContext.Provider>
  );
}

export const useAuthContext = () => useContext(AuthContext);
