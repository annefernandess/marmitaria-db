"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Users,
  Package,
  AlertCircle,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { formatCurrency, getErrorMessage } from "@/lib/format";
import type {
  RelatorioClientes,
  RelatorioEstoque,
  RelatorioVendas,
} from "@/lib/types";

function ReportCard({
  title,
  icon: Icon,
  color,
  stats,
}: {
  title: string;
  icon: React.ElementType;
  color: string;
  stats: { label: string; value: string }[];
}) {
  return (
    <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-xl"
          style={{ backgroundColor: `${color}15` }}
        >
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
        <h2 className="text-lg font-bold text-[#1B2A4A]">{title}</h2>
      </div>

      <div className="space-y-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="flex items-center justify-between border-b border-[#F5C451]/10 pb-3 last:border-0 last:pb-0"
          >
            <span className="text-sm text-[#1B2A4A]/50">{stat.label}</span>
            <span className="text-sm font-semibold text-[#1B2A4A]">
              {stat.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RelatoriosPage() {
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
          Relatórios
        </h1>
        <p className="mt-1 text-[#1B2A4A]/50">Resumo geral do negócio</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        <ReportCard
          title="Relatório de Vendas"
          icon={TrendingUp}
          color="#F5A623"
          stats={[
            { label: "Total de Pedidos", value: loading ? "..." : String(vendas?.total_pedidos ?? 0) },
            { label: "Valor Total", value: loading ? "..." : formatCurrency(vendas?.valor_total ?? 0) },
            { label: "Pedidos Pagos", value: loading ? "..." : String(vendas?.pedidos_pagos ?? 0) },
            { label: "Pedidos Não Pagos", value: loading ? "..." : String(vendas?.pedidos_nao_pagos ?? 0) },
            { label: "Ticket Médio", value: loading ? "..." : formatCurrency(vendas?.ticket_medio ?? 0) },
          ]}
        />

        <ReportCard
          title="Relatório de Estoque"
          icon={Package}
          color="#3BB5E8"
          stats={[
            { label: "Itens Cadastrados", value: loading ? "..." : String(estoque?.itens_cadastrados ?? 0) },
            { label: "Quantidade Total", value: loading ? "..." : String(estoque?.quantidade_total ?? 0) },
            { label: "Valor de Inventário", value: loading ? "..." : formatCurrency(estoque?.valor_inventario ?? 0) },
            { label: "Itens sem Estoque", value: loading ? "..." : String(estoque?.itens_sem_estoque ?? 0) },
          ]}
        />

        <ReportCard
          title="Relatório de Clientes"
          icon={Users}
          color="#E85B5B"
          stats={[
            { label: "Total de Clientes", value: loading ? "..." : String(clientes?.total_clientes ?? 0) },
            {
              label: "Clientes com Pedidos Ativos",
              value: loading ? "..." : String(clientes?.clientes_com_pedidos_ativos ?? 0),
            },
            { label: "Clientes sem Pedidos", value: loading ? "..." : String(clientes?.clientes_sem_pedidos ?? 0) },
          ]}
        />
      </div>

      <div className="mt-8 rounded-2xl border border-[#F5C451]/20 bg-white/80 p-8 text-center">
        {error ? (
          <>
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
              Não foi possível carregar os relatórios
            </h2>
            <p className="mt-2 text-sm text-[#1B2A4A]/40 max-w-md mx-auto">
              {error}
            </p>
          </>
        ) : (
          <>
            <BarChart3 className="mx-auto h-12 w-12 text-[#1B2A4A]/20" />
            <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
              Dados em tempo real
            </h2>
            <p className="mt-2 text-sm text-[#1B2A4A]/40 max-w-md mx-auto">
              Os cartões acima já refletem os dados vindos do backend em tempo real.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
