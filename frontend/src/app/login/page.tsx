"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import CoxinhaCascade from "@/components/CoxinhaCascade";
import { LogIn, AlertCircle, Loader2, UserPlus } from "lucide-react";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(false);

    const success = await login(email, password);
    if (!success) {
      setError(true);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#FFF5E6]">
      <CoxinhaCascade count={40} />

      <div className="absolute inset-0 bg-gradient-to-b from-[#FFF5E6] via-transparent to-[#FFF5E6] z-[1]" />

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-8 backdrop-blur-xl shadow-2xl shadow-[#F5A623]/5">
          <div className="mb-8 flex flex-col items-center">
            <div className="mb-4 rounded-2xl bg-[#FFF5E6] p-3">
              <Image
                src="/logo.jpeg"
                alt="YAO Lanches"
                width={72}
                height={72}
                className="rounded-xl"
                priority
              />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#1B2A4A]">
              YAO Lanches
            </h1>
            <div className="mt-2 h-px w-16 bg-[#F5C451]/30" />
            <p className="mt-3 text-sm text-[#1B2A4A]/50">
              Acesse sua conta para continuar
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                E-mail ou senha inválidos
              </div>
            )}

            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                E-mail
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none transition-all focus:border-[#F5A623]/40 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                Senha
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none transition-all focus:border-[#F5A623]/40 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#F5A623] px-6 py-3.5 text-sm font-bold text-[#1B2A4A] transition-all duration-200 hover:bg-[#F5C451] hover:shadow-lg hover:shadow-[#F5A623]/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <LogIn className="h-4 w-4" />
              )}
              {isLoading ? "Entrando..." : "Entrar"}
            </button>
          </form>

          <div className="mt-6 rounded-xl border border-[#F5C451]/20 bg-[#FFF5E6]/60 p-4 text-center">
            <p className="text-sm text-[#1B2A4A]/55">
              Ainda não tem conta?
            </p>
            <Link
              href="/cadastro"
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-[#1B2A4A] transition-all hover:border-[#F5C451]/30 hover:bg-[#FDE7B4]"
            >
              <UserPlus className="h-4 w-4" />
              Criar cadastro
            </Link>
          </div>

          <p className="mt-6 text-center text-xs text-[#1B2A4A]/30">
            Projeto acadêmico — Banco de Dados © {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </div>
  );
}
