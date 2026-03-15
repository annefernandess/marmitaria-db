"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

type UserRole = "admin" | "user";

interface User {
  email: string;
  role: UserRole;
  nome: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const MOCK_USERS: { email: string; password: string; role: UserRole; nome: string }[] = [
  {
    email: "yao@lanches.com",
    password: "admin",
    role: "admin",
    nome: "YAO Admin",
  },
  {
    email: "pedro.kruta@academico.ufpb.br",
    password: "user",
    role: "user",
    nome: "Pedro Kruta",
  },
];

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const login = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      setIsLoading(true);

      await new Promise((r) => setTimeout(r, 600));

      const found = MOCK_USERS.find(
        (u) => u.email === email.toLowerCase().trim() && u.password === password
      );

      if (!found) {
        setIsLoading(false);
        return false;
      }

      const loggedUser: User = {
        email: found.email,
        role: found.role,
        nome: found.nome,
      };

      setUser(loggedUser);
      setIsLoading(false);

      if (found.role === "admin") {
        router.push("/dashboard");
      } else {
        router.push("/pedido");
      }

      return true;
    },
    [router]
  );

  const logout = useCallback(() => {
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
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
