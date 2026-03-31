import Image from "next/image";
import Link from "next/link";
import { ChefHat, ShoppingCart, Users, Package } from "lucide-react";
import CoxinhaCascade from "@/components/CoxinhaCascade";

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="group relative rounded-2xl border border-[#F5C451]/20 bg-white/80 backdrop-blur-sm p-6 transition-all duration-300 hover:border-[#F5A623]/40 hover:-translate-y-1 hover:shadow-lg hover:shadow-[#F5A623]/10">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#F5A623]/10">
        <Icon className="h-6 w-6 text-[#F5A623]" />
      </div>
      <h3 className="mb-2 text-lg font-bold text-[#1B2A4A]">{title}</h3>
      <p className="text-sm text-[#1B2A4A]/50 leading-relaxed">{description}</p>
    </div>
  );
}

export default function Home() {
  return (
    <div className="relative min-h-screen bg-[#FFF5E6] overflow-hidden">
      <CoxinhaCascade />

      <div className="absolute inset-0 bg-gradient-to-b from-[#FFF5E6] via-transparent to-[#FFF5E6] z-[1] pointer-events-none" />

      <div className="relative z-10">
        <nav className="flex items-center justify-between px-6 py-5 md:px-12 lg:px-20">
          <div className="flex items-center gap-3">
            <Image
              src="/logo.jpeg"
              alt="YAO Lanches"
              width={44}
              height={44}
              className="rounded-lg"
              priority
            />
            <span className="text-lg font-bold text-[#1B2A4A] hidden sm:block">
              YAO Lanches
            </span>
          </div>
          <Link
            href="/login"
            className="rounded-full bg-white/80 border border-[#F5C451]/20 px-6 py-2.5 text-sm font-medium text-[#1B2A4A]/80 backdrop-blur-sm transition-all duration-300 hover:bg-white hover:text-[#1B2A4A] hover:border-[#F5C451]/40"
          >
            Entrar
          </Link>
        </nav>

        <main className="flex flex-col items-center px-6 pt-20 pb-20 md:pt-28 lg:pt-36">
          <div className="flex flex-col items-center text-center max-w-3xl">
            <div className="mb-8 rounded-2xl bg-white/80 backdrop-blur-sm p-2 border border-[#F5C451]/20">
              <Image
                src="/logo.jpeg"
                alt="YAO Lanches"
                width={160}
                height={160}
                className="rounded-xl"
                priority
              />
            </div>

            <h1
              className="mb-6 font-extrabold tracking-[-0.02em] text-[#1B2A4A] leading-[1.1]"
              style={{ fontSize: "clamp(2.5rem, 7vw, 4.5rem)" }}
            >
              Gestão completa para o seu{" "}
              <span className="bg-gradient-to-r from-[#F5A623] to-[#F5C451] bg-clip-text text-transparent">
                negócio
              </span>
            </h1>

            <div className="mx-auto mb-6 h-px w-24 bg-[#F5C451]/30" />

            <p className="mb-10 max-w-xl text-lg text-[#1B2A4A]/60 leading-relaxed md:text-xl">
              Controle clientes, pedidos, estoque e relatórios em um só lugar.
              Simples, rápido e feito pra quem vende comida de verdade.
            </p>

            <div className="flex flex-col gap-4 sm:flex-row">
              <Link
                href="/login"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#F5A623] px-8 py-4 text-lg font-bold text-[#1B2A4A] shadow-lg shadow-[#F5A623]/20 transition-all duration-300 hover:bg-[#F5C451] hover:shadow-xl hover:shadow-[#F5A623]/30 hover:scale-105"
              >
                <ChefHat className="h-5 w-5" />
                Acessar Painel
              </Link>
              <a
                href="#funcionalidades"
                className="inline-flex items-center justify-center rounded-full border border-[#F5C451]/20 bg-white/80 px-8 py-4 text-lg font-medium text-[#1B2A4A]/70 backdrop-blur-sm transition-all duration-300 hover:border-[#F5C451]/40 hover:bg-white hover:text-[#1B2A4A]"
              >
                Saiba mais
              </a>
            </div>
          </div>

          <section
            id="funcionalidades"
            className="mt-32 w-full max-w-5xl md:mt-40"
          >
            <h2 className="mb-4 text-center text-3xl font-bold text-[#1B2A4A] md:text-4xl tracking-[-0.02em]">
              Tudo que você precisa
            </h2>
            <div className="mx-auto mb-12 h-px w-16 bg-[#F5C451]/30" />

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <FeatureCard
                icon={Users}
                title="Clientes"
                description="Cadastre e gerencie seus clientes com busca rápida por nome."
              />
              <FeatureCard
                icon={Package}
                title="Estoque"
                description="Controle do cardápio com quantidade disponível e preços."
              />
              <FeatureCard
                icon={ShoppingCart}
                title="Pedidos"
                description="Crie pedidos, acompanhe o estado e controle pagamentos."
              />
              <FeatureCard
                icon={ChefHat}
                title="Relatórios"
                description="Visualize vendas, estoque e dados de clientes em tempo real."
              />
            </div>
          </section>
        </main>

        <footer className="border-t border-[#F5C451]/20 bg-white/60 backdrop-blur-sm px-6 py-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Image
              src="/logo.jpeg"
              alt="YAO Lanches"
              width={28}
              height={28}
              className="rounded-md"
            />
            <span className="font-bold text-[#1B2A4A]/80">YAO Lanches</span>
          </div>
          <p className="text-sm text-[#1B2A4A]/30" suppressHydrationWarning>
            Projeto acadêmico — Banco de Dados © {new Date().getFullYear()}
          </p>
        </footer>
      </div>
    </div>
  );
}
