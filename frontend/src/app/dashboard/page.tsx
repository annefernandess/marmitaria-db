"use client";

import { useEffect, useState } from "react";
import { Users, ShoppingCart, DollarSign, Package, AlertCircle } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { formatCurrency, getErrorMessage } from "@/lib/format";
import type {
  RelatorioClientes,
  RelatorioEstoque,
  RelatorioVendas,
} from "@/lib/types";

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-6 transition-all duration-300 hover:border-[#F5C451]/30 hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-[#1B2A4A]/50">{label}</p>
          <p className="mt-2 text-3xl font-bold text-[#1B2A4A]">{value}</p>
        </div>
        <div
          className="flex h-14 w-14 items-center justify-center rounded-2xl"
          style={{ backgroundColor: `${color}15` }}
        >
          <Icon className="h-7 w-7" style={{ color }} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardHome() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [vendas, setVendas] = useState<RelatorioVendas | null>(null);
  const [estoque, setEstoque] = useState<RelatorioEstoque | null>(null);
  const [clientes, setClientes] = useState<RelatorioClientes | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);

        const [vendasData, estoqueData, clientesData] = await Promise.all([
          apiFetch<RelatorioVendas>("/relatorios/vendas"),
          apiFetch<RelatorioEstoque>("/relatorios/estoque"),
          apiFetch<RelatorioClientes>("/relatorios/clientes"),
        ]);

        setVendas(vendasData);
        setEstoque(estoqueData);
        setClientes(clientesData);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#1B2A4A] sm:text-3xl tracking-[-0.02em]">
          Dashboard
        </h1>
        <p className="mt-1 text-[#1B2A4A]/50">Visão geral do seu negócio</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Users}
          label="Total de Clientes"
          value={loading ? "..." : String(clientes?.total_clientes ?? 0)}
          color="#3BB5E8"
        />
        <StatCard
          icon={ShoppingCart}
          label="Pedidos Hoje"
          value={loading ? "..." : String(vendas?.total_pedidos ?? 0)}
          color="#F5A623"
        />
        <StatCard
          icon={DollarSign}
          label="Receita do Mês"
          value={loading ? "..." : formatCurrency(vendas?.valor_total ?? 0)}
          color="#4CAF50"
        />
        <StatCard
          icon={Package}
          label="Itens em Estoque"
          value={loading ? "..." : String(estoque?.itens_cadastrados ?? 0)}
          color="#E85B5B"
        />
      </div>

      <div className="mt-10 rounded-2xl border border-[#F5C451]/20 bg-white/80 p-8 text-center">
        {error ? (
          <>
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
              Não foi possível carregar o dashboard
            </h2>
            <p className="mt-2 text-sm text-[#1B2A4A]/40 max-w-md mx-auto">
              {error}
            </p>
          </>
        ) : (
          <>
            <ShoppingCart className="mx-auto h-12 w-12 text-[#1B2A4A]/20" />
            <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
              Backend integrado
            </h2>
            <p className="mt-2 text-sm text-[#1B2A4A]/40 max-w-md mx-auto">
              O painel já está consumindo os relatórios da API. Use o menu lateral
              para gerenciar clientes, estoque e pedidos em tempo real.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
