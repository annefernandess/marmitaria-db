"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Eye,
  ClipboardList,
  Clock,
  CheckCircle2,
  Truck,
  XCircle,
  Loader2,
  X,
  AlertCircle,
  Check,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api";
import { formatCurrency, formatDate, getErrorMessage } from "@/lib/format";
import type {
  Cliente,
  EstadoPedido,
  EstoqueItem,
  FormaPagamento,
  Pedido,
  StatusPagamento,
} from "@/lib/types";

const estadoConfig: Record<
  EstadoPedido,
  { label: string; icon: React.ElementType; classes: string }
> = {
  EM_ANDAMENTO: {
    label: "Em Andamento",
    icon: Clock,
    classes: "bg-amber-50 text-amber-700",
  },
  PRONTO: {
    label: "Pronto",
    icon: CheckCircle2,
    classes: "bg-green-50 text-green-700",
  },
  ENTREGUE: {
    label: "Entregue",
    icon: Truck,
    classes: "bg-blue-50 text-blue-700",
  },
  CANCELADO: {
    label: "Cancelado",
    icon: XCircle,
    classes: "bg-red-50 text-red-700",
  },
};

const formaPagamentoLabels: Record<FormaPagamento, string> = {
  PIX: "Pix",
  CARTAO: "Cartão",
  BOLETO: "Boleto",
  BERRIES: "Berries",
};

const statusPagamentoConfig: Record<
  StatusPagamento,
  { label: string; classes: string }
> = {
  PENDENTE: { label: "Pendente", classes: "bg-amber-50 text-amber-700" },
  CONFIRMADO: { label: "Confirmado", classes: "bg-green-50 text-green-700" },
  REJEITADO: { label: "Rejeitado", classes: "bg-red-50 text-red-700" },
};

export default function PedidosPage() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [filtroEstado, setFiltroEstado] = useState<EstadoPedido | "TODOS">(
    "TODOS"
  );
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [estoque, setEstoque] = useState<EstoqueItem[]>([]);
  const [selected, setSelected] = useState<Pedido | null>(null);
  const [editing, setEditing] = useState<Pedido | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [clienteId, setClienteId] = useState("");
  const [itemId, setItemId] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [draftItems, setDraftItems] = useState<Array<{ item_id: number; quantidade: number }>>([]);
  const [editEstado, setEditEstado] = useState<EstadoPedido>("EM_ANDAMENTO");
  const [editPago, setEditPago] = useState("false");
  const [editStatusPagamento, setEditStatusPagamento] =
    useState<StatusPagamento>("PENDENTE");
  const [formaPagamento, setFormaPagamento] = useState<FormaPagamento | "">("");

  async function loadAuxiliar() {
    try {
      const [clientesData, estoqueData] = await Promise.all([
        apiFetch<Cliente[]>("/clientes"),
        apiFetch<EstoqueItem[]>("/estoque"),
      ]);
      setClientes(clientesData);
      setEstoque(estoqueData);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function loadPedidos(term = searchTerm, estado = filtroEstado) {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch<Pedido[]>("/pedidos", {
        query: {
          cliente_nome: term || undefined,
          estado: estado === "TODOS" ? undefined : estado,
        },
      });
      setPedidos(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAuxiliar();
  }, []);

  useEffect(() => {
    void loadPedidos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, filtroEstado]);

  const filtered = useMemo(() => pedidos, [pedidos]);

  function resetForm() {
    setClienteId("");
    setItemId("");
    setQuantidade("1");
    setDraftItems([]);
    setFormaPagamento("");
  }

  function toggleForm() {
    if (showForm) {
      resetForm();
    }
    setShowForm((prev) => !prev);
  }

  function addDraftItem() {
    if (!itemId) {
      return;
    }

    const selectedItem = estoque.find((item) => item.id === Number(itemId));
    if (!selectedItem) {
      return;
    }

    const qty = Number(quantidade);
    if (qty <= 0) {
      return;
    }

    setDraftItems((prev) => {
      const existing = prev.find((entry) => entry.item_id === selectedItem.id);
      if (existing) {
        return prev.map((entry) =>
          entry.item_id === selectedItem.id
            ? { ...entry, quantidade: entry.quantidade + qty }
            : entry
        );
      }

      return [...prev, { item_id: selectedItem.id, quantidade: qty }];
    });

    setItemId("");
    setQuantidade("1");
  }

  function removeDraftItem(targetItemId: number) {
    setDraftItems((prev) => prev.filter((item) => item.item_id !== targetItemId));
  }

  async function handleCreatePedido() {
    if (!clienteId || draftItems.length === 0) {
      setError("Selecione um cliente e adicione pelo menos um item ao pedido.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await apiFetch<Pedido>("/pedidos", {
        method: "POST",
        body: JSON.stringify({
          cliente_id: Number(clienteId),
          itens: draftItems,
          vendedor_id: user?.id ?? null,
          forma_pagamento: formaPagamento || null,
        }),
      });

      resetForm();
      setShowForm(false);
      await Promise.all([loadPedidos(), loadAuxiliar()]);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeletePedido(pedido: Pedido) {
    const confirmed = window.confirm(`Deseja remover o pedido #${pedido.id}?`);
    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      await apiFetch<void>(`/pedidos/${pedido.id}`, { method: "DELETE" });
      if (selected?.id === pedido.id) {
        setSelected(null);
      }
      await Promise.all([loadPedidos(), loadAuxiliar()]);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handlePatchPedido(
    pedido: Pedido,
    payload: {
      estado?: EstadoPedido;
      pago?: boolean;
      status_pagamento?: StatusPagamento;
    }
  ) {
    try {
      setError(null);
      setSubmitting(true);
      const updated = await apiFetch<Pedido>(`/pedidos/${pedido.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });

      setPedidos((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      if (selected?.id === updated.id) {
        setSelected(updated);
      }
      if (editing?.id === updated.id) {
        setEditing(updated);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  function openEditPedido(pedido: Pedido) {
    setEditing(pedido);
    setEditEstado(pedido.estado);
    setEditPago(String(pedido.pago));
    setEditStatusPagamento(pedido.status_pagamento);
  }

  function closeEditPedido() {
    setEditing(null);
  }

  async function handleSaveEditPedido() {
    if (!editing) {
      return;
    }

    await handlePatchPedido(editing, {
      estado: editEstado,
      pago: editPago === "true",
      status_pagamento: editStatusPagamento,
    });
  }

  function getItemName(targetItemId: number): string {
    return estoque.find((item) => item.id === targetItemId)?.item ?? `Item #${targetItemId}`;
  }

  const draftTotal = draftItems.reduce((sum, item) => {
    const currentItem = estoque.find((entry) => entry.id === item.item_id);
    return sum + (currentItem?.valor ?? 0) * item.quantidade;
  }, 0);

  return (
    <div>
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B2A4A] sm:text-3xl tracking-[-0.02em]">
            Pedidos
          </h1>
          <p className="mt-1 text-[#1B2A4A]/50">
            Acompanhe e gerencie os pedidos
          </p>
        </div>
        <button
          onClick={toggleForm}
          className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-5 py-3 text-sm font-bold text-[#1B2A4A] transition-all duration-200 hover:bg-[#F5C451] hover:shadow-lg hover:shadow-[#F5A623]/20"
        >
          <Plus className="h-4 w-4" />
          {showForm ? "Fechar formulário" : "Novo Pedido"}
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-2xl border border-[#F5C451]/20 bg-white/90 p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#1B2A4A]">
                Criar pedido manualmente
              </h2>
              <p className="text-sm text-[#1B2A4A]/50">
                Selecione o cliente e monte os itens antes de enviar ao backend.
              </p>
            </div>
            <button
              onClick={toggleForm}
              className="rounded-lg p-2 text-[#1B2A4A]/40 transition-colors hover:bg-[#FFF5E6] hover:text-[#1B2A4A]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-[1.2fr_1fr_140px_auto]">
            <select
              value={clienteId}
              onChange={(e) => setClienteId(e.target.value)}
              className="rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
            >
              <option value="">Selecione um cliente</option>
              {clientes.map((cliente) => (
                <option key={cliente.id} value={cliente.id}>
                  {cliente.nome}
                </option>
              ))}
            </select>

            <select
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              className="rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
            >
              <option value="">Selecione um item</option>
              {estoque.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.item} ({item.quantidade_disponivel} disp.)
                </option>
              ))}
            </select>

            <input
              value={quantidade}
              onChange={(e) => setQuantidade(e.target.value)}
              type="number"
              min="1"
              className="rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
            />

            <button
              onClick={addDraftItem}
              className="rounded-xl border border-[#F5A623]/20 bg-[#FFF5E6] px-4 py-3 text-sm font-semibold text-[#1B2A4A] transition-colors hover:bg-[#FDE7B4]"
            >
              Adicionar
            </button>
          </div>

          {draftItems.length > 0 ? (
            <div className="mt-4 rounded-2xl border border-[#F5C451]/20 bg-[#FFF5E6]/50 p-4">
              <div className="space-y-3">
                {draftItems.map((item) => (
                  <div
                    key={item.item_id}
                    className="flex items-center justify-between gap-4 rounded-xl bg-white px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-[#1B2A4A]">
                        {getItemName(item.item_id)}
                      </p>
                      <p className="text-sm text-[#1B2A4A]/50">
                        Quantidade: {item.quantidade}
                      </p>
                    </div>
                    <button
                      onClick={() => removeDraftItem(item.item_id)}
                      className="rounded-lg p-2 text-[#E85B5B]/70 transition-colors hover:bg-red-50 hover:text-[#E85B5B]"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-[#1B2A4A]/50">
                  Total estimado:{" "}
                  <span className="font-semibold text-[#1B2A4A]">
                    {formatCurrency(draftTotal)}
                  </span>
                </p>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                  <select
                    value={formaPagamento}
                    onChange={(e) =>
                      setFormaPagamento(e.target.value as FormaPagamento | "")
                    }
                    className="rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
                  >
                    <option value="">Forma de pagamento</option>
                    <option value="PIX">Pix</option>
                    <option value="CARTAO">Cartão</option>
                    <option value="BOLETO">Boleto</option>
                    <option value="BERRIES">Berries</option>
                  </select>
                  <button
                    onClick={() => void handleCreatePedido()}
                    disabled={submitting}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#F5A623] px-4 py-2.5 text-sm font-bold text-[#1B2A4A] transition-all hover:bg-[#F5C451] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                    Criar pedido
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="mb-6 flex flex-col gap-4 sm:flex-row">
        <div className="flex flex-1 items-center gap-3 rounded-xl border border-[#F5C451]/20 bg-white/80 px-4 py-3 focus-within:border-[#F5A623]/30 focus-within:ring-2 focus-within:ring-[#F5A623]/10 transition-all">
          <Search className="h-5 w-5 text-[#1B2A4A]/30" />
          <input
            type="text"
            placeholder="Pesquisar por cliente..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-transparent text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none"
          />
        </div>

        <select
          value={filtroEstado}
          onChange={(e) =>
            setFiltroEstado(e.target.value as EstadoPedido | "TODOS")
          }
          className="rounded-xl border border-[#F5C451]/20 bg-white/80 px-4 py-3 text-sm text-[#1B2A4A]/60 outline-none focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
        >
          <option value="TODOS">Todos os estados</option>
          <option value="EM_ANDAMENTO">Em Andamento</option>
          <option value="PRONTO">Pronto</option>
          <option value="ENTREGUE">Entregue</option>
          <option value="CANCELADO">Cancelado</option>
        </select>
      </div>

      {selected && (
        <div className="mb-6 rounded-2xl border border-[#3BB5E8]/20 bg-[#3BB5E8]/5 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#3BB5E8]">
                Pedido selecionado
              </p>
              <h2 className="mt-1 text-lg font-semibold text-[#1B2A4A]">
                Pedido #{selected.id} - {selected.cliente_nome}
              </h2>
              <p className="mt-1 text-sm text-[#1B2A4A]/60">
                {formatDate(selected.data)} • {formatCurrency(selected.valor)}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {selected.forma_pagamento ? (
                  <span className="inline-flex rounded-full bg-[#FFF5E6] px-2.5 py-0.5 text-xs font-semibold text-[#1B2A4A]">
                    {formaPagamentoLabels[selected.forma_pagamento]}
                  </span>
                ) : null}
                <span
                  className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusPagamentoConfig[selected.status_pagamento].classes}`}
                >
                  {statusPagamentoConfig[selected.status_pagamento].label}
                </span>
                {selected.vendedor_nome ? (
                  <span className="text-xs text-[#1B2A4A]/50">
                    Vendedor: {selected.vendedor_nome}
                  </span>
                ) : null}
              </div>
              {selected.desconto > 0 ? (
                <p className="mt-1 text-sm font-medium text-[#F5A623]">
                  Desconto: {formatCurrency(selected.desconto)}
                </p>
              ) : null}
              <div className="mt-3 space-y-2">
                {selected.itens.map((item) => (
                  <p key={item.id} className="text-sm text-[#1B2A4A]/60">
                    {getItemName(item.item_id)} • {item.quantidade} x{" "}
                    {formatCurrency(item.valor_unitario)}
                  </p>
                ))}
              </div>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="rounded-lg p-2 text-[#1B2A4A]/40 transition-colors hover:bg-white/70 hover:text-[#1B2A4A]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {editing && (
        <div className="mb-6 rounded-2xl border border-[#F5A623]/20 bg-white/90 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#F5A623]">
                Editar pedido manualmente
              </p>
              <h2 className="mt-1 text-lg font-semibold text-[#1B2A4A]">
                Pedido #{editing.id} - {editing.cliente_nome}
              </h2>
              <p className="mt-1 text-sm text-[#1B2A4A]/50">
                Ajuste o estado e o pagamento manualmente antes de salvar.
              </p>
            </div>
            <button
              onClick={closeEditPedido}
              className="rounded-lg p-2 text-[#1B2A4A]/40 transition-colors hover:bg-[#FFF5E6] hover:text-[#1B2A4A]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-4">
            <div className="rounded-xl border border-[#F5C451]/20 bg-[#FFF5E6]/40 px-4 py-3">
              <p className="text-xs uppercase tracking-wider text-[#1B2A4A]/40">
                Cliente
              </p>
              <p className="mt-1 text-sm font-medium text-[#1B2A4A]">
                {editing.cliente_nome}
              </p>
            </div>
            <div className="rounded-xl border border-[#F5C451]/20 bg-[#FFF5E6]/40 px-4 py-3">
              <p className="text-xs uppercase tracking-wider text-[#1B2A4A]/40">
                Data
              </p>
              <p className="mt-1 text-sm font-medium text-[#1B2A4A]">
                {formatDate(editing.data)}
              </p>
            </div>
            <div className="rounded-xl border border-[#F5C451]/20 bg-[#FFF5E6]/40 px-4 py-3">
              <p className="text-xs uppercase tracking-wider text-[#1B2A4A]/40">
                Valor
              </p>
              <p className="mt-1 text-sm font-medium text-[#1B2A4A]">
                {formatCurrency(editing.valor)}
              </p>
            </div>
            <div className="rounded-xl border border-[#F5C451]/20 bg-[#FFF5E6]/40 px-4 py-3">
              <p className="text-xs uppercase tracking-wider text-[#1B2A4A]/40">
                Itens
              </p>
              <p className="mt-1 text-sm font-medium text-[#1B2A4A]">
                {editing.itens.length}
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                Estado
              </label>
              <select
                value={editEstado}
                onChange={(e) => setEditEstado(e.target.value as EstadoPedido)}
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
              >
                <option value="EM_ANDAMENTO">Em andamento</option>
                <option value="PRONTO">Pronto</option>
                <option value="ENTREGUE">Entregue</option>
                <option value="CANCELADO">Cancelado</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                Pago
              </label>
              <select
                value={editPago}
                onChange={(e) => setEditPago(e.target.value)}
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
              >
                <option value="false">Não</option>
                <option value="true">Sim</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                Status do pagamento
              </label>
              <select
                value={editStatusPagamento}
                onChange={(e) =>
                  setEditStatusPagamento(e.target.value as StatusPagamento)
                }
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
              >
                <option value="PENDENTE">Pendente</option>
                <option value="CONFIRMADO">Confirmado</option>
                <option value="REJEITADO">Rejeitado</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-end gap-3">
            <button
              onClick={closeEditPedido}
              className="rounded-xl border border-[#F5C451]/20 px-4 py-2.5 text-sm font-medium text-[#1B2A4A]/70 transition-colors hover:bg-[#FFF5E6]"
            >
              Cancelar
            </button>
            <button
              onClick={() => void handleSaveEditPedido()}
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-4 py-2.5 text-sm font-bold text-[#1B2A4A] transition-all hover:bg-[#F5C451] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Edit2 className="h-4 w-4" />}
              Salvar pedido
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-[#F5A623]" />
          <p className="mt-3 text-sm text-[#1B2A4A]/40">Carregando pedidos...</p>
        </div>
      ) : filtered.length > 0 ? (
        <div className="overflow-x-auto rounded-2xl border border-[#F5C451]/20 bg-white/80">
          <table className="w-full min-w-[960px]">
            <thead>
              <tr className="border-b border-[#F5C451]/10">
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Pedido
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Cliente
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Data
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Estado
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Valor
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Forma
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Status pg.
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Vendedor
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Pago
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F5C451]/10">
              {filtered.map((pedido) => {
                const estado = estadoConfig[pedido.estado];
                const EstadoIcon = estado.icon;
                const sp = statusPagamentoConfig[pedido.status_pagamento];
                return (
                  <tr
                    key={pedido.id}
                    className="transition-colors hover:bg-[#FFF5E6]/30"
                  >
                    <td className="px-6 py-4 text-sm font-mono text-[#1B2A4A]/40">
                      #{pedido.id}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-[#1B2A4A]">
                      {pedido.cliente_nome}
                    </td>
                    <td className="px-6 py-4 text-sm text-[#1B2A4A]/60">
                      {formatDate(pedido.data)}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${estado.classes}`}
                      >
                        <EstadoIcon className="h-3.5 w-3.5" />
                        {estado.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-[#1B2A4A]">
                        {formatCurrency(pedido.valor)}
                      </p>
                      {pedido.desconto > 0 ? (
                        <p className="mt-0.5 text-xs text-[#1B2A4A]/50">
                          Desconto: {formatCurrency(pedido.desconto)}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-6 py-4">
                      {pedido.forma_pagamento ? (
                        <span className="inline-flex rounded-full bg-[#FFF5E6] px-3 py-1 text-xs font-semibold text-[#1B2A4A]">
                          {formaPagamentoLabels[pedido.forma_pagamento]}
                        </span>
                      ) : (
                        <span className="text-sm text-[#1B2A4A]/30">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${sp.classes}`}
                      >
                        {sp.label}
                      </span>
                    </td>
                    <td className="max-w-[140px] truncate px-6 py-4 text-sm text-[#1B2A4A]/70">
                      {pedido.vendedor_nome ?? (
                        <span className="text-[#1B2A4A]/30">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                          pedido.pago
                            ? "bg-green-50 text-green-700"
                            : "bg-red-50 text-red-700"
                        }`}
                      >
                        {pedido.pago ? "Sim" : "Não"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelected(pedido)}
                          className="rounded-lg p-2 text-[#3BB5E8]/60 hover:bg-[#3BB5E8]/10 hover:text-[#3BB5E8] transition-colors"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openEditPedido(pedido)}
                          className="rounded-lg p-2 text-[#F5A623]/60 hover:bg-[#F5A623]/10 hover:text-[#F5A623] transition-colors"
                          title="Editar pedido manualmente"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => void handleDeletePedido(pedido)}
                          className="rounded-lg p-2 text-[#E85B5B]/60 hover:bg-[#E85B5B]/10 hover:text-[#E85B5B] transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
          <ClipboardList className="mx-auto h-16 w-16 text-[#1B2A4A]/20" />
          <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
            {searchTerm || filtroEstado !== "TODOS"
              ? "Nenhum pedido encontrado"
              : "Nenhum pedido cadastrado"}
          </h2>
          <p className="mt-2 text-sm text-[#1B2A4A]/40">
            {searchTerm || filtroEstado !== "TODOS"
              ? "Tente ajustar os filtros de busca."
              : "Comece criando o primeiro pedido."}
          </p>
        </div>
      )}
    </div>
  );
}
