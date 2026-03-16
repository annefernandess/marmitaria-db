"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { getErrorMessage } from "@/lib/format";

type UserRole = "admin" | "user";

interface User {
  id: number;
  email: string;
  role: UserRole;
  nome: string;
  numero: string;
  clienteId: number | null;
}

interface RegisterInput {
  nome: string;
  email: string;
  password: string;
  numero: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (input: RegisterInput) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const AUTH_STORAGE_KEY = "yao-auth-user";

function readStoredUser(): User | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as User;
    if (
      !parsed?.email ||
      !parsed?.role ||
      !parsed?.nome ||
      !parsed?.numero ||
      typeof parsed.id !== "number"
    ) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => readStoredUser());
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const redirectByRole = useCallback(
    (role: UserRole) => {
      if (role === "admin") {
        router.push("/dashboard");
      } else {
        router.push("/pedido");
      }
    },
    [router]
  );

  const login = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      setIsLoading(true);
      try {
        const loggedUserResponse = await apiFetch<{
          id: number;
          nome: string;
          email: string;
          numero: string;
          role: UserRole;
          cliente_id: number | null;
        }>("/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email,
            senha: password,
          }),
        });

        const loggedUser: User = {
          id: loggedUserResponse.id,
          email: loggedUserResponse.email,
          role: loggedUserResponse.role,
          nome: loggedUserResponse.nome,
          numero: loggedUserResponse.numero,
          clienteId: loggedUserResponse.cliente_id,
        };

        window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(loggedUser));
        setUser(loggedUser);
        redirectByRole(loggedUser.role);
        return true;
      } catch {
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [redirectByRole]
  );

  const register = useCallback(
    async (input: RegisterInput): Promise<{ success: boolean; message?: string }> => {
      setIsLoading(true);
      try {
        const createdUser = await apiFetch<{
          id: number;
          nome: string;
          email: string;
          numero: string;
          role: UserRole;
          cliente_id: number | null;
        }>("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            nome: input.nome,
            email: input.email,
            senha: input.password,
            numero: input.numero,
          }),
        });

        const loggedUser: User = {
          id: createdUser.id,
          email: createdUser.email,
          role: createdUser.role,
          nome: createdUser.nome,
          numero: createdUser.numero,
          clienteId: createdUser.cliente_id,
        };

        window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(loggedUser));
        setUser(loggedUser);
        redirectByRole(loggedUser.role);
        return { success: true };
      } catch (error) {
        return { success: false, message: getErrorMessage(error) };
      } finally {
        setIsLoading(false);
      }
    },
    [redirectByRole]
  );

  const logout = useCallback(() => {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
