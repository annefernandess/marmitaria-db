"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Eye,
  PackageX,
  Loader2,
  X,
  AlertCircle,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { formatCurrency, getErrorMessage } from "@/lib/format";
import type { EstoqueItem } from "@/lib/types";

export default function EstoquePage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [estoque, setEstoque] = useState<EstoqueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<EstoqueItem | null>(null);
  const [editing, setEditing] = useState<EstoqueItem | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    item: "",
    quantidade_disponivel: "0",
    valor: "0",
  });

  async function loadEstoque(term = searchTerm) {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch<EstoqueItem[]>("/estoque", {
        query: { nome: term || undefined },
      });
      setEstoque(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadEstoque();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm]);

  const filtered = useMemo(() => estoque, [estoque]);

  function openCreate() {
    setEditing(null);
    setForm({ item: "", quantidade_disponivel: "0", valor: "0" });
    setShowForm(true);
  }

  function openEdit(item: EstoqueItem) {
    setEditing(item);
    setForm({
      item: item.item,
      quantidade_disponivel: String(item.quantidade_disponivel),
      valor: String(item.valor),
    });
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
    setForm({ item: "", quantidade_disponivel: "0", valor: "0" });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError(null);

      const payload = {
        item: form.item,
        quantidade_disponivel: Number(form.quantidade_disponivel),
        valor: Number(form.valor),
      };

      if (editing) {
        await apiFetch<EstoqueItem>(`/estoque/${editing.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch<EstoqueItem>("/estoque", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }

      closeForm();
      await loadEstoque();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(item: EstoqueItem) {
    const confirmed = window.confirm(
      `Deseja remover o item "${item.item}" do estoque?`
    );
    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      await apiFetch<void>(`/estoque/${item.id}`, { method: "DELETE" });
      if (selected?.id === item.id) {
        setSelected(null);
      }
      await loadEstoque();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B2A4A] sm:text-3xl tracking-[-0.02em]">
            Estoque
          </h1>
          <p className="mt-1 text-[#1B2A4A]/50">
            Gerencie o cardápio e a disponibilidade dos itens
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-5 py-3 text-sm font-bold text-[#1B2A4A] transition-all duration-200 hover:bg-[#F5C451] hover:shadow-lg hover:shadow-[#F5A623]/20"
        >
          <Plus className="h-4 w-4" />
          Novo Item
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 rounded-2xl border border-[#F5C451]/20 bg-white/90 p-6"
        >
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#1B2A4A]">
                {editing ? "Editar item" : "Novo item"}
              </h2>
              <p className="text-sm text-[#1B2A4A]/50">
                Cadastre ou atualize o cardápio em tempo real.
              </p>
            </div>
            <button
              type="button"
              onClick={closeForm}
              className="rounded-lg p-2 text-[#1B2A4A]/40 transition-colors hover:bg-[#FFF5E6] hover:text-[#1B2A4A]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label
                htmlFor="item"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                Produto
              </label>
              <input
                id="item"
                value={form.item}
                onChange={(e) => setForm((prev) => ({ ...prev, item: e.target.value }))}
                placeholder="Nome do item"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>
            <div>
              <label
                htmlFor="quantidade_disponivel"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                Quantidade
              </label>
              <input
                id="quantidade_disponivel"
                value={form.quantidade_disponivel}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    quantidade_disponivel: e.target.value,
                  }))
                }
                type="number"
                min="0"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>
            <div>
              <label
                htmlFor="valor"
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-[#1B2A4A]/40"
              >
                Valor
              </label>
              <input
                id="valor"
                value={form.valor}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    valor: e.target.value.replace(",", "."),
                  }))
                }
                type="text"
                inputMode="decimal"
                placeholder="0.00"
                required
                className="w-full rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
              />
            </div>
          </div>

          <div className="mt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={closeForm}
              className="rounded-xl border border-[#F5C451]/20 px-4 py-2.5 text-sm font-medium text-[#1B2A4A]/70 transition-colors hover:bg-[#FFF5E6]"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-4 py-2.5 text-sm font-bold text-[#1B2A4A] transition-all hover:bg-[#F5C451] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {editing ? "Salvar alterações" : "Cadastrar item"}
            </button>
          </div>
        </form>
      )}

      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="mb-6 flex items-center gap-3 rounded-xl border border-[#F5C451]/20 bg-white/80 px-4 py-3 focus-within:border-[#F5A623]/30 focus-within:ring-2 focus-within:ring-[#F5A623]/10 transition-all">
        <Search className="h-5 w-5 text-[#1B2A4A]/30" />
        <input
          type="text"
          placeholder="Pesquisar item..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 bg-transparent text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none"
        />
      </div>

      {selected && (
        <div className="mb-6 rounded-2xl border border-[#3BB5E8]/20 bg-[#3BB5E8]/5 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#3BB5E8]">
                Item selecionado
              </p>
              <h2 className="mt-1 text-lg font-semibold text-[#1B2A4A]">
                {selected.item}
              </h2>
              <p className="mt-1 text-sm text-[#1B2A4A]/60">
                Disponível: {selected.quantidade_disponivel}
              </p>
              <p className="text-sm text-[#1B2A4A]/60">
                Valor: {formatCurrency(selected.valor)}
              </p>
              <p className="text-sm text-[#1B2A4A]/40">ID #{selected.id}</p>
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

      {loading ? (
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-[#F5A623]" />
          <p className="mt-3 text-sm text-[#1B2A4A]/40">Carregando estoque...</p>
        </div>
      ) : filtered.length > 0 ? (
        <div className="overflow-hidden rounded-2xl border border-[#F5C451]/20 bg-white/80">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#F5C451]/10">
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Item
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Qtd. Disponível
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Valor
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F5C451]/10">
              {filtered.map((item) => (
                <tr
                  key={item.id}
                  className="transition-colors hover:bg-[#FFF5E6]/30"
                >
                  <td className="px-6 py-4 text-sm font-mono text-[#1B2A4A]/40">
                    #{item.id}
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-[#1B2A4A]">
                    {item.item}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                        item.quantidade_disponivel > 10
                          ? "bg-green-50 text-green-700"
                          : item.quantidade_disponivel > 0
                          ? "bg-amber-50 text-amber-700"
                          : "bg-red-50 text-red-700"
                      }`}
                    >
                      {item.quantidade_disponivel}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#1B2A4A]/60">
                    {formatCurrency(item.valor)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setSelected(item)}
                        className="rounded-lg p-2 text-[#3BB5E8]/60 hover:bg-[#3BB5E8]/10 hover:text-[#3BB5E8] transition-colors"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openEdit(item)}
                        className="rounded-lg p-2 text-[#F5A623]/60 hover:bg-[#F5A623]/10 hover:text-[#F5A623] transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => void handleDelete(item)}
                        className="rounded-lg p-2 text-[#E85B5B]/60 hover:bg-[#E85B5B]/10 hover:text-[#E85B5B] transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
          <PackageX className="mx-auto h-16 w-16 text-[#1B2A4A]/20" />
          <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
            {searchTerm ? "Nenhum item encontrado" : "Estoque vazio"}
          </h2>
          <p className="mt-2 text-sm text-[#1B2A4A]/40">
            {searchTerm
              ? `Nenhum resultado para "${searchTerm}"`
              : "Comece cadastrando os itens do cardápio."}
          </p>
        </div>
      )}
    </div>
  );
}
