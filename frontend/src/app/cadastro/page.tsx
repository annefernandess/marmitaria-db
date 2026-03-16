"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import CoxinhaCascade from "@/components/CoxinhaCascade";
import { UserPlus, AlertCircle, Loader2, LogIn } from "lucide-react";

export default function CadastroPage() {
  const { register, isLoading } = useAuth();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [numero, setNumero] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const result = await register({
      nome,
      email,
      numero,
      password,
    });

    if (!result.success) {
      setError(result.message ?? "Não foi possível concluir o cadastro.");
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#FFF5E6]">
      <CoxinhaCascade count={40} />

      <div className="absolute inset-0 z-[1] bg-gradient-to-b from-[#FFF5E6] via-transparent to-[#FFF5E6]" />

      <div className="relative z-10 w-full max-w-xl px-6">
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
              Criar cadastro
            </h1>
            <div className="mt-2 h-px w-16 bg-[#F5C451]/30" />
            <p className="mt-3 text-center text-sm text-[#1B2A4A]/50">
              Cadastre nome do cliente, e-mail, telefone e senha para acessar o sistema.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label
                htmlFor="nome"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                Nome do cliente
              </label>
              <input
                id="nome"
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Seu nome completo"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none transition-all focus:border-[#F5A623]/40 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>

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
                htmlFor="numero"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                Número de telefone
              </label>
              <input
                id="numero"
                type="text"
                value={numero}
                onChange={(e) => setNumero(e.target.value)}
                placeholder="(83) 99999-0000"
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
                placeholder="Digite sua senha"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none transition-all focus:border-[#F5A623]/40 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#F5A623] px-6 py-3.5 text-sm font-bold text-[#1B2A4A] transition-all duration-200 hover:bg-[#F5C451] hover:shadow-lg hover:shadow-[#F5A623]/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              {isLoading ? "Cadastrando..." : "Cadastrar"}
            </button>
          </form>

          <div className="mt-6 rounded-xl border border-[#F5C451]/20 bg-[#FFF5E6]/60 p-4 text-center">
            <p className="text-sm text-[#1B2A4A]/55">
              Já tem conta?
            </p>
            <Link
              href="/login"
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-[#1B2A4A] transition-all hover:bg-[#FDE7B4]"
            >
              <LogIn className="h-4 w-4" />
              Voltar para login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
