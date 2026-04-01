"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

type UserRole = "admin" | "user";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export default function ProtectedRoute({
  children,
  allowedRoles,
}: ProtectedRouteProps) {
  const { user, isLoading, isHydrating } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading || isHydrating) return;

    if (!user) {
      router.replace("/login");
      return;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
      if (user.role === "admin") {
        router.replace("/dashboard");
      } else {
        router.replace("/pedido");
      }
    }
  }, [user, isLoading, isHydrating, allowedRoles, router]);

  if (isLoading || isHydrating || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#FFF5E6]">
        <Loader2 className="h-8 w-8 animate-spin text-[#F5A623]" />
      </div>
    );
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#FFF5E6]">
        <Loader2 className="h-8 w-8 animate-spin text-[#F5A623]" />
      </div>
    );
  }

  return <>{children}</>;
}
